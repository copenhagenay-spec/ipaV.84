"""Steam library detection helpers."""

from __future__ import annotations

import glob
import os
import re
from typing import Dict, List


def _default_steam_roots() -> List[str]:
    roots = []
    pf86 = os.environ.get("PROGRAMFILES(X86)")
    pf = os.environ.get("PROGRAMFILES")
    if pf86:
        roots.append(os.path.join(pf86, "Steam"))
    if pf:
        roots.append(os.path.join(pf, "Steam"))
    return roots


def _parse_libraryfolders(path: str) -> List[str]:
    if not os.path.exists(path):
        return []
    try:
        text = open(path, "r", encoding="utf-8", errors="ignore").read()
    except Exception:
        return []
    paths = []
    for match in re.finditer(r'"path"\s+"([^"]+)"', text):
        p = match.group(1).replace("\\\\", "\\")
        paths.append(p)
    return paths


def _parse_appmanifest(path: str) -> Dict[str, str]:
    try:
        text = open(path, "r", encoding="utf-8", errors="ignore").read()
    except Exception:
        return {}
    appid_match = re.search(r'"appid"\s+"(\d+)"', text)
    name_match = re.search(r'"name"\s+"([^"]+)"', text)
    if not appid_match or not name_match:
        return {}
    return {"appid": appid_match.group(1), "name": name_match.group(1)}


def find_steam_apps() -> List[Dict[str, str]]:
    libs = []
    for root in _default_steam_roots():
        libfile = os.path.join(root, "steamapps", "libraryfolders.vdf")
        if os.path.exists(libfile):
            libs.append(root)
            libs.extend(_parse_libraryfolders(libfile))

    # Deduplicate
    libs = [p for p in dict.fromkeys(libs) if p]

    apps: List[Dict[str, str]] = []
    for lib in libs:
        steamapps = os.path.join(lib, "steamapps")
        for manifest in glob.glob(os.path.join(steamapps, "appmanifest_*.acf")):
            data = _parse_appmanifest(manifest)
            if data:
                apps.append(data)

    # Deduplicate by appid
    by_id = {}
    for app in apps:
        by_id[app["appid"]] = app
    return list(by_id.values())
