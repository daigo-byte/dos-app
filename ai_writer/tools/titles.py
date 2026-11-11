import streamlit as st

from ai_writer import ui

KEY = "titles"

TARGETS = [
    "ブログ記事のタイトル",
    "YouTube動画のタイトル",
    "メールの件名",
    "商品・サービスのキャッチコピー",
    "広告の見出し",
    "プレゼン・資料のタイトル",
    "見出し（H2）",
]
TECHNIQUES = ["数字を入れる", "疑問形", "ベネフィットを明示", "意外性・逆説", "限定性・緊急性", "ターゲットを呼びかけ", "短く言い切る"]


def render() -> None:
    st.title("💡 タイトル・キャッチコピー")
    st.caption("記事タイトル・メール件名・キャッチコピーなどを、狙いの解説付きで大量に提案します。")

    with st.form("titles_form"):
        target = st.selectbox("作りたいもの", TARGETS)
        description = st.text_area(
            "内容・伝えたいこと *",
            height=140,
            placeholder="例: 在宅ワークで集中力が続かない人向けに、すぐ試せる7つの習慣を紹介する記事",
        )
        c1, c2 = st.columns(2)
        audience = c1.text_input("ターゲット（任意）", placeholder="例: 20〜30代の会社員")
        keyword = c2.text_input("必ず入れたい言葉（任意）", placeholder="例: 在宅ワーク")
        techniques = st.multiselect("使いたいテクニック（任意）", TECHNIQUES)
        c3, c4 = st.columns(2)
        count = c3.slider("案の数", 5, 20, 10)
        max_len = c4.number_input("最大文字数（0 = 指定なし）", 0, 200, 0, step=5)
        submitted = st.form_submit_button("✨ 案を出す", type="primary")

    if submitted:
        if not description.strip():
            st.warning("内容・伝えたいことを入力してください。")
        else:
            ui.generate(KEY, f"{target}: {description.strip()[:20]}", _prompt(target, description, audience, keyword, techniques, count, max_len))

    ui.show_result(KEY)


def _prompt(target, description, audience, keyword, techniques, count, max_len) -> str:
    rules = [
        ui.bullet("ターゲット", audience),
        ui.bullet("必ず入れる言葉", keyword),
        ui.bullet("使うテクニック", "、".join(techniques), "バランスよく様々な切り口で"),
        ui.bullet("最大文字数", f"{max_len}文字以内" if max_len else ""),
    ]
    return (
        f"以下の内容について「{target}」の案を{count}個作成してください。\n\n"
        f"# 内容\n{description.strip()}\n\n# 条件\n" + "\n".join(rules) + "\n\n"
        "# 出力形式\n"
        "| No | 案 | 文字数 | 狙い・使ったテクニック | の表で出力し、表の後に `## おすすめ TOP3` として理由付きで3つ選んでください。"
    )
