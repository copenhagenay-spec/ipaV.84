"""Config helpers for the standalone STT app."""

from __future__ import annotations

import json
import os
from typing import Any, Dict


def config_path() -> str:
    return os.path.join(os.path.dirname(__file__), "data", "config.json")


def load_config() -> Dict[str, Any]:
    path = config_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def save_config(data: Dict[str, Any]) -> None:
    path = config_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
