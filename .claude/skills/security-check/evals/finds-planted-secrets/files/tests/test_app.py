import json

import pytest
from google.genai import errors
from streamlit.testing.v1 import AppTest

from ai_writer import storage, ui

TIMEOUT = 30
ALL_PAGES = [
    "blog", "mail", "sns", "summary", "proofread", "translate", "notes", "review",
    "titles", "ideas", "chat", "history", "settings",
]  # fmt: skip


def page(mod: str) -> AppTest:
    code = f"from ai_writer import ui\nfrom ai_writer.tools import {mod}\nui.render_sidebar()\n{mod}.render()\n"
    return AppTest.from_string(code, default_timeout=TIMEOUT)


def by_label(widgets, label):
    return next(w for w in widgets if w.label == label)


def test_app_entrypoint_runs():
    at = AppTest.from_file("../app.py", default_timeout=TIMEOUT).run()
    assert not at.exception


@pytest.mark.parametrize("mod", ALL_PAGES)
def test_page_renders(mod):
    at = page(mod).run()
    assert not at.exception


# (ツール, {text_area ラベル: 値}, {text_input ラベル: 値}, 送信ボタン)
GENERATE_CASES = [
    ("blog", {}, {"記事のテーマ *": "在宅ワーク"}, "✨ 記事を生成"),
    ("mail", {"受け取ったメール本文 *": "来週打ち合わせできますか？"}, {}, "✨ メールを作成"),
    ("sns", {"投稿したい内容 *": "新記事を公開"}, {}, "✨ 投稿文を作成"),
    ("summary", {"要約したい文章 *": "長い文章。" * 50}, {}, "✨ 要約する"),
    ("proofread", {"対象の文章 *": "こんにちわ。"}, {}, "✨ 実行する"),
    ("translate", {"翻訳する文章 *": "おはよう"}, {}, "✨ 翻訳する"),
    ("notes", {"メモ・文字起こし *": "定例 リリース来月15日"}, {}, "✨ 整形する"),
    ("review", {"レビューしてほしい文章 *": "私の強みは継続力です。"}, {}, "✨ レビューする"),
    ("titles", {"内容・伝えたいこと *": "集中力の記事"}, {}, "✨ 案を出す"),
    ("ideas", {"テーマ・状況 *": "キャリアブログ"}, {}, "✨ アイデアを出す"),
]


@pytest.mark.parametrize(("mod", "areas", "inputs", "submit"), GENERATE_CASES, ids=[c[0] for c in GENERATE_CASES])
def test_generate_refine_and_history(mod, areas, inputs, submit, fake_llm, data_dir):
    at = page(mod).run()
    for label, value in areas.items():
        by_label(at.text_area, label).input(value)
    for label, value in inputs.items():
        by_label(at.text_input, label).input(value)
    by_label(at.button, submit).click()
    at.run()
    assert not at.exception and not at.error
    assert "turns=1 model=gemini-3.7-flash" in " ".join(m.value for m in at.markdown)

    by_label(at.text_area, "🔁 この結果を修正する").input("短くして")
    by_label(at.button, "修正して再生成").click()
    at.run()
    assert "turns=3" in " ".join(m.value for m in at.markdown)

    saved = json.loads((data_dir / storage.HISTORY_FILE).read_text(encoding="utf-8"))
    assert [h["tool"] for h in saved] == [mod, mod]


def test_empty_input_shows_warning(fake_llm):
    at = page("blog").run()
    by_label(at.button, "✨ 記事を生成").click()
    at.run()
    assert at.warning and not fake_llm


def test_chat_keeps_conversation(fake_llm):
    at = page("chat").run()
    at.chat_input[0].set_value("こんにちは").run()
    at.chat_input[0].set_value("続けて").run()
    messages = at.session_state["chat_messages"]
    assert [m["role"] for m in messages] == ["user", "assistant", "user", "assistant"]
    assert len(fake_llm[-1]["contents"]) == 3


def test_history_loaded_from_disk(data_dir):
    storage.save(storage.HISTORY_FILE, [{"tool": "blog", "title": "保存済み", "text": "本文", "time": "2026-11-11 10:00"}])
    at = page("history").run()
    assert not at.exception
    assert any("保存済み" in e.label for e in at.expander)


def test_profile_saved_and_applied(fake_llm, data_dir):
    at = page("settings").run()
    by_label(at.text_input, ui.PROFILE_FIELDS["name"]).input("山田")
    by_label(at.text_area, ui.PROFILE_FIELDS["about"]).input("技術ブロガー")
    by_label(at.button, "保存").click()
    at.run()
    saved = json.loads((data_dir / storage.PROFILE_FILE).read_text(encoding="utf-8"))
    assert saved["about"] == "技術ブロガー"

    at = page("blog").run()
    by_label(at.text_input, "記事のテーマ *").input("在宅ワーク")
    by_label(at.button, "✨ 記事を生成").click()
    at.run()
    assert "技術ブロガー" in fake_llm[-1]["system"]


def test_profile_disabled_not_applied(fake_llm, data_dir):
    storage.save(storage.PROFILE_FILE, {"enabled": False, "about": "技術ブロガー"})
    at = page("ideas").run()
    by_label(at.text_area, "テーマ・状況 *").input("ネタ")
    by_label(at.button, "✨ アイデアを出す").click()
    at.run()
    assert "技術ブロガー" not in fake_llm[-1]["system"]


@pytest.mark.parametrize(
    ("code", "message", "expected"),
    [
        (400, "API key not valid. Please pass a valid API key.", "APIキーが無効"),
        (429, "Resource exhausted", "利用上限"),
        (503, "Unavailable", "一時的なエラー"),
    ],
)
def test_describe_error(code, message, expected):
    cls = errors.ServerError if code >= 500 else errors.ClientError
    e = cls(code, {"error": {"code": code, "message": message, "status": "X"}})
    assert expected in ui.describe_error(e)
