"""
VERA memory system.

Long-term: persistent key/value store written to data/memory.json.
Short-term: in-memory session context, resets on restart. Never written to disk.
"""

import json
import os
import time

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


# ---------------------------------------------------------------------------
# Short-term session memory (in-RAM only, resets on restart)
# ---------------------------------------------------------------------------

_SESSION: dict = {
    "start_time": time.time(),
    "mood": None,           # e.g. "tired", "hungry", "frustrated", "good"
    "mood_time": None,      # time.time() when mood was last set
    "activity": None,       # e.g. "star citizen", "working", "gaming"
    "last_topic": None,     # last thing the user mentioned
    "last_command": None,   # last command type that ran e.g. "open", "search"
    "last_app": None,       # last app opened by name
    "command_count": 0,
    "repeat_transcript": None,   # last transcript, for repeat detection
    "repeat_count": 0,           # how many times same transcript repeated
}


def set_session(key: str, value) -> None:
    """Set a session context value."""
    _SESSION[key] = value


def get_session(key: str, default=None):
    """Get a session context value."""
    return _SESSION.get(key, default)


def session_minutes() -> float:
    """How many minutes since VERA started this session."""
    return (time.time() - _SESSION["start_time"]) / 60


def increment_command_count() -> int:
    """Increment and return the session command count."""
    _SESSION["command_count"] = _SESSION.get("command_count", 0) + 1
    return _SESSION["command_count"]


def clear_session() -> None:
    """Reset session context (called on restart)."""
    _SESSION.clear()
    _SESSION.update({
        "start_time": time.time(),
        "mood": None,
        "mood_time": None,
        "activity": None,
        "last_topic": None,
        "last_command": None,
        "last_app": None,
        "command_count": 0,
        "repeat_transcript": None,
        "repeat_count": 0,
    })
