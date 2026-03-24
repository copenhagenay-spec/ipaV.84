"""
VERA memory system — persistent key/value store for things VERA learns about the user.
Stored in data/memory.json. All reads/writes go through this module.
"""

import json
import os

_MEMORY_PATH = os.path.join(os.path.dirname(__file__), "data", "memory.json")


def load_memory() -> dict:
    try:
        with open(_MEMORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_memory(data: dict) -> None:
    os.makedirs(os.path.dirname(_MEMORY_PATH), exist_ok=True)
    with open(_MEMORY_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def remember(key: str, value: str) -> None:
    """Save a key/value pair to memory."""
    data = load_memory()
    data[key.lower().strip()] = value.strip()
    save_memory(data)


def forget(key: str) -> bool:
    """Remove a key from memory. Returns True if it existed."""
    data = load_memory()
    key = key.lower().strip()
    if key in data:
        del data[key]
        save_memory(data)
        return True
    return False


def recall(key: str, default=None):
    """Look up a value by key. Returns default if not found."""
    return load_memory().get(key.lower().strip(), default)


def recall_all() -> dict:
    """Return the full memory dict."""
    return load_memory()
