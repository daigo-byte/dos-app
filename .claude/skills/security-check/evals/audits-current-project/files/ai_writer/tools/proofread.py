import streamlit as st

from ai_writer import ui

KEY = "proofread"

MODES = [
    "校正（誤字脱字・文法チェック）",
    "読みやすくリライト",
    "トーン・文体を変える",
    "文字数を調整する",
    "箇条書き ⇔ 文章を変換",
]


def render() -> None:
    st.title("🔍 校正・リライト")
    st.caption("誤字脱字のチェックから、読みやすさ改善・トーン変換・文字数調整まで行います。")

    mode = st.radio("やりたいこと", MODES, horizontal=True)

    with st.form("proofread_form"):
        text = st.text_area("対象の文章 *", height=260)
        option = ""
        if mode == "トーン・文体を変える":
            option = st.selectbox("変換後のトーン", ui.TONES + ["子どもにも分かるやさしい言葉", "熱量のあるセールス調"])
        elif mode == "文字数を調整する":
            option = str(st.number_input("目標の文字数", min_value=20, max_value=20000, value=300, step=50))
        elif mode == "箇条書き ⇔ 文章を変換":
            option = st.radio("変換の向き", ["文章 → 箇条書き", "箇条書き → 文章"], horizontal=True)
        elif mode == "読みやすくリライト":
            option = st.select_slider("変更の度合い", ["最小限", "標準", "大胆に"], value="標準")
        notes = st.text_input("補足の指示（任意）", placeholder="例: 専門用語はそのまま残して")
        submitted = st.form_submit_button("✨ 実行する", type="primary")

    if submitted:
        if not text.strip():
            st.warning("対象の文章を入力してください。")
        else:
            ui.generate(KEY, f"{mode.split('（')[0]}: {text.strip()[:20]}", _prompt(mode, option, notes, text))

    ui.show_result(KEY)


def _prompt(mode: str, option: str, notes: str, text: str) -> str:
    if mode.startswith("校正"):
        task = (
            "以下の文章を校正してください。文意や文体は変えず、誤字脱字・文法の誤り・表記ゆれ・不自然な表現だけを直してください。\n"
            "出力形式:\n"
            "1. `## 修正後の文章`: 修正を反映した全文\n"
            "2. `## 修正箇所`: | 修正前 | 修正後 | 理由 | の表（修正がなければ「修正箇所はありません」）"
        )
    elif mode.startswith("読みやすく"):
        task = (
            f"以下の文章を、意味を変えずに読みやすくリライトしてください（変更の度合い: {option}）。"
            "冗長な表現の削除、一文の長さの調整、論理の流れの整理を行ってください。\n"
            "出力形式: `## リライト後` に全文、`## 主な改善点` に箇条書きで3〜5点"
        )
    elif mode.startswith("トーン"):
        task = f"以下の文章の内容を保ったまま、トーン・文体を「{option}」に書き換えてください。書き換えた文章のみ出力してください。"
    elif mode.startswith("文字数"):
        task = (
            f"以下の文章を、重要な内容を保ったまま約{option}文字に調整してください（現在 {len(text.strip())} 文字）。"
            "調整後の文章のみを出力してください。"
        )
    else:
        task = (
            "以下の文章を、要点を漏らさず見やすい箇条書きに変換してください。"
            if option.startswith("文章")
            else "以下の箇条書きを、自然なつながりのある文章に変換してください。"
        )
    if notes.strip():
        task += f"\n補足の指示: {notes.strip()}"
    return f"{task}\n\n# 対象の文章\n```\n{text.strip()}\n```"
