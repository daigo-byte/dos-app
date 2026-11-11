import streamlit as st

from ai_writer import ui


def render() -> None:
    st.title("👤 マイ設定")
    st.caption(
        "自分の情報や文体の好みを登録しておくと、すべてのツールの生成に反映されます。"
        "このPCの data/profile.json に保存されます。"
    )

    profile = ui.get_profile()
    with st.form("profile_form"):
        enabled = st.toggle("マイ設定を生成に反映する", value=profile.get("enabled", True))
        name = st.text_input(ui.PROFILE_FIELDS["name"], value=profile["name"], placeholder="例: 山田太郎")
        signature = st.text_area(
            ui.PROFILE_FIELDS["signature"] + "（メール作成の署名欄に自動で入ります）",
            value=profile["signature"],
            height=100,
            placeholder="例:\n山田太郎\n株式会社サンプル 開発部\nyamada@example.com",
        )
        about = st.text_area(
            ui.PROFILE_FIELDS["about"],
            value=profile["about"],
            height=100,
            placeholder="例: フリーランスのWebエンジニア。ブログでは技術とキャリアについて発信している。",
        )
        style = st.text_area(
            ui.PROFILE_FIELDS["style"],
            value=profile["style"],
            height=100,
            placeholder="例: 一文は短め。「〜させていただく」は多用しない。専門用語には簡単な補足を入れる。",
        )
        saved = st.form_submit_button("保存", type="primary")

    if saved:
        ui.save_profile(
            {"enabled": enabled, "name": name, "signature": signature, "about": about, "style": style}
        )
        st.success("保存しました。")

    with st.expander("AIに渡される内容を確認"):
        st.code(ui.with_profile("") or "（反映される情報はありません）", language=None, wrap_lines=True)
