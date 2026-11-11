from datetime import datetime

import streamlit as st

from ai_writer import ui


def render() -> None:
    st.title("🕘 生成履歴")
    st.caption("生成した結果はこのPCの data/history.json に保存され、再起動後も残ります（最新300件）。")

    ui._init_state()
    history: list[dict] = st.session_state["history"]
    if not history:
        st.info("まだ履歴はありません。各ツールで文章を生成するとここに表示されます。")
        return

    labels = sorted({ui.TOOL_LABELS.get(h["tool"], h["tool"]) for h in history})
    selected = st.multiselect("ツールで絞り込み", labels)
    query = st.text_input("キーワード検索")

    items = [
        h
        for h in history
        if (not selected or ui.TOOL_LABELS.get(h["tool"], h["tool"]) in selected)
        and (not query or query in h["title"] or query in h["text"])
    ]

    c1, c2 = st.columns(2)
    all_md = "\n\n---\n\n".join(f"# {h['title']}\n_{h['time']}_\n\n{h['text']}" for h in items)
    c1.download_button(
        f"⬇️ 表示中の{len(items)}件をまとめて保存",
        all_md,
        file_name=f"history_{datetime.now():%Y%m%d_%H%M}.md",
        mime="text/markdown",
        disabled=not items,
    )
    with c2.popover("🗑️ 履歴をすべて削除"):
        st.write(f"{len(history)}件の履歴を削除します。元に戻せません。")
        if st.button("削除する", type="primary"):
            st.session_state["history"] = []
            ui.save_history()
            st.rerun()

    for i, h in enumerate(items):
        label = ui.TOOL_LABELS.get(h["tool"], h["tool"])
        with st.expander(f"{h['time']}　{label}　{h['title']}"):
            preview, raw = st.tabs(["プレビュー", "コピー用テキスト"])
            preview.markdown(h["text"])
            raw.code(h["text"], language=None, wrap_lines=True)
            if st.button("この履歴を削除", key=f"del_{i}"):
                history.remove(h)
                ui.save_history()
                st.rerun()
