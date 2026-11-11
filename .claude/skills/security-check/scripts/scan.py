"""Python / Streamlit / LLM API アプリ向けの機械的セキュリティスキャナ（標準ライブラリのみ）。

使い方:
    python scan.py [プロジェクトのパス] [--format markdown|json]

検出内容は「候補」。最終判断はコードを読んで行うこと（SKILL.md 参照）。
見つかった秘密情報は先頭だけ残してマスクして表示する。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    tomllib = None

SKIP_DIRS = {
    ".git", ".venv", "venv", "env", "node_modules", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "dist", "build", ".idea", ".vscode",
}  # fmt: skip
# スキル自身（検出パターンを含む）はスキャンしない
SKIP_PATH_PARTS = {("skills", "security-check")}
TEXT_EXT = {
    ".py", ".toml", ".cfg", ".ini", ".json", ".yaml", ".yml", ".txt", ".md", ".bat", ".cmd",
    ".ps1", ".sh", ".env", ".js", ".ts", ".html", ".example",
}  # fmt: skip
MAX_FILE_BYTES = 2_000_000

SECRET_PATTERNS = [
    ("Google / Gemini APIキー", re.compile(r"AIza[0-9A-Za-z_\-]{35}")),
    ("Anthropic APIキー", re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")),
    ("OpenAI APIキー", re.compile(r"sk-(?!ant-)(?:proj-)?[A-Za-z0-9_\-]{20,}")),
    ("AWS アクセスキー", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("GitHub トークン", re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}")),
    ("秘密鍵", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
]
GENERIC_SECRET = re.compile(
    r"""(?i)\b(api[_-]?key|secret|token|password|passwd)\b\s*[:=]\s*["']([^"'\s]{12,})["']"""
)
PLACEHOLDER_HINT = re.compile(r"(?i)(xxx|your|dummy|example|sample|placeholder|test|<|\.\.\.|\*\*\*)")

CODE_PATTERNS = [
    ("高", "危険なHTML描画", re.compile(r"unsafe_allow_html\s*=\s*True"),
     "LLM出力やユーザー入力をHTMLとして描画するとスクリプト注入（XSS）の恐れ。描画する値の出どころを確認する"),
    ("高", "危険なHTML描画", re.compile(r"components\.v1\.html|components\.html\("),
     "任意HTML/JSの埋め込み。LLM出力・ユーザー入力が流れ込まないか確認する"),
    ("高", "任意コード実行", re.compile(r"(?<![\w.])(eval|exec)\s*\("), "文字列をコードとして実行している"),
    ("高", "安全でない逆シリアライズ", re.compile(r"pickle\.loads?\(|yaml\.load\((?![^)]*SafeLoader)"),
     "信頼できないデータを読み込むと任意コード実行の恐れ"),
    ("高", "シェル実行", re.compile(r"shell\s*=\s*True|os\.system\(|os\.popen\("),
     "外部入力が混ざるとコマンド注入の恐れ"),
    ("中", "TLS検証の無効化", re.compile(r"verify\s*=\s*False"), "通信の盗聴・改ざんを検知できなくなる"),
    ("中", "秘密情報の出力", re.compile(r"(?i)(print|st\.(write|text|code|markdown|json|info|error|caption)|log\w*\.\w+)\s*\(.*(api_?key|secret|token|password)"),
     "APIキー等を画面・ログに出している可能性"),
    ("中", "URLへの秘密情報", re.compile(r"(?i)query_params.*(api_?key|token)|(api_?key|token).*query_params"),
     "URLに載った秘密情報は履歴・ログに残る"),
]  # fmt: skip

SENSITIVE_TRACKED = re.compile(r"(^|/)(\.env(\..*)?|data/.*|.*\.pem|.*\.key|secrets\.toml|profile\.json|history\.json)$")
SAFE_ENV_NAMES = {".env.example", ".env.sample", ".env.template"}
LOCAL_ADDRESSES = {"localhost", "127.0.0.1", "::1"}


@dataclass
class Finding:
    severity: str
    category: str
    message: str
    file: str = ""
    line: int = 0
    evidence: str = ""


@dataclass
class Report:
    root: str
    findings: list[Finding] = field(default_factory=list)
    passed: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)

    def add(self, *args, **kwargs) -> None:
        self.findings.append(Finding(*args, **kwargs))


def mask(secret: str) -> str:
    return secret[:6] + "*" * 6 + f"（{len(secret)}文字）" if len(secret) > 8 else "***"


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def iter_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        parts = Path(dirpath).relative_to(root).parts
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        if any(all(p in parts for p in skip) for skip in SKIP_PATH_PARTS) or "data" in parts[:1]:
            continue
        for name in filenames:
            path = Path(dirpath) / name
            if (path.suffix.lower() in TEXT_EXT or name.startswith(".env")) and path.stat().st_size < MAX_FILE_BYTES:
                yield path


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="cp932", errors="replace")


def git(root: Path, *args: str) -> str | None:
    if not (root / ".git").exists() or not shutil.which("git"):
        return None
    try:
        out = subprocess.run(["git", "-C", str(root), *args], capture_output=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return out.stdout.decode("utf-8", errors="replace") if out.returncode == 0 else None


def is_ignored(root: Path, relpath: str) -> bool | None:
    """git があれば check-ignore、無ければ .gitignore を簡易解析。"""
    if (root / ".git").exists() and shutil.which("git"):
        # --no-index: 追跡済みファイルでも .gitignore のルールで判定する
        r = subprocess.run(["git", "-C", str(root), "check-ignore", "-q", "--no-index", relpath], capture_output=True)
        return r.returncode == 0
    gi = root / ".gitignore"
    if not gi.exists():
        return None
    target = relpath.rstrip("/")
    for raw in read(gi).splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("!"):
            continue
        pat = line.strip("/")
        if pat == target or pat == target.split("/")[0] or (pat.startswith("*") and target.endswith(pat[1:])):
            return True
    return False


# ---------------------------------------------------------------------------
def check_secrets(root: Path, rep: Report) -> None:
    hits = 0
    for path in iter_files(root):
        name = path.name
        is_env = name.startswith(".env") and name not in SAFE_ENV_NAMES
        for lineno, line in enumerate(read(path).splitlines(), 1):
            for label, pat in SECRET_PATTERNS:
                for m in pat.finditer(line):
                    hits += 1
                    if is_env:
                        continue  # .env にあるのは正しい置き場所。git 管理の有無は別チェック
                    rep.add("重大", "秘密情報のハードコード", f"{label}らしき文字列がソースに直接書かれている",
                            rel(path, root), lineno, mask(m.group(0)))
            if path.suffix == ".py":
                for m in GENERIC_SECRET.finditer(line):
                    value = m.group(2)
                    if not PLACEHOLDER_HINT.search(value) and not value.startswith(("os.", "st.")):
                        rep.add("高", "秘密情報のハードコード", f"`{m.group(1)}` に固定値が代入されている",
                                rel(path, root), lineno, mask(value))
    if not any(f.category == "秘密情報のハードコード" for f in rep.findings):
        rep.passed.append("ソースコード・設定ファイルにAPIキー等のハードコードは見つからない")


def check_gitignore(root: Path, rep: Report) -> None:
    targets = {".env": "APIキー", "data/": "履歴・プロフィール等の個人データ", ".venv/": "仮想環境"}
    ok = True
    for target, what in targets.items():
        exists = (root / target.rstrip("/")).exists()
        ignored = is_ignored(root, target.rstrip("/") + ("/x" if target.endswith("/") else ""))
        if ignored is None:
            rep.add("中", "Git除外設定", ".gitignore が無い。git 管理を始めると秘密情報・個人データがコミットされる恐れ", ".gitignore")
            return
        if not ignored:
            ok = False
            sev = "高" if target != ".venv/" and exists else "中"
            rep.add(sev, "Git除外設定", f"`{target}`（{what}）が .gitignore で除外されていない", ".gitignore")
    if ok:
        rep.passed.append(".env / data/ / .venv/ は .gitignore で除外されている")


def check_git(root: Path, rep: Report) -> None:
    files = git(root, "ls-files")
    if files is None:
        rep.skipped.append("Git 管理外のため、コミット済みファイル・履歴の秘密情報チェックは対象外")
        return
    tracked = [f for f in files.splitlines() if SENSITIVE_TRACKED.search(f) and Path(f).name not in SAFE_ENV_NAMES]
    for f in tracked:
        rep.add("重大" if ".env" in f else "高", "コミット済みの機密ファイル",
                "Gitで管理されている（リポジトリを共有・公開すると漏れる）。除外後も履歴に残る", f)
    log = git(root, "log", "--all", "-p", "--no-color", "-U0") or ""
    leaked = set()
    for label, pat in SECRET_PATTERNS:
        for m in pat.finditer(log):
            leaked.add((label, m.group(0)))
    for label, secret in sorted(leaked):
        rep.add("重大", "Git履歴の秘密情報", f"{label}がGit履歴に含まれている。ファイル削除では消えないため、キーの無効化・再発行が必要",
                "(git history)", 0, mask(secret))
    if not tracked and not leaked:
        rep.passed.append("Git 管理下のファイル・履歴に機密ファイルや秘密情報は見つからない")


def _streamlit_configs(root: Path) -> list[Path]:
    paths = [root / ".streamlit" / "config.toml", Path.home() / ".streamlit" / "config.toml"]
    return [p for p in paths if p.exists()]


def check_streamlit(root: Path, rep: Report) -> None:
    if not any("streamlit" in read(p) for p in root.glob("*.py")) and not (root / ".streamlit").exists():
        rep.skipped.append("Streamlit アプリではないため、サーバー設定チェックは対象外")
        return

    address = None
    sources = []
    for cfg in _streamlit_configs(root):
        if tomllib is None:
            break
        try:
            data = tomllib.loads(read(cfg))
        except Exception:  # noqa: BLE001
            continue
        server = data.get("server", {})
        where = str(cfg) if not cfg.is_relative_to(root) else rel(cfg, root)
        if "address" in server:
            address = server["address"]
            sources.append(where)
        if server.get("enableXsrfProtection") is False:
            rep.add("中", "Streamlit設定", "XSRF保護が無効（enableXsrfProtection = false）", where)
        if server.get("enableCORS") is False:
            rep.add("中", "Streamlit設定", "CORS保護が無効（enableCORS = false）", where)
        if int(server.get("maxUploadSize", 200)) > 200:
            rep.add("低", "Streamlit設定", f"アップロード上限が大きい（maxUploadSize = {server['maxUploadSize']}MB）", where)

    launch_re = re.compile(r"--server\.address[ =]+[\"']?([\w.:\-]+)")
    for path in iter_files(root):
        if path.suffix.lower() in {".bat", ".cmd", ".ps1", ".sh", ".json", ".toml", ".py"} or path.name == "Procfile":
            for lineno, line in enumerate(read(path).splitlines(), 1):
                m = launch_re.search(line)
                if m:
                    address = m.group(1)
                    sources.append(f"{rel(path, root)}:{lineno}")

    if address is None:
        rep.add("高", "ネットワーク公開", "server.address が未設定のため、Streamlit は全ネットワークインターフェースで待ち受ける。"
                "同じWi-Fi/LANの他人が認証なしでアプリを使え、APIキー（課金）と履歴・プロフィールにアクセスできる",
                ".streamlit/config.toml（未作成）")
    elif address not in LOCAL_ADDRESSES:
        rep.add("高", "ネットワーク公開", f"server.address = {address} で外部から接続可能。認証のないアプリでは危険", ", ".join(sources))
    else:
        rep.passed.append(f"Streamlit は {address} のみで待ち受け（{', '.join(sources)}）")


def check_code(root: Path, rep: Report) -> None:
    count = 0
    for path in iter_files(root):
        if path.suffix != ".py" or "tests" in path.parts:
            continue
        for lineno, line in enumerate(read(path).splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for sev, cat, pat, why in CODE_PATTERNS:
                if pat.search(line):
                    count += 1
                    rep.add(sev, cat, why, rel(path, root), lineno, stripped[:120])
    if not count:
        rep.passed.append("危険な関数・設定（unsafe_allow_html, eval/exec, pickle, shell=True, verify=False 等）は使われていない")


def check_dependencies(root: Path, rep: Report) -> None:
    reqs = sorted(root.glob("requirements*.txt"))
    unpinned = []
    for req in reqs:
        for line in read(req).splitlines():
            line = line.split("#")[0].strip()
            if line and not line.startswith("-") and "==" not in line:
                unpinned.append(line)
    if unpinned:
        rep.add("低", "依存関係", "バージョンが固定されていない（再インストール時に未検証の版が入る）: " + ", ".join(unpinned),
                ", ".join(rel(r, root) for r in reqs))
    venv_py = next((p for p in [root / ".venv" / "Scripts" / "python.exe", root / ".venv" / "bin" / "python"] if p.exists()), None)
    has_audit = shutil.which("pip-audit") or (venv_py and (venv_py.parent / ("pip-audit.exe" if os.name == "nt" else "pip-audit")).exists())
    if has_audit:
        rep.skipped.append("pip-audit が利用可能。既知の脆弱性チェックは SKILL.md の手順で別途実行する")
    else:
        rep.skipped.append("pip-audit が未インストールのため、依存パッケージの既知の脆弱性（CVE）は未確認")


# ---------------------------------------------------------------------------
SEV_ORDER = {"重大": 0, "高": 1, "中": 2, "低": 3, "情報": 4}


def to_markdown(rep: Report) -> str:
    rep.findings.sort(key=lambda f: (SEV_ORDER.get(f.severity, 9), f.category, f.file, f.line))
    counts = {s: sum(f.severity == s for f in rep.findings) for s in SEV_ORDER}
    out = [f"# 機械スキャン結果: {rep.root}", "",
           "検出数: " + " / ".join(f"{s} {n}" for s, n in counts.items() if n) if rep.findings else "検出なし", ""]
    if rep.findings:
        out += ["| # | 重要度 | 分類 | 場所 | 内容 | 根拠 |", "|---|---|---|---|---|---|"]
        for i, f in enumerate(rep.findings, 1):
            loc = f"{f.file}:{f.line}" if f.line else f.file
            evidence = f.evidence.replace("|", "\\|")
            out.append(f"| {i} | {f.severity} | {f.category} | `{loc}` | {f.message} | {evidence} |")
    out += ["", "## 問題なし"] + [f"- {p}" for p in rep.passed]
    out += ["", "## 未確認・対象外"] + [f"- {s}" for s in rep.skipped]
    return "\n".join(out)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    rep = Report(root=str(root))
    for check in (check_secrets, check_gitignore, check_git, check_streamlit, check_code, check_dependencies):
        check(root, rep)

    if args.format == "json":
        print(json.dumps(asdict(rep), ensure_ascii=False, indent=2))
    else:
        print(to_markdown(rep))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
