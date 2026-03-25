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

from config import load_config
from personality import get_confirm, handle_social, get_fallback, get_joke


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

def _log_transcript(text: str) -> None:
    try:
        base_dir = os.path.dirname(__file__)
        logs_dir = os.path.join(base_dir, "data", "logs")
        os.makedirs(logs_dir, exist_ok=True)
        log_path = os.path.join(logs_dir, "transcripts.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {text.strip()}\n")
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

_VERA_KOKORO_VOICE = "af_heart"
_kokoro_instance = None


def _get_kokoro_models_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "data", "models")


def _get_kokoro():
    """Lazy-init kokoro-onnx — loads model files on first call."""
    global _kokoro_instance
    if _kokoro_instance is None:
        from kokoro_onnx import Kokoro  # type: ignore
        models_dir = _get_kokoro_models_dir()
        onnx_path = os.path.join(models_dir, "kokoro-v1.0.onnx")
        voices_path = os.path.join(models_dir, "voices-v1.0.bin")
        _kokoro_instance = Kokoro(onnx_path, voices_path)
    return _kokoro_instance


def _kokoro_tts_play(text: str) -> None:
    """Generate and play audio via Kokoro TTS synchronously. Falls back to pyttsx3."""
    try:
        import sounddevice as sd  # type: ignore
        kokoro = _get_kokoro()
        samples, sample_rate = kokoro.create(text, voice=_VERA_KOKORO_VOICE, speed=1.0, lang="en-us")
        sd.play(samples, samplerate=sample_rate)
        sd.wait()
    except Exception as e:
        _log_event(f"TTS_KOKORO_ERROR: {e}")
        # Fallback to pyttsx3
        try:
            import pyttsx3  # type: ignore
            engine = pyttsx3.init()
            voices = engine.getProperty("voices")
            female = next((v for v in voices if "zira" in v.name.lower()), None)
            if female:
                engine.setProperty("voice", female.id)
            engine.say(text)
            engine.runAndWait()
        except Exception as e2:
            _log_event(f"TTS_FALLBACK_ERROR: {e2}")


def _tts_speak(text: str) -> bool:
    try:
        threading.Thread(target=_kokoro_tts_play, args=(text,), daemon=True).start()
        _log_event(f"TTS_SPEAK: {text}")
        return True
    except Exception as exc:
        print(f"TTS failed: {exc}")
        _log_event(f"TTS_FAILED: {exc}")
        return False


def _vera_confirm(category: str = "default") -> None:
    """Speak a random confirmation line appropriate for the action category."""
    _tts_speak(get_confirm(category))


def _list_notes(limit: int = 5) -> None:
    try:
        path = _notes_path()
        if not os.path.exists(path):
            _tts_speak("You have no notes saved.")
            _log_event("NOTES_LIST: empty (file missing)")
            return
        with open(path, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f.readlines() if ln.strip()]
        if not lines:
            _tts_speak("You have no notes saved.")
            _log_event("NOTES_LIST: empty")
            return
        notes = lines[-limit:]
        spoken = f"You have {len(notes)} note{'s' if len(notes) != 1 else ''}. " + ". ".join(notes)
        _tts_speak(spoken)
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

def _get_volume_interface():
    from ctypes import cast, POINTER
    import comtypes  # type: ignore
    from comtypes import CLSCTX_ALL  # type: ignore
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume  # type: ignore
    comtypes.CoInitialize()
    device = AudioUtilities.GetSpeakers()
    # Newer pycaw wraps device in AudioDevice object — unwrap if needed
    raw = device._dev if hasattr(device, '_dev') else device
    interface = raw.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return cast(interface, POINTER(IAudioEndpointVolume))


def _set_volume(level: int) -> bool:
    try:
        vol = _get_volume_interface()
        scalar = max(0.0, min(1.0, level / 100.0))
        vol.SetMasterVolumeLevelScalar(scalar, None)
        _log_event(f"VOLUME_SET: {level}%")
        return True
    except Exception as exc:
        print(f"Volume set failed: {exc}")
        _log_event(f"VOLUME_SET_FAILED: {exc}")
        return False


def _adjust_volume(direction: str, step: int = 10) -> bool:
    try:
        vol = _get_volume_interface()
        current = round(vol.GetMasterVolumeLevelScalar() * 100)
        new = min(100, current + step) if direction == "up" else max(0, current - step)
        vol.SetMasterVolumeLevelScalar(new / 100.0, None)
        _log_event(f"VOLUME_{direction.upper()}: {current}% -> {new}%")
        return True
    except Exception as exc:
        print(f"Volume adjust failed: {exc}")
        _log_event(f"VOLUME_ADJUST_FAILED: {exc}")
        return False


_active_timers: list[threading.Event] = []

def _start_timer(seconds: int, label: str) -> None:
    cancel_event = threading.Event()
    _active_timers.append(cancel_event)

    def _alarm():
        try:
            cancelled = cancel_event.wait(timeout=seconds)
            if cancelled:
                return
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
                messagebox.showinfo("VERA Timer", f"Timer done: {label}")
                root.destroy()
            except Exception:
                print(f"Timer done: {label}")
        except Exception:
            pass
        finally:
            if cancel_event in _active_timers:
                _active_timers.remove(cancel_event)

    threading.Thread(target=_alarm, daemon=True).start()


def _cancel_all_timers() -> int:
    count = len(_active_timers)
    for event in list(_active_timers):
        event.set()
    return count

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
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
    "hundred": 100,
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

def _spotify_search(query: str) -> bool:
    try:
        import webbrowser
        if query:
            webbrowser.open(f"spotify:search:{quote_plus(query)}")
        else:
            webbrowser.open("spotify:")
        return True
    except Exception:
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


_MISHEAR_MAP = {
    # medal variants
    "close metal": "close medal",
    # youtube variants
    "of a new job": "open youtube",
    "oh finish your job": "open youtube",
    "often you tube": "open youtube",
    "often youtube": "open youtube",
    "open the you tube": "open youtube",
    "open the youtube": "open youtube",
    "start your job": "open youtube",
    "start you tube": "open youtube",
    "start you do": "open youtube",
    "start you did": "open youtube",
    "start youtube": "open youtube",
    "but open you tube": "open youtube",
    "the you tube": "open youtube",
    "open you did": "open youtube",
    "open you do": "open youtube",
    "open he did": "open youtube",
    "open needed": "open youtube",
    "open needs him": "open youtube",
    "open need to": "open youtube",
    "open into": "open youtube",
    "your job": "youtube",
    "you tube": "youtube",
    "you did": "youtube",
    "you do": "youtube",
    "utube": "youtube",
    "u tube": "youtube",
    "your tube": "youtube",
    # spotify variants
    "spotty": "spotify",
    "spot if i": "spotify",
    "spot ify": "spotify",
    # search variants
    "any may": "anime",
    "any me": "anime",
    "anymay": "anime",
    # purge variants
    "perch": "purge",
    "perge": "purge",
    "merge": "purge",
    # restart assistant variants
    "we start assistant": "restart assistant",
    "i start assistant": "restart assistant",
    "start assistance": "restart assistant",
    "we start sf": "restart assistant",
    "restart as": "restart assistant",
    "we start": "restart assistant",
    "re start assistant": "restart assistant",
}

_FUZZY_TARGETS = {
    "youtube": 0.75,
    "spotify": 0.80,
}

def _apply_mishear_corrections(text: str) -> str:
    t = text.lower()
    # Apply explicit map first (longest phrases first, word boundaries)
    for mishear, correction in sorted(_MISHEAR_MAP.items(), key=lambda x: -len(x[0])):
        t = re.sub(r'\b' + re.escape(mishear) + r'\b', correction, t)

    # Fuzzy pass: check each individual word against key targets
    words = t.split()
    result = []
    for word in words:
        replaced = False
        for target, cutoff in _FUZZY_TARGETS.items():
            if word != target and difflib.SequenceMatcher(None, word, target).ratio() >= cutoff:
                result.append(target)
                replaced = True
                break
        if not replaced:
            result.append(word)
    return " ".join(result)


_FILLER_WORDS = re.compile(
    r"\b(um+|uh+|hmm+|hm+|like|you know|i mean|so|well|actually|basically|literally|right)\b"
)

_LEADING_NOISE = re.compile(r"^(the|a|an|i|hey|so|well|okay|ok)\s+")
_TRAILING_NOISE = re.compile(r"\s+(please|now|for me|for me please)\s*$")

_NOISE_WORDS = {"the", "a", "an", "and", "of", "to", "in", "is", "it", "i", "uh", "um", "hmm"}


def preprocess_transcript(text: str) -> str:
    """Single pipeline that cleans a raw transcript before command matching."""
    t = text.strip().lower()
    # 1. Strip punctuation (faster-whisper adds commas, periods, question marks)
    t = re.sub(r"[^\w\s]", "", t)
    # 2. Apply mishear corrections
    t = _apply_mishear_corrections(t)
    # 3. Strip filler words
    t = _FILLER_WORDS.sub("", t)
    # 4. Collapse extra whitespace
    t = re.sub(r"\s+", " ", t).strip()
    # 5. Strip leading noise words
    t = _LEADING_NOISE.sub("", t).strip()
    # 6. Strip trailing polite words that add no meaning
    t = _TRAILING_NOISE.sub("", t).strip()
    return t


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


def _add_alias(alias: str, target: str) -> bool:
    try:
        from config import save_config
        cfg = load_config()
        aliases = cfg.get("app_aliases", {})
        if not isinstance(aliases, dict):
            aliases = {}
        aliases[alias.lower()] = target.lower()
        cfg["app_aliases"] = aliases
        save_config(cfg)
        _log_event(f"ALIAS_ADDED: {alias} -> {target}")
        _tts_speak(f"Alias {alias} added for {target}.")
        return True
    except Exception as exc:
        _log_event(f"ALIAS_ADD_FAILED: {exc}")
        _tts_speak("Failed to add alias.")
        return False


_last_app: dict = {"name": None, "command": None}
_saved_volume: dict = {"level": None}  # stores volume before mute so unmute can restore it


_CLOSE_OVERRIDES = {
    "discord": "discord.exe",
    "steam": "steam.exe",
    "spotify": "spotify.exe",
    "chrome": "chrome.exe",
    "firefox": "firefox.exe",
    "edge": "msedge.exe",
    "opera gx": "opera.exe",
    "opera": "opera.exe",
    "notepad": "notepad.exe",
}


def _close_app(app_name: str) -> bool:
    normalized = _normalize_name(app_name)
    _norm_overrides = {_normalize_name(k): v for k, v in _CLOSE_OVERRIDES.items()}
    candidates = []

    if normalized in _norm_overrides:
        candidates.append(_norm_overrides[normalized])
    else:
        match = difflib.get_close_matches(normalized, list(_norm_overrides.keys()), n=1, cutoff=0.7)
        if match:
            candidates.append(_norm_overrides[match[0]])

    # Also try app name directly as exe
    candidates.append(normalized.replace(" ", "") + ".exe")

    for exe in candidates:
        try:
            result = subprocess.run(
                ["taskkill", "/f", "/im", exe],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            _log_event(f"CLOSE_ATTEMPT: {exe} -> rc={result.returncode} err={result.stderr.decode(errors='ignore').strip()}")
            if result.returncode == 0:
                return True
        except Exception as exc:
            _log_event(f"CLOSE_EXCEPTION: {exe} -> {exc}")
    _log_event(f"CLOSE_FAILED: {app_name} (candidates={candidates})")
    return False


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
        _last_app["name"] = app_name
        _last_app["command"] = command
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


def _show_help() -> None:
    cfg = load_config()
    lines = [
        "=== Built-in Commands ===",
        "",
        "Apps & Actions:",
        "  open <app>",
        "  launch <app>",
        "",
        "Web:",
        "  search for <query>",
        "  web search for <query>",
        "",
        "YouTube:",
        "  open youtube",
        "  youtube <query>",
        "  youtube play / pause / next / back",
        "",
        "Media (Spotify / general):",
        "  play / pause",
        "  skip / next",
        "  back / previous",
        "  sound on / sound off",
        "",
        "Timers:",
        "  set a timer <n> minutes",
        "  set a timer <n> seconds",
        "  set a timer <n> hours",
        "",
        "Notes:",
        "  note <text>",
        "  open notes",
        "  list notes",
        "  delete last note",
        "  clear all notes",
        "",
        "System:",
        "  sleep computer",
        "  restart computer",
        "  shut down computer",
        "  restart assistant",
        "  type <text>",
        "  send message <text>",
        "  read out <text>",
        "",
        "Discord:",
        "  discord <channel> <message>",
        "  read discord <channel>",
        "",
        "AI:",
        "  ask <question>",
        "",
        "Key Binds:",
        "  <your phrase>  (configured in Actions tab)",
        "",
        "Help:",
        "  what can i say",
    ]

    apps = cfg.get("apps", {})
    if isinstance(apps, dict) and apps:
        lines.append("")
        lines.append("=== Your Apps ===")
        for name in sorted(apps.keys()):
            lines.append(f"  open {name}")

    actions = cfg.get("actions", [])
    if isinstance(actions, list) and actions:
        lines.append("")
        lines.append("=== Custom Actions ===")
        for a in actions:
            phrase = a.get("phrase", "").strip()
            if phrase:
                lines.append(f"  {phrase}")

    SECTIONS = [
        ("Apps & Actions", [
            "open <app>  /  launch <app>",
            "open that again",
            "close <app>  /  close this",
            "add alias <name> for <app>",
        ]),
        ("Web", [
            "search for <query>",
            "web search for <query>",
        ]),
        ("YouTube", [
            "open youtube",
            "youtube <query>  /  youtube play <query>",
            "youtube play / pause / next / back",
        ]),
        ("Spotify", [
            "spotify <query>  /  spotify play <query>",
            "play / pause  /  skip / next  /  back / previous",
            "sound on / sound off",
        ]),
        ("Timers", [
            "set a timer <n> minutes",
            "set a timer <n> seconds",
            "set a timer <n> hours",
        ]),
        ("Notes", [
            "note <text>",
            "open notes  /  list notes",
            "delete last note  /  clear all notes",
        ]),
        ("System", [
            "sleep computer",
            "restart computer  /  shut down computer",
            "restart assistant",
            "type <text>",
            "send message <text>",
            "read out <text>",
        ]),
        ("Discord", [
            "discord <channel> <message>",
            "read discord <channel>",
        ]),
        ("AI", [
            "ask <question>",
        ]),
        ("Key Binds", [
            "<your phrase>  (configured in Actions tab)",
        ]),
        ("Help", [
            "what can i say",
        ]),
    ]

    apps = cfg.get("apps", {})
    non_steam = sorted(k for k, v in apps.items() if isinstance(v, str) and "steam://run" not in v)
    app_commands = ["open <steam game name>"] + [f"open {name}" for name in non_steam]

    actions = cfg.get("actions", [])
    action_commands = []
    if isinstance(actions, list) and actions:
        for a in actions:
            phrase = a.get("phrase", "").strip()
            if phrase:
                action_commands.append(phrase)

    try:
        import customtkinter as ctk
        ctk.set_appearance_mode("dark")

        root = ctk.CTk()
        root.withdraw()
        win = ctk.CTkToplevel(root)
        win.title("What Can I Say?")
        win.geometry("480x620")
        win.resizable(True, True)

        title = ctk.CTkLabel(win, text="What Can I Say?", font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=(16, 4))

        divider = ctk.CTkFrame(win, height=2, fg_color="#3a3a3a")
        divider.pack(fill="x", padx=16, pady=(0, 8))

        scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        def _add_section(title_text, items):
            hdr = ctk.CTkLabel(scroll, text=title_text, font=ctk.CTkFont(size=13, weight="bold"),
                               text_color="#4fa3e0", anchor="w")
            hdr.pack(fill="x", padx=8, pady=(12, 3))
            card = ctk.CTkFrame(scroll, fg_color="#252525", corner_radius=10)
            card.pack(fill="x", padx=4, pady=(0, 4))
            for i, item in enumerate(items):
                row_bg = "#2a2a2a" if i % 2 == 0 else "#252525"
                row = ctk.CTkFrame(card, fg_color=row_bg, corner_radius=6)
                row.pack(fill="x", padx=6, pady=2)
                # Split on <placeholders> and render with color
                import re as _re
                parts = _re.split(r"(<[^>]+>)", item)
                inner = ctk.CTkFrame(row, fg_color="transparent")
                inner.pack(anchor="w", padx=10, pady=5)
                for part in parts:
                    if part.startswith("<") and part.endswith(">"):
                        lbl = ctk.CTkLabel(inner, text=part, font=ctk.CTkFont(size=12, slant="italic"),
                                           text_color="#7ec8e3")
                    else:
                        lbl = ctk.CTkLabel(inner, text=part, font=ctk.CTkFont(size=12),
                                           text_color="#d0d0d0")
                    lbl.pack(side="left")

        for section_title, items in SECTIONS:
            _add_section(section_title, items)

        if app_commands:
            _add_section("Your Apps", app_commands)

        if action_commands:
            _add_section("Custom Actions", action_commands)

        win.protocol("WM_DELETE_WINDOW", lambda: (win.destroy(), root.destroy()))
        win.lift()
        win.focus_force()
        root.mainloop()
    except Exception as exc:
        print(f"Help display failed: {exc}")


def _resolve_key(raw: str):
    """Resolve a single key string to a pynput key object or mouse button."""
    raw = raw.strip().lower()
    if raw.startswith("<") and raw.endswith(">"):
        raw = raw[1:-1].strip()
    if raw in ("x1", "x2"):
        from pynput import mouse as _mouse  # type: ignore
        return ("mouse", _mouse.Button.x1 if raw == "x1" else _mouse.Button.x2)
    from pynput import keyboard  # type: ignore
    if len(raw) == 1:
        return ("key", keyboard.KeyCode.from_char(raw))
    obj = getattr(keyboard.Key, raw, None)
    if obj is None:
        return None
    return ("key", obj)


_MODIFIER_NAMES = {"ctrl", "alt", "shift", "cmd"}


def _press_key(key: str, count: int = 1) -> bool:
    """Press a single key or combo (e.g. 'alt+n', 'ctrl+shift+f', 'x1')."""
    try:
        from pynput import keyboard as _kb  # type: ignore
        from pynput import mouse as _mouse  # type: ignore

        parts = [p.strip().lower() for p in key.split("+")]
        modifiers = []
        main = None

        for part in parts:
            clean = part.strip("<>")
            if clean in _MODIFIER_NAMES:
                mod = getattr(_kb.Key, clean, None)
                if mod:
                    modifiers.append(mod)
            else:
                main = part

        if main is None:
            return False

        resolved = _resolve_key(main)
        if resolved is None:
            _log_event(f"PRESS_KEY_FAILED: unknown key: {main}")
            return False

        kb_ctl = _kb.Controller()
        ms_ctl = _mouse.Controller()

        for i in range(max(1, count)):
            for mod in modifiers:
                kb_ctl.press(mod)
            if resolved[0] == "mouse":
                ms_ctl.press(resolved[1])
                ms_ctl.release(resolved[1])
            else:
                kb_ctl.press(resolved[1])
                kb_ctl.release(resolved[1])
            for mod in reversed(modifiers):
                kb_ctl.release(mod)
            if count > 1 and i < count - 1:
                time.sleep(0.1)

        _log_event(f"PRESS_KEY: {key} x{count}")
        return True
    except Exception as exc:
        _log_event(f"PRESS_KEY_FAILED: {exc}")
        return False


def _run_macro(sequence: str, count: int = 1) -> bool:
    """Run a macro sequence of key steps separated by '>'. e.g. 'x1 > q' or 'alt+n'."""
    steps = [s.strip() for s in sequence.split(">") if s.strip()]
    for _ in range(max(1, count)):
        for step in steps:
            _press_key(step, 1)
            time.sleep(0.15)
    _log_event(f"MACRO_RUN: {sequence} x{count}")
    return True


def _send_message(text: str) -> bool:
    try:
        from pynput.keyboard import Controller, Key  # type: ignore
        time.sleep(0.3)
        ctl = Controller()
        ctl.type(text)
        time.sleep(0.5)
        ctl.press(Key.enter)
        ctl.release(Key.enter)
        _log_event(f"SEND_MESSAGE: {text}")
        return True
    except Exception as exc:
        _log_event(f"SEND_MESSAGE_FAILED: {exc}")
        return False


def _type_text(text: str) -> bool:
    try:
        from pynput.keyboard import Controller  # type: ignore
        time.sleep(0.3)
        Controller().type(text)
        _log_event(f"TYPE_TEXT: {text}")
        return True
    except Exception as exc:
        print(f"Failed to type text: {exc}")
        _log_event(f"TYPE_TEXT_FAILED: {exc}")
        return False


def _ask_ai(question: str) -> bool:
    cfg = load_config()
    api_key = cfg.get("gemini_api_key", "").strip()
    if not api_key:
        _log_event("ASK_AI_FAILED: no AI API key configured")
        _tts_speak("No AI API key configured. Please add your Groq key in settings.")
        return False

    today = time.strftime("%B %d, %Y")
    now = time.strftime("%I:%M %p")
    prompt = (
        f"Today's date is {today} and the current time is {now}.\n\n"
        f"{question.strip()}\n\n"
        "Answer in 2 to 3 sentences maximum. Be direct and concise."
    )

    def _run():
        try:
            import json
            import urllib.request
            import urllib.error

            if api_key.startswith("sk-ant-"):
                # Anthropic / Claude
                url = "https://api.anthropic.com/v1/messages"
                body = json.dumps({
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 150,
                    "messages": [{"role": "user", "content": prompt}],
                }).encode("utf-8")
                req = urllib.request.Request(
                    url,
                    data=body,
                    headers={
                        "Content-Type": "application/json",
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "User-Agent": "VERA/1.0",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                answer = (
                    data.get("content", [{}])[0]
                    .get("text", "")
                    .strip()
                )
            elif api_key.startswith("sk-"):
                # OpenAI
                url = "https://api.openai.com/v1/chat/completions"
                body = json.dumps({
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 150,
                }).encode("utf-8")
                req = urllib.request.Request(
                    url,
                    data=body,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {api_key}",
                        "User-Agent": "VERA/1.0",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                answer = (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                    .strip()
                )
            else:
                # Groq (default)
                url = "https://api.groq.com/openai/v1/chat/completions"
                body = json.dumps({
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 150,
                }).encode("utf-8")
                req = urllib.request.Request(
                    url,
                    data=body,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {api_key}",
                        "User-Agent": "VERA/1.0",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                answer = (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                    .strip()
                )
            if not answer:
                _log_event("ASK_AI_FAILED: empty response")
                _tts_speak("I didn't get a response from the AI.")
                return
            _log_event(f"ASK_AI: {question} -> {answer}")
            _tts_speak(answer)
        except urllib.error.HTTPError as exc:
            try:
                body = exc.read().decode("utf-8")
            except Exception:
                body = "(no body)"
            _log_event(f"ASK_AI_FAILED: {exc} — {body}")
            _tts_speak("AI request failed. Check your API key.")
        except Exception as exc:
            _log_event(f"ASK_AI_FAILED: {exc}")
            _tts_speak("AI request failed.")

    threading.Thread(target=_run, daemon=True).start()
    return True


def _discord_read(channel_name: str) -> bool:
    cfg = load_config()
    token = cfg.get("discord_bot_token", "").strip()
    guild_id = cfg.get("discord_server_id", "").strip()

    if not token:
        print("Discord bot token not configured.")
        _log_event("DISCORD_READ_FAILED: no bot token")
        return False
    if not guild_id:
        print("Discord server ID not configured.")
        _log_event("DISCORD_READ_FAILED: no server ID")
        return False

    try:
        import json
        import urllib.request
        import urllib.error

        headers = {
            "Authorization": f"Bot {token}",
            "User-Agent": "VERA/1.0",
        }

        req = urllib.request.Request(
            f"https://discord.com/api/v10/guilds/{guild_id}/channels",
            headers=headers,
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            channels = json.loads(resp.read().decode("utf-8"))

        channel_id = None
        for ch in channels:
            if ch.get("type") == 0 and ch.get("name", "").lower() == channel_name.lower():
                channel_id = ch["id"]
                break

        if not channel_id:
            _log_event(f"DISCORD_READ_FAILED: channel not found: {channel_name}")
            _tts_speak(f"Channel {channel_name} not found.")
            return False

        req = urllib.request.Request(
            f"https://discord.com/api/v10/channels/{channel_id}/messages?limit=1",
            headers=headers,
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            messages = json.loads(resp.read().decode("utf-8"))

        if not messages:
            _tts_speak(f"No messages in {channel_name}.")
            return True

        msg = messages[0]
        author = msg.get("author", {}).get("username", "Unknown")
        content = msg.get("content", "").strip()

        if not content:
            _tts_speak(f"Last message in {channel_name} has no text.")
            return True

        _tts_speak(f"{author} said: {content}")
        _log_event(f"DISCORD_READ: #{channel_name}: {author}: {content}")
        return True

    except urllib.error.HTTPError as exc:
        try:
            body = exc.read().decode("utf-8")
        except Exception:
            body = "(no body)"
        print(f"Failed to read Discord: {exc} — {body}")
        _log_event(f"DISCORD_READ_FAILED: {exc} — {body}")
        return False
    except Exception as exc:
        print(f"Failed to read Discord: {exc}")
        _log_event(f"DISCORD_READ_FAILED: {exc}")
        return False


def _discord_send(channel_name: str, message: str) -> bool:
    cfg = load_config()
    channels = cfg.get("discord_channels", {})
    if not isinstance(channels, dict):
        channels = {}

    webhook_url = channels.get(channel_name)
    if not webhook_url:
        norm_map = {_normalize_name(k): v for k, v in channels.items()}
        webhook_url = norm_map.get(_normalize_name(channel_name))

    if not webhook_url:
        print(f"Discord channel not configured: {channel_name}")
        _log_event(f"DISCORD_CHANNEL_NOT_FOUND: {channel_name}")
        return False

    try:
        import json
        import urllib.request
        import urllib.error
        data = json.dumps({"content": message}).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "VERA/1.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10):
            pass
        _log_event(f"DISCORD_SENT: #{channel_name}: {message}")
        return True
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read().decode("utf-8")
        except Exception:
            body = "(no body)"
        print(f"Failed to send Discord message: {exc} — {body}")
        _log_event(f"DISCORD_SEND_FAILED: {exc} — {body}")
        return False
    except Exception as exc:
        print(f"Failed to send Discord message: {exc}")
        _log_event(f"DISCORD_SEND_FAILED: {exc}")
        return False


def _discord_delete_last(channel_name: str) -> bool:
    cfg = load_config()
    token = cfg.get("discord_bot_token", "").strip()
    guild_id = cfg.get("discord_server_id", "").strip()
    if not token or not guild_id:
        _tts_speak("Discord bot token or server ID not configured.")
        return False
    try:
        import json, urllib.request, urllib.error
        headers = {"Authorization": f"Bot {token}", "User-Agent": "VERA/1.0"}

        req = urllib.request.Request(
            f"https://discord.com/api/v10/guilds/{guild_id}/channels", headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            channels = json.loads(resp.read().decode("utf-8"))
        channel_id = next(
            (ch["id"] for ch in channels
             if ch.get("type") == 0 and ch.get("name", "").lower() == channel_name.lower()),
            None)
        if not channel_id:
            _tts_speak(f"Channel {channel_name} not found.")
            return False

        req = urllib.request.Request(
            f"https://discord.com/api/v10/channels/{channel_id}/messages?limit=1",
            headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            messages = json.loads(resp.read().decode("utf-8"))
        if not messages:
            _tts_speak(f"No messages to delete in {channel_name}.")
            return True

        msg_id = messages[0]["id"]
        req = urllib.request.Request(
            f"https://discord.com/api/v10/channels/{channel_id}/messages/{msg_id}",
            headers=headers, method="DELETE")
        with urllib.request.urlopen(req, timeout=10):
            pass
        _tts_speak(f"Last message in {channel_name} deleted.")
        _log_event(f"DISCORD_DELETE: #{channel_name} msg {msg_id}")
        return True
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8") if hasattr(exc, "read") else ""
        _log_event(f"DISCORD_DELETE_FAILED: {exc} — {body}")
        _tts_speak("Failed to delete message. Check bot permissions.")
        return False
    except Exception as exc:
        _log_event(f"DISCORD_DELETE_FAILED: {exc}")
        return False


def _discord_purge(channel_name: str, count: int) -> bool:
    cfg = load_config()
    token = cfg.get("discord_bot_token", "").strip()
    guild_id = cfg.get("discord_server_id", "").strip()
    if not token or not guild_id:
        _tts_speak("Discord bot token or server ID not configured.")
        return False
    count = max(1, min(count, 100))
    try:
        import json, urllib.request, urllib.error
        headers = {
            "Authorization": f"Bot {token}",
            "User-Agent": "VERA/1.0",
            "Content-Type": "application/json",
        }

        req = urllib.request.Request(
            f"https://discord.com/api/v10/guilds/{guild_id}/channels", headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            channels = json.loads(resp.read().decode("utf-8"))
        channel_id = next(
            (ch["id"] for ch in channels
             if ch.get("type") == 0 and ch.get("name", "").lower() == channel_name.lower()),
            None)
        if not channel_id:
            _tts_speak(f"Channel {channel_name} not found.")
            return False

        req = urllib.request.Request(
            f"https://discord.com/api/v10/channels/{channel_id}/messages?limit={count}",
            headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            messages = json.loads(resp.read().decode("utf-8"))
        if not messages:
            _tts_speak(f"No messages to delete in {channel_name}.")
            return True

        msg_ids = [m["id"] for m in messages]
        if len(msg_ids) == 1:
            req = urllib.request.Request(
                f"https://discord.com/api/v10/channels/{channel_id}/messages/{msg_ids[0]}",
                headers=headers, method="DELETE")
            with urllib.request.urlopen(req, timeout=10):
                pass
        else:
            data = json.dumps({"messages": msg_ids}).encode("utf-8")
            req = urllib.request.Request(
                f"https://discord.com/api/v10/channels/{channel_id}/messages/bulk-delete",
                data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=10):
                pass
        _tts_speak(f"Deleted {len(msg_ids)} messages from {channel_name}.")
        _log_event(f"DISCORD_PURGE: #{channel_name} x{len(msg_ids)}")
        return True
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8") if hasattr(exc, "read") else ""
        _log_event(f"DISCORD_PURGE_FAILED: {exc} — {body}")
        _tts_speak("Failed to purge messages. Check bot permissions.")
        return False
    except Exception as exc:
        _log_event(f"DISCORD_PURGE_FAILED: {exc}")
        return False


# ---------------------------------------------------------------------------
# Intent Router
# ---------------------------------------------------------------------------
# Each command handler is registered with a priority and a trigger pattern.
# handle_transcript iterates handlers in descending priority order and calls
# the first handler whose pattern matches the cleaned transcript.
# Handlers return True to claim the transcript, False to pass to the next.

_INTENT_REGISTRY: list = []  # list of (priority, compiled_pattern, handler_fn)


def _intent(priority: int, pattern: str):
    """Decorator that registers an intent handler at the given priority."""
    def decorator(fn):
        _INTENT_REGISTRY.append((priority, re.compile(pattern), fn))
        return fn
    return decorator


# --- Help ---
@_intent(1000, r"\b(what can i say|show commands|show help|list commands)\b")
def _ih_help(m, t, allow_prompt, confirm_fn, restart_fn):
    threading.Thread(target=_show_help, daemon=True).start()
    return True


# --- Restart VERA ---
@_intent(990, r"(\b(restart|reboot)\s+(vera|assistant|the assistant)\b|^(restart|reboot)$)")
def _ih_restart_vera(m, t, allow_prompt, confirm_fn, restart_fn):
    from memory import clear_session as _clear_session
    _clear_session()
    _log_event("RESTART_IPA: voice command")
    if restart_fn is not None:
        threading.Thread(target=restart_fn, daemon=True).start()
    return True


# --- Keybinds (exact phrase match) ---
@_intent(980, r"^.+$")
def _ih_keybinds(m, t, allow_prompt, confirm_fn, restart_fn):
    cfg = load_config()
    keybinds = cfg.get("keybinds", [])
    if not isinstance(keybinds, list) or not keybinds:
        return False
    norm_t = _normalize_text(t)
    for kb in keybinds:
        phrase = str(kb.get("phrase", "")).strip().lower()
        key = str(kb.get("key", "")).strip()
        count = int(kb.get("count", 1))
        if not phrase or not key:
            continue
        if _normalize_text(phrase) == norm_t:
            _run_macro(key, count)
            return True
    return False


# --- Send message ---
@_intent(850, r"\bsend\s+message\s+(.+)$")
def _ih_send_message(m, t, allow_prompt, confirm_fn, restart_fn):
    _send_message(m.group(1).strip())
    return True


# --- Ask AI ---
@_intent(840, r"^ask\s+(.+)$")
def _ih_ask_ai(m, t, allow_prompt, confirm_fn, restart_fn):
    _ask_ai(m.group(1).strip())
    return True


# --- Memory: set name ---
@_intent(880, r"\bmy\s+name\s+is\s+(.+)$")
def _ih_set_name(m, t, allow_prompt, confirm_fn, restart_fn):
    from memory import remember as _remember
    name = m.group(1).strip().title()
    _remember("name", name)
    _tts_speak(f"Got it, I'll remember that. Nice to meet you, {name}")
    return True


# --- Memory: ask name ---
@_intent(879, r"\b(what is my name|do you know my name|what('s| is) my name)\b")
def _ih_ask_name(m, t, allow_prompt, confirm_fn, restart_fn):
    from memory import recall as _recall
    name = _recall("name")
    if name:
        _tts_speak(f"Your name is {name}")
    else:
        _tts_speak("I don't know your name yet. Tell me with 'my name is'")
    return True


# --- Memory: remember fact ---
@_intent(875, r"\b(remember|vera remember|don't forget)\s+(?:that\s+)?(.+)$")
def _ih_remember(m, t, allow_prompt, confirm_fn, restart_fn):
    from memory import remember as _remember
    fact = m.group(2).strip()
    # Try to parse "my X is Y" style facts
    name_match = re.match(r"my\s+(\w+)\s+is\s+(.+)$", fact)
    if name_match:
        key = f"my_{name_match.group(1).lower()}"
        value = name_match.group(2).strip()
        _remember(key, value)
        _tts_speak(f"Got it, remembered that your {name_match.group(1)} is {value}")
    else:
        _remember(f"fact_{len(fact)}", fact)
        _tts_speak("Got it, I'll remember that")
    return True


# --- Memory: forget ---
@_intent(874, r"\b(forget|vera forget)\s+(?:my\s+)?(.+)$")
def _ih_forget(m, t, allow_prompt, confirm_fn, restart_fn):
    from memory import forget as _forget
    key = m.group(2).strip().lower()
    if _forget(key) or _forget(f"my_{key}"):
        _tts_speak(f"Done, I've forgotten that")
    else:
        _tts_speak("I don't have anything stored for that")
    return True


# --- Memory: what do you know ---
@_intent(873, r"\b(what do you know about me|what do you remember|what have you remembered)\b")
def _ih_recall_all(m, t, allow_prompt, confirm_fn, restart_fn):
    from memory import recall_all as _recall_all
    data = _recall_all()
    if not data:
        _tts_speak("I don't know anything about you yet")
        return True
    parts = []
    for key, value in data.items():
        parts.append(f"{key.replace('_', ' ')}: {value}")
    _tts_speak("Here's what I know. " + ", ".join(parts))
    return True


# --- Type text ---
@_intent(830, r"\btype\s+(.+)$")
def _ih_type(m, t, allow_prompt, confirm_fn, restart_fn):
    _type_text(m.group(1).strip())
    return True


# --- Read out (TTS) ---
@_intent(820, r"\bread\s+out\s+(.+)$")
def _ih_read_out(m, t, allow_prompt, confirm_fn, restart_fn):
    _tts_speak(m.group(1).strip())
    return True


# --- Discord read ---
@_intent(810, r"\bread\s+discord\s+(\w+)\b")
def _ih_discord_read(m, t, allow_prompt, confirm_fn, restart_fn):
    threading.Thread(target=_discord_read, args=(m.group(1).strip(),), daemon=True).start()
    return True


# --- Discord delete last ---
@_intent(808, r"\bdiscord\s+delete\s+(\w+)\b")
def _ih_discord_delete(m, t, allow_prompt, confirm_fn, restart_fn):
    threading.Thread(target=_discord_delete_last, args=(m.group(1).strip(),), daemon=True).start()
    return True


# --- Discord purge ---
@_intent(806, r"\bdiscord\s+purge\s+(\w+)\s+(\d+)\b")
def _ih_discord_purge(m, t, allow_prompt, confirm_fn, restart_fn):
    threading.Thread(target=_discord_purge, args=(m.group(1).strip(), int(m.group(2))), daemon=True).start()
    return True


# --- Discord send ---
@_intent(800, r"\bdiscord\s+(\w+)\s+(.+)$")
def _ih_discord_send(m, t, allow_prompt, confirm_fn, restart_fn):
    _discord_send(m.group(1).strip(), m.group(2).strip())
    return True


# --- Notes: clear all ---
@_intent(760, r"\b(clear|delete|remove)\s+(all\s+)?notes\b")
def _ih_notes_clear_all(m, t, allow_prompt, confirm_fn, restart_fn):
    if confirm_fn and not confirm_fn("Clear all notes?"):
        return True
    _clear_notes()
    return True


# --- Notes: open ---
@_intent(755, r"\b(open|show)\s+notes?\b")
def _ih_notes_open(m, t, allow_prompt, confirm_fn, restart_fn):
    _open_notes()
    return True


# --- Notes: list ---
@_intent(750, r"\b(list|show)\s+notes\b")
def _ih_notes_list(m, t, allow_prompt, confirm_fn, restart_fn):
    _list_notes()
    return True


# --- Notes: delete last ---
@_intent(745, r"\b(delete|remove|undo)\s+(last\s+)?note\b")
def _ih_notes_delete_last(m, t, allow_prompt, confirm_fn, restart_fn):
    if confirm_fn and not confirm_fn("Delete last note?"):
        return True
    _delete_last_note()
    return True


# --- Notes: add ---
@_intent(740, r"\b(note|notes|take a note|add note|remember)\b\s*(.+)?$")
def _ih_note_add(m, t, allow_prompt, confirm_fn, restart_fn):
    note_text = (m.group(2) or "").strip()
    if not note_text:
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
        _vera_confirm("note")
    else:
        print("No note text provided.")
        _log_event("NOTE_SKIPPED: no text")
    return True


# --- Restart PC ---
@_intent(720, r"\b(restart (the )?(pc|computer)|reboot (the )?(pc|computer))\b")
def _ih_restart_pc(m, t, allow_prompt, confirm_fn, restart_fn):
    if confirm_fn and not confirm_fn("Restart the computer?"):
        return True
    try:
        _run_command("shutdown /r /t 5")
    except Exception as exc:
        _log_event(f"RESTART_PC_FAILED: {exc}")
    return True


# --- Shutdown PC ---
@_intent(710, r"\b(shut down|shutdown|turn off|power off) (the )?(pc|computer)\b")
def _ih_shutdown_pc(m, t, allow_prompt, confirm_fn, restart_fn):
    if confirm_fn and not confirm_fn("Shut down the computer?"):
        return True
    try:
        _run_command("shutdown /s /t 5")
    except Exception as exc:
        _log_event(f"SHUTDOWN_PC_FAILED: {exc}")
    return True


# --- Sleep PC ---
@_intent(700, r"\b(sleep|sleep computer|sleep pc|go to sleep|put (the )?(pc|computer) to sleep)\b")
def _ih_sleep_pc(m, t, allow_prompt, confirm_fn, restart_fn):
    if confirm_fn and not confirm_fn("Put the computer to sleep?"):
        return True
    try:
        _run_command("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    except Exception as exc:
        print(f"Failed to sleep: {exc}")
    return True


# --- Mute ---
@_intent(660, r"\b(mute|mute audio|mute volume|sound off|audio off|volume off|turn sound off|turn audio off)\b")
def _ih_mute(m, t, allow_prompt, confirm_fn, restart_fn):
    try:
        vol = _get_volume_interface()
        _saved_volume["level"] = round(vol.GetMasterVolumeLevelScalar() * 100)
    except Exception:
        _saved_volume["level"] = 50
    if _set_volume(0):
        _vera_confirm("volume")
        return True
    return False


# --- Unmute ---
@_intent(655, r"\b(un\s*mute|unmute audio|unmute volume|sound on|audio on|volume on|turn sound on|turn audio on)\b")
def _ih_unmute(m, t, allow_prompt, confirm_fn, restart_fn):
    restore = _saved_volume["level"] if _saved_volume["level"] is not None else 50
    if _set_volume(restore):
        _saved_volume["level"] = None
        _vera_confirm("volume")
        return True
    return False


# --- Volume max ---
@_intent(650, r"\bset\s+volume\s+(max|maximum|full)\b")
def _ih_volume_max(m, t, allow_prompt, confirm_fn, restart_fn):
    if _set_volume(100):
        _vera_confirm("volume")
        return True
    return False


# --- Volume set ---
@_intent(645, r"\bset\s+volume\s+(\d{1,3}|\w+)\b")
def _ih_volume_set(m, t, allow_prompt, confirm_fn, restart_fn):
    raw = m.group(1)
    level = int(raw) if raw.isdigit() else _word_to_num(raw)
    if level is not None:
        level = max(0, min(100, round(int(level) / 10) * 10))
        if _set_volume(level):
            _vera_confirm("volume")
            return True
    return False


# --- Volume up ---
@_intent(640, r"\bvolume\s+up\b")
def _ih_volume_up(m, t, allow_prompt, confirm_fn, restart_fn):
    if _adjust_volume("up"):
        _vera_confirm("volume")
        return True
    return False


# --- Volume down ---
@_intent(635, r"\bvolume\s+down\b")
def _ih_volume_down(m, t, allow_prompt, confirm_fn, restart_fn):
    if _adjust_volume("down"):
        _vera_confirm("volume")
        return True
    return False


# --- YouTube: open ---
@_intent(600, r"\b(open|start|launch)\s+(you\s*tube|youtube|yt)\b")
def _ih_youtube_open(m, t, allow_prompt, confirm_fn, restart_fn):
    return bool(_youtube_search(""))


# --- YouTube: search ---
@_intent(595, r"\b(youtube|yt)\s+(.+)$")
def _ih_youtube_search(m, t, allow_prompt, confirm_fn, restart_fn):
    query = m.group(2).strip()
    play_search = re.match(r"^play\s+(.+)$", query)
    if play_search:
        query = play_search.group(1).strip()
    if query in ("open", "home"):
        return bool(_youtube_search(""))
    if query not in ("play", "pause", "next", "skip", "previous", "back"):
        if _youtube_search(query):
            return True
    return False


# --- YouTube: controls ---
@_intent(590, r"\b(youtube|yt)\b")
def _ih_youtube_controls(m, t, allow_prompt, confirm_fn, restart_fn):
    for word, action in (
        ("next", "next"), ("skip", "next"),
        ("previous", "previous"), ("back", "previous"),
        ("play", "play_pause"), ("pause", "play_pause"),
    ):
        if word in t:
            if _media_key(action):
                return True
    return False


# --- Pause/play video ---
@_intent(585, r"\b(pause|play)\s+(video|vid)\b")
def _ih_pause_video(m, t, allow_prompt, confirm_fn, restart_fn):
    return bool(_media_key("play_pause"))


# --- Cancel timer ---
@_intent(580, r"\b(cancel timer|stop timer|never mind|nevermind|forget it|cancel that)\b")
def _ih_cancel_timer(m, t, allow_prompt, confirm_fn, restart_fn):
    count = _cancel_all_timers()
    if count > 0:
        _tts_speak("Timer cancelled" if count == 1 else f"{count} timers cancelled")
    else:
        _tts_speak("No timers running")
    return True


# --- Set timer ---
@_intent(575, r"^.+$")
def _ih_set_timer(m, t, allow_prompt, confirm_fn, restart_fn):
    timer = _parse_timer(t)
    if timer:
        seconds, label = timer
        _vera_confirm("timer")
        _start_timer(seconds, label)
        return True
    return False


# --- Custom actions ---
@_intent(450, r"^.+$")
def _ih_custom_actions(m, t, allow_prompt, confirm_fn, restart_fn):
    cfg = load_config()
    actions = cfg.get("actions", [])
    if not isinstance(actions, list) or not actions:
        return False
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
        if norm_t == norm_phrase or norm_t.startswith(norm_phrase):
            if not _confirm(f"Run action: {phrase}?", allow_prompt, confirm_fn=confirm_fn):
                return True
            _run_command(command)
            _log_event(f"ACTION_RUN: {phrase} -> {command}")
            return True
        tokens = [tok for tok in re.split(r"\s+", t) if tok]
        if tokens:
            match = difflib.get_close_matches(phrase, tokens, n=1, cutoff=0.85)
            if match:
                if not _confirm(f"Run action: {phrase}?", allow_prompt, confirm_fn=confirm_fn):
                    return True
                _run_command(command)
                _log_event(f"ACTION_RUN: {phrase} -> {command}")
                return True
    return False


# --- Spotify ---
@_intent(400, r"^.+$")
def _ih_spotify(m, t, allow_prompt, confirm_fn, restart_fn):
    cfg = load_config()
    if not cfg.get("spotify_media", False):
        return False
    require_spotify = cfg.get("spotify_requires_keyword", True)
    keywords = _get_spotify_keywords(cfg)
    has_spotify = _has_keyword(t, keywords)
    if not require_spotify or has_spotify:
        sp_search = re.search(r"\bspotify\s+(?:play\s+|search\s+)?(.+)$", t)
        if sp_search:
            query = sp_search.group(1).strip()
            if query not in ("play", "pause", "next", "skip", "previous", "back", "resume", "stop"):
                if _spotify_search(query):
                    return True
        action = None
        if re.search(r"\b(play|pause|resume|stop)(\s+(song|track))?\b", t):
            action = "play_pause"
        elif re.search(r"\b(next|skip)(\s+(song|track))?\b", t):
            action = "next"
        elif re.search(r"\b(previous|back|rewind)(\s+(song|track))?\b", t):
            action = "previous"
        if action:
            if _media_key(action):
                return True
    return False


# --- Add alias ---
@_intent(350, r"\badd alias\s+(.+?)\s+for\s+(.+)$")
def _ih_add_alias(m, t, allow_prompt, confirm_fn, restart_fn):
    _add_alias(m.group(1).strip(), m.group(2).strip())
    return True


# --- Open again ---
@_intent(340, r"\b(open|launch|start)\s+(that|it)\s+again\b")
def _ih_open_again(m, t, allow_prompt, confirm_fn, restart_fn):
    if _last_app["command"]:
        try:
            _run_command(_last_app["command"])
            return True
        except Exception:
            pass
    return False


# --- Close current window ---
@_intent(330, r"\b(close|quit|exit)\s+(this|current|window)\b")
def _ih_close_current(m, t, allow_prompt, confirm_fn, restart_fn):
    try:
        import ctypes
        import ctypes.wintypes
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        pid = ctypes.wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        result = subprocess.run(
            ["taskkill", "/f", "/pid", str(pid.value)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        return result.returncode == 0
    except Exception:
        return False


# --- Close app ---
@_intent(320, r"\b(close|quit|exit)\s+(.+)$")
def _ih_close_app(m, t, allow_prompt, confirm_fn, restart_fn):
    app = m.group(2).strip()
    if _close_app(app):
        _vera_confirm("close")
        return True
    return False


# --- Open app ---
@_intent(310, r"\b(open|launch|start)\s+(.+)$")
def _ih_open_app(m, t, allow_prompt, confirm_fn, restart_fn):
    app = m.group(2).strip()
    app = re.sub(r"^the\s+", "", app)
    if " " not in app and difflib.SequenceMatcher(None, app, "youtube").ratio() >= 0.6:
        if _youtube_search(""):
            return True
    result = _open_app(app, allow_prompt, confirm_fn=confirm_fn)
    if result:
        _vera_confirm("open")
    return result


# --- Search ---
@_intent(300, r"\b(search|look up|lookup|find)(\s+(for\s+)?(.+))?$")
def _ih_search(m, t, allow_prompt, confirm_fn, restart_fn):
    query = (m.group(4) or "").strip()
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


# --- Web search ---
@_intent(295, r"\b(search the web|web search)\s+(for\s+)?(.+)$")
def _ih_web_search(m, t, allow_prompt, confirm_fn, restart_fn):
    return _web_search(m.group(3).strip(), allow_prompt, confirm_fn=confirm_fn)


# --- Clipboard: read ---
@_intent(260, r"\bread\s+clipboard\b")
def _ih_clipboard_read(m, t, allow_prompt, confirm_fn, restart_fn):
    try:
        import tkinter as _tk
        _r = _tk.Tk()
        _r.withdraw()
        clip = _r.clipboard_get()
        _r.destroy()
        _tts_speak(clip.strip() if clip.strip() else "Clipboard is empty")
    except Exception:
        _tts_speak("Couldn't read the clipboard")
    return True


# --- Clipboard: clear ---
@_intent(255, r"\bclear\s+clipboard\b")
def _ih_clipboard_clear(m, t, allow_prompt, confirm_fn, restart_fn):
    try:
        import tkinter as _tk
        _r = _tk.Tk()
        _r.withdraw()
        _r.clipboard_clear()
        _r.clipboard_append("")
        _r.update()
        _r.destroy()
        _vera_confirm("default")
    except Exception:
        _tts_speak("Couldn't clear the clipboard")
    return True


# --- Clipboard: paste ---
@_intent(250, r"\b(paste\s+clipboard|paste\s+that|paste\s+it)\b")
def _ih_clipboard_paste(m, t, allow_prompt, confirm_fn, restart_fn):
    try:
        from pynput.keyboard import Controller as _KbCtrl, Key as _Key
        _kb = _KbCtrl()
        _kb.press(_Key.ctrl)
        _kb.press('v')
        _kb.release('v')
        _kb.release(_Key.ctrl)
        _vera_confirm("default")
    except Exception:
        _tts_speak("Couldn't paste")
    return True


# --- Clipboard: copy ---
@_intent(245, r"\bcopy\s+(.+)$")
def _ih_clipboard_copy(m, t, allow_prompt, confirm_fn, restart_fn):
    text_to_copy = m.group(1).strip()
    try:
        import tkinter as _tk
        _r = _tk.Tk()
        _r.withdraw()
        _r.clipboard_clear()
        _r.clipboard_append(text_to_copy)
        _r.update()
        _r.destroy()
        _vera_confirm("default")
    except Exception:
        _tts_speak("Couldn't copy that")
    return True


# --- State detection ("I'm tired", "I'm playing SC", etc.) ---
@_intent(210, r"\bi('m| am)\s+(tired|exhausted|sleepy|bored|hungry|frustrated|stressed|anxious|happy|good|great|feeling\s+\w+|playing\s+.+|working\s+.+|gaming\b)")
def _ih_state(m, t, allow_prompt, confirm_fn, restart_fn):
    from memory import set_session as _set_session, get_session as _get_session
    import random as _r
    state = m.group(2).strip().lower()

    # Detect activity vs mood
    if state.startswith("playing "):
        activity = state[8:].strip()
        _set_session("activity", activity)
        _set_session("last_topic", f"playing {activity}")
        responses = [
            f"Nice, have a good session",
            f"Sounds fun, let me know if you need anything",
            f"Got it, I'll be here if you need me",
        ]
        _tts_speak(_r.choice(responses))
        return True

    if state in ("working", "gaming"):
        _set_session("activity", state)
        _set_session("last_topic", state)
        _tts_speak(_r.choice(["Got it, I'll stay out of your way", "Okay, here if you need me"]))
        return True

    # Mood states
    _set_session("mood", state)
    _set_session("last_topic", state)

    mood_responses = {
        "tired":       (["Rough day? Hope you can rest soon", "You doing okay?", "Take it easy when you can"], True),
        "exhausted":   (["Take a break when you can", "You should rest up", "Hope you get some downtime soon"], False),
        "sleepy":      (["Maybe wrap up soon and get some sleep", "Don't push too hard", "Rest up when you can"], False),
        "bored":       (["Want me to put something on? I can open Spotify", "Anything I can do to help?", "I got you, what do you want to do"], True),
        "hungry":      (["Go grab something to eat, I'll be here", "You should eat something", "Don't let me keep you from food"], False),
        "frustrated":  (["What's going on?", "Talk to me, what happened?", "I hear you, what's up?"], True),
        "stressed":    (["What's going on?", "Take a breath, what's up?", "I'm here, what do you need?"], True),
        "anxious":     (["You alright?", "What's on your mind?", "I'm here if you want to talk"], True),
        "happy":       (["That's what I like to hear", "Good, keep that energy", "Love to hear it"], False),
        "good":        (["Good to hear", "Glad you're doing well", "Nice, let's keep it that way"], False),
        "great":       (["Let's go, good energy", "Love to hear it", "That's what's up"], False),
    }

    # Fuzzy match mood key
    matched_key = None
    for key in mood_responses:
        if key in state:
            matched_key = key
            break

    if matched_key:
        pool, _ = mood_responses[matched_key]
        _tts_speak(_r.choice(pool))
    else:
        _tts_speak(_r.choice(["Got it", "I hear you", "Noted"]))
    return True


# --- Jokes ---
@_intent(200, r"\b(tell me a joke|say a joke|give me a joke|tell a joke|make me laugh|joke)\b")
def _ih_joke(m, t, allow_prompt, confirm_fn, restart_fn):
    _tts_speak(get_joke())
    return True


# Pre-sort the registry once at import time for fast dispatch
_INTENT_REGISTRY.sort(key=lambda x: -x[0])


def handle_transcript(text: str, allow_prompt: bool = True, confirm_fn=None, restart_fn=None) -> bool:
    """
    Clean the transcript through preprocess_transcript, then dispatch to the
    first registered intent handler whose pattern matches. Returns True if a
    handler claimed the transcript.
    """
    _log_transcript(text)
    t = preprocess_transcript(text)
    if not t or t in _NOISE_WORDS:
        return False

    from memory import increment_command_count as _inc_cmd
    for _priority, pattern, handler in _INTENT_REGISTRY:
        m = pattern.search(t)
        if m:
            if handler(m, t, allow_prompt, confirm_fn, restart_fn):
                _inc_cmd()
                return True

    if handle_social(t, _tts_speak):
        return True

    _tts_speak(get_fallback())
    return False
