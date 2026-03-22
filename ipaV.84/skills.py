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


_MISHEAR_MAP = {
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

    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        win = tk.Toplevel(root)
        win.title("What Can I Say?")
        win.geometry("400x500")
        win.resizable(True, True)

        frame = tk.Frame(win)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")

        text_widget = tk.Text(frame, yscrollcommand=scrollbar.set, wrap="word", font=("Consolas", 10))
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=text_widget.yview)

        text_widget.insert("end", "\n".join(lines))
        text_widget.configure(state="disabled")

        win.protocol("WM_DELETE_WINDOW", lambda: (win.destroy(), root.destroy()))
        win.lift()
        win.focus_force()
        root.mainloop()
    except Exception as exc:
        print(f"Help display failed: {exc}")


def _press_key(key: str, count: int = 1) -> bool:
    try:
        from pynput import keyboard  # type: ignore
        ctl = keyboard.Controller()
        raw = str(key).strip().lower()
        if raw.startswith("<") and raw.endswith(">"):
            raw = raw[1:-1].strip()
        if len(raw) == 1:
            key_obj = keyboard.KeyCode.from_char(raw)
        else:
            key_obj = getattr(keyboard.Key, raw, None)
            if key_obj is None:
                _log_event(f"PRESS_KEY_FAILED: unknown key: {key}")
                return False
        for i in range(max(1, count)):
            ctl.press(key_obj)
            ctl.release(key_obj)
            if count > 1 and i < count - 1:
                time.sleep(0.1)
        _log_event(f"PRESS_KEY: {key} x{count}")
        return True
    except Exception as exc:
        _log_event(f"PRESS_KEY_FAILED: {exc}")
        return False


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
                        "User-Agent": "IPA-Assistant/1.0",
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
                        "User-Agent": "IPA-Assistant/1.0",
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
                        "User-Agent": "IPA-Assistant/1.0",
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


def _tts_speak(text: str) -> bool:
    try:
        import pyttsx3  # type: ignore
        def _run():
            try:
                engine = pyttsx3.init()
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                _log_event(f"TTS_ERROR: {e}")
        threading.Thread(target=_run, daemon=True).start()
        _log_event(f"TTS_SPEAK: {text}")
        return True
    except Exception as exc:
        print(f"TTS failed: {exc}")
        _log_event(f"TTS_FAILED: {exc}")
        return False


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
            "User-Agent": "IPA-Assistant/1.0",
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
                "User-Agent": "IPA-Assistant/1.0",
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


def handle_transcript(text: str, allow_prompt: bool = True, confirm_fn=None, restart_fn=None) -> bool:
    """
    Try to match transcript to skills.
    Returns True if a skill handled it.
    """
    _log_transcript(text)
    t = _apply_mishear_corrections(text.strip().lower())
    if not t:
        return False

    # Help
    if re.search(r"\b(what can i say|show commands|show help|list commands)\b", t):
        _show_help()
        return True

    # Restart IPA
    if re.search(r"\b(restart|reboot)\s+(ipa|assistant|the assistant)\b", t) or t.strip() in ("restart", "reboot"):
        _log_event("RESTART_IPA: voice command")
        if restart_fn is not None:
            threading.Thread(target=restart_fn, daemon=True).start()
        return True

    # Key binds (disabled — under development)

    # Send message (type + Enter)
    send_match = re.search(r"\bsend\s+message\s+(.+)$", t)
    if send_match:
        _send_message(send_match.group(1).strip())
        return True

    # Ask AI
    ask_match = re.search(r"^ask\s+(.+)$", t)
    if ask_match:
        _ask_ai(ask_match.group(1).strip())
        return True

    # Type text
    type_match = re.search(r"\btype\s+(.+)$", t)
    if type_match:
        text_to_type = type_match.group(1).strip()
        _type_text(text_to_type)
        return True

    # TTS
    say_match = re.search(r"\bread\s+out\s+(.+)$", t)
    if say_match:
        _tts_speak(say_match.group(1).strip())
        return True

    # Discord read
    discord_read_match = re.search(r"\bread\s+discord\s+(\w+)\b", t)
    if discord_read_match:
        threading.Thread(target=_discord_read, args=(discord_read_match.group(1).strip(),), daemon=True).start()
        return True

    # Discord send
    discord_match = re.search(r"\bdiscord\s+(\w+)\s+(.+)$", t)
    if discord_match:
        channel = discord_match.group(1).strip()
        msg = discord_match.group(2).strip()
        _discord_send(channel, msg)
        return True

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

    # Restart PC
    if re.search(r"\b(restart (the )?(pc|computer)|reboot (the )?(pc|computer))\b", t):
        if confirm_fn and not confirm_fn("Restart the computer?"):
            return True
        try:
            _run_command("shutdown /r /t 5")
        except Exception as exc:
            _log_event(f"RESTART_PC_FAILED: {exc}")
        return True

    # Shutdown PC
    if re.search(r"\b(shut down|shutdown|turn off|power off) (the )?(pc|computer)\b", t):
        if confirm_fn and not confirm_fn("Shut down the computer?"):
            return True
        try:
            _run_command("shutdown /s /t 5")
        except Exception as exc:
            _log_event(f"SHUTDOWN_PC_FAILED: {exc}")
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

    # Add alias
    alias_match = re.search(r"\badd alias\s+(.+?)\s+for\s+(.+)$", t)
    if alias_match:
        _add_alias(alias_match.group(1).strip(), alias_match.group(2).strip())
        return True

    open_match = re.search(r"\b(open|launch|start)\s+(.+)$", t)
    if open_match:
        app = open_match.group(2).strip()
        # Strip leading "the" inserted by accent mishears (e.g. "open the youtube")
        app = re.sub(r"^the\s+", "", app)
        # If app is a single unknown word and fuzzy-matches "youtube", open it
        if " " not in app and difflib.SequenceMatcher(None, app, "youtube").ratio() >= 0.6:
            if _youtube_search(""):
                return True
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
