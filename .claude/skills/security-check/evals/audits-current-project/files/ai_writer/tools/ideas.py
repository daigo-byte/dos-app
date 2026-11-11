import streamlit as st

from ai_writer import ui

KEY = "ideas"

KINDS = {
    "ブログ・記事のネタ": "書くべき記事ネタ。各ネタに想定読者と検索されそうなキーワードを添える",
    "文章の切り口・構成": "同じテーマを書くときの異なる切り口・構成パターン",
    "企画・コンテンツのアイデア": "実行可能な企画アイデア。各案に概要と実行の第一歩を添える",
    "例え話・具体例": "説明を分かりやすくする例え話や具体例",
    "反論・別の視点": "テーマに対する反論、見落としがちな視点、読者が抱く疑問",
}


def render() -> None:
    st.title("🧠 アイデア出し")
    st.caption("書くネタに困ったとき、切り口や企画を一緒にブレインストーミングします。")

    with st.form("ideas_form"):
        topic = st.text_area("テーマ・状況 *", height=120, placeholder="例: 30代エンジニア向けのキャリアブログを始めたい")
        c1, c2 = st.columns(2)
        kind = c1.selectbox("欲しいアイデア", list(KINDS))
        count = c2.slider("アイデアの数", 3, 20, 10)
        constraints = st.text_input("条件・制約（任意）", placeholder="例: 自分の実体験を活かせるもの / 低予算")
        submitted = st.form_submit_button("✨ アイデアを出す", type="primary")

    if submitted:
        if not topic.strip():
            st.warning("テーマ・状況を入力してください。")
        else:
            prompt = (
                f"次のテーマについて、{KINDS[kind]}を{count}個提案してください。\n"
                "ありきたりな案だけでなく、意外性のある案も混ぜてください。番号付きリストで、各案に一言の説明を付けてください。\n\n"
                f"# テーマ・状況\n{topic.strip()}\n\n"
                + (f"# 条件・制約\n{constraints.strip()}\n" if constraints.strip() else "")
            )
            ui.generate(KEY, f"{kind}: {topic.strip()[:20]}", prompt)

    ui.show_result(KEY)
