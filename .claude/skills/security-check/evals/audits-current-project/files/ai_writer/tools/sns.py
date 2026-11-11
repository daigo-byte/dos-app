import streamlit as st

from ai_writer import ui

KEY = "sns"

PLATFORMS = {
    "X（旧Twitter）": "全角140文字以内。冒頭1行で興味を引く",
    "Instagram": "キャプションとして、改行と絵文字で読みやすく。最後にハッシュタグをまとめる",
    "Threads": "500文字以内。会話的で親しみやすく",
    "Facebook": "ストーリー性を持たせ、200〜400文字程度",
    "LinkedIn": "ビジネスパーソン向けに、学びや知見が伝わる構成。300〜800文字程度",
    "note / ブログ告知": "記事の要点と読むメリットを伝え、リンクへ誘導する告知文",
}
PURPOSES = ["お知らせ・告知", "ノウハウ・学びの共有", "商品・サービス紹介", "日常・体験談", "イベント集客", "問いかけ・エンゲージメント"]


def render() -> None:
    st.title("📣 SNS投稿作成")
    st.caption("伝えたい内容から、各SNSに最適化した投稿文を複数案作成します。")

    with st.form("sns_form"):
        content = st.text_area(
            "投稿したい内容 *",
            height=160,
            placeholder="例: 新しいブログ記事「在宅ワークで集中力を保つ7つの方法」を公開した。朝の散歩とポモドーロが特におすすめ。",
        )
        c1, c2 = st.columns(2)
        platform = c1.selectbox("プラットフォーム", list(PLATFORMS))
        purpose = c2.selectbox("投稿の目的", PURPOSES)
        tone = c1.selectbox("トーン", ["親しみやすい", "丁寧", "熱量高め", "知的・落ち着いた", "ユーモア"])
        count = c2.slider("案の数", 1, 5, 3)
        emoji = c1.select_slider("絵文字", ["なし", "控えめ", "多め"], value="控えめ")
        hashtags = c2.checkbox("ハッシュタグを付ける", value=True)
        url = st.text_input("リンクURL（任意）")
        submitted = st.form_submit_button("✨ 投稿文を作成", type="primary")

    if submitted:
        if not content.strip():
            st.warning("投稿したい内容を入力してください。")
        else:
            ui.generate(KEY, f"{platform}: {content.strip()[:20]}", _prompt(content, platform, purpose, tone, count, emoji, hashtags, url))

    ui.show_result(KEY)


def _prompt(content, platform, purpose, tone, count, emoji, hashtags, url) -> str:
    rules = [
        f"プラットフォーム: {platform}（{PLATFORMS[platform]}）",
        f"目的: {purpose}",
        f"トーン: {tone}",
        f"絵文字: {emoji}",
        "ハッシュタグ: " + ("内容に合うものを3〜6個" if hashtags else "付けない"),
        f"切り口（書き出し・構成）を変えた{count}案を `## 案1` のように見出しで分けて出力する",
        "各案の後に `（約N文字）` と文字数の目安を書く",
    ]
    if url.strip():
        rules.append(f"URL `{url.strip()}` を自然に含める")
    return "以下の内容でSNS投稿文を作成してください。\n\n# ルール\n" + "\n".join(f"- {r}" for r in rules) + f"\n\n# 投稿したい内容\n{content.strip()}"
