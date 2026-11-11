import streamlit as st

from ai_writer import ui

KEY = "review"

KINDS = ["ブログ記事", "メール", "企画書・提案書", "自己PR・応募書類", "SNS投稿", "レポート・論文", "その他"]
STRICTNESS = {
    "やさしく": "良い点を多めに挙げ、改善点は重要なものに絞って前向きに伝える",
    "標準": "良い点と改善点をバランスよく率直に伝える",
    "辛口": "プロの編集者として遠慮なく厳しく指摘する。ただし人格ではなく文章を評価する",
}


def render() -> None:
    st.title("🧑‍🏫 文章レビュー")
    st.caption("書いた文章を第三者の目で評価し、点数と具体的な改善案を返します。公開・送信前のチェックに。")

    with st.form("review_form"):
        text = st.text_area("レビューしてほしい文章 *", height=260)
        c1, c2 = st.columns(2)
        kind = c1.selectbox("文章の種類", KINDS)
        strictness = c2.select_slider("レビューの厳しさ", list(STRICTNESS), value="標準")
        reader = c1.text_input("想定読者（任意）", placeholder="例: 採用担当者")
        goal = c2.text_input("文章の目的（任意）", placeholder="例: 面談につなげたい")
        submitted = st.form_submit_button("✨ レビューする", type="primary")

    if submitted:
        if not text.strip():
            st.warning("レビューしてほしい文章を入力してください。")
        else:
            prompt = (
                f"以下の{kind}をレビューしてください。\n\n# 条件\n"
                + "\n".join(
                    [
                        ui.bullet("想定読者", reader),
                        ui.bullet("文章の目的", goal),
                        ui.bullet("レビューの姿勢", STRICTNESS[strictness]),
                    ]
                )
                + "\n\n# 出力形式\n"
                "1. `## 総合評価`: 10点満点の点数と一言講評\n"
                "2. `## 観点別評価`: | 観点 | 点数(5点満点) | コメント | の表。観点は「分かりやすさ」「構成・論理」「説得力」「読者への配慮」「表現・文法」\n"
                "3. `## 良い点`: 箇条書きで2〜4点\n"
                "4. `## 改善点`: 重要な順に。各項目に `修正前` → `修正案` の具体的な書き換え例を付ける\n"
                "5. `## 読者が抱きそうな疑問`: 2〜3点\n\n"
                f"# 対象の文章\n```\n{text.strip()}\n```"
            )
            ui.generate(KEY, f"レビュー({kind}): {text.strip()[:20]}", prompt)

    ui.show_result(KEY)
