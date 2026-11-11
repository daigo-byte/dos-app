"""テスト共通設定: Gemini 呼び出しを差し替え、保存先を一時フォルダにする。"""

import pytest
import streamlit as st

from ai_writer import llm, storage


@pytest.fixture(autouse=True)
def data_dir(monkeypatch, tmp_path):
    """実際の data/ を汚さないよう、保存先を一時フォルダにする。"""
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path)
    monkeypatch.setenv("GEMINI_API_KEY", "dummy")
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    return tmp_path


@pytest.fixture(autouse=True)
def fake_llm(monkeypatch):
    """Gemini を呼ばずに、受け取った引数を記録して固定文を返す。"""
    calls: list[dict] = []

    def fake_stream(client, model, contents, system=None, temperature=0.7):
        calls.append({"model": model, "contents": contents, "system": system})
        yield "## 結果\n"
        yield f"turns={len(contents)} model={model}"

    monkeypatch.setattr(llm, "stream_text", fake_stream)
    monkeypatch.setattr(llm, "get_client", lambda api_key: object())
    monkeypatch.setattr(llm, "list_text_models", lambda client: ["gemini-3.7-flash", "gemini-3.6-flash"])
    st.cache_data.clear()
    st.cache_resource.clear()
    return calls
