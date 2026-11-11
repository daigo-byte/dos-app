import streamlit as st

from ai_writer import ui

KEY = "translate"

LANGUAGES = [
    "自動（日本語 ⇔ 英語）",
    "英語",
    "日本語",
    "中国語（簡体字）",
    "中国語（繁体字）",
    "韓国語",
    "スペイン語",
    "フランス語",
    "ドイツ語",
    "エストニア語",
]
STYLES = ["自然な意訳", "直訳寄り（原文に忠実）", "ビジネス・フォーマル", "カジュアル・会話調"]


def render() -> None:
    st.title("🌐 翻訳")
    st.caption("ニュアンスを保った自然な翻訳を行います。用途に合わせて訳し方を選べます。")

    with st.form("translate_form"):
        text = st.text_area("翻訳する文章 *", height=220)
        c1, c2 = st.columns(2)
        target = c1.selectbox("翻訳先の言語", LANGUAGES)
        style = c2.selectbox("訳し方", STYLES)
        explain = st.checkbox("重要な語句・ニュアンスの解説を付ける")
        context = st.text_input("用途・背景（任意）", placeholder="例: 海外の取引先に送るメール / 技術ドキュメント")
        submitted = st.form_submit_button("✨ 翻訳する", type="primary")

    if submitted:
        if not text.strip():
            st.warning("翻訳する文章を入力してください。")
        else:
            ui.generate(KEY, f"翻訳→{target}: {text.strip()[:20]}", _prompt(text, target, style, explain, context))

    ui.show_result(KEY)


def _prompt(text, target, style, explain, context) -> str:
    if target.startswith("自動"):
        target_rule = "原文が日本語なら英語に、それ以外の言語なら日本語に翻訳する"
    else:
        target_rule = f"{target}に翻訳する"
    rules = [
        target_rule,
        f"訳し方: {style}",
        "固有名詞・数値・URL・コードは正確に保つ",
        "Markdownや改行などの書式は原文に合わせる",
    ]
    if context.strip():
        rules.append(f"用途・背景: {context.strip()}（それにふさわしい語彙・敬語レベルを選ぶ）")
    if explain:
        rules.append("訳文の後に `## 解説` として、訳し分けた語句やニュアンスの違いを日本語で3〜5点解説する")
    else:
        rules.append("訳文のみを出力する")
    return "以下の文章を翻訳してください。\n\n# ルール\n" + "\n".join(f"- {r}" for r in rules) + f"\n\n# 原文\n```\n{text.strip()}\n```"
