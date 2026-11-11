import streamlit as st

from ai_writer import ui

KEY = "notes"

OUTPUTS = {
    "議事録": (
        "議事録",
        "`## 概要`（日時・参加者・目的が分かれば記載）、`## 決定事項`、`## 議論のポイント`、"
        "`## ToDo`（| 担当 | 内容 | 期限 | の表。不明な項目は「未定」）、`## 次回までの課題` の構成",
    ),
    "日報・業務報告": (
        "日報",
        "`## 本日の業務`（箇条書き）、`## 成果・進捗`、`## 課題・懸念`、`## 明日の予定` の構成。そのまま上司に送れる丁寧な文体",
    ),
    "手順書・マニュアル": ("手順書", "目的、前提条件、番号付きの手順、注意点の構成。誰が読んでも再現できる粒度"),
    "ToDoリスト": ("ToDoリスト", "優先度（高・中・低）ごとに分けたチェックボックス形式（`- [ ]`）。期限があれば併記"),
    "読みやすい文章": ("文章", "話し言葉や断片的なメモを、内容を変えずに論理的で読みやすい文章に整える"),
}


def render() -> None:
    st.title("🗒️ メモ整形")
    st.caption("走り書きのメモ・音声入力の文字起こし・箇条書きを、議事録や日報などの体裁に整えます。")

    with st.form("notes_form"):
        memo = st.text_area(
            "メモ・文字起こし *",
            height=260,
            placeholder="例: 定例 田中さん 佐藤 新機能リリース来月15日で決定 テスト足りない→佐藤さん今週中に追加 デザイン修正はまだ…",
        )
        output = st.selectbox("整形後の形式", list(OUTPUTS))
        notes = st.text_input("補足の指示（任意）", placeholder="例: 社外向けなので固有の社内用語は言い換える")
        submitted = st.form_submit_button("✨ 整形する", type="primary")

    if submitted:
        if not memo.strip():
            st.warning("メモを入力してください。")
        else:
            name, spec = OUTPUTS[output]
            prompt = (
                f"以下のメモを{name}に整形してください。\n\n# ルール\n"
                f"- 形式: {spec}\n"
                "- メモに書かれていない事実を補わない。意味が読み取れない箇所は `【要確認: ...】` と明記する\n"
                "- 誤変換・フィラー（えー、あのー等）・重複は取り除く\n"
                + (f"- 補足: {notes.strip()}\n" if notes.strip() else "")
                + f"\n# メモ\n```\n{memo.strip()}\n```"
            )
            ui.generate(KEY, f"{output}: {memo.strip()[:20]}", prompt)

    ui.show_result(KEY)
