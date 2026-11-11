"""AI Writing Studio - 個人用AIライティングツール（Streamlit + Gemini API）

起動: streamlit run app.py
"""

import streamlit as st
from dotenv import load_dotenv

from ai_writer import ui
from ai_writer.tools import (
    blog,
    chat,
    history,
    ideas,
    mail,
    notes,
    proofread,
    review,
    settings,
    sns,
    summary,
    titles,
    translate,
)

load_dotenv()

st.set_page_config(page_title="AI Writing Studio", page_icon="✍️", layout="centered")

pages = {
    "書く": [
        st.Page(blog.render, title="ブログ記事作成", icon="📝", url_path="blog", default=True),
        st.Page(mail.render, title="メール作成・返信", icon="✉️", url_path="mail"),
        st.Page(sns.render, title="SNS投稿作成", icon="📣", url_path="sns"),
    ],
    "整える": [
        st.Page(summary.render, title="要約", icon="📄", url_path="summary"),
        st.Page(proofread.render, title="校正・リライト", icon="🔍", url_path="proofread"),
        st.Page(translate.render, title="翻訳", icon="🌐", url_path="translate"),
        st.Page(notes.render, title="メモ整形", icon="🗒️", url_path="notes"),
        st.Page(review.render, title="文章レビュー", icon="🧑‍🏫", url_path="review"),
    ],
    "ひらめく": [
        st.Page(titles.render, title="タイトル・キャッチコピー", icon="💡", url_path="titles"),
        st.Page(ideas.render, title="アイデア出し", icon="🧠", url_path="ideas"),
        st.Page(chat.render, title="フリーチャット", icon="💬", url_path="chat"),
    ],
    "記録・設定": [
        st.Page(history.render, title="生成履歴", icon="🕘", url_path="history"),
        st.Page(settings.render, title="マイ設定", icon="👤", url_path="settings"),
    ],
}

nav = st.navigation(pages)
ui.render_sidebar()
nav.run()
