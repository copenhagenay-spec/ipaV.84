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


_WELL_KNOWN_APPS = {
    "chrome": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ],
    "firefox": [
        r"C:\Program Files\Mozilla Firefox\firefox.exe",
        r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
    ],
    "edge": [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ],
    "opera gx": [
        os.path.join(os.path.expanduser("~"), r"AppData\Local\Programs\Opera GX\opera.exe"),
    ],
    "opera": [
        os.path.join(os.path.expanduser("~"), r"AppData\Local\Programs\Opera\opera.exe"),
    ],
    "notepad": [r"C:\Windows\notepad.exe"],
    "calculator": [r"C:\Windows\System32\calc.exe"],
    "steam": [
        r"C:\Program Files (x86)\Steam\steam.exe",
        r"C:\Program Files\Steam\steam.exe",
    ],
    "vlc": [
        r"C:\Program Files\VideoLAN\VLC\vlc.exe",
        r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
    ],
    "obs": [
        r"C:\Program Files\obs-studio\bin\64bit\obs64.exe",
    ],
    "task manager": [r"C:\Windows\System32\taskmgr.exe"],
    "file explorer": [r"C:\Windows\explorer.exe"],
}


def discover_apps(cfg: Dict[str, Any]) -> bool:
    """Check well-known install paths and add found apps to config. Returns True if config changed."""
    apps = cfg.setdefault("apps", {})
    changed = False
    for name, paths in _WELL_KNOWN_APPS.items():
        if name in apps:
            continue
        for path in paths:
            if os.path.exists(path):
                apps[name] = path
                changed = True
                break
    return changed
