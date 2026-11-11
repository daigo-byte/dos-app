import streamlit as st

from ai_writer import ui

KEY = "blog"

EXTRAS = {
    "タイトル案（5つ）": "## タイトル案\n記事タイトルの別案を5つ、クリックしたくなる表現で。",
    "メタディスクリプション": "## メタディスクリプション\n検索結果に表示される120文字前後の説明文。",
    "FAQ（よくある質問）": "## よくある質問\n読者が抱きそうな質問と回答を3〜5個。",
    "まとめ・CTA": "本文の最後に、読者に次の行動を促すCTA（行動喚起）を入れる。",
    "表や箇条書きを活用": "比較や手順は表・箇条書きを使って読みやすくする。",
}


def render() -> None:
    st.title("📝 ブログ記事作成")
    st.caption("テーマとキーワードから、構成案またはSEOを意識したブログ記事を作成します。")

    with st.form("blog_form"):
        theme = st.text_input("記事のテーマ *", placeholder="例: 在宅ワークで集中力を保つ方法")
        keywords = st.text_input("SEOキーワード（カンマ区切り）", placeholder="例: 在宅ワーク, 集中力, コツ")
        c1, c2 = st.columns(2)
        reader = c1.text_input("想定読者", placeholder="例: 在宅勤務を始めたばかりの会社員")
        tone = c2.selectbox("文体・トーン", ui.TONES)
        length = c1.select_slider("本文の目安文字数", options=[1000, 2000, 3000, 5000, 8000], value=3000)
        mode = c2.radio("出力内容", ["構成案のみ", "本文まで作成"], index=1, horizontal=True)
        extras = st.multiselect(
            "追加で含める要素",
            list(EXTRAS),
            default=["メタディスクリプション", "まとめ・CTA", "表や箇条書きを活用"],
        )
        notes = st.text_area(
            "その他の指示・盛り込みたい内容",
            placeholder="例: 自分の体験談（朝の散歩で集中力が上がった）を入れたい",
            height=100,
        )
        submitted = st.form_submit_button("✨ 記事を生成", type="primary")

    if submitted:
        if not theme.strip():
            st.warning("記事のテーマを入力してください。")
        else:
            ui.generate(KEY, f"ブログ: {theme}", _prompt(theme, keywords, reader, tone, length, mode, extras, notes))

    ui.show_result(KEY)


def _prompt(theme, keywords, reader, tone, length, mode, extras, notes) -> str:
    conditions = "\n".join(
        [
            ui.bullet("テーマ", theme),
            ui.bullet("SEOキーワード", keywords) + "（タイトル・見出し・本文に自然に含める）",
            ui.bullet("想定読者", reader),
            ui.bullet("文体", tone),
            ui.bullet("本文の目安文字数", f"約{length}文字"),
            ui.bullet("その他の指示", notes),
        ]
    )
    if mode == "構成案のみ":
        output = (
            "ブログ記事の構成案を作成してください。本文は書かないでください。\n"
            "1. `# タイトル`\n"
            "2. `## 記事の狙い`: 読者の悩み・検索意図と、読み終えたときのゴール\n"
            "3. `## 見出し構成`: H2/H3の見出しと、各見出しで書く内容の要点（箇条書き）と目安文字数"
        )
    else:
        output = (
            "ブログ記事の本文を作成してください。\n"
            "1. `# 記事タイトル`\n"
            "2. 導入文: 読者の悩みに共感し、この記事を読むメリットを示す\n"
            "3. `##` / `###` の見出しで構成した本文。具体例・根拠・手順を交え、抽象論で終わらせない\n"
            "4. `## まとめ`"
        )
    extra_text = "\n".join(f"- {EXTRAS[e]}" for e in extras)
    return (
        f"以下の条件で{output}\n\n# 条件\n{conditions}\n\n"
        + (f"# 追加で含める要素（記事の後ろに付ける）\n{extra_text}\n" if extra_text else "")
    )
