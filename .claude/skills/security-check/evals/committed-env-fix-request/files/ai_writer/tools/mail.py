import streamlit as st

from ai_writer import ui

KEY = "mail"

RELATIONS = ["取引先・顧客", "社内の上司", "社内の同僚・部下", "初めて連絡する相手", "友人・知人", "その他"]
STANCES = ["指定なし", "承諾・同意する", "お断りする", "質問・確認する", "お礼を伝える", "お詫びする", "日程を調整する"]
TONES = ["丁寧（標準的なビジネス）", "とても丁寧（かしこまった）", "簡潔・要点のみ", "フレンドリー"]


def render() -> None:
    st.title("✉️ メール作成・返信")
    st.caption("受け取ったメールへの返信文や、新規メールの文面を作成します。")

    mode = st.radio("作成するメール", ["返信を作成", "新規メールを作成"], horizontal=True)

    with st.form("mail_form"):
        received = ""
        if mode == "返信を作成":
            received = st.text_area("受け取ったメール本文 *", height=200, placeholder="ここに返信したいメールを貼り付け")
        points = st.text_area(
            "伝えたい要点" + (" *" if mode == "新規メールを作成" else ""),
            height=120,
            placeholder="例: 打ち合わせは来週火曜の14時なら参加可能。資料は前日までに送る。",
        )
        c1, c2 = st.columns(2)
        relation = c1.selectbox("相手との関係", RELATIONS)
        tone = c2.selectbox("トーン", TONES)
        stance = c1.selectbox("返信の方向性", STANCES) if mode == "返信を作成" else "指定なし"
        variations = c2.number_input("パターン数", 1, 3, 1)
        profile = ui.get_profile()
        sender = c1.text_area(
            "署名（マイ設定で既定値を登録できます）",
            value=profile["signature"] or profile["name"],
            height=68,
            placeholder="例: 山田太郎（株式会社サンプル）",
        )
        with_subject = c2.checkbox("件名も作成する", value=mode == "新規メールを作成")
        submitted = st.form_submit_button("✨ メールを作成", type="primary")

    if submitted:
        if mode == "返信を作成" and not received.strip():
            st.warning("受け取ったメール本文を入力してください。")
        elif mode == "新規メールを作成" and not points.strip():
            st.warning("伝えたい要点を入力してください。")
        else:
            title = "メール返信" if mode == "返信を作成" else f"新規メール: {points.strip()[:20]}"
            ui.generate(KEY, title, _prompt(mode, received, points, relation, tone, stance, variations, sender, with_subject))

    ui.show_result(KEY)


def _prompt(mode, received, points, relation, tone, stance, variations, sender, with_subject) -> str:
    task = "以下のメールへの返信文" if mode == "返信を作成" else "以下の条件で新規メール"
    lines = [
        ui.bullet("相手との関係", relation),
        ui.bullet("トーン", tone),
        ui.bullet("伝えたい要点", points, "受信メールの内容に適切に応答する"),
        ui.bullet("署名", sender, "署名欄は「（署名）」としておく"),
    ]
    if mode == "返信を作成":
        lines.insert(2, ui.bullet("返信の方向性", stance))
    rules = [
        "日本のビジネスメールの慣習（宛名・挨拶・結び）に沿う。ただしフレンドリーの場合は堅くしすぎない",
        "要点が一読で伝わるよう、段落を分けて簡潔に書く",
        "事実が不明な部分は勝手に作らず【 】で埋めるべき箇所を示す",
    ]
    if with_subject:
        rules.append("冒頭に `件名: ...` を付ける")
    if variations > 1:
        rules.append(f"トーンや言い回しを変えた{variations}パターンを `## パターン1` のように見出しで分けて出力する")
    body = f"{task}を作成してください。\n\n# 条件\n" + "\n".join(lines)
    body += "\n\n# ルール\n" + "\n".join(f"- {r}" for r in rules)
    if received:
        body += f"\n\n# 受け取ったメール\n```\n{received.strip()}\n```"
    return body
