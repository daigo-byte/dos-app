# 修正レシピ

レポートで承認された項目を直すときに参照する。プロジェクトの実際のコードに合わせて調整すること。

## 目次
1. ネットワーク公開（server.address 未設定・0.0.0.0）
2. APIキーのハードコード
3. Git にコミット済みの機密ファイル・履歴の秘密情報
4. .gitignore の不足
5. LLM出力の Markdown 画像による外部送信
6. unsafe_allow_html / components.html
7. Streamlit の保護設定（XSRF / CORS / アップロード上限）
8. 依存パッケージの固定と脆弱性確認

---

## 1. ネットワーク公開

`.streamlit/config.toml` を作成（既存なら `[server]` に追記）:

```toml
[server]
address = "localhost"
```

起動スクリプトに `--server.address 0.0.0.0` 等があれば削除するか `localhost` にする。
**影響**: スマホや別のPCからは開けなくなる。それが必要なら、認証の追加や VPN（Tailscale 等）経由を別途提案する。単にアドレスを戻すのは勧めない。

確認: 起動ログに `Network URL` が出ず `Local URL: http://localhost:8501` だけになる。

## 2. APIキーのハードコード

- 直書きを削除し `os.getenv("GEMINI_API_KEY")` で読む。値は `.env` へ（`.env.example` にはキー名だけ）。
- そのキーは既に漏れたものとして扱い、ユーザーに AI Studio で削除・再発行してもらう。

## 3. Git の機密ファイル・履歴

```bash
git rm --cached .env
git rm -r --cached data
```

その後 `.gitignore` に追加してコミット。ただしこれは**今後の追跡を止めるだけで、履歴には残る**。

- キーが履歴にある → キーの再発行が必須（これが本当の対策）。
- リポジトリが未公開なら、履歴の書き換え（`git filter-repo --path .env --invert-paths`）も選択肢。履歴を書き換えると共有済みのクローンと不整合になるため、同意を得てから。公開済みなら書き換えても既に複製されている前提で考える。

## 4. .gitignore

最低限:

```gitignore
.env
data/
.venv/
__pycache__/
.streamlit/secrets.toml
```

## 5. LLM出力の Markdown 画像

`ai_writer/ui.py` などで生成結果を描画する直前に、外部画像を無効化する。例:

```python
import re

_MD_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)]*)\)")

def neutralize_images(text: str) -> str:
    """Markdown 画像を「[画像: alt](url)」のリンク表記にして自動読み込みを防ぐ。"""
    return _MD_IMAGE.sub(lambda m: f"[画像: {m.group(1) or 'no alt'}]({m.group(2)})", text)
```

`st.markdown(res["text"])` → `st.markdown(neutralize_images(res["text"]))`。コピー用テキスト・保存内容は元のままでよい。ストリーミング中の `st.write_stream` も Markdown を描画するので、気になる場合はストリーミング表示を `st.text` 系にするか、表示前に同じ変換をかける。テストを追加する。

## 6. unsafe_allow_html

LLM出力・ユーザー入力が入る箇所では外す。装飾目的でどうしても必要なら、固定のHTMLだけに使い、可変部分は `html.escape()` する。

## 7. Streamlit の保護設定

`enableXsrfProtection = false` / `enableCORS = false` の行を削除（既定で有効）。`maxUploadSize` は用途に足りる値（例: 20）に。

## 8. 依存パッケージ

- 動作確認済みの版で固定: `.venv\Scripts\pip freeze > requirements.lock` を作り、README の手順をそれに合わせるか、`requirements.txt` を `==` で固定する。
- 脆弱性確認: `pip install pip-audit`（ダウンロードを伴うのでユーザーの了承を得る）→ `pip-audit -r requirements.txt`。
