import streamlit as st
from google.genai import types

from ai_writer import llm, ui

KEY = "summary"

FORMATS = {
    "箇条書き": "重要なポイントを箇条書きで",
    "3行要約": "全体をちょうど3行（3文）で",
    "段落（文章）": "流れのある文章（段落）で",
    "見出し付きレポート": "`##` 見出しで「概要」「主なポイント」「結論」に分けたレポート形式で",
    "一言で（TL;DR）": "一文（50文字程度）で核心だけを",
}
LENGTHS = {"短め": "できるだけ短く", "標準": "元の文章の1〜2割程度の分量で", "詳しめ": "重要な細部も残して詳しめに"}
EXTRAS = {
    "結論を最初に書く": "冒頭に `**結論:**` として最も重要な結論を1文で示す",
    "キーワードを抽出": "最後に `## キーワード` として重要語句を5〜10個挙げる",
    "アクション項目を抽出": "最後に `## やるべきこと` として読み手が取るべき行動・タスクを箇条書きにする",
    "疑問点・不明点を指摘": "最後に `## 不明点・確認したい点` として内容の曖昧な点を挙げる",
}


def render() -> None:
    st.title("📄 文章の要約")
    st.caption("長い文章・議事録・記事・PDFなどを、目的に合った形式で要約します。")

    source = st.radio("入力方法", ["テキストを貼り付け", "ファイルをアップロード（txt / md / pdf）"], horizontal=True)

    with st.form("summary_form"):
        text, uploaded = "", None
        if source == "テキストを貼り付け":
            text = st.text_area("要約したい文章 *", height=260)
        else:
            uploaded = st.file_uploader("ファイル *", type=["txt", "md", "pdf"])
        c1, c2 = st.columns(2)
        fmt = c1.selectbox("要約の形式", list(FORMATS))
        length = c2.select_slider("長さ", list(LENGTHS), value="標準")
        extras = st.multiselect("追加オプション", list(EXTRAS), default=["結論を最初に書く"])
        focus = st.text_input("特に注目してほしい観点（任意）", placeholder="例: 費用とスケジュールに関する部分")
        submitted = st.form_submit_button("✨ 要約する", type="primary")

    if submitted:
        parts = _source_parts(text, uploaded)
        if parts is None:
            st.warning("要約する文章またはファイルを入力してください。")
        else:
            name = uploaded.name if uploaded else text.strip()[:20]
            prompt = _prompt(fmt, length, extras, focus)
            ui.generate(KEY, f"要約: {name}", [llm.user_content(*parts, prompt)])

    ui.show_result(KEY)


def _source_parts(text: str, uploaded) -> list[str | types.Part] | None:
    if uploaded is not None:
        data = uploaded.getvalue()
        if uploaded.name.lower().endswith(".pdf"):
            return [types.Part.from_bytes(data=data, mime_type="application/pdf")]
        for enc in ("utf-8", "cp932"):
            try:
                return [f"# 対象の文章\n{data.decode(enc)}"]
            except UnicodeDecodeError:
                continue
        return [f"# 対象の文章\n{data.decode('utf-8', errors='replace')}"]
    if text.strip():
        return [f"# 対象の文章\n{text.strip()}"]
    return None


def _prompt(fmt, length, extras, focus) -> str:
    rules = [
        f"{FORMATS[fmt]}要約する",
        f"分量: {LENGTHS[length]}",
        "元の文章にない情報や推測を加えない",
        "数値・固有名詞・日付は正確に残す",
    ]
    if focus.strip():
        rules.append(f"特に「{focus.strip()}」に関する内容を重視する")
    rules += [EXTRAS[e] for e in extras]
    return "上の文章（または添付ファイル）を、以下のルールで日本語で要約してください。\n\n# ルール\n" + "\n".join(
        f"- {r}" for r in rules
    )
