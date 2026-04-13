"""Simple skills for the standalone assistant."""

from __future__ import annotations

import re
import difflib
import threading
import time
import os
import json
from urllib.parse import quote_plus
import subprocess
import webbrowser

from config import load_config
from personality import get_confirm, handle_social, get_fallback, get_joke, get_failure


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

_VERA_KOKORO_VOICE_DEFAULT = "af_heart"
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


def _get_tts_device():
    """Return sounddevice device index for the configured TTS output device, or None for default."""
    import sounddevice as sd
    device_name = load_config().get("tts_output_device", None)
    if not device_name:
        return None
    devices = sd.query_devices()
    for i, d in enumerate(devices):
        if d["max_output_channels"] > 0 and device_name.lower() in d["name"].lower():
            return i
    return None


def _kokoro_tts_play(text: str) -> None:
    """Generate and play audio via Kokoro TTS synchronously. Falls back to pyttsx3."""
    try:
        import sounddevice as sd  # type: ignore
        kokoro = _get_kokoro()
        voice = load_config().get("tts_voice", _VERA_KOKORO_VOICE_DEFAULT)
        samples, sample_rate = kokoro.create(text, voice=voice, speed=1.0, lang="en-us")
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


_tts_hooks: list = []  # callables(text) registered externally to observe TTS output
_tts_idle = threading.Event()
_tts_idle.set()  # starts in idle state (not speaking)


def _wait_for_tts(timeout: float = 30.0) -> None:
    """Block until TTS is no longer playing (or timeout expires)."""
    _tts_idle.wait(timeout=timeout)


def _tts_speak(text: str, bypass_mute: bool = False) -> bool:
    if _vera_muted["value"] and not bypass_mute:
        return False
    for _hook in _tts_hooks:
        try:
            _hook(text)
        except Exception:
            pass
    _tts_idle.clear()  # mark busy before thread starts so callers see it immediately
    def _speak_and_signal():
        try:
            _kokoro_tts_play(text)
        finally:
            _tts_idle.set()
    try:
        threading.Thread(target=_speak_and_signal, daemon=True).start()
        _log_event(f"TTS_SPEAK: {text}")
        return True
    except Exception as exc:
        print(f"TTS failed: {exc}")
        _log_event(f"TTS_FAILED: {exc}")
        return False


def _kokoro_tts_play_device(text: str) -> None:
    """Play TTS through the configured voice output device (for read out command only)."""
    try:
        import sounddevice as sd
        kokoro = _get_kokoro()
        voice = load_config().get("tts_voice", _VERA_KOKORO_VOICE_DEFAULT)
        samples, sample_rate = kokoro.create(text, voice=voice, speed=1.0, lang="en-us")
        device = _get_tts_device()
        sd.play(samples, samplerate=sample_rate, device=device)
        sd.wait()
    except Exception as e:
        _log_event(f"TTS_DEVICE_ERROR: {e}")
        _kokoro_tts_play(text)


def _tts_speak_to_device(text: str) -> bool:
    """Speak through the configured voice output device (read out command only)."""
    try:
        threading.Thread(target=_kokoro_tts_play_device, args=(text,), daemon=True).start()
        _log_event(f"TTS_DEVICE_SPEAK: {text}")
        return True
    except Exception as exc:
        _log_event(f"TTS_DEVICE_FAILED: {exc}")
        return False


def _vera_confirm(category: str = "default") -> None:
    """Speak a random confirmation line appropriate for the action category."""
    _tts_speak(get_confirm(category))


def _vera_failure(category: str = "default") -> None:
    """Speak a random failure line appropriate for the action category."""
    _tts_speak(get_failure(category))


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
    m = re.search(r"\b(set\s+a\s+timer|set\s+timer|timer)\s+(for\s+)?(\d+|\w+)\s*(seconds?|secs?|minutes?|mins?|hours?|hrs?)?\b", text)
    if not m:
        return None
    raw = m.group(3)
    if raw.isdigit():
        value = int(raw)
    else:
        value = _word_to_num(raw)
        if value is None:
            return None
    unit = (m.group(4) or "seconds").lower()
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

# ---------------------------------------------------------------------------
# User mishear corrections (runtime-loaded from data/user_mishears.json)
# ---------------------------------------------------------------------------
_USER_MISHEAR_PATH = os.path.join(os.path.dirname(__file__), "data", "user_mishears.json")
_UNMATCHED_PATH = os.path.join(os.path.dirname(__file__), "data", "unmatched.json")


def _load_user_mishears() -> dict:
    """Return user corrections from data/user_mishears.json, or {} on error."""
    import json
    if not os.path.exists(_USER_MISHEAR_PATH):
        return {}
    try:
        with open(_USER_MISHEAR_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def _normalize_mishear(text: str) -> str:
    """Strip punctuation and lowercase — matches what preprocess_transcript sees."""
    return re.sub(r"[^\w\s]", "", text.strip().lower())


def save_user_mishear(mishear: str, correction: str) -> None:
    """Add or update a user correction and persist to disk."""
    import json
    os.makedirs(os.path.dirname(_USER_MISHEAR_PATH), exist_ok=True)
    data = _load_user_mishears()
    key = _normalize_mishear(mishear)
    val = _normalize_mishear(correction)
    data[key] = val
    with open(_USER_MISHEAR_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    # Merge into live map immediately so it takes effect without restart
    _MISHEAR_MAP[key] = val


def log_unmatched(raw_text: str) -> None:
    """Append a raw transcript to data/unmatched.json when no intent matched."""
    import json
    os.makedirs(os.path.dirname(_UNMATCHED_PATH), exist_ok=True)
    entries: list = []
    if os.path.exists(_UNMATCHED_PATH):
        try:
            with open(_UNMATCHED_PATH, "r", encoding="utf-8") as f:
                entries = json.load(f)
            if not isinstance(entries, list):
                entries = []
        except Exception:
            entries = []
    entry = raw_text.strip()
    if entry and entry not in entries:
        entries.append(entry)
        with open(_UNMATCHED_PATH, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)


_GROQ_HANDLED_PATH = os.path.join(os.path.dirname(__file__), "data", "groq_handled.json")


def log_groq_handled(raw_text: str) -> None:
    """Log a transcript that Groq handled conversationally — not a real skill."""
    import json
    os.makedirs(os.path.dirname(_GROQ_HANDLED_PATH), exist_ok=True)
    entries: list = []
    if os.path.exists(_GROQ_HANDLED_PATH):
        try:
            with open(_GROQ_HANDLED_PATH, "r", encoding="utf-8") as f:
                entries = json.load(f)
            if not isinstance(entries, list):
                entries = []
        except Exception:
            entries = []
    entry = raw_text.strip()
    if entry and entry not in entries:
        entries.append(entry)
        with open(_GROQ_HANDLED_PATH, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)


def load_groq_handled() -> list:
    """Return the list of Groq-handled transcripts."""
    import json
    if not os.path.exists(_GROQ_HANDLED_PATH):
        return []
    try:
        with open(_GROQ_HANDLED_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []


def dismiss_groq_handled(raw_text: str) -> None:
    """Remove a single entry from the groq handled list."""
    import json
    entries = load_groq_handled()
    entries = [e for e in entries if e != raw_text]
    with open(_GROQ_HANDLED_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)


def load_unmatched() -> list:
    """Return the list of unmatched transcripts."""
    import json
    if not os.path.exists(_UNMATCHED_PATH):
        return []
    try:
        with open(_UNMATCHED_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []


def dismiss_unmatched(raw_text: str) -> None:
    """Remove a single entry from the unmatched list."""
    import json
    entries = load_unmatched()
    entries = [e for e in entries if e != raw_text]
    os.makedirs(os.path.dirname(_UNMATCHED_PATH), exist_ok=True)
    with open(_UNMATCHED_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)


# Merge user corrections into the built-in map at import time
_MISHEAR_MAP.update(_load_user_mishears())


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
    r"\b(um+|uh+|hmm+|hm+|like|i mean|so|well|actually|basically|literally|right)\b"
)

# Conversational prefixes people naturally say before a command
_CONVERSATIONAL_PREFIX = re.compile(
    r"^(hey vera[,]?\s*|vera[,]?\s*|hey there[,]?\s*|"
    r"can you\s+|could you\s+|would you\s+|will you\s+|"
    r"please\s+|go ahead and\s+|go on and\s+|"
    r"i need you to\s+|i want you to\s+|i'd like you to\s+|id like you to\s+|"
    r"i need to\s+|i want to\s+|"
    r"hey can you\s+|hey could you\s+|hey would you\s+|"
    r"do me a favor and\s+|do me a favour and\s+)"
)

_LEADING_NOISE = re.compile(r"^(the|a|an|i|hey|so|well)\s+")
_TRAILING_NOISE = re.compile(r"\s+(please|now|for me|for me please|for me thanks|thanks|thank you|real quick)\s*$")

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
    # 5. Strip conversational prefixes ("can you", "hey vera", "i need you to", etc.)
    #    Loop to handle stacked prefixes e.g. "hey vera can you open discord"
    for _ in range(3):
        stripped = _CONVERSATIONAL_PREFIX.sub("", t).strip()
        if stripped == t:
            break
        t = stripped
    # 6. Strip leading noise words
    t = _LEADING_NOISE.sub("", t).strip()
    # 7. Strip trailing polite words that add no meaning
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
_vera_muted: dict = {"value": False, "status_fn": None}  # mute state + optional UI callback
_gaming_mode: dict = {"value": False, "status_fn": None}  # gaming mode state + optional UI callback
_groq_flash_fn = {"fn": None}  # callback to flash status bar when Groq responds


def set_groq_flash_callback(fn) -> None:
    """Register a callback to flash the status bar when Groq handles a response."""
    _groq_flash_fn["fn"] = fn


def trigger_groq_flash() -> None:
    """Fire the groq flash callback if registered."""
    fn = _groq_flash_fn.get("fn")
    if fn:
        try:
            fn()
        except Exception:
            pass


def set_mute_status_callback(fn) -> None:
    """Register a callback to update the UI status bar when mute state changes."""
    _vera_muted["status_fn"] = fn


def is_muted() -> bool:
    return bool(_vera_muted["value"])


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
    "vera": None,  # handled via PID file — see _close_app
}


_PROTECTED_PROCESSES = {
    "explorer.exe", "winlogon.exe", "lsass.exe", "csrss.exe",
    "svchost.exe", "services.exe", "smss.exe", "wininit.exe",
    "system", "registry", "dwm.exe", "taskmgr.exe",
}


def _close_app(app_name: str) -> bool:
    normalized = _normalize_name(app_name)
    _norm_overrides = {_normalize_name(k): v for k, v in _CLOSE_OVERRIDES.items()}
    candidates = []

    if normalized in _norm_overrides:
        target = _norm_overrides[normalized]
        if target is None:
            # PID-based kill (e.g. vera — kills only this instance)
            try:
                pid_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "vera.pid")
                with open(pid_path) as _pf:
                    pid = int(_pf.read().strip())
                result = subprocess.run(["taskkill", "/f", "/pid", str(pid)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                _log_event(f"CLOSE_VERA_PID: {pid} -> rc={result.returncode}")
                return result.returncode == 0
            except Exception as exc:
                _log_event(f"CLOSE_VERA_PID_FAILED: {exc}")
                return False
        candidates.append(target)
    else:
        match = difflib.get_close_matches(normalized, list(_norm_overrides.keys()), n=1, cutoff=0.7)
        if match:
            candidates.append(_norm_overrides[match[0]])

    # Also try app name directly as exe
    candidates.append(normalized.replace(" ", "") + ".exe")

    for exe in candidates:
        if exe and exe.lower() in _PROTECTED_PROCESSES:
            _log_event(f"CLOSE_BLOCKED: {exe} is a protected process")
            return False
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
        return False
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
        "  open <app>  /  launch <app>",
        "  open that again",
        "  close <app>  /  close this",
        "  add alias <name> for <app>",
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
        "Volume:",
        "  mute / unmute",
        "  volume up / volume down",
        "  set volume <0-100>",
        "  set volume max",
        "  set <app> volume <0-100>",
        "",
        "Timers:",
        "  set a timer <n> minutes",
        "  set a timer <n> seconds",
        "  set a timer <n> hours",
        "  cancel timer",
        "",
        "Reminders:",
        "  remind me in <n> minutes to <message>",
        "  remind me at <time> to <message>",
        "  what are my reminders",
        "  cancel all reminders",
        "",
        "Notes:",
        "  note <text>",
        "  open notes",
        "  list notes",
        "  delete last note",
        "  clear all notes",
        "",
        "Clipboard:",
        "  read clipboard",
        "  copy <text>",
        "  paste that / paste clipboard",
        "  clear clipboard",
        "",
        "Time & Info:",
        "  what time is it",
        "  what's the date / what day is it",
        "  what's the weather in <city>",
        "  give me the news",
        "",
        "VERA:",
        "  be quiet / silence",
        "  you can talk / wake up vera",
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
        "  discord <server> <channel> <message>",
        "  read discord <channel>",
        "  discord delete <channel>",
        "  discord purge <channel> <n>",
        "",
        "AI:",
        "  ask <question>",
        "",
        "Memory:",
        "  my name is <name>",
        "  my birthday is <month> <day>",
        "  remember <fact>",
        "  forget <thing>",
        "  what do you know about me",
        "  what do you remember",
        "",
        "Key Binds:",
        "  <your phrase>  (configured in Actions tab)",
        "",
        "Conversation:",
        "  i'm tired / i'm happy / i'm stressed",
        "  i'm playing <game>",
        "  tell me a joke",
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
        ("Volume", [
            "mute  /  unmute",
            "volume up  /  volume down",
            "set volume <0-100>",
            "set volume max",
        ]),
        ("Timers", [
            "set a timer <n> minutes / seconds / hours",
            "cancel timer  /  stop timer",
        ]),
        ("Reminders", [
            "remind me in <n> minutes to <message>",
            "remind me at <time> to <message>",
            "what are my reminders",
            "cancel all reminders",
        ]),
        ("Notes", [
            "note <text>",
            "open notes  /  list notes",
            "delete last note  /  clear all notes",
        ]),
        ("Clipboard", [
            "read clipboard",
            "copy <text>",
            "paste that  /  paste clipboard",
            "clear clipboard",
        ]),
        ("Time & Date", [
            "what time is it",
            "what's the date  /  what day is it",
        ]),
        ("VERA", [
            "be quiet  /  silence",
            "you can talk  /  wake up vera",
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
            "discord <server> <channel> <message>",
            "read discord <channel>",
            "discord delete <channel>",
            "discord purge <channel> <n>",
        ]),
        ("AI", [
            "ask <question>",
        ]),
        ("Memory", [
            "my name is <name>",
            "my birthday is <month> <day>",
            "remember <fact>",
            "forget <thing>",
            "what do you know about me",
            "what do you remember",
        ]),
        ("Key Binds", [
            "<your phrase>  (configured in Actions tab)",
        ]),
        ("Conversation", [
            "i'm tired / happy / stressed / playing <game>",
            "tell me a joke",
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
        from pynput import KbController as Controller, Key  # type: ignore
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
        from pynput import KbController as Controller  # type: ignore
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


def _discord_read(channel_name: str, server_name: str = "") -> bool:
    cfg = load_config()
    token = cfg.get("discord_bot_token", "").strip()

    # Resolve server_id — check discord_servers list first, fall back to legacy single server_id
    guild_id = ""
    if server_name:
        servers = cfg.get("discord_servers", [])
        norm = _normalize_name(server_name)
        for s in servers:
            if isinstance(s, dict) and _normalize_name(s.get("nickname", "")) == norm:
                guild_id = str(s.get("server_id", "")).strip()
                break
    if not guild_id:
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


def _resolve_discord_webhook(channel_name: str, server_name: str = "") -> str:
    """Find webhook URL for a channel, optionally filtered by server nickname."""
    cfg = load_config()
    channels_cfg = cfg.get("discord_channels", {})

    # Normalize to list format
    if isinstance(channels_cfg, dict):
        channels = [{"name": k.lower(), "url": v, "server": ""} for k, v in channels_cfg.items()]
    elif isinstance(channels_cfg, list):
        channels = channels_cfg
    else:
        channels = []

    norm_ch = _normalize_name(channel_name)
    norm_srv = _normalize_name(server_name) if server_name else ""

    for ch in channels:
        ch_match = _normalize_name(ch.get("name", "")) == norm_ch
        srv_match = not norm_srv or _normalize_name(ch.get("server", "")) == norm_srv
        if ch_match and srv_match:
            return ch.get("url", "")
    return ""


def _discord_send(channel_name: str, message: str, server_name: str = "") -> bool:
    webhook_url = _resolve_discord_webhook(channel_name, server_name)

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
@_intent(1000, r"\b(what can i say|show commands|show help|list commands|what can you do|what can youtube|what do you do|what are you capable of)\b")
def _ih_help(m, t, allow_prompt, confirm_fn, restart_fn):
    threading.Thread(target=_show_help, daemon=True).start()
    return True


# --- Gaming Mode ---
_GAMING_CONFIRMS = ["Done", "On it", "Got it", "Done.", "Set.", "Sent.", "Closed."]


def _gaming_confirm() -> str:
    import random
    return random.choice(_GAMING_CONFIRMS)


@_intent(993, r"^(start|enable|turn on|activate)\s+(gaming mode|game mode)$")
def _ih_gaming_mode_on(m, t, allow_prompt, confirm_fn, restart_fn):
    _gaming_mode["value"] = True
    fn = _gaming_mode.get("status_fn")
    if fn:
        fn(True)
    _tts_speak("Gaming mode on.")
    return True


@_intent(993, r"^(stop|disable|turn off|deactivate|exit)\s+(gaming mode|game mode)$")
def _ih_gaming_mode_off(m, t, allow_prompt, confirm_fn, restart_fn):
    _gaming_mode["value"] = False
    fn = _gaming_mode.get("status_fn")
    if fn:
        fn(False)
    _tts_speak("Gaming mode off.")
    return True


# --- Game Overlay ---
_overlay_callbacks: dict = {"show": None, "hide": None}


@_intent(992, r"^(show|open|enable|turn on)\s+(the\s+)?(game\s+)?overlay$")
def _ih_show_overlay(m, t, allow_prompt, confirm_fn, restart_fn):
    fn = _overlay_callbacks.get("show")
    if fn:
        fn()
        _tts_speak("Overlay on.")
    return True


@_intent(992, r"^(hide|close|disable|turn off)\s+(the\s+)?(game\s+)?overlay$")
def _ih_hide_overlay(m, t, allow_prompt, confirm_fn, restart_fn):
    fn = _overlay_callbacks.get("hide")
    if fn:
        fn()
        _tts_speak("Overlay off.")
    return True


# --- Restart VERA ---
@_intent(990, r"(\b(restart|reboot)\s+(vera|assistant|the assistant)\b|^(restart|reboot)$)")
def _ih_restart_vera(m, t, allow_prompt, confirm_fn, restart_fn):
    from memory import clear_session as _clear_session
    _clear_session()
    _log_event("RESTART_IPA: voice command")
    if restart_fn is not None:
        restart_fn()  # calls os._exit(0) in finally — process dies here, no race
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
    if not _send_message(m.group(1).strip()):
        _vera_failure("send")
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
@_intent(879, r"\b(what is my name|do you know my name|what(?:s| is) my name)\b")
def _ih_ask_name(m, t, allow_prompt, confirm_fn, restart_fn):
    from memory import recall as _recall
    name = _recall("name")
    if name:
        _tts_speak(f"Your name is {name}")
    else:
        _tts_speak("I don't know your name yet. Tell me with 'my name is'")
    return True


# --- Memory: remember fact ---
@_intent(875, r"\b(remember|vera remember|don'?t forget)\s+(?:that\s+)?(.+)$")
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
        key = f"fact_{int(time.time())}"
        _remember(key, fact)
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
@_intent(876, r"\b(what do you know about me|what do about me|what about me|know about me|what do you remember|what have you remembered|tell me what you know)\b")
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


# ---------------------------------------------------------------------------
# Reminders
# ---------------------------------------------------------------------------

_REMINDERS_PATH = os.path.join(os.path.dirname(__file__), "data", "reminders.json")
_MACROS_PATH    = os.path.join(os.path.dirname(__file__), "data", "macros.json")


def load_macros() -> list:
    try:
        with open(_MACROS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_macros(macros: list) -> None:
    try:
        os.makedirs(os.path.dirname(_MACROS_PATH), exist_ok=True)
        with open(_MACROS_PATH, "w", encoding="utf-8") as f:
            json.dump(macros, f, indent=2)
    except Exception:
        pass


def _load_reminders() -> list:
    try:
        with open(_REMINDERS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_reminders(reminders: list) -> None:
    try:
        os.makedirs(os.path.dirname(_REMINDERS_PATH), exist_ok=True)
        with open(_REMINDERS_PATH, "w", encoding="utf-8") as f:
            json.dump(reminders, f)
    except Exception:
        pass


def check_due_reminders() -> list:
    """Return messages for any due reminders and remove them from storage."""
    reminders = _load_reminders()
    now = time.time()
    due = [r["msg"] for r in reminders if r["ts"] <= now]
    if due:
        _save_reminders([r for r in reminders if r["ts"] > now])
    return due


def _parse_reminder_time(s: str):
    """Parse time strings into a Unix timestamp. Returns None on failure."""
    import datetime
    s = s.strip().lower()
    # strip leading "in/for/at" prefix so bare "two minutes" also works
    s_bare = re.sub(r"^(in|for|at)\s+", "", s).strip()
    now = datetime.datetime.now()

    word_map = {
        "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "fifteen": 15, "twenty": 20, "thirty": 30, "forty": 40,
        "forty five": 45, "fortyfive": 45, "sixty": 60, "half": 30,
    }

    # "X minutes/hours" (with or without in/for prefix)
    m = re.match(
        r"(a|an|\d+|one|two|three|four|five|six|seven|eight|nine|ten|"
        r"fifteen|twenty|thirty|forty|forty five|fortyfive|sixty|half)\s+"
        r"(minute|minutes|min|mins|hour|hours|hr|hrs)",
        s_bare,
    )
    if m:
        qty_str = m.group(1)
        unit = m.group(2)
        qty = word_map.get(qty_str)
        if qty is None:
            try:
                qty = int(qty_str)
            except Exception:
                return None
        if "hour" in unit or "hr" in unit:
            return (now + datetime.timedelta(hours=qty)).timestamp()
        return (now + datetime.timedelta(minutes=qty)).timestamp()

    # "H:MM am/pm" or "H am/pm" or "H" (with or without "at" prefix)
    # Note: preprocess strips colons, so "9:30pm" arrives as "930pm"
    # Handle both colon and no-colon forms
    m = re.match(r"(\d{1,2})(?::?(\d{2}))?\s*(am|pm)?$", s_bare)
    if m:
        hour = int(m.group(1))
        raw_mins = m.group(2)
        # If no colon was present (preprocess stripped it), only treat as HMM if 3-4 digits total
        if raw_mins and not re.search(r":", s):
            # e.g. "930pm" → hour=9, raw_mins="30"
            minute = int(raw_mins)
        elif raw_mins:
            minute = int(raw_mins)
        else:
            minute = 0
        meridiem = m.group(3)
        if meridiem == "pm" and hour != 12:
            hour += 12
        elif meridiem == "am" and hour == 12:
            hour = 0
        target = now.replace(hour=hour % 24, minute=minute, second=0, microsecond=0)
        if target <= now:
            if meridiem is None and hour < 12:
                target = target.replace(hour=hour + 12)
            if target <= now:
                target += datetime.timedelta(days=1)
        return target.timestamp()

    return None


def _format_reminder_time(ts: float) -> str:
    import datetime
    dt = datetime.datetime.fromtimestamp(ts)
    now = datetime.datetime.now()
    time_str = dt.strftime("%I:%M %p").lstrip("0")
    return f"today at {time_str}" if dt.date() == now.date() else f"tomorrow at {time_str}"


# --- Set reminder ---
@_intent(873, r"\b(?:remind me|set (?:a )?reminder)\b")
def _ih_set_reminder(m, t, allow_prompt, confirm_fn, restart_fn):
    time_str = None
    msg = "reminder"

    # Pattern 1: [time] to [message]  e.g. "remind me in 5 minutes to take meds"
    m1 = re.search(r"\b(?:remind me|set (?:a )?reminder)\s+(?:for\s+)?(.+?)\s+to\s+(.+)$", t)
    if m1:
        ts = _parse_reminder_time(m1.group(1).strip())
        if ts is not None:
            time_str, msg = m1.group(1).strip(), m1.group(2).strip()

    # Pattern 2: to [message] [time]  e.g. "set a reminder to take meds in 5 minutes"
    if time_str is None:
        m2 = re.search(r"\b(?:remind me|set (?:a )?reminder)\s+to\s+(.+?)\s+((?:in|for|at)\s+.+)$", t)
        if m2:
            ts = _parse_reminder_time(m2.group(2).strip())
            if ts is not None:
                msg, time_str = m2.group(1).strip(), m2.group(2).strip()

    # Pattern 3: bare time, no message  e.g. "set a reminder for two minutes"
    if time_str is None:
        m3 = re.search(r"\b(?:remind me|set (?:a )?reminder)\s+(?:for\s+|in\s+|at\s+)?(.+)$", t)
        if m3:
            ts = _parse_reminder_time(m3.group(1).strip())
            if ts is not None:
                time_str = m3.group(1).strip()

    if time_str is None:
        _tts_speak("I didn't catch the time. Try 'remind me in 30 minutes to...' or 'remind me at 9pm to...'")
        return True

    reminders = _load_reminders()
    reminders.append({"ts": ts, "msg": msg})
    _save_reminders(reminders)
    label = f": {msg}" if msg != "reminder" else ""
    _tts_speak(f"Reminder set for {_format_reminder_time(ts)}{label}")
    return True


# --- Cancel all reminders ---
@_intent(871, r"\b(?:cancel all reminders|clear all reminders|delete all reminders|cancel my reminders|remove all reminders)\b")
def _ih_cancel_all_reminders(m, t, allow_prompt, confirm_fn, restart_fn):
    reminders = _load_reminders()
    count = len([r for r in reminders if r["ts"] > time.time()])
    _save_reminders([])
    if count == 0:
        _tts_speak("No reminders to cancel.")
    else:
        _tts_speak(f"Cleared {count} reminder{'s' if count > 1 else ''}.")
    return True


# --- List reminders ---
@_intent(872, r"\b(?:what are my reminders|list my reminders|show my reminders|do i have any reminders|my reminders)\b")
def _ih_list_reminders(m, t, allow_prompt, confirm_fn, restart_fn):
    import datetime as _dt
    reminders = _load_reminders()
    reminders = [r for r in reminders if r["ts"] > time.time()]
    if not reminders:
        _tts_speak("No reminders set.")
        return True
    reminders.sort(key=lambda r: r["ts"])
    parts = [f"{_format_reminder_time(r['ts'])}: {r['msg']}" for r in reminders]
    count = len(parts)
    _tts_speak(f"You have {count} reminder{'s' if count > 1 else ''}. " + ". ".join(parts))
    return True


# --- Type text ---
@_intent(830, r"\btype\s+(.+)$")
def _ih_type(m, t, allow_prompt, confirm_fn, restart_fn):
    if not _type_text(m.group(1).strip()):
        _vera_failure("typing")
    return True


# --- Read out (TTS) ---
@_intent(820, r"\bread\s+out\s+(.+)$")
def _ih_read_out(m, t, allow_prompt, confirm_fn, restart_fn):
    _tts_speak_to_device(m.group(1).strip())
    return True


# --- Discord read (server + channel OR channel only) ---
@_intent(812, r"\bread\s+discord\s+(\w+)\s+(\w+)\b")
def _ih_discord_read_server(m, t, allow_prompt, confirm_fn, restart_fn):
    # "read discord <server> <channel>"
    threading.Thread(target=_discord_read, args=(m.group(2).strip(), m.group(1).strip()), daemon=True).start()
    return True

@_intent(810, r"\bread\s+discord\s+(\w+)\b")
def _ih_discord_read(m, t, allow_prompt, confirm_fn, restart_fn):
    # "read discord <channel>"
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


# --- Discord send (server + channel + message OR channel + message) ---
@_intent(802, r"\bdiscord\s+(\w+)\s+(\w+)\s+(.+)$")
def _ih_discord_send_server(m, t, allow_prompt, confirm_fn, restart_fn):
    # "discord <server> <channel> <message>" — verify server exists first
    cfg = load_config()
    servers = cfg.get("discord_servers", [])
    server_names = [s.get("nickname", "").lower() for s in servers if isinstance(s, dict)]
    if _normalize_name(m.group(1).strip()) in [_normalize_name(s) for s in server_names]:
        _discord_send(m.group(2).strip(), m.group(3).strip(), m.group(1).strip())
        return True
    return False  # fall through to channel-only handler

@_intent(800, r"\bdiscord\s+(\w+)\s+(.+)$")
def _ih_discord_send(m, t, allow_prompt, confirm_fn, restart_fn):
    # "discord <channel> <message>"
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
# High-priority variant: fires when transcript explicitly STARTS with "note/notes",
# outranking the memory "remember" handler (875) so "note remember to..." saves a note.
@_intent(886, r"^(note|notes|take a note|add note)\s+(.+)$")
def _ih_note_add_explicit(m, t, allow_prompt, confirm_fn, restart_fn):
    note_text = m.group(2).strip()
    if note_text:
        _append_note(note_text)
        _vera_confirm("note")
    return True


@_intent(740, r"\b(note|notes|take a note|add note)\b\s*(.+)?$")
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
    else:
        _vera_failure("volume")
    return True


# --- Unmute ---
@_intent(655, r"\b(un\s*mute|unmute audio|unmute volume|sound on|audio on|volume on|turn sound on|turn audio on)\b")
def _ih_unmute(m, t, allow_prompt, confirm_fn, restart_fn):
    restore = _saved_volume["level"] if _saved_volume["level"] is not None else 50
    if _set_volume(restore):
        _saved_volume["level"] = None
        _vera_confirm("volume")
    else:
        _vera_failure("volume")
    return True


# --- Volume max ---
@_intent(650, r"\b(set\s+volume\s+(max|maximum|full)|turn\s+(the\s+)?volume\s+(up\s+)?(to\s+)?(max|maximum|full)|volume\s+(to\s+)?(max|maximum|full))\b")
def _ih_volume_max(m, t, allow_prompt, confirm_fn, restart_fn):
    if _set_volume(100):
        _vera_confirm("volume")
    else:
        _vera_failure("volume")
    return True


# --- Volume set ---
@_intent(645, r"\bset\s+volume\s+(\d{1,3}|\w+)\b")
def _ih_volume_set(m, t, allow_prompt, confirm_fn, restart_fn):
    raw = m.group(1)
    level = int(raw) if raw.isdigit() else _word_to_num(raw)
    if level is not None:
        level = max(0, min(100, round(int(level) / 10) * 10))
        if _set_volume(level):
            _vera_confirm("volume")
        else:
            _vera_failure("volume")
    return True


# --- Volume up ---
@_intent(640, r"\b(volume\s+up|turn\s+(the\s+)?volume\s+up|raise\s+(the\s+)?volume|volume\s+higher|louder)\b")
def _ih_volume_up(m, t, allow_prompt, confirm_fn, restart_fn):
    if _adjust_volume("up"):
        _vera_confirm("volume")
    else:
        _vera_failure("volume")
    return True


# --- Volume down ---
@_intent(635, r"\b(volume\s+down|turn\s+(the\s+)?volume\s+down|lower\s+(the\s+)?volume|volume\s+lower|quieter|quiet(er)?\s+down)\b")
def _ih_volume_down(m, t, allow_prompt, confirm_fn, restart_fn):
    if _adjust_volume("down"):
        _vera_confirm("volume")
    else:
        _vera_failure("volume")
    return True


# --- Per-app volume ---
@_intent(803, r"\bset\s+(.+?)\s+volume\s+(?:to\s+)?(\d{1,3}|\w+)\b")
def _ih_app_volume(m, t, allow_prompt, confirm_fn, restart_fn):
    app_name = m.group(1).strip().lower()
    raw_level = m.group(2).strip()
    try:
        from pycaw.pycaw import AudioUtilities  # type: ignore
        import comtypes  # type: ignore
        comtypes.CoInitialize()
        try:
            level = int(raw_level)
        except ValueError:
            _tts_speak("I didn't catch the volume level")
            return True
        level = max(0, min(100, level))
        sessions = AudioUtilities.GetAllSessions()
        matched = []
        for session in sessions:
            if session.Process and app_name in session.Process.name().lower():
                matched.append(session)
        if not matched:
            _tts_speak(f"I couldn't find {app_name} running")
            return True
        success = False
        for session in matched:
            try:
                vol = session.SimpleAudioVolume
                vol.SetMasterVolume(level / 100.0, None)
                success = True
            except Exception:
                pass
        if success:
            _vera_confirm("volume")
        else:
            _vera_failure("volume")
    except Exception as exc:
        _log_event(f"APP_VOLUME_FAILED: {exc}")
        _vera_failure("volume")
    return True


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


# --- Command macros (premium) ---
@_intent(460, r"^.+$")
def _ih_macros(m, t, allow_prompt, confirm_fn, restart_fn):
    macros = load_macros()
    if not macros:
        return False
    norm_t = _normalize_text(t)
    for macro in macros:
        phrase = str(macro.get("phrase", "")).strip().lower()
        steps  = macro.get("steps", [])
        if not phrase or not steps:
            continue
        if _normalize_text(phrase) != norm_t:
            continue
        try:
            from license import is_premium as _is_premium
            _premium = _is_premium()
        except Exception:
            _premium = False
        if not _premium:
            _tts_speak("Command macros require a premium license.")
            return True
        def _run_steps(steps=steps):
            import time as _t
            for step in steps:
                handle_transcript(step, allow_prompt=False, confirm_fn=confirm_fn, restart_fn=restart_fn)
                _wait_for_tts()   # wait for any TTS from this step to finish
                _t.sleep(1.5)     # then add the fixed gap before the next step
        threading.Thread(target=_run_steps, daemon=True).start()
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


# --- Spotify / media keys ---
@_intent(400, r"^.+$")
def _ih_spotify(m, t, allow_prompt, confirm_fn, restart_fn):
    cfg = load_config()
    spotify_enabled = cfg.get("spotify_media", False)
    require_spotify = cfg.get("spotify_requires_keyword", True)
    keywords = _get_spotify_keywords(cfg)
    has_spotify = _has_keyword(t, keywords)

    # Spotify search — requires spotify_media enabled
    if spotify_enabled and (not require_spotify or has_spotify):
        sp_search = re.search(r"\bspotify\s+(?:play\s+|search\s+)?(.+)$", t)
        if sp_search:
            query = sp_search.group(1).strip()
            if query not in ("play", "pause", "next", "skip", "previous", "back", "resume", "stop"):
                if _spotify_search(query):
                    return True

    # Media keys — work with any player (Spotify, Apple Music, etc.)
    action = None
    if re.search(r"\b(play|pause|resume|stop)(\s+(song|track|music|video|vid))?\b", t):
        action = "play_pause"
    elif re.search(r"\b(next|skip)(\s+(song|track))?\b", t):
        action = "next"
    elif re.search(r"\b(previous|back|rewind)(\s+(song|track))?\b", t):
        action = "previous"
    if action:
        return bool(_media_key(action))
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
            timeout=5,
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
    _vera_failure("close")
    return True


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
        from memory import set_session as _ss
        _ss("last_command", "open")
        _ss("last_app", app)
        _vera_confirm("open")
    else:
        _vera_failure("open")
        result = True
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


# --- Clipboard helpers (subprocess — reliable on all Windows installs) ---
def _clip_get() -> str:
    import subprocess
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Get-Clipboard"],
            capture_output=True, text=True, timeout=8,
            creationflags=0x08000000,  # CREATE_NO_WINDOW
        )
        return result.stdout.rstrip("\r\n")
    except Exception:
        return ""


def _clip_set(text: str) -> None:
    import subprocess
    # clip.exe is built into Windows and reliably writes to clipboard
    proc = subprocess.Popen(
        ["clip"],
        stdin=subprocess.PIPE,
        creationflags=0x08000000,  # CREATE_NO_WINDOW
    )
    proc.communicate(input=text.encode("utf-16-le"))


# --- Clipboard: read ---
@_intent(260, r"\bread\s+clipboard\b")
def _ih_clipboard_read(m, t, allow_prompt, confirm_fn, restart_fn):
    try:
        clip = _clip_get().strip()
        _tts_speak(clip if clip else "Clipboard is empty")
    except Exception:
        _tts_speak("Couldn't read the clipboard")
    return True


# --- Clipboard: clear ---
@_intent(255, r"\bclear\s+clipboard\b")
def _ih_clipboard_clear(m, t, allow_prompt, confirm_fn, restart_fn):
    try:
        _clip_set("")
        _vera_confirm("default")
    except Exception:
        _tts_speak("Couldn't clear the clipboard")
    return True


# --- Clipboard: paste ---
@_intent(250, r"\bpaste(?:\s+(?:clipboard|that|it|this|text|now))?\b")
def _ih_clipboard_paste(m, t, allow_prompt, confirm_fn, restart_fn):
    try:
        import time as _time
        from pynput import KbController as _KbCtrl, Key as _Key
        _vera_confirm("default")
        _time.sleep(0.5)  # let focus return to target window before keystroke
        _kb = _KbCtrl()
        _kb.press(_Key.ctrl)
        _kb.press('v')
        _kb.release('v')
        _kb.release(_Key.ctrl)
    except Exception:
        _tts_speak("Couldn't paste")
    return True


# --- Clipboard: copy ---
@_intent(245, r"\bcopy\s+(.+)$")
def _ih_clipboard_copy(m, t, allow_prompt, confirm_fn, restart_fn):
    text_to_copy = m.group(1).strip()
    try:
        _clip_set(text_to_copy)
        _vera_confirm("default")
    except Exception:
        _tts_speak("Couldn't copy that")
    return True


# --- State detection ("I'm tired", "I'm playing SC", etc.) ---
@_intent(210, r"\bi('m|m| am)\s+(tired|exhausted|sleepy|bored|hungry|frustrated|stressed|anxious|happy|good|great|feeling\s+\w+|playing\s+.+|working\s+.+|gaming\b)")
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
    import time as _time
    _set_session("mood", state)
    _set_session("mood_time", _time.time())
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


# --- Birthday ---
_MONTH_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}

@_intent(877, r"\bmy birthday is\s+(.+)$")
def _ih_set_birthday(m, t, allow_prompt, confirm_fn, restart_fn):
    import re as _re
    raw = m.group(1).strip()
    # Try to parse month and day from the phrase
    month = None
    day = None

    # Match patterns like "october 15", "the 15th of october", "15th october"
    month_match = _re.search(r"(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)", raw)
    day_match = _re.search(r"\b(\d{1,2})(st|nd|rd|th)?\b", raw)

    if month_match:
        month = _MONTH_MAP.get(month_match.group(1).lower())
    if day_match:
        day = int(day_match.group(1))

    if not month or not day or not (1 <= day <= 31):
        _tts_speak("I couldn't quite catch that. Try saying something like 'my birthday is October 15th'.")
        return True

    # Save to config
    import json as _json
    cfg = load_config()
    cfg["birthday_month"] = month
    cfg["birthday_day"] = day
    from config import save_config as _save
    _save(cfg)

    month_name = list(_MONTH_MAP.keys())[list(_MONTH_MAP.values()).index(month)].capitalize()
    _tts_speak(f"Got it, I'll remember your birthday is {month_name} {day}.")
    return True


# --- Mute / Unmute ---
@_intent(950, r"\b(mute|be quiet|shut up vera|silence|go quiet|stop talking)\b")
def _ih_mute(m, t, allow_prompt, confirm_fn, restart_fn):
    _vera_muted["value"] = True
    fn = _vera_muted.get("status_fn")
    if fn:
        fn("Muted")
    _log_event("VERA_MUTED")
    return True


@_intent(951, r"\b(unmute|you can talk|start talking|come back|wake up vera|i can hear you now|okay vera|ok vera|vera come back|vera unmute)\b")
def _ih_unmute(m, t, allow_prompt, confirm_fn, restart_fn):
    _vera_muted["value"] = False
    fn = _vera_muted.get("status_fn")
    if fn:
        fn(None)  # None tells assistant.py to restore the real status label
    _tts_speak("I'm back.", bypass_mute=True)
    _log_event("VERA_UNMUTED")
    return True


# --- Time ---
@_intent(820, r"\b(what(?:'?s| is) the time|what time is it|current time|tell me the time)\b")
def _ih_time(m, t, allow_prompt, confirm_fn, restart_fn):
    import datetime as _dt
    now = _dt.datetime.now()
    hour = now.strftime("%I").lstrip("0") or "12"
    minute = now.strftime("%M")
    period = now.strftime("%p").lower()
    if minute == "00":
        _tts_speak(f"It's {hour} {period}")
    else:
        _tts_speak(f"It's {hour} {minute} {period}")
    return True


# --- Date ---
@_intent(818, r"\b(what(?:'?s| is) (the |today'?s? )?date|what day is it|what(?:'?s| is) today|today'?s? date)\b")
def _ih_date(m, t, allow_prompt, confirm_fn, restart_fn):
    import datetime as _dt
    now = _dt.datetime.now()
    day_name  = now.strftime("%A")
    month     = now.strftime("%B")
    day       = now.strftime("%d").lstrip("0")
    year      = now.strftime("%Y")
    _tts_speak(f"Today is {day_name}, {month} {day}, {year}")
    return True


# --- News ---
_NEWS_FEEDS = {
    "BBC":         "https://feeds.bbci.co.uk/news/rss.xml",
    "Reuters":     "https://feeds.reuters.com/reuters/topNews",
    "NPR":         "https://feeds.npr.org/1001/rss.xml",
    "AP News":     "https://rsshub.app/apnews/topics/apf-topnews",
    "The Guardian":"https://www.theguardian.com/world/rss",
    "Al Jazeera":  "https://www.aljazeera.com/xml/rss/all.xml",
}

@_intent(815, r"\b(give me the news|read the news|whats?(?:\s+(?:in|the))*\s+news(?: today)?|what is(?:\s+(?:in|the))*\s+news(?: today)?|news briefing|top headlines|headlines)\b")
def _ih_news(m, t, allow_prompt, confirm_fn, restart_fn):
    import urllib.request as _ur
    import urllib.error as _ue
    import xml.etree.ElementTree as _xml

    cfg = load_config()
    source = cfg.get("news_source", "BBC")
    url = _NEWS_FEEDS.get(source, _NEWS_FEEDS["BBC"])

    try:
        req = _ur.Request(url, headers={"User-Agent": "curl/7.0"})
        with _ur.urlopen(req, timeout=8) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")

        root = _xml.fromstring(raw)
        # RSS titles are in channel/item/title
        items = root.findall(".//item/title")
        if not items:
            _tts_speak("Couldn't find any headlines right now.")
            return True

        headlines = []
        for item in items[:5]:
            text = (item.text or "").strip()
            # Strip CDATA markers if present
            text = text.replace("<![CDATA[", "").replace("]]>", "").strip()
            if text:
                headlines.append(text)

        if not headlines:
            _tts_speak("No headlines available right now.")
            return True

        intro = f"Here are the top headlines from {source}. "
        body = ". ".join(f"{i+1}. {h}" for i, h in enumerate(headlines)) + "."
        _tts_speak(intro + body)

    except _ue.URLError:
        _tts_speak("I can't reach the news right now. Check your connection.")
    except Exception:
        _tts_speak("Had trouble pulling the news. Try again in a moment.")

    return True


# --- Weather ---
@_intent(810, r"\b(what(?:s| is) the weather(?: like)?(?:\s+(?:in|for|at)\s+(.+))?|weather(?: in| for| at)?\s+(.+)?|how(?:s| is) the weather(?: (?:in|for|at)\s+(.+))?)\b")
def _ih_weather(m, t, allow_prompt, confirm_fn, restart_fn):
    import urllib.request as _ur
    import urllib.error as _ue

    # Extract city from whichever capture group matched
    city = None
    for g in m.groups()[1:]:
        if g and g.strip():
            city = g.strip()
            break

    if not city:
        # No city — ask the user
        _tts_speak("What city do you want the weather for?")
        return True

    try:
        import json as _json
        url = f"https://wttr.in/{quote_plus(city)}?format=j1"
        req = _ur.Request(url, headers={"User-Agent": "curl/7.0"})
        with _ur.urlopen(req, timeout=6) as resp:
            data = _json.loads(resp.read().decode("utf-8"))

        cur = data["current_condition"][0]
        desc = cur["weatherDesc"][0]["value"]
        temp_f = cur["temp_F"]
        feels_f = cur["FeelsLikeF"]
        humidity = cur["humidity"]

        _tts_speak(
            f"Weather in {city}: {desc}, {temp_f} degrees, feels like {feels_f}, humidity {humidity} percent."
        )

    except _ue.URLError:
        _tts_speak("I can't reach the weather service right now. Check your connection.")
    except Exception:
        _tts_speak(f"Couldn't get the weather for {city}.")

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

    # Track repeat transcripts for conversational awareness
    from memory import get_session as _gs, set_session as _ss, increment_command_count as _inc_cmd
    last_repeat = _gs("repeat_transcript")
    repeat_count = int(_gs("repeat_count") or 0)
    if last_repeat == t:
        _ss("repeat_count", repeat_count + 1)
    else:
        _ss("repeat_transcript", t)
        _ss("repeat_count", 0)

    for _priority, pattern, handler in _INTENT_REGISTRY:
        m = pattern.search(t)
        if m:
            if handler(m, t, allow_prompt, confirm_fn, restart_fn):
                _inc_cmd()
                return True

    if not _gaming_mode["value"]:
        if handle_social(t, _tts_speak):
            return True

    log_unmatched(t)
    if not _gaming_mode["value"]:
        _tts_speak(get_fallback())
    return False
