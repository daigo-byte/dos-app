# ✍️ AI Writing Studio

Gemini API を使った個人用 AI ライティングツールです（Python + Streamlit）。
データベース・ログイン機能はなく、ローカルで起動してブラウザから使います。

## 機能

| カテゴリ | ツール | できること |
|---|---|---|
| 書く | 📝 ブログ記事作成 | テーマ・キーワード・読者・文字数から構成案 or 本文を作成（タイトル案・メタディスクリプション・FAQ も追加可） |
| | ✉️ メール作成・返信 | 受信メールへの返信、新規メールの作成。相手との関係・方向性・トーン・複数パターン対応 |
| | 📣 SNS投稿作成 | X / Instagram / Threads / Facebook / LinkedIn / note 向けの投稿文を複数案 |
| 整える | 📄 要約 | テキスト貼り付け or txt/md/pdf アップロード。箇条書き・3行・レポート形式など、アクション項目抽出も |
| | 🔍 校正・リライト | 誤字脱字チェック（修正箇所の表付き）、読みやすくリライト、トーン変換、文字数調整、箇条書き⇔文章 |
| | 🌐 翻訳 | 多言語翻訳。意訳／直訳／ビジネス／カジュアル、用途指定、ニュアンス解説付き |
| | 🗒️ メモ整形 | 走り書き・音声入力の文字起こしを、議事録・日報・手順書・ToDoリスト・文章に整える |
| | 🧑‍🏫 文章レビュー | 書いた文章を点数付きで評価し、修正前→修正案の具体的な改善点を提示（厳しさ調整可） |
| ひらめく | 💡 タイトル・キャッチコピー | 記事タイトル・メール件名・YouTube タイトル・コピーを狙い付きで大量提案＋おすすめTOP3 |
| | 🧠 アイデア出し | 記事ネタ・切り口・企画・例え話・反論の視点をブレスト |
| | 💬 フリーチャット | 役割設定（システムプロンプト）を変えられる自由チャット |
| 記録・設定 | 🕘 生成履歴 | 生成結果を一覧・検索・個別削除・まとめて Markdown 保存（再起動後も残る、最新300件） |
| | 👤 マイ設定 | 名前・署名・自分について・文体の好みを登録し、全ツールの生成に反映。署名はメール作成に自動入力 |

履歴とマイ設定は `data/` フォルダ（`history.json` / `profile.json`）に保存されます。DBは使いません。

全ツール共通:
- 結果はストリーミング表示
- 「コピー用テキスト」タブからワンクリックでコピー、Markdown でダウンロード
- **「この結果を修正する」** で追加の指示を出し、会話の流れを保ったまま再生成（例: 「この構成で本文を書いて」「3割短く」）
- サイドバーでモデルと創造性（temperature）を切り替え

## セットアップ

1. [Google AI Studio](https://aistudio.google.com/apikey) で Gemini APIキーを取得
2. `.env.example` を `.env` にコピーし、`GEMINI_API_KEY=` にキーを書く
   （`.env` を作らずに、アプリのサイドバーで入力してもOK）
3. 起動

```bash
run.bat
```

または手動で:

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\streamlit run app.py
```

ブラウザで http://localhost:8501 が開きます。

## テスト

Gemini を呼ばずに全ツールの画面・生成・修正・履歴保存・マイ設定を確認します（APIキー不要）。

```bash
.venv\Scripts\pip install -r requirements-dev.txt
.venv\Scripts\python -m pytest
```

## ファイル構成

```
app.py                  # エントリーポイント（ページ構成）
ai_writer/
  llm.py                # Gemini API クライアント・ストリーミング・モデル一覧
  ui.py                 # サイドバー、生成実行、結果表示・修正・履歴・マイ設定・エラー表示の共通処理
  storage.py            # data/ への JSON 保存
  tools/                # 各ツールの画面（render() とプロンプト組み立て）
tests/                  # pytest（Streamlit AppTest + Gemini のスタブ）
```

## ツールを追加するには

1. `ai_writer/tools/` に `render()` を持つモジュールを作る
   （フォーム → `ui.generate(KEY, タイトル, プロンプト)` → `ui.show_result(KEY)` の形）
2. `app.py` の `pages` に `st.Page(...)` を追加
3. 履歴の表示名を `ui.TOOL_LABELS` に追加
