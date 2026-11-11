# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 概要

個人用 AI ライティングツール「AI Writing Studio」。Python + Streamlit + Gemini API。DB・認証なし（意図的。追加しない）。永続化は `data/` 配下のローカル JSON のみ。UI 文言・プロンプトはすべて日本語。

## コマンド（Windows / PowerShell）

```bash
# 起動（.venv が無ければ作成して requirements をインストール）
run.bat

# 手動起動
.venv\Scripts\python -m streamlit run app.py

# テスト（APIキー不要。初回は requirements-dev.txt をインストール）
.venv\Scripts\python -m pytest
.venv\Scripts\python -m pytest tests/test_app.py -k blog     # 1件だけ
```

- APIキーは `.env` の `GEMINI_API_KEY`（`.env.example` 参照）またはサイドバー入力。`GEMINI_MODEL` で既定モデルを指定可。
- ブラウザプレビュー用の起動設定は `.claude/launch.json`（名前: `ai-writing-studio`, port 8501）。
- `data/history.json` / `data/profile.json` はユーザーの実データ。テストや作業で上書き・削除しない。

## アーキテクチャ

- **`app.py`**: `st.navigation` に各ツールの `render` 関数を `st.Page` として登録。関数名がすべて `render` なので `url_path` の明示が必須。`ui.render_sidebar()` はページ実行前に毎回呼ぶ（設定値をセッションに入れるため）。
- **`ai_writer/llm.py`**: Gemini 呼び出し専用で Streamlit 非依存。新 SDK `google-genai`（`from google import genai`）を使用。旧 `google.generativeai` は使わない。
- **`ai_writer/storage.py`**: `DATA_DIR` 配下への JSON 読み書き。`DATA_DIR` は呼び出し時に参照するので、テストでは monkeypatch で一時フォルダに差し替える。
- **`ai_writer/ui.py`**: 全ツール共通の処理。
  - 設定はセッションの `api_key` / `model` / `temperature` キー。履歴（`history`）とマイ設定（`profile`）は初回アクセス時に `data/` から読み込み、変更時に `save_history()` / `save_profile()` で書き戻す。
  - `generate(tool_key, title, contents, system)`: `st.empty()` 内でストリーミング表示 → 表示を消し、`session_state.results[tool_key]` に本文・**会話履歴（`types.Content` のリスト＋モデル応答）**・system を保存し、履歴に追加して保存。
  - `show_result(tool_key)`: 保存済み結果を描画。「この結果を修正する」は保存済み会話に追加指示を足してマルチターンで再生成するので、各ツールは修正機能を自前で持たない。
  - `stream()` が唯一の Gemini 呼び出し口で、ここで `with_profile()` によりマイ設定を system プロンプトに追記する（generate・修正・チャットすべてに効く）。保存される `system` は追記前のもの。
  - API エラーは `describe_error()` で日本語化（400 キー無効 / 403 / 404 モデルなし / 429 上限 / 5xx）。
- **`ai_writer/tools/*.py`**: 1ツール1モジュール。`KEY` 定数とフォーム → プロンプト組み立て → `ui.generate` → `ui.show_result` の型。例外は `chat.py`（独自の `chat_messages` で `ui.stream` を直接使う）、`history.py` / `settings.py`（生成なし）。
- モード切替で表示項目が変わるウィジェット（ラジオ等）は `st.form` の**外**に置く。フォーム内だと送信まで再描画されないため。
- 要約の PDF は文字抽出せず `types.Part.from_bytes(..., mime_type="application/pdf")` で Gemini に直接渡す。

## テストの仕組み

`tests/conftest.py` の autouse フィクスチャが、`llm.stream_text` / `get_client` / `list_text_models` をスタブに差し替え（`ui` は `llm.xxx` をモジュール属性経由で呼ぶので効く）、`storage.DATA_DIR` を `tmp_path` にし、Streamlit のキャッシュをクリアする。`fake_llm` フィクスチャは呼び出し引数（model / contents / system）のリストを返す。各ページは `AppTest.from_string` で `ui.render_sidebar(); <tool>.render()` を実行して検証する。ツールを追加したら `ALL_PAGES` と `GENERATE_CASES` にも追加する。

## 規約

- 共通 system プロンプト `ui.BASE_SYSTEM`: Markdown 出力・前置きや挨拶なし。プロンプトは「タスク文 + `# 条件` / `# ルール` の箇条書き + 対象テキスト」の形で、`ui.bullet()` で行を作る。
- モデル名はハードコードしない。サイドバーが API からモデル一覧を取得し、`GEMINI_MODEL` → `llm.PREFERRED_MODELS` → flash 系の順で既定を選ぶ。新モデルが出たら `PREFERRED_MODELS` / `FALLBACK_MODELS` を更新。

## ツールの追加手順

1. `ai_writer/tools/` に `render()` を持つモジュールを作成（上記の型に従う）
2. `app.py` の `pages` に `st.Page(..., url_path=...)` を追加
3. `ui.TOOL_LABELS` に履歴表示名を追加
4. `tests/test_app.py` の `ALL_PAGES` / `GENERATE_CASES` に追加
