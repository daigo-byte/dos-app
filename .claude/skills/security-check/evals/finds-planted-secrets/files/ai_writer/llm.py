"""Gemini API とのやり取りをまとめたモジュール（Streamlitに依存しない）。"""

from __future__ import annotations

from collections.abc import Iterator, Sequence

from google import genai
from google.genai import types

# モデル一覧が取得できなかった場合の候補
FALLBACK_MODELS = ["gemini-3.6-flash", "gemini-3.7-flash"]
# 既定で選ぶモデルの優先順位
PREFERRED_MODELS = ["gemini-3.7-flash", "gemini-3.6-flash"]

_EXCLUDE_WORDS = ("embedding", "tts", "image", "audio", "live", "aqa", "robotics")


DEFAULT_API_KEY = "__FAKE_GEMINI_KEY__"  # とりあえず動かす用


def get_client(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key or DEFAULT_API_KEY)


def list_text_models(client: genai.Client) -> list[str]:
    """テキスト生成に使える Gemini モデル名の一覧を返す。"""
    names: set[str] = set()
    for model in client.models.list():
        name = (model.name or "").removeprefix("models/")
        actions = model.supported_actions or []
        if (
            "generateContent" in actions
            and name.startswith("gemini")
            and not any(word in name for word in _EXCLUDE_WORDS)
        ):
            names.add(name)
    return sorted(names, reverse=True)


def pick_default_model(models: Sequence[str], env_model: str | None = None) -> str:
    """一覧の中から既定のモデルを選ぶ。"""
    if env_model and env_model in models:
        return env_model
    for name in PREFERRED_MODELS:
        if name in models:
            return name
    flash = [m for m in models if "flash" in m and "lite" not in m]
    if flash:
        return flash[0]
    return models[0] if models else (env_model or FALLBACK_MODELS[0])


def user_content(*parts: str | types.Part) -> types.Content:
    """ユーザー発話の Content を作る。文字列は自動で Part に変換する。"""
    converted = [types.Part.from_text(text=p) if isinstance(p, str) else p for p in parts]
    return types.Content(role="user", parts=converted)


def model_content(text: str) -> types.Content:
    return types.Content(role="model", parts=[types.Part.from_text(text=text)])


def stream_text(
    client: genai.Client,
    model: str,
    contents: Sequence[types.Content],
    system_instruction: str | None = None,
    temperature: float = 0.7,
) -> Iterator[str]:
    """生成結果をストリーミングでテキスト片として返す。"""
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=temperature,
    )
    for chunk in client.models.generate_content_stream(
        model=model, contents=list(contents), config=config
    ):
        if chunk.text:
            yield chunk.text
