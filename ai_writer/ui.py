"""共通UI部品: サイドバー設定・生成の実行・結果表示・履歴管理。"""

from __future__ import annotations

import os
from datetime import datetime

import streamlit as st
from google import genai
from google.genai import errors, types

from ai_writer import llm, storage

BASE_SYSTEM = (
    "あなたは日本語の文章に精通したプロのライター兼編集者です。"
    "ユーザーの指示と条件に忠実に、自然で読みやすく、具体的な文章を作成してください。"
    "出力はMarkdown形式とし、「承知しました」などの前置きや締めの挨拶は書かず、成果物だけを出力してください。"
)

TOOL_LABELS = {
    "blog": "📝 ブログ記事",
    "mail": "✉️ メール",
    "summary": "📄 要約",
    "proofread": "🔍 校正・リライト",
    "translate": "🌐 翻訳",
    "sns": "📣 SNS投稿",
    "titles": "💡 タイトル・コピー",
    "ideas": "🧠 アイデア出し",
    "notes": "🗒️ メモ整形",
    "review": "🧑‍🏫 文章レビュー",
}

PROFILE_FIELDS = {
    "name": "名前",
    "signature": "署名",
    "about": "自分について（立場・仕事・発信テーマ）",
    "style": "文体の好み・避けたい表現",
}

TONES = [
    "です・ます調（丁寧）",
    "だ・である調",
    "カジュアル・親しみやすい",
    "ビジネス・フォーマル",
    "専門的・論理的",
]


# ---------------------------------------------------------------------------
# サイドバー
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def _client(api_key: str) -> genai.Client:
    return llm.get_client(api_key)


@st.cache_data(ttl=3600, show_spinner=False)
def _models(api_key: str) -> list[str]:
    return llm.list_text_models(_client(api_key))


def render_sidebar() -> None:
    env_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
    env_model = os.getenv("GEMINI_MODEL")

    with st.sidebar:
        st.markdown("### ⚙️ 設定")
        typed_key = st.text_input(
            "Gemini APIキー",
            type="password",
            placeholder="設定済み（.env）" if env_key else "AIza...",
            help=".env に GEMINI_API_KEY を書いておくと入力不要になります。",
        )
        api_key = typed_key.strip() or env_key
        st.session_state["api_key"] = api_key
        if not api_key:
            st.warning("APIキーを入力してください。")
            st.link_button("APIキーを取得する", "https://aistudio.google.com/apikey")

        models: list[str] = []
        if api_key:
            try:
                models = _models(api_key)
            except Exception as e:  # noqa: BLE001
                st.caption(f"モデル一覧を取得できませんでした: {e}")
        if not models:
            models = llm.FALLBACK_MODELS
        default = llm.pick_default_model(models, env_model)
        if st.session_state.get("model") not in models:
            st.session_state["model"] = default
        st.selectbox("モデル", models, key="model")

        st.slider(
            "創造性（temperature）",
            0.0,
            2.0,
            value=0.7,
            step=0.1,
            key="temperature",
            help="低いほど正確・安定、高いほど自由で多様な表現になります。",
        )
        profile = get_profile()
        if profile.get("enabled") and any(profile.get(k, "").strip() for k in ("name", "about", "style")):
            st.caption("👤 マイ設定を反映中")
        st.divider()
        st.caption("履歴・マイ設定はこのPCの data/ フォルダに保存されます。")


# ---------------------------------------------------------------------------
# 生成
# ---------------------------------------------------------------------------
def _init_state() -> None:
    st.session_state.setdefault("results", {})
    if "history" not in st.session_state:
        st.session_state["history"] = storage.load(storage.HISTORY_FILE, [])


def save_history() -> None:
    history = st.session_state.get("history", [])[: storage.HISTORY_LIMIT]
    st.session_state["history"] = history
    storage.save(storage.HISTORY_FILE, history)


# ---------------------------------------------------------------------------
# マイ設定（プロフィール）
# ---------------------------------------------------------------------------
def get_profile() -> dict:
    if "profile" not in st.session_state:
        default = {key: "" for key in PROFILE_FIELDS} | {"enabled": True}
        st.session_state["profile"] = default | storage.load(storage.PROFILE_FILE, {})
    return st.session_state["profile"]


def save_profile(profile: dict) -> None:
    st.session_state["profile"] = profile
    storage.save(storage.PROFILE_FILE, profile)


def with_profile(system: str | None) -> str | None:
    """マイ設定が有効なら、system プロンプトにユーザー情報を追記する。"""
    profile = get_profile()
    lines = [
        f"- {label}: {profile[key].strip()}"
        for key, label in PROFILE_FIELDS.items()
        if key != "signature" and profile.get(key, "").strip()
    ]
    if not profile.get("enabled") or not lines:
        return system
    return (
        f"{system or ''}\n\n# 文章を依頼しているユーザーの情報\n"
        + "\n".join(lines)
        + "\nこの情報は、一人称で書く文章の視点や文体に反映してください。依頼内容と矛盾する場合は依頼内容を優先してください。"
    )


# ---------------------------------------------------------------------------
# 生成
# ---------------------------------------------------------------------------
def describe_error(e: Exception) -> str:
    """API エラーを分かりやすい日本語メッセージにする。"""
    if isinstance(e, errors.APIError):
        message = str(getattr(e, "message", "") or e)
        if e.code == 400 and "API key" in message:
            return "APIキーが無効です。サイドバーのAPIキーを確認してください。"
        if e.code in (401, 403):
            return "このAPIキーではアクセスが許可されていません。キーの権限・プロジェクト設定を確認してください。"
        if e.code == 404:
            return f"モデル「{st.session_state.get('model')}」が見つかりません。サイドバーで別のモデルを選んでください。"
        if e.code == 429:
            return "利用上限（レート制限）に達しました。少し待ってから再実行するか、別のモデルを選んでください。"
        if e.code >= 500:
            return "Gemini 側で一時的なエラーが発生しました。少し待ってから再実行してください。"
        return f"Gemini APIエラー（{e.code}）: {message}"
    return f"エラーが発生しました: {e}"


def get_client() -> genai.Client | None:
    api_key = st.session_state.get("api_key", "")
    if not api_key:
        st.error("サイドバーで Gemini APIキーを設定してください。")
        return None
    return _client(api_key)


def stream(contents: list[types.Content], system: str | None) -> str:
    """現在の設定でストリーミング生成し、全文を返す（例外はそのまま投げる）。"""
    client = get_client()
    if client is None:
        raise RuntimeError("APIキーが未設定です。")
    result = st.write_stream(
        llm.stream_text(
            client,
            st.session_state["model"],
            contents,
            with_profile(system),
            st.session_state.get("temperature", 0.7),
        )
    )
    return result if isinstance(result, str) else "".join(map(str, result))


def generate(
    tool_key: str,
    title: str,
    contents: str | list[types.Content],
    system: str = BASE_SYSTEM,
) -> str | None:
    """生成を実行し、結果をセッションと履歴に保存する。"""
    _init_state()
    if get_client() is None:
        return None
    if isinstance(contents, str):
        contents = [llm.user_content(contents)]

    placeholder = st.empty()
    try:
        with placeholder.container(border=True):
            st.caption(f"✍️ 生成中…（{st.session_state['model']}）")
            text = stream(contents, system)
    except Exception as e:  # noqa: BLE001
        placeholder.empty()
        st.error(describe_error(e))
        return None
    placeholder.empty()

    if not text.strip():
        st.warning("結果が空でした。条件を変えてもう一度お試しください。")
        return None

    st.session_state.results[tool_key] = {
        "title": title,
        "text": text,
        "contents": [*contents, llm.model_content(text)],
        "system": system,
    }
    st.session_state.history.insert(
        0,
        {
            "tool": tool_key,
            "title": title,
            "text": text,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        },
    )
    save_history()
    return text


def show_result(tool_key: str) -> None:
    """保存済みの生成結果を表示し、コピー・ダウンロード・追加修正を提供する。"""
    _init_state()
    res = st.session_state.results.get(tool_key)
    if not res:
        return

    st.divider()
    head, clear = st.columns([5, 1])
    head.subheader("生成結果")
    if clear.button("クリア", key=f"clear_{tool_key}"):
        del st.session_state.results[tool_key]
        st.rerun()

    preview, raw = st.tabs(["プレビュー", "コピー用テキスト"])
    with preview:
        st.markdown(res["text"])
    with raw:
        st.code(res["text"], language=None, wrap_lines=True)

    info, dl = st.columns([3, 2])
    info.caption(f"{len(res['text']):,} 文字 ・ 右上のアイコンでコピーできます（コピー用テキスト）")
    dl.download_button(
        "⬇️ Markdownで保存",
        res["text"],
        file_name=f"{tool_key}_{datetime.now():%Y%m%d_%H%M}.md",
        mime="text/markdown",
        key=f"dl_{tool_key}",
    )

    with st.form(f"refine_{tool_key}", clear_on_submit=True):
        instruction = st.text_area(
            "🔁 この結果を修正する",
            placeholder="例: もう少しカジュアルに / 3割短く / 2つ目の見出しを詳しく / この構成で本文を書いて",
            height=80,
        )
        submitted = st.form_submit_button("修正して再生成")
    if submitted and instruction.strip():
        contents = [*res["contents"], llm.user_content(instruction)]
        if generate(tool_key, f"{res['title']}（修正）", contents, res["system"]):
            st.rerun()


def bullet(label: str, value: str | None, default: str = "指定なし") -> str:
    """プロンプト用の「- ラベル: 値」行を作る。"""
    value = (value or "").strip()
    return f"- {label}: {value or default}"
