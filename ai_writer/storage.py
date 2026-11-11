"""ローカルJSONファイルへの保存（DBの代わり）。保存先は プロジェクト直下の data/ 。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
HISTORY_FILE = "history.json"
PROFILE_FILE = "profile.json"
HISTORY_LIMIT = 300


def load(name: str, default: Any) -> Any:
    path = DATA_DIR / name
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def save(name: str, data: Any) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / name
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)
