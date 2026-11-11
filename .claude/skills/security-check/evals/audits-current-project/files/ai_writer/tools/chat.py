import streamlit as st

from ai_writer import llm, ui

STATE = "chat_messages"
DEFAULT_SYSTEM = (
    "あなたは優秀な文章アシスタントです。ユーザーの文章作成・推敲・相談に、具体的かつ簡潔に答えてください。"
    "必要に応じてMarkdownを使ってください。"
)


def render() -> None:
    st.title("💬 フリーチャット")
    st.caption("決まった型に当てはまらない依頼は、ここで自由に相談できます。会話の流れを踏まえて回答します。")

    st.session_state.setdefault(STATE, [])
    messages: list[dict] = st.session_state[STATE]

    c1, c2 = st.columns([4, 1])
    with c1.expander("AIの役割設定（システムプロンプト）"):
        system = st.text_area("システムプロンプト", value=DEFAULT_SYSTEM, key="chat_system", label_visibility="collapsed")
    if c2.button("会話をリセット", disabled=not messages):
        messages.clear()
        st.rerun()

    for m in messages:
        with st.chat_message(m["role"]):
            st.markdown(m["text"])

    prompt = st.chat_input("メッセージを入力（例: この文章をもっと説得力のあるものにして…）")
    if not prompt:
        return

    messages.append({"role": "user", "text": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    contents = [
        llm.user_content(m["text"]) if m["role"] == "user" else llm.model_content(m["text"]) for m in messages
    ]
    with st.chat_message("assistant"):
        try:
            text = ui.stream(contents, system)
        except Exception as e:  # noqa: BLE001
            st.error(ui.describe_error(e))
            messages.pop()
            return
    messages.append({"role": "assistant", "text": text})
