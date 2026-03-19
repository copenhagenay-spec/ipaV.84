"""Simple skills for the standalone assistant."""

from __future__ import annotations

import re
import difflib
import threading
import time
import os
from urllib.parse import quote_plus
import subprocess
import webbrowser
from urllib.parse import quote_plus

from config import load_config


def _confirm(prompt: str, allow_prompt: bool, confirm_fn=None) -> bool:
    cfg = load_config()
    if not cfg.get("confirm_actions", False):
        return True
    if confirm_fn is not None:
        try:
            return bool(confirm_fn(prompt))
        except Exception:
            return False
    if not allow_prompt:
        # Avoid blocking for input in background threads (hotkey/hold).
        return True
    try:
        reply = input(f"{prompt} [y/N]: ").strip().lower()
    except Exception:
        return False
    return reply in ("y", "yes")


def _run_command(command: str) -> None:
    subprocess.Popen(command, shell=True)

def _log_event(message: str) -> None:
    try:
        base_dir = os.path.dirname(__file__)
        logs_dir = os.path.join(base_dir, "data", "logs")
        os.makedirs(logs_dir, exist_ok=True)
        log_path = os.path.join(logs_dir, "assistant.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {message}\n")
    except Exception:
        pass

def _append_note(text: str) -> bool:
    try:
        notes_path = _notes_path()
        with open(notes_path, "a", encoding="utf-8") as f:
            f.write(_normalize_numbers_in_text(text.strip()) + "\n")
        print(f"Note saved: {text.strip()}")
        _log_event(f"NOTE_SAVED: {text.strip()}")
        return True
    except Exception as exc:
        print(f"Failed to save note: {exc}")
        _log_event(f"NOTE_SAVE_FAILED: {exc}")
        return False

def _notes_path() -> str:
    base_dir = os.path.dirname(__file__)
    notes_dir = os.path.join(base_dir, "data")
    os.makedirs(notes_dir, exist_ok=True)
    return os.path.join(notes_dir, "notes.txt")

def _open_notes() -> bool:
    try:
        path = _notes_path()
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write("")
        _run_command(f"notepad.exe \"{path}\"")
        _log_event(f"NOTES_OPENED: {path}")
        return True
    except Exception as exc:
        print(f"Failed to open notes: {exc}")
        _log_event(f"NOTES_OPEN_FAILED: {exc}")
        return False

def _list_notes(limit: int = 5) -> None:
    try:
        path = _notes_path()
        if not os.path.exists(path):
            print("No notes yet.")
            _log_event("NOTES_LIST: empty (file missing)")
            return
        with open(path, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f.readlines() if ln.strip()]
        if not lines:
            print("No notes yet.")
            _log_event("NOTES_LIST: empty")
            return
        print("Recent notes:")
        for note in lines[-limit:]:
            print(f"- {note}")
        _log_event(f"NOTES_LIST: {len(lines)}")
    except Exception as exc:
        print(f"Failed to list notes: {exc}")
        _log_event(f"NOTES_LIST_FAILED: {exc}")

def _delete_last_note() -> bool:
    try:
        notes_path = _notes_path()
        if not os.path.exists(notes_path):
            print("No notes file found.")
            _log_event("NOTE_DELETE: no file")
            return False
        with open(notes_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if not lines:
            print("No notes to delete.")
            _log_event("NOTE_DELETE: empty")
            return False
        lines.pop()
        with open(notes_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print("Deleted last note.")
        _log_event("NOTE_DELETED_LAST")
        return True
    except Exception as exc:
        print(f"Failed to delete note: {exc}")
        _log_event(f"NOTE_DELETE_FAILED: {exc}")
        return False

def _clear_notes() -> bool:
    try:
        notes_path = _notes_path()
        with open(notes_path, "w", encoding="utf-8") as f:
            f.write("")
        print("Cleared all notes.")
        _log_event("NOTES_CLEARED_ALL")
        return True
    except Exception as exc:
        print(f"Failed to clear notes: {exc}")
        _log_event(f"NOTES_CLEAR_FAILED: {exc}")
        return False

def _start_timer(seconds: int, label: str) -> None:
    def _alarm():
        try:
            time.sleep(seconds)
            try:
                import winsound  # type: ignore
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                winsound.Beep(880, 500)
                winsound.Beep(880, 500)
            except Exception:
                pass
            try:
                import tkinter as tk
                from tkinter import messagebox
                root = tk.Tk()
                root.withdraw()
                messagebox.showinfo("IPA Timer", f"Timer done: {label}")
                root.destroy()
            except Exception:
                print(f"Timer done: {label}")
        except Exception:
            pass

    threading.Thread(target=_alarm, daemon=True).start()

_NUM_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
}

_ORDINALS = {
    "first": 1,
    "second": 2,
    "third": 3,
    "fourth": 4,
    "fifth": 5,
    "sixth": 6,
    "seventh": 7,
    "eighth": 8,
    "ninth": 9,
    "tenth": 10,
    "eleventh": 11,
    "twelfth": 12,
    "thirteenth": 13,
    "fourteenth": 14,
    "fifteenth": 15,
    "sixteenth": 16,
    "seventeenth": 17,
    "eighteenth": 18,
    "nineteenth": 19,
    "twentieth": 20,
    "twenty first": 21,
    "twenty second": 22,
    "twenty third": 23,
    "twenty fourth": 24,
    "twenty fifth": 25,
    "twenty sixth": 26,
    "twenty seventh": 27,
    "twenty eighth": 28,
    "twenty ninth": 29,
    "thirtieth": 30,
    "thirty first": 31,
}

_MONTHS = {
    "january": "January",
    "february": "February",
    "march": "March",
    "april": "April",
    "may": "May",
    "june": "June",
    "july": "July",
    "august": "August",
    "september": "September",
    "october": "October",
    "november": "November",
    "december": "December",
}


def _word_to_num(word: str):
    return _NUM_WORDS.get(word.lower())

def _parse_year_words(text: str):
    t = text.lower().strip()
    # "two thousand and twenty six" -> 2026
    m = re.search(r"\btwo thousand( and)?\s+(.+)$", t)
    if m:
        tail = m.group(2).strip()
        parts = tail.split()
        total = 0
        for p in parts:
            if p in _NUM_WORDS:
                total += _NUM_WORDS[p]
        if total:
            return 2000 + total
    return None

def _normalize_numbers_in_text(text: str) -> str:
    t = text.strip()
    tl = t.lower()
    # Month + ordinal + year words
    for month_key, month_val in _MONTHS.items():
        if month_key in tl:
            # Try ordinal phrases (longest first)
            for ord_phrase, ord_num in sorted(_ORDINALS.items(), key=lambda x: -len(x[0])):
                if ord_phrase in tl:
                    year = _parse_year_words(tl)
                    if year:
                        return f"{month_val} {ord_num}, {year}"
    return t


def _parse_timer(text: str):
    # Examples: "set timer 5 minutes", "timer 10 sec", "set timer 1 hour"
    m = re.search(r"\b(set\s+a\s+timer|set\s+timer|timer)\s+(\d+|\w+)\s*(seconds?|secs?|minutes?|mins?|hours?|hrs?)?\b", text)
    if not m:
        return None
    raw = m.group(2)
    if raw.isdigit():
        value = int(raw)
    else:
        value = _word_to_num(raw)
        if value is None:
            return None
    unit = (m.group(3) or "seconds").lower()
    if unit.startswith("hour") or unit.startswith("hr"):
        seconds = value * 3600
        label = f"{value} hour(s)"
    elif unit.startswith("min"):
        seconds = value * 60
        label = f"{value} minute(s)"
    else:
        seconds = value
        label = f"{value} second(s)"
    return seconds, label

def _media_key(action: str) -> bool:
    try:
        from pynput import keyboard  # type: ignore
    except Exception:
        print("Missing dependency: pynput (needed for media keys).")
        return False
    keymap = {
        "play_pause": keyboard.Key.media_play_pause,
        "next": keyboard.Key.media_next,
        "previous": keyboard.Key.media_previous,
        "mute": keyboard.Key.media_volume_mute,
    }
    key = keymap.get(action)
    if not key:
        return False
    try:
        ctl = keyboard.Controller()
        ctl.press(key)
        ctl.release(key)
        return True
    except Exception as exc:
        print(f"Failed to send media key: {exc}")
        return False

def _youtube_search(query: str) -> bool:
    if not query:
        url = "https://www.youtube.com/"
    else:
        url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
    try:
        import webbrowser
        webbrowser.open(url)
        return True
    except Exception as exc:
        print(f"Failed to open browser: {exc}")
        return False


def _normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _get_spotify_keywords(cfg) -> list:
    raw = cfg.get("spotify_keywords")
    if isinstance(raw, list):
        keywords = [str(x).strip().lower() for x in raw if str(x).strip()]
    elif isinstance(raw, str) and raw.strip():
        keywords = [x.strip().lower() for x in raw.split(",") if x.strip()]
    else:
        # Default includes common mis-hears without being too broad.
        keywords = ["spotify", "spot if i", "spot ify", "spotty"]
    return keywords


def _has_keyword(text: str, keywords: list) -> bool:
    if not keywords:
        return False
    text_l = text.lower()
    tokens = [re.sub(r"[^a-z0-9]+", "", t) for t in text_l.split()]
    tokens = [t for t in tokens if t]
    norm_text = _normalize_text(text_l)
    for kw in keywords:
        if not kw:
            continue
        if kw in text_l:
            return True
        norm_kw = _normalize_text(kw)
        if norm_kw and norm_kw in norm_text:
            return True
        if tokens and norm_kw:
            match = difflib.get_close_matches(norm_kw, tokens, n=1, cutoff=0.75)
            if match:
                return True
    return False


def _normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _open_app(app_name: str, allow_prompt: bool, confirm_fn=None) -> bool:
    cfg = load_config()
    apps = cfg.get("apps", {})
    if not isinstance(apps, dict):
        apps = {}

    # Merge aliases into app map
    aliases = cfg.get("app_aliases", {})
    if isinstance(aliases, dict):
        for alias, target in aliases.items():
            if not isinstance(alias, str) or not isinstance(target, str):
                continue
            target_cmd = apps.get(target)
            if target_cmd:
                apps[alias] = target_cmd
    exact = apps.get(app_name)
    if exact:
        command = exact
    else:
        # Try normalized match
        norm_map = {_normalize_name(k): v for k, v in apps.items()}
        target = _normalize_name(app_name)
        command = norm_map.get(target)
        if not command and target:
            # Fuzzy match closest app name
            candidates = list(norm_map.keys())
            match = difflib.get_close_matches(target, candidates, n=1, cutoff=0.6)
            if match:
                command = norm_map.get(match[0])
    if not command:
        return False
    if not _confirm(f"Open app: {app_name}?", allow_prompt, confirm_fn=confirm_fn):
        return True
    try:
        _run_command(command)
    except Exception as exc:
        print(f"Failed to open app '{app_name}': {exc}")
    return True


def _web_search(query: str, allow_prompt: bool, confirm_fn=None) -> bool:
    cfg = load_config()
    template = cfg.get("search_engine", "https://www.google.com/search?q={query}")
    if "{query}" not in template:
        template = "https://www.google.com/search?q={query}"
    url = template.format(query=quote_plus(query))
    if not _confirm(f"Search the web for: {query}?", allow_prompt, confirm_fn=confirm_fn):
        return True
    try:
        webbrowser.open(url)
    except Exception as exc:
        print(f"Failed to open browser: {exc}")
    return True


def handle_transcript(text: str, allow_prompt: bool = True, confirm_fn=None) -> bool:
    """
    Try to match transcript to skills.
    Returns True if a skill handled it.
    """
    t = text.strip().lower()
    if not t:
        return False

    # Notes
    if re.search(r"\b(clear|delete|remove)\s+(all\s+)?notes\b", t):
        if confirm_fn and not confirm_fn("Clear all notes?"):
            return True
        _clear_notes()
        return True

    if re.search(r"\b(open|show)\s+notes?\b", t):
        _open_notes()
        return True

    if re.search(r"\b(list|show)\s+notes\b", t):
        _list_notes()
        return True

    if re.search(r"\b(delete|remove|undo)\s+(last\s+)?note\b", t):
        if confirm_fn and not confirm_fn("Delete last note?"):
            return True
        _delete_last_note()
        return True

    note_match = re.search(r"\b(note|notes|take a note|add note|remember)\b\s*(.+)?$", t)
    if note_match:
        note_text = (note_match.group(2) or "").strip()
        if not note_text:
            # Fallback: take everything after the first word "note/notes"
            parts = t.split(" ", 1)
            if len(parts) == 2:
                note_text = parts[1].strip()
        if not note_text and allow_prompt:
            try:
                note_text = input("Note: ").strip()
            except Exception:
                note_text = ""
        if note_text:
            _append_note(note_text)
        else:
            print("No note text provided.")
            _log_event("NOTE_SKIPPED: no text")
        return True

    # Sleep command (Windows)
    if re.search(r"\b(sleep|sleep computer|sleep pc|go to sleep|put (the )?(pc|computer) to sleep)\b", t):
        if confirm_fn and not confirm_fn("Put the computer to sleep?"):
            return True
        try:
            _run_command("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        except Exception as exc:
            print(f"Failed to sleep: {exc}")
        return True

    # System audio mute/unmute (toggle)
    if re.search(
        r"\b(mute|un\s*mute|toggle mute|mute audio|un\s*mute audio|mute volume|un\s*mute volume|"
        r"sound off|sound on|audio off|audio on|volume off|volume on|turn sound off|turn sound on)\b",
        t,
    ):
        if _media_key("mute"):
            return True

    # YouTube support (lightweight)
    if "youtube" in t or re.search(r"\byt\b", t):
        for word, action in (
            ("next", "next"),
            ("skip", "next"),
            ("previous", "previous"),
            ("back", "previous"),
            ("play", "play_pause"),
            ("pause", "play_pause"),
        ):
            if word in t:
                if _media_key(action):
                    return True

    yt_open = re.search(r"\b(open|start|launch)\s+(you\s*tube|youtube|yt)\b", t)
    if yt_open:
        if _youtube_search(""):
            return True

    yt_match = re.search(r"\b(youtube|yt)\s+(.+)$", t)
    if yt_match:
        query = yt_match.group(2).strip()
        if query in ("open", "home"):
            return _youtube_search("")
        if _youtube_search(query):
            return True

    if re.search(r"\b(pause|play)\s+(video|vid)\b", t):
        if _media_key("play_pause"):
            return True

    timer = _parse_timer(t)
    if timer:
        seconds, label = timer
        _start_timer(seconds, label)
        return True

    # Custom actions (phrase -> command)
    cfg = load_config()
    actions = cfg.get("actions", [])
    if isinstance(actions, list) and actions:
        norm_t = _normalize_text(t)
        for action in actions:
            if not isinstance(action, dict):
                continue
            phrase = str(action.get("phrase", "")).strip().lower()
            command = str(action.get("command", "")).strip()
            if not phrase or not command:
                continue
            norm_phrase = _normalize_text(phrase)
            if not norm_phrase:
                continue
            # Match exact or prefix to allow "open blue" style phrases
            if norm_t == norm_phrase or norm_t.startswith(norm_phrase):
                if not _confirm(f"Run action: {phrase}?", allow_prompt, confirm_fn=confirm_fn):
                    return True
                _run_command(command)
                _log_event(f"ACTION_RUN: {phrase} -> {command}")
                return True
            # Fuzzy match against individual tokens for STT hiccups
            tokens = [tok for tok in re.split(r"\s+", t) if tok]
            if tokens:
                match = difflib.get_close_matches(phrase, tokens, n=1, cutoff=0.85)
                if match:
                    if not _confirm(f"Run action: {phrase}?", allow_prompt, confirm_fn=confirm_fn):
                        return True
                    _run_command(command)
                    _log_event(f"ACTION_RUN: {phrase} -> {command}")
                    return True

    if cfg.get("spotify_media", False):
        require_spotify = cfg.get("spotify_requires_keyword", True)
        keywords = _get_spotify_keywords(cfg)
        has_spotify = _has_keyword(t, keywords)
        if (not require_spotify) or has_spotify:
            action = None
            if re.search(r"\b(play|pause|resume|stop)(\s+(song|track))?\b", t):
                action = "play_pause"
            elif re.search(r"\b(next|skip)(\s+(song|track))?\b", t):
                action = "next"
            elif re.search(r"\b(previous|back|rewind)(\s+(song|track))?\b", t):
                action = "previous"
            if action:
                ok = _media_key(action)
                if ok:
                    return True

    open_match = re.search(r"\b(open|launch|start)\s+(.+)$", t)
    if open_match:
        app = open_match.group(2).strip()
        return _open_app(app, allow_prompt, confirm_fn=confirm_fn)

    search_match = re.search(r"\b(search|look up|lookup|find)(\s+(for\s+)?(.+))?$", t)
    if search_match:
        query = (search_match.group(4) or "").strip()
        # Common mis-hears -> intended search terms
        if query in ("any may", "anymay", "any maye", "any me", "anyme"):
            query = "anime"
        if not query and allow_prompt:
            try:
                query = input("Search for: ").strip()
            except Exception:
                query = ""
        if query:
            return _web_search(query, allow_prompt, confirm_fn=confirm_fn)
        print("No search query provided.")
        return True

    web_match = re.search(r"\b(search the web|web search)\s+(for\s+)?(.+)$", t)
    if web_match:
        query = web_match.group(3).strip()
        return _web_search(query, allow_prompt, confirm_fn=confirm_fn)

    return False
