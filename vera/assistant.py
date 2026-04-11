"""All-in-one UI + background listener for the standalone assistant."""

from __future__ import annotations

import threading
import queue
import subprocess
import sys
import traceback
import os
import time
import zipfile
import shutil
import tempfile
import urllib.request
import json
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QInputDialog,
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QFileDialog,
)
from PySide6.QtCore import Qt, QTimer, QObject, Signal
from PySide6.QtGui import QIcon, QCloseEvent

import ui
import wizard


# ---------------------------------------------------------------------------
# SimpleVar — drop-in replacement for tk.StringVar / tk.BooleanVar / tk.IntVar
# ---------------------------------------------------------------------------

class SimpleVar:
    """Minimal Tk variable replacement with .get(), .set(), .trace_add()."""

    def __init__(self, value=""):
        self._value = value
        self._write_callbacks: list = []
        self._ui_update = None   # optional direct widget updater set by ui.py

    def get(self):
        return self._value

    def set(self, value):
        self._value = value
        for cb in list(self._write_callbacks):
            try:
                cb()
            except Exception:
                pass

    def trace_add(self, mode: str, callback) -> None:
        if mode == "write":
            if callback not in self._write_callbacks:
                self._write_callbacks.append(callback)

    def trace_remove(self, mode: str, callback) -> None:
        if mode == "write":
            try:
                self._write_callbacks.remove(callback)
            except ValueError:
                pass


# ---------------------------------------------------------------------------
# UIBridge — thread-safe dispatcher from background threads to Qt main loop
# ---------------------------------------------------------------------------

class _UIBridge(QObject):
    """Carries arbitrary callables from background threads to the main thread."""
    _invoke = Signal(object)

    def __init__(self):
        super().__init__()
        self._invoke.connect(lambda fn: fn())

    def post(self, fn):
        """Call fn() on the Qt main thread (thread-safe from any thread)."""
        self._invoke.emit(fn)


_bridge = _UIBridge()

from app import MissingDependencyError, transcribe_mic, transcribe_mic_hold
from config import load_config, save_config, discover_apps
from skills import handle_transcript, log_unmatched
from steam import find_steam_apps


HOTKEY_CHOICES = [
    "<ctrl>+<alt>+s",
    "<ctrl>+<alt>+v",
    "<ctrl>+<shift>+s",
    "<ctrl>+<shift>+v",
    "<alt>+<shift>+s",
    "<alt>+<shift>+v",
    "<ctrl>+<alt>+<space>",
]

HOLD_CHOICES = ["caps_lock"]
LANG_CHOICES = ["English", "Spanish"]
UI_NOTIFY_INFO = None
UI_NOTIFY_ERROR = None
UI_CONFIRM = None


def _notify_info(title: str, message: str) -> None:
    if callable(UI_NOTIFY_INFO):
        UI_NOTIFY_INFO(title, message)
    else:
        QMessageBox.information(None, title, message)


def _notify_error(title: str, message: str) -> None:
    if callable(UI_NOTIFY_ERROR):
        UI_NOTIFY_ERROR(title, message)
    else:
        QMessageBox.critical(None, title, message)


def _confirm_dialog(title: str, message: str) -> bool:
    if callable(UI_CONFIRM):
        return bool(UI_CONFIRM(title, message))
    result = QMessageBox.question(None, title, message,
                                  QMessageBox.Yes | QMessageBox.No)
    return result == QMessageBox.Yes


class BackgroundListener:
    def __init__(self):
        self.listener = None
        self.mode = None
        self.stop_event = threading.Event()
        self.recording_flag = threading.Event()

    def stop(self):
        if self.listener is not None:
            try:
                self.listener.stop()
            except Exception:
                pass
        self.listener = None
        self.stop_event.clear()
        self.recording_flag.clear()

    def _play_ptt_beep(self, freq: int) -> None:
        threading.Thread(
            target=_ptt_beep,
            args=(freq, 60, load_config().get("ptt_beep_volume", 80)),
            daemon=True,
        ).start()

    def start_toggle(self, toggle_key: str, model_path: str, confirm_fn, on_text=None, restart_fn=None, on_record_start=None, on_record_end=None):
        from pynput import keyboard  # type: ignore

        def _record():
            if on_record_start:
                on_record_start()
            text = _run_hold(self.stop_event, toggle_key, model_path, confirm_fn=confirm_fn, restart_fn=restart_fn)
            if on_record_end:
                on_record_end()
            if on_text and text:
                on_text(text)
            self.recording_flag.clear()
            self.stop_event.clear()

        key_obj = _resolve_hold_key(toggle_key, keyboard)
        if not key_obj:
            raise ValueError("Invalid toggle key")

        def _on_press(key):
            if key == key_obj:
                if not self.recording_flag.is_set():
                    # First press — start recording
                    self.recording_flag.set()
                    self.stop_event.clear()
                    threading.Thread(target=_record, daemon=True).start()
                    self._play_ptt_beep(660)
                else:
                    # Second press — stop recording
                    self._play_ptt_beep(440)
                    self.stop_event.set()

        self.stop()
        self.mode = "toggle"
        self.listener = keyboard.Listener(on_press=_on_press)
        self.listener.start()

    def start_hold(self, hold_key: str, model_path: str, confirm_fn, on_text=None, restart_fn=None, on_record_start=None, on_record_end=None):
        from pynput import keyboard  # type: ignore

        def _record():
            if on_record_start:
                on_record_start()
            text = _run_hold(self.stop_event, hold_key, model_path, confirm_fn=confirm_fn, restart_fn=restart_fn)
            if on_record_end:
                on_record_end()
            if on_text and text:
                on_text(text)
            self.recording_flag.clear()
            self.stop_event.clear()

        if _is_mouse_button(hold_key):
            from pynput import mouse  # type: ignore
            button_obj = _resolve_mouse_button(hold_key, mouse)
            if not button_obj:
                raise ValueError("Invalid mouse button")

            _mouse_released = {"done": False}

            def _on_click(x, y, button, pressed):
                if button != button_obj:
                    return
                if pressed and not self.recording_flag.is_set():
                    _mouse_released["done"] = False
                    self.recording_flag.set()
                    self.stop_event.clear()
                    threading.Thread(target=_record, daemon=True).start()
                    self._play_ptt_beep(660)
                elif not pressed and self.recording_flag.is_set() and not _mouse_released["done"]:
                    _mouse_released["done"] = True
                    self._play_ptt_beep(440)
                    self.stop_event.set()

            self.stop()
            self.mode = "hold"
            self.listener = mouse.Listener(on_click=_on_click)
            self.listener.start()

        else:
            key_obj = _resolve_hold_key(hold_key, keyboard)
            if not key_obj:
                raise ValueError("Invalid hold key")

            # Caps Lock suppression — local only, never pushed to public build
            _caps_desired = {"state": None}
            _kb_released = {"done": False}
            _restoring_caps = {"active": False}

            def _on_press(key):
                if key == key_obj and not self.recording_flag.is_set() and not _restoring_caps["active"]:
                    if key == keyboard.Key.caps_lock:
                        try:
                            import ctypes
                            current = ctypes.windll.user32.GetKeyState(0x14) & 0x0001
                            _caps_desired["state"] = 0 if current else 1
                        except Exception:
                            pass
                    _kb_released["done"] = False
                    self.recording_flag.set()
                    self.stop_event.clear()
                    threading.Thread(target=_record, daemon=True).start()
                    self._play_ptt_beep(660)

            def _on_release(key):
                if key == key_obj and self.recording_flag.is_set() and not _kb_released["done"] and not _restoring_caps["active"]:
                    _kb_released["done"] = True
                    self._play_ptt_beep(440)
                    self.stop_event.set()
                    if key == keyboard.Key.caps_lock and _caps_desired["state"] is not None:
                        desired = _caps_desired["state"]
                        def _restore():
                            import time as _time
                            import ctypes as _ctypes
                            _time.sleep(0.15)
                            current = _ctypes.windll.user32.GetKeyState(0x14) & 0x0001
                            if current != desired:
                                _restoring_caps["active"] = True
                                _ctypes.windll.user32.keybd_event(0x14, 0, 0, 0)
                                _ctypes.windll.user32.keybd_event(0x14, 0, 2, 0)
                                _time.sleep(0.1)
                                _restoring_caps["active"] = False
                        threading.Thread(target=_restore, daemon=True).start()
                        _caps_desired["state"] = None

            self.stop()
            self.mode = "hold"
            self.listener = keyboard.Listener(on_press=_on_press, on_release=_on_release)
            self.listener.start()


def _resolve_hold_key(key_name: str, keyboard):
    if not key_name:
        return None
    raw = str(key_name).strip().lower()
    if raw.startswith("<") and raw.endswith(">"):
        raw = raw[1:-1].strip()
    if len(raw) == 1:
        return keyboard.KeyCode.from_char(raw)
    try:
        return getattr(keyboard.Key, raw)
    except Exception:
        return None


def _is_mouse_button(key_name: str) -> bool:
    return _normalize_record_key_name(key_name) in ("x1", "x2")


def _resolve_mouse_button(key_name: str, mouse):
    raw = _normalize_record_key_name(key_name)
    if raw == "x1":
        return mouse.Button.x1
    if raw == "x2":
        return mouse.Button.x2
    return None


def _normalize_record_key_name(key_name: str) -> str:
    raw = str(key_name).strip().lower()
    aliases = {
        "mouse back": "x1",
        "mouse back (x1)": "x1",
        "back mouse button": "x1",
        "mouse forward": "x2",
        "mouse fwd": "x2",
        "mouse fwd (x2)": "x2",
        "mouse forward (x2)": "x2",
        "forward mouse button": "x2",
    }
    return aliases.get(raw, raw)


def _format_record_key_name(key_name: str) -> str:
    raw = _normalize_record_key_name(key_name)
    if raw == "x1":
        return "Mouse Back"
    if raw == "x2":
        return "Mouse Forward"
    # Strip angle brackets for display — <caps_lock> → caps_lock
    display = str(key_name).strip()
    if display.startswith("<") and display.endswith(">"):
        display = display[1:-1]
    return display


def _run_mic(seconds: int, model_path: str, confirm_fn=None, allow_prompt: bool = True, restart_fn=None):
    try:
        text = transcribe_mic(seconds=seconds, model_path=model_path)
        if text:
            if not handle_transcript(text, allow_prompt=allow_prompt, confirm_fn=confirm_fn, restart_fn=restart_fn):
                log_unmatched(text)
        return text
    except MissingDependencyError as exc:
        _notify_error("Missing Dependency", str(exc))
    except Exception as exc:
        _notify_error("Error", str(exc))
    return ""


def _run_hold(stop_event: threading.Event, hold_key: str, model_path: str, confirm_fn=None, restart_fn=None):
    try:
        text = transcribe_mic_hold(stop_event=stop_event, model_path=model_path)
        if text:
            if not handle_transcript(text, allow_prompt=False, confirm_fn=confirm_fn, restart_fn=restart_fn):
                log_unmatched(text)
        return text
    except MissingDependencyError as exc:
        _notify_error("Missing Dependency", str(exc))
    except Exception as exc:
        _notify_error("Error", str(exc))
    return ""


def _ptt_beep(freq: int, duration_ms: int, volume: int) -> None:
    """Play a sine-wave beep at a specific volume (0-100) using winsound.PlaySound."""
    try:
        import winsound, struct, math
        import numpy as np
        sample_rate = 44100
        n_samples = int(sample_rate * duration_ms / 1000)
        amplitude = int(32767 * max(0, min(100, volume)) / 100)
        samples = [int(amplitude * math.sin(2 * math.pi * freq * i / sample_rate)) for i in range(n_samples)]
        # Build a minimal WAV in memory
        data = struct.pack(f"<{n_samples}h", *samples)
        header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF", 36 + len(data), b"WAVE",
            b"fmt ", 16, 1, 1, sample_rate, sample_rate * 2, 2, 16,
            b"data", len(data),
        )
        winsound.PlaySound(header + data, winsound.SND_MEMORY)
    except Exception:
        try:
            import winsound
            winsound.Beep(freq, duration_ms)
        except Exception:
            pass


def main() -> None:
    # Single instance enforcement — prevent multiple VERA windows
    _mutex = None
    try:
        import ctypes
        _mutex = ctypes.windll.kernel32.CreateMutexW(None, True, "VERASingleInstanceMutex")
        if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            _si_app = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.warning(None, "VERA", "VERA is already running.")
            return
    except Exception:
        pass

    # Write PID file so "close vera" can target this process specifically
    _pid_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "vera.pid")
    try:
        os.makedirs(os.path.dirname(_pid_path), exist_ok=True)
        with open(_pid_path, "w") as _pf:
            _pf.write(str(os.getpid()))
    except Exception:
        pass

    def _release_mutex():
        try:
            if _mutex:
                import ctypes as _ct
                _ct.windll.kernel32.ReleaseMutex(_mutex)
                _ct.windll.kernel32.CloseHandle(_mutex)
        except Exception:
            pass

    # --- Discord Rich Presence ---
    _RPC_CLIENT_ID = "1484663083438837801"
    _rpc = {"conn": None, "start": int(time.time())}

    def _rpc_connect():
        try:
            from pypresence import Presence
            rpc = Presence(_RPC_CLIENT_ID)
            rpc.connect()
            _rpc["conn"] = rpc
            _rpc_set("Standing by")
        except Exception:
            pass

    def _rpc_set(state: str):
        if not _rpc["conn"]:
            return
        try:
            _rpc["conn"].update(
                details="Voice assistant",
                state=state,
                start=_rpc["start"],
            )
        except Exception:
            _rpc["conn"] = None

    def _rpc_close():
        if _rpc["conn"]:
            try:
                _rpc["conn"].close()
            except Exception:
                pass
            _rpc["conn"] = None

    threading.Thread(target=_rpc_connect, daemon=True).start()

    _test_update_alert = "--test-update-alert" in sys.argv

    cfg = load_config()
    if cfg and "wizard_done" not in cfg:
        cfg["wizard_done"] = True
        save_config(cfg)

    if cfg:
        if discover_apps(cfg):
            save_config(cfg)

    try:
        import ctypes  # type: ignore
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("VERA.Assistant")
    except Exception:
        pass

    # --- PySide6 setup ---
    app = QApplication.instance() or QApplication(sys.argv)
    ui._apply_qt_theme(True)

    _quitting = {"flag": False}

    class _VERAWindow(QMainWindow):
        def closeEvent(self, event: QCloseEvent):
            if _quitting["flag"]:
                event.accept()
            else:
                _on_close()
                event.ignore()

        def changeEvent(self, event):
            from PySide6.QtCore import QEvent
            super().changeEvent(event)
            if event.type() == QEvent.WindowStateChange and self.isMinimized():
                if tray_ready["ok"]:
                    QTimer.singleShot(0, self.hide)

    root = _VERAWindow()
    root.setWindowTitle("VERA")
    root.resize(620, 560)
    root.setMinimumSize(580, 460)
    try:
        icon_path = os.path.join(os.path.dirname(__file__), "data", "assets", "ipa.ico")
        if os.path.exists(icon_path):
            root.setWindowIcon(QIcon(icon_path))
    except Exception:
        pass

    # --- State variables (SimpleVar replaces tk.StringVar / BooleanVar / IntVar) ---
    _saved_mode = cfg.get("mode", "hold")
    if _saved_mode == "mic":
        _saved_mode = "hold"  # migrate old timed mic users to hold
    mode = SimpleVar(value=_saved_mode)
    language = SimpleVar(value=cfg.get("language", "English"))
    seconds = SimpleVar(value=str(cfg.get("seconds", 5)))
    hotkey = SimpleVar(value=_normalize_record_key_name(cfg.get("hotkey", HOTKEY_CHOICES[0])))
    holdkey = SimpleVar(value=_normalize_record_key_name(cfg.get("hold_key", HOLD_CHOICES[0])))
    hotkey_display = SimpleVar(value=_format_record_key_name(hotkey.get()))
    holdkey_display = SimpleVar(value=_format_record_key_name(holdkey.get()))
    search_engine = SimpleVar(
        value=cfg.get("search_engine", "https://www.google.com/search?q={query}")
    )
    ptt_beep_volume = SimpleVar(value=int(cfg.get("ptt_beep_volume", 80)))

    # TTS output device — get available output device names for dropdown
    import sounddevice as _sd
    _all_devices = _sd.query_devices()
    tts_device_choices = ["Default"] + [d["name"] for d in _all_devices if d["max_output_channels"] > 0]
    tts_output_device = SimpleVar(value=cfg.get("tts_output_device", "") or "Default")
    tts_voice_choices = [
        "af_heart", "af_bella", "af_nicole", "af_sarah", "af_sky",
        "am_adam", "am_michael",
        "bf_emma", "bf_isabella",
        "bm_george", "bm_lewis",
    ]
    tts_voice = SimpleVar(value=cfg.get("tts_voice", "af_heart"))
    personality_mode = SimpleVar(value=cfg.get("personality_mode", "default"))
    bug_report_secret_var = SimpleVar(value=cfg.get("bug_report_secret", "") or "Z3JlZW5pc2RheQ==")
    premium = SimpleVar(value=bool(cfg.get("premium", False)))
    confirm_actions = SimpleVar(value=bool(cfg.get("confirm_actions", False)))
    spotify_media = SimpleVar(value=bool(cfg.get("spotify_media", False)))
    spotify_requires = SimpleVar(value=bool(cfg.get("spotify_requires_keyword", False)))
    spotify_keywords = SimpleVar(value=str(cfg.get("spotify_keywords", "spotify")))
    news_source = SimpleVar(value=cfg.get("news_source", "BBC"))
    birthday_month = SimpleVar(value=str(cfg.get("birthday_month", "")))
    birthday_day = SimpleVar(value=str(cfg.get("birthday_day", "")))

    actions = cfg.get("actions", [])
    if not isinstance(actions, list):
        actions = []
    actions = [
        {"phrase": str(a.get("phrase", "")).strip(), "command": str(a.get("command", "")).strip()}
        for a in actions
        if isinstance(a, dict)
    ]

    apps = []
    apps_cfg = cfg.get("apps", {})
    if isinstance(apps_cfg, dict):
        for name, command in apps_cfg.items():
            apps.append({"name": str(name).lower(), "command": str(command)})

    aliases = []
    aliases_cfg = cfg.get("app_aliases", {})
    if isinstance(aliases_cfg, dict):
        for alias, target in aliases_cfg.items():
            aliases.append({"alias": str(alias).lower(), "target": str(target).lower()})

    discord_channels = []
    discord_cfg = cfg.get("discord_channels", {})
    if isinstance(discord_cfg, dict):
        # Legacy format: {"channel": "url"}
        for name, url in discord_cfg.items():
            discord_channels.append({"name": str(name).lower(), "url": str(url), "server": ""})
    elif isinstance(discord_cfg, list):
        for ch in discord_cfg:
            if isinstance(ch, dict) and ch.get("name") and ch.get("url"):
                discord_channels.append({
                    "name": str(ch.get("name", "")).strip().lower(),
                    "url": str(ch.get("url", "")).strip(),
                    "server": str(ch.get("server", "")).strip().lower(),
                })

    discord_servers = []
    discord_servers_cfg = cfg.get("discord_servers", [])
    if isinstance(discord_servers_cfg, list):
        for s in discord_servers_cfg:
            if isinstance(s, dict) and s.get("nickname"):
                discord_servers.append({
                    "nickname": str(s.get("nickname", "")).strip().lower(),
                    "server_id": str(s.get("server_id", "")).strip(),
                })

    keybinds = cfg.get("keybinds", [])
    if not isinstance(keybinds, list):
        keybinds = []
    keybinds = [
        {
            "phrase": str(k.get("phrase", "")).strip().lower(),
            "key": str(k.get("key", "")).strip(),
            "count": int(k.get("count", 1)),
        }
        for k in keybinds
        if isinstance(k, dict)
    ]

    status_var = SimpleVar(value="Idle")
    transcript_var = SimpleVar(value="")

    # Hook whisper model download status into the UI status bar
    import app as _app_module
    _app_module.on_model_status = lambda msg: _bridge.post(lambda m=msg: status_var.set(m))
    app_name_var = SimpleVar()
    app_cmd_var = SimpleVar()
    alias_var = SimpleVar()
    alias_target_var = SimpleVar()
    phrase_var = SimpleVar()
    command_var = SimpleVar()
    discord_ch_name_var = SimpleVar()
    discord_ch_url_var = SimpleVar()
    discord_ch_server_var = SimpleVar()
    discord_bot_token_var = SimpleVar(value=cfg.get("discord_bot_token", ""))
    discord_server_id_var = SimpleVar(value=cfg.get("discord_server_id", ""))
    discord_srv_nickname_var = SimpleVar()
    discord_srv_id_var = SimpleVar()
    gemini_api_key_var = SimpleVar(value=cfg.get("gemini_api_key", ""))
    keybind_phrase_var = SimpleVar()
    keybind_key_var = SimpleVar()
    keybind_count_var = SimpleVar(value="1")

    def _bind_record_key_display(raw_var: SimpleVar, display_var: SimpleVar) -> None:
        _syncing = {"raw": False, "display": False}

        def _sync_from_raw(*_args):
            if _syncing["display"]:
                return
            normalized = _normalize_record_key_name(raw_var.get())
            pretty = _format_record_key_name(normalized)
            if raw_var.get() != normalized:
                _syncing["raw"] = True
                raw_var.set(normalized)
                _syncing["raw"] = False
            if display_var.get() != pretty:
                _syncing["display"] = True
                display_var.set(pretty)
                _syncing["display"] = False

        def _sync_from_display(*_args):
            if _syncing["raw"]:
                return
            normalized = _normalize_record_key_name(display_var.get())
            if raw_var.get() != normalized:
                _syncing["raw"] = True
                raw_var.set(normalized)
                _syncing["raw"] = False

        raw_var.trace_add("write", _sync_from_raw)
        display_var.trace_add("write", _sync_from_display)
        _sync_from_raw()

    _bind_record_key_display(hotkey, hotkey_display)
    _bind_record_key_display(holdkey, holdkey_display)
    apps_textbox = None
    aliases_textbox = None
    actions_textbox = None
    discord_channels_textbox = None
    discord_servers_textbox = None
    keybinds_textbox = None
    listener = BackgroundListener()
    tray_icon = {"icon": None}
    tray_ready = {"ok": False}
    _model_preload_started = {"done": False}
    _saved_config_signature = [""]
    _runtime_mode = {"value": "idle"}
    _notice_after_id = {"id": None}
    _notice_action = {"callback": None}
    _idle_timer = {"handle": None}
    _update_action = {"callback": None}
    _dismissed_update_version = {"value": str(cfg.get("dismissed_update_version", "")).strip()}
    save_button = None
    notice_frame = None
    notice_label = None
    notice_action_button = None
    notice_close_button = None
    update_frame = None
    update_label = None
    update_action_button = None
    update_close_button = None
    loading_overlay = None
    loading_progress = None
    record_backdrop = None
    record_overlay = None
    record_title_label = None
    record_message_label = None
    record_status_label = None
    _record_overlay_session = {"id": 0}
    _active_recorders = []

    # --- Helper functions (logic unchanged) ---

    def _model_dir() -> str:
        # No longer used for STT — faster-whisper manages its own model cache
        return ""

    def _model_present() -> bool:
        # faster-whisper auto-downloads on first use — always report ready
        return True

    def _build_config(wizard_done: bool | None = None) -> dict:
        try:
            secs = int(seconds.get())
            if secs <= 0:
                secs = 5
        except Exception:
            secs = 5
        data = {
            "theme": "dark",
            "mode": mode.get(),
            "language": language.get(),
            "seconds": secs,
            "hotkey": hotkey.get(),
            "hold_key": holdkey.get(),
            "search_engine": search_engine.get().strip(),
            "ptt_beep_volume": int(ptt_beep_volume.get()),
            "tts_output_device": "" if tts_output_device.get() == "Default" else tts_output_device.get(),
            "tts_voice": tts_voice.get(),
            "personality_mode": personality_mode.get(),
            "premium": bool(premium.get()),
            "confirm_actions": bool(confirm_actions.get()),
            "spotify_media": bool(spotify_media.get()),
            "spotify_requires_keyword": bool(spotify_requires.get()),
            "spotify_keywords": spotify_keywords.get().strip(),
            "news_source": news_source.get(),
            "birthday_month": int(birthday_month.get()) if birthday_month.get().isdigit() else 0,
            "birthday_day": int(birthday_day.get()) if birthday_day.get().isdigit() else 0,
            "actions": [a for a in actions if a.get("phrase") and a.get("command")],
            "apps": {a.get("name"): a.get("command") for a in apps if a.get("name") and a.get("command")},
            "app_aliases": {a.get("alias"): a.get("target") for a in aliases if a.get("alias") and a.get("target")},
            "discord_channels": [{"name": a.get("name"), "url": a.get("url"), "server": a.get("server", "")} for a in discord_channels if a.get("name") and a.get("url")],
            "discord_servers": [s for s in discord_servers if s.get("nickname") and s.get("server_id")],
            "discord_bot_token": discord_bot_token_var.get().strip(),
            "discord_server_id": discord_server_id_var.get().strip(),
            "gemini_api_key": gemini_api_key_var.get().strip(),
            "premium": bool(cfg.get("premium", False)),
            "keybinds": [k for k in keybinds if k.get("phrase") and k.get("key")],
            "dismissed_update_version": _dismissed_update_version["value"],
            "bug_report_secret": bug_report_secret_var.get(),
        }
        if wizard_done is not None:
            data["wizard_done"] = bool(wizard_done)
        return data

    def _config_signature(data: dict | None = None) -> str:
        payload = data if data is not None else _build_config()
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    def _confirm_prompt(prompt: str) -> bool:
        if not confirm_actions.get():
            return True
        return _confirm_dialog("Confirm", prompt)

    def _do_restart():
        try:
            listener.stop()
            try:
                if tray_icon["icon"] is not None:
                    tray_icon["icon"].stop()
            except Exception:
                pass
            _rpc_close()
            _release_mutex()
            script_path = os.path.abspath(__file__)
            subprocess.Popen([sys.executable, script_path])
        except Exception as exc:
            print(f"Restart failed: {exc}")
        finally:
            os._exit(0)

    def _read_local_version() -> str:
        try:
            version_path = os.path.join(os.path.dirname(__file__), "VERSION")
            if os.path.exists(version_path):
                with open(version_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
        except Exception:
            pass
        return "0.0"

    def _parse_version(value: str):
        parts = []
        for chunk in value.replace("v", "").split("."):
            try:
                parts.append(int(chunk))
            except Exception:
                parts.append(0)
        return tuple(parts)

    def _fetch_latest_version() -> str | None:
        url = "https://raw.githubusercontent.com/copenhagenay-spec/Vera-beta/main/vera/VERSION"
        with urllib.request.urlopen(url, timeout=10) as resp:
            return resp.read().decode("utf-8").strip()

    def _backup_current_app(backup_dir: str) -> None:
        base_dir = os.path.dirname(__file__)
        os.makedirs(backup_dir, exist_ok=True)
        for name in os.listdir(base_dir):
            if name.lower() == "data":
                continue
            src = os.path.join(base_dir, name)
            dst = os.path.join(backup_dir, name)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)

    def _apply_update_from_zip(zip_path: str) -> None:
        base_dir = os.path.dirname(__file__)
        tmp_dir = tempfile.mkdtemp(prefix="vera_update_")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp_dir)

        # GitHub zip extracts to a single top-level folder
        entries = [os.path.join(tmp_dir, n) for n in os.listdir(tmp_dir)]
        root_dir = next((p for p in entries if os.path.isdir(p)), tmp_dir)

        # If repo has a nested app folder, pick the one containing assistant.py
        candidate = None
        for path, dirs, files in os.walk(root_dir):
            if "assistant.py" in files:
                candidate = path
                break
        src_root = candidate or root_dir

        for name in os.listdir(src_root):
            if name.lower() == "data":
                continue
            src = os.path.join(src_root, name)
            dst = os.path.join(base_dir, name)
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)

        shutil.rmtree(tmp_dir, ignore_errors=True)

    def _log_to_file(message: str) -> None:
        try:
            log_dir = os.path.join(os.path.dirname(__file__), "data", "logs")
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, "assistant.log")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {message}\n")
        except Exception:
            pass

    def _check_for_updates():
        current = _read_local_version()
        try:
            latest = _fetch_latest_version()
        except Exception as exc:
            _log_to_file(f"UPDATE_CHECK_FAILED: {exc}")
            _notify_error("Update Failed", f"Could not check for updates.\n\n{exc}")
            return
        if not latest:
            _notify_info("Update", "Could not check for updates (no connection).")
            return
        if _parse_version(latest) <= _parse_version(current):
            _notify_info("Update", f"You're up to date (v{current}).")
            return

        if not _confirm_dialog("Update Available", f"Update to v{latest}?"):
            return

        try:
            base_dir = os.path.dirname(__file__)
            data_dir = os.path.join(base_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            backup_dir = os.path.join(data_dir, f"backup_{time.strftime('%Y%m%d_%H%M%S')}")
            _backup_current_app(backup_dir)

            zip_url = "https://github.com/copenhagenay-spec/Vera-beta/archive/refs/heads/main.zip"
            zip_path = os.path.join(data_dir, "update.zip")
            urllib.request.urlretrieve(zip_url, zip_path)
            _apply_update_from_zip(zip_path)
            try:
                os.remove(zip_path)
            except Exception:
                pass

            # Update VERA.exe launcher
            exe_url = f"https://github.com/copenhagenay-spec/Vera-beta/releases/download/v{latest}/VERA.exe"
            launcher_out = os.path.join(base_dir, "launcher_out", "VERA.exe")
            if os.path.exists(os.path.dirname(launcher_out)):
                try:
                    urllib.request.urlretrieve(exe_url, launcher_out)
                except Exception:
                    pass

            _notify_info("Update", "Update installed. Restarting VERA...")
            _release_mutex()
            script_path = os.path.abspath(__file__)
            subprocess.Popen([sys.executable, script_path])
            os._exit(0)
        except Exception as exc:
            _notify_error("Update Failed", str(exc))

    def _startup_update_check():
        try:
            local = _read_local_version()
            latest = _fetch_latest_version()
            if latest and _parse_version(latest) > _parse_version(local):
                _bridge.post(lambda v=latest: _show_update_notice(v))
        except Exception:
            pass

    def _record_hotkey(target_var: SimpleVar) -> None:
        try:
            from pynput import keyboard  # type: ignore
        except Exception:
            _notify_error("Missing Dependency", "pynput is required to record hotkeys.")
            return

        dialog, status = _create_record_popup(
            "Record Toggle Key",
            "Press the key combination you want VERA to use for toggle-to-talk.",
            size="400x170",
        )

        modifier_keys = {
            keyboard.Key.ctrl,
            keyboard.Key.ctrl_l,
            keyboard.Key.ctrl_r,
            keyboard.Key.alt,
            keyboard.Key.alt_l,
            keyboard.Key.alt_r,
            keyboard.Key.shift,
            keyboard.Key.shift_l,
            keyboard.Key.shift_r,
            keyboard.Key.cmd,
            keyboard.Key.cmd_l,
            keyboard.Key.cmd_r,
        }

        def _modifier_name(key):
            if key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
                return "ctrl"
            if key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r):
                return "alt"
            if key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
                return "shift"
            if key in (keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r):
                return "cmd"
            return None

        def _key_name(key):
            if isinstance(key, keyboard.KeyCode) and key.char:
                return key.char.lower()
            if key == keyboard.Key.space:
                return "<space>"
            name = getattr(key, "name", None)
            if name:
                return f"<{name}>"
            return None

        pressed_mods = set()
        last_key = {"key": None}

        def _finish(combo: str | None):
            if combo:
                target_var.set(combo)
                status.set(f"Captured: {combo}")
            else:
                status.set("Canceled")
            try:
                listener.stop()
            except Exception:
                pass
            dialog.after(400, dialog.destroy)

        def _on_press(key):
            if key == keyboard.Key.esc:
                _finish(None)
                return False
            if key in modifier_keys:
                name = _modifier_name(key)
                if name:
                    pressed_mods.add(name)
                return
            last_key["key"] = key

        def _on_release(key):
            if key in modifier_keys:
                name = _modifier_name(key)
                if name in pressed_mods:
                    pressed_mods.remove(name)
                return
            if last_key["key"] == key:
                key_name = _key_name(key)
                if not key_name:
                    _finish(None)
                    return False
                mods = []
                if "ctrl" in pressed_mods:
                    mods.append("<ctrl>")
                if "alt" in pressed_mods:
                    mods.append("<alt>")
                if "shift" in pressed_mods:
                    mods.append("<shift>")
                if "cmd" in pressed_mods:
                    mods.append("<cmd>")
                combo = "+".join(mods + [key_name])
                _finish(combo)
                return False

        listener = keyboard.Listener(on_press=_on_press, on_release=_on_release)
        _active_recorders.append(listener)
        listener.start()

    def _record_hold_key(target_var: SimpleVar) -> None:
        try:
            from pynput import keyboard  # type: ignore
            from pynput import mouse as pynput_mouse  # type: ignore
        except Exception:
            _notify_error("Missing Dependency", "pynput is required to record keys.")
            return

        dialog, status = _create_record_popup(
            "Record Hold Key",
            "Press the key or side mouse button you want VERA to use for hold-to-talk.",
            size="410x170",
        )

        modifier_keys = {
            keyboard.Key.ctrl,
            keyboard.Key.ctrl_l,
            keyboard.Key.ctrl_r,
            keyboard.Key.alt,
            keyboard.Key.alt_l,
            keyboard.Key.alt_r,
            keyboard.Key.shift,
            keyboard.Key.shift_l,
            keyboard.Key.shift_r,
            keyboard.Key.cmd,
            keyboard.Key.cmd_l,
            keyboard.Key.cmd_r,
        }

        def _key_name(key):
            if isinstance(key, keyboard.KeyCode) and key.char:
                return key.char.lower()
            if key == keyboard.Key.space:
                return "space"
            name = getattr(key, "name", None)
            if name:
                return name.lower()
            return None

        active = {"kb": None, "ms": None}

        def _finish(value: str | None, display: str | None = None):
            if value:
                target_var.set(value)
                status.set(f"Captured: {display or value}")
            else:
                status.set("Canceled")
            try:
                if active["kb"]:
                    active["kb"].stop()
                if active["ms"]:
                    active["ms"].stop()
            except Exception:
                pass
            dialog.after(400, dialog.destroy)

        def _on_press(key):
            if key == keyboard.Key.esc:
                _finish(None)
                return False
            if key in modifier_keys:
                return
            name = _key_name(key)
            if name:
                _finish(name)
            else:
                _finish(None)
            return False

        def _on_click(x, y, button, pressed):
            if not pressed:
                return
            if button == pynput_mouse.Button.x1:
                _finish("x1", "Mouse Back (x1)")
                return False
            elif button == pynput_mouse.Button.x2:
                _finish("x2", "Mouse Fwd (x2)")
                return False

        active["kb"] = keyboard.Listener(on_press=_on_press)
        _active_recorders.append(active["kb"])
        active["kb"].start()
        active["ms"] = pynput_mouse.Listener(on_click=_on_click)
        _active_recorders.append(active["ms"])
        active["ms"].start()

    def _load_logo():
        logo_path = os.path.join(os.path.dirname(__file__), "data", "assets", "ipa_logo.png")
        if os.path.exists(logo_path):
            return logo_path
        return None

    def _save():
        data = _build_config()
        save_config(data)
        _saved_config_signature[0] = _config_signature(data)
        _apply_runtime_config()
        _refresh_save_prompt()
        _notify_info("Saved", "Configuration saved.")

    def _prime_speech_model() -> None:
        if _model_preload_started["done"]:
            return
        _model_preload_started["done"] = True

        def _run():
            try:
                import app as _app_module
                _app_module._get_whisper_model()
            except Exception:
                pass

        threading.Thread(target=_run, daemon=True).start()

    def _background_active() -> bool:
        wake_alive = _wake_thread[0] is not None and _wake_thread[0].is_alive()
        return bool(listener.listener is not None or wake_alive or _runtime_mode["value"] != "idle")

    def _apply_runtime_config() -> None:
        if not _background_active():
            return
        _stop_background()
        QTimer.singleShot(120, _start_background)

    def _hide_inline_notice() -> None:
        if notice_frame is None:
            return
        if _notice_after_id["id"] is not None:
            try:
                _notice_after_id["id"].stop()
            except Exception:
                pass
            _notice_after_id["id"] = None
        notice_frame.setVisible(False)
        if notice_action_button is not None:
            notice_action_button.setVisible(False)
        if notice_close_button is not None:
            notice_close_button.setVisible(False)
        _notice_action["callback"] = None

    def _run_notice_action() -> None:
        callback = _notice_action.get("callback")
        if callable(callback):
            callback()

    def _show_inline_notice(
        message: str,
        tone: str = "error",
        duration_ms: int = 7000,
        action_text: str | None = None,
        action_callback=None,
        closable: bool = False,
    ) -> None:
        if notice_frame is None or notice_label is None:
            return
        bg_colors = {
            "error": ("#4a1f1f", "#ffb4b4"),
            "info":  ("#1f304a", "#b7d4ff"),
            "update": ("#4a3a1f", "#ffd67d"),
        }
        bg, fg = bg_colors.get(tone, bg_colors["error"])
        notice_frame.setStyleSheet(f"background-color: {bg}; border-radius: 8px;")
        notice_label.setStyleSheet(f"color: {fg}; font-size: 11px;")
        notice_label.setText(message)
        if notice_action_button is not None:
            if action_text and callable(action_callback):
                _notice_action["callback"] = action_callback
                notice_action_button.setText(action_text)
                try:
                    notice_action_button.clicked.disconnect()
                except Exception:
                    pass
                notice_action_button.clicked.connect(_run_notice_action)
                notice_action_button.setVisible(True)
            else:
                notice_action_button.setVisible(False)
        if notice_close_button is not None:
            if closable:
                try:
                    notice_close_button.clicked.disconnect()
                except Exception:
                    pass
                notice_close_button.clicked.connect(_hide_inline_notice)
                notice_close_button.setVisible(True)
            else:
                notice_close_button.setVisible(False)
        notice_frame.setVisible(True)
        if _notice_after_id["id"] is not None:
            try:
                _notice_after_id["id"].stop()
            except Exception:
                pass
            _notice_after_id["id"] = None
        if duration_ms and duration_ms > 0:
            t = QTimer()
            t.setSingleShot(True)
            t.timeout.connect(_hide_inline_notice)
            t.start(duration_ms)
            _notice_after_id["id"] = t

    def _hide_update_notice() -> None:
        if update_frame is None:
            return
        update_frame.setVisible(False)
        if update_action_button is not None:
            update_action_button.setVisible(False)
        if update_close_button is not None:
            update_close_button.setVisible(False)
        _update_action["callback"] = None

    def _dismiss_update_notice(version: str | None = None) -> None:
        if version and version != "TEST":
            _dismissed_update_version["value"] = version
            save_config(_build_config())
            _saved_config_signature[0] = _config_signature()
            _refresh_save_prompt()
        _hide_update_notice()

    def _run_update_action() -> None:
        callback = _update_action.get("callback")
        if callable(callback):
            callback()

    def _show_ui_info(title: str, message: str) -> None:
        prefix = f"{title}: " if title and title.lower() != "info" else ""
        _show_inline_notice(prefix + message, tone="info", duration_ms=5000)

    def _show_ui_error(title: str, message: str) -> None:
        prefix = f"{title}: " if title else ""
        _show_inline_notice(prefix + message, tone="error", duration_ms=7000, closable=True)

    def _show_update_notice(version: str, test: bool = False) -> None:
        if not test and _dismissed_update_version["value"] == version:
            return
        if update_frame is None or update_label is None:
            return
        prefix = "Test update available." if test else f"New update available: v{version}."
        update_label.setText(f"{prefix} Check here to update.")
        if update_action_button is not None:
            _update_action["callback"] = _check_for_updates
            update_action_button.setText("Check Updates")
            try:
                update_action_button.clicked.disconnect()
            except Exception:
                pass
            update_action_button.clicked.connect(_run_update_action)
            update_action_button.setVisible(True)
        if update_close_button is not None:
            try:
                update_close_button.clicked.disconnect()
            except Exception:
                pass
            update_close_button.clicked.connect(lambda checked=False, v=version: _dismiss_update_notice(v))
            update_close_button.setVisible(True)
        update_frame.setVisible(True)

    def _stop_active_recorders() -> None:
        while _active_recorders:
            current = _active_recorders.pop()
            try:
                current.stop()
            except Exception:
                pass

    def _create_record_popup(title: str, instruction: str, size: str = "380x150"):
        class _InlineRecordDialog:
            def __init__(self, session_id: int):
                self.session_id = session_id
                self._closed = False

            def after(self, delay_ms: int, callback):
                def _run():
                    if self._closed or self.session_id != _record_overlay_session["id"]:
                        return
                    callback()

                def _schedule():
                    QTimer.singleShot(delay_ms, _run)

                _bridge.post(_schedule)
                return None  # no cancel handle needed

            def destroy(self):
                if self._closed:
                    return
                self._closed = True
                if self.session_id != _record_overlay_session["id"]:
                    return
                if record_status_label is not None:
                    try:
                        record_status_label.setText("Listening for your input...")
                    except Exception:
                        pass
                _stop_active_recorders()
                if record_backdrop is not None:
                    try:
                        record_backdrop.hide_over()
                    except Exception:
                        pass

        _stop_active_recorders()

        if record_backdrop is None or record_overlay is None or record_title_label is None or record_message_label is None or record_status_label is None:
            status = SimpleVar(value="Listening for your input...")
            return _InlineRecordDialog(-1), status

        _record_overlay_session["id"] += 1
        session_id = _record_overlay_session["id"]
        status = SimpleVar(value="Listening for your input...")
        status.trace_add("write", lambda *_: record_status_label.setText(status.get()))

        record_title_label.setText(title)
        record_message_label.setText(instruction)
        record_status_label.setText(status.get())
        record_backdrop.show_over()
        root.activateWindow()
        return _InlineRecordDialog(session_id), status

    def _ask_ui_confirm(title: str, message: str) -> bool:
        result = QMessageBox.question(root, title, message,
                                      QMessageBox.Yes | QMessageBox.No)
        return result == QMessageBox.Yes

    def _on_mode_change() -> None:
        if _background_active():
            _stop_background()
            QTimer.singleShot(80, _start_background)
        else:
            _runtime_mode["value"] = "idle"
            status_var.set("Idle")
        _refresh_save_prompt()

    def _refresh_save_prompt(*_args) -> None:
        if save_button is None:
            return
        is_dirty = _config_signature() != _saved_config_signature[0]
        save_button.setVisible(is_dirty)

    global UI_NOTIFY_INFO, UI_NOTIFY_ERROR, UI_CONFIRM
    UI_NOTIFY_INFO = _show_ui_info
    UI_NOTIFY_ERROR = _show_ui_error
    UI_CONFIRM = _ask_ui_confirm

    # --- Actions list helpers ---
    def _refresh_actions():
        if actions_textbox is None:
            return
        actions_textbox.clear()
        for a in actions:
            phrase = a.get("phrase", "")
            command = a.get("command", "")
            actions_textbox.addItem(f"{phrase}  ->  {command}")

    def _add_action():
        phrase = phrase_var.get().strip()
        command = command_var.get().strip()
        if not phrase or not command:
            _notify_error("Invalid", "Phrase and command are required.")
            return
        actions.append({"phrase": phrase, "command": command})
        phrase_var.set("")
        command_var.set("")
        _refresh_actions()
        _refresh_save_prompt()

    def _remove_action():
        if not actions or actions_textbox is None:
            return
        row = actions_textbox.currentRow()
        idx = row if row >= 0 else len(actions) - 1
        if 0 <= idx < len(actions):
            actions.pop(idx)
        _refresh_actions()
        _refresh_save_prompt()

    # --- Apps list helpers ---
    def _refresh_apps():
        if apps_textbox is None:
            return
        apps_textbox.clear()
        for a in apps:
            name = a.get("name", "")
            command = a.get("command", "")
            apps_textbox.addItem(f"{name}  ->  {command}")

    def _refresh_aliases():
        if aliases_textbox is None:
            return
        aliases_textbox.clear()
        for a in aliases:
            aliases_textbox.addItem(f"{a.get('alias')}  ->  {a.get('target')}")

    def _add_alias():
        alias = alias_var.get().strip().lower()
        target = alias_target_var.get().strip().lower()
        if not alias or not target:
            _notify_error("Invalid", "Alias and target app are required.")
            return
        aliases.append({"alias": alias, "target": target})
        alias_var.set("")
        alias_target_var.set("")
        _refresh_aliases()
        _refresh_save_prompt()

    def _remove_alias():
        if not aliases:
            return
        row = aliases_textbox.currentRow() if aliases_textbox else -1
        idx = row if row >= 0 else len(aliases) - 1
        if 0 <= idx < len(aliases):
            aliases.pop(idx)
        _refresh_aliases()
        _refresh_save_prompt()

    def _add_app():
        name = app_name_var.get().strip().lower()
        command = app_cmd_var.get().strip()
        if not name or not command:
            _notify_error("Invalid", "App name and command are required.")
            return
        apps.append({"name": name, "command": command})
        app_name_var.set("")
        app_cmd_var.set("")
        _refresh_apps()
        _refresh_save_prompt()

    def _test_app():
        command = app_cmd_var.get().strip()
        if not command:
            _notify_error("Invalid", "App command is required to test.")
            return
        try:
            subprocess.Popen(command, shell=True)
        except Exception as exc:
            _notify_error("Test Failed", str(exc))

    def _remove_app():
        if not apps:
            return
        row = apps_textbox.currentRow() if apps_textbox else -1
        idx = row if row >= 0 else len(apps) - 1
        if 0 <= idx < len(apps):
            apps.pop(idx)
        _refresh_apps()
        _refresh_save_prompt()

    # --- Discord servers helpers ---
    def _refresh_discord_servers():
        if discord_servers_textbox is None:
            return
        discord_servers_textbox.clear()
        for s in discord_servers:
            discord_servers_textbox.addItem(f"{s.get('nickname')}  ->  {s.get('server_id')}")

    def _add_discord_server():
        nickname = discord_srv_nickname_var.get().strip().lower()
        server_id = discord_srv_id_var.get().strip()
        if not nickname or not server_id:
            _notify_error("Invalid", "Nickname and Server ID are required.")
            return
        discord_servers.append({"nickname": nickname, "server_id": server_id})
        discord_srv_nickname_var.set("")
        discord_srv_id_var.set("")
        _refresh_discord_servers()
        _refresh_save_prompt()

    def _remove_discord_server():
        if discord_servers_textbox is None or not discord_servers:
            return
        row = discord_servers_textbox.currentRow()
        idx = row if row >= 0 else len(discord_servers) - 1
        discord_servers.pop(idx)
        _refresh_discord_servers()
        _refresh_save_prompt()

    # --- Discord channels helpers ---
    def _refresh_discord_channels():
        if discord_channels_textbox is None:
            return
        discord_channels_textbox.clear()
        for ch in discord_channels:
            server = ch.get("server", "")
            prefix = f"[{server}] " if server else ""
            discord_channels_textbox.addItem(f"{prefix}#{ch.get('name')}  ->  {ch.get('url')}")

    def _add_discord_channel():
        name = discord_ch_name_var.get().strip().lower()
        url = discord_ch_url_var.get().strip()
        server = discord_ch_server_var.get().strip().lower()
        if not name or not url:
            _notify_error("Invalid", "Channel name and webhook URL are required.")
            return
        discord_channels.append({"name": name, "url": url, "server": server})
        discord_ch_name_var.set("")
        discord_ch_url_var.set("")
        discord_ch_server_var.set("")
        _refresh_discord_channels()
        _refresh_save_prompt()

    def _remove_discord_channel():
        if discord_channels_textbox is None or not discord_channels:
            return
        row = discord_channels_textbox.currentRow()
        idx = row if row >= 0 else len(discord_channels) - 1
        discord_channels.pop(idx)
        _refresh_discord_channels()
        _refresh_save_prompt()

    # --- Keybinds helpers ---
    def _refresh_keybinds():
        if keybinds_textbox is None:
            return
        keybinds_textbox.clear()
        for kb in keybinds:
            count = kb.get("count", 1)
            suffix = f" x{count}" if int(count) > 1 else ""
            keybinds_textbox.addItem(f"{kb.get('phrase')}  ->  {kb.get('key')}{suffix}")

    def _record_keybind_step(target_var: SimpleVar) -> None:
        """Record a single key/combo and append it as a macro step."""
        try:
            from pynput import keyboard as _kb  # type: ignore
            from pynput import mouse as _ms  # type: ignore
        except Exception:
            _notify_error("Missing Dependency", "pynput is required to record keys.")
            return

        dialog, status = _create_record_popup(
            "Record Key Step",
            "Press a key, combo, or side mouse button to add the next step to this key bind.",
            size="420x170",
        )

        modifier_keys = {_kb.Key.ctrl, _kb.Key.ctrl_l, _kb.Key.ctrl_r,
                         _kb.Key.alt, _kb.Key.alt_l, _kb.Key.alt_r,
                         _kb.Key.shift, _kb.Key.shift_l, _kb.Key.shift_r,
                         _kb.Key.cmd, _kb.Key.cmd_l, _kb.Key.cmd_r}
        pressed_mods: list = []
        active = {"kb": None, "ms": None, "done": False}

        def _mod_name(k):
            n = getattr(k, "name", "").lower()
            for m in ("ctrl", "alt", "shift", "cmd"):
                if m in n:
                    return m
            return None

        def _finish(value, display=None):
            if active["done"]:
                return
            active["done"] = True
            if value:
                current = target_var.get().strip()
                if current:
                    target_var.set(current + " > " + value)
                else:
                    target_var.set(value)
                status.set(f"Added: {display or value}")
            else:
                status.set("Canceled")
            try:
                if active["kb"]: active["kb"].stop()
                if active["ms"]: active["ms"].stop()
            except Exception:
                pass
            dialog.after(400, dialog.destroy)

        def _on_press(key):
            if key == _kb.Key.esc:
                _finish(None)
                return False
            mn = _mod_name(key)
            if mn and mn not in pressed_mods:
                pressed_mods.append(mn)
                return

        def _on_release(key):
            mn = _mod_name(key)
            if mn:
                if mn in pressed_mods:
                    pressed_mods.remove(mn)
                return
            name = None
            if isinstance(key, _kb.KeyCode) and key.char:
                name = key.char.lower()
            elif key == _kb.Key.space:
                name = "space"
            else:
                name = getattr(key, "name", None)
                if name:
                    name = name.lower()
            if not name:
                _finish(None)
                return False
            parts = pressed_mods + [name]
            combo = "+".join(parts)
            _finish(combo, combo)
            return False

        def _on_click(x, y, button, pressed):
            if not pressed:
                return
            if button == _ms.Button.x1:
                _finish("x1", "Mouse Back (x1)")
                return False
            elif button == _ms.Button.x2:
                _finish("x2", "Mouse Fwd (x2)")
                return False

        active["kb"] = _kb.Listener(on_press=_on_press, on_release=_on_release)
        _active_recorders.append(active["kb"])
        active["kb"].start()
        active["ms"] = _ms.Listener(on_click=_on_click)
        _active_recorders.append(active["ms"])
        active["ms"].start()

    def _add_keybind():
        phrase = keybind_phrase_var.get().strip().lower()
        key = keybind_key_var.get().strip()
        try:
            count = max(1, int(keybind_count_var.get().strip()))
        except Exception:
            count = 1
        if not phrase or not key:
            _notify_error("Invalid", "Phrase and key are required.")
            return
        keybinds.append({"phrase": phrase, "key": key, "count": count})
        keybind_phrase_var.set("")
        keybind_key_var.set("")
        keybind_count_var.set("1")
        _refresh_keybinds()
        _refresh_save_prompt()

    def _remove_keybind():
        if not keybinds or keybinds_textbox is None:
            return
        row = keybinds_textbox.currentRow()
        idx = row if row >= 0 else len(keybinds) - 1
        if 0 <= idx < len(keybinds):
            keybinds.pop(idx)
        _refresh_keybinds()
        _refresh_save_prompt()

    def _import_steam():
        try:
            found = find_steam_apps()
        except Exception as exc:
            _notify_error("Steam Import Error", str(exc))
            return
        if not found:
            _notify_info("Steam Import", "No Steam apps found.")
            return
        existing = {a.get("name") for a in apps}
        added = 0
        for app in found:
            name = app.get("name", "").strip().lower()
            appid = app.get("appid")
            if not name or not appid:
                continue
            if name in existing:
                continue
            command = f"start steam://run/{appid}"
            apps.append({"name": name, "command": command})
            existing.add(name)
            added += 1
        _refresh_apps()
        _refresh_save_prompt()
        _notify_info("Steam Import", f"Added {added} apps.")

    def _run_now():
        try:
            secs = int(seconds.get())
        except Exception:
            secs = 5
        if mode.get() == "hold":
            _notify_info("Hold Mode", "Hold mode only runs in the background.")
        elif mode.get() == "toggle":
            _notify_info("Toggle Mode", "Toggle mode only runs in the background.")
        elif mode.get() == "wake":
            _notify_info("Wake Word Mode", "Wake word mode only runs in the background.")
        else:
            _notify_info("Info", "Start Background to begin listening.")

    def _reset_idle_timer():
        if _idle_timer["handle"] is not None:
            try:
                _idle_timer["handle"].stop()
            except Exception:
                pass
            _idle_timer["handle"] = None
        if not cfg.get("idle_chatter", True):
            return
        idle_ms = int(cfg.get("idle_minutes", 45)) * 60 * 1000

        def _fire_idle():
            _idle_timer["handle"] = None
            if not cfg.get("idle_chatter", True):
                return
            def _speak():
                from skills import _tts_speak
                from personality import get_idle_thought
                _tts_speak(get_idle_thought())
            threading.Thread(target=_speak, daemon=True).start()
            _reset_idle_timer()

        t = QTimer()
        t.setSingleShot(True)
        t.timeout.connect(_fire_idle)
        t.start(idle_ms)
        _idle_timer["handle"] = t

    def _start_background():
        try:
            secs = int(seconds.get())
        except Exception:
            secs = 5
        _prime_speech_model()
        try:
            if mode.get() == "hold":
                _runtime_mode["value"] = "hold"
                _hold_label = f"Listening (hold {holdkey.get()})"
                listener.start_hold(
                    holdkey.get(),
                    model_path=_model_dir(),
                    confirm_fn=_confirm_prompt,
                    on_text=lambda t: _bridge.post(lambda _t=t: _update_transcript(_t)),
                    restart_fn=_do_restart,
                    on_record_start=lambda: (_bridge.post(lambda: status_var.set("Recording...")), _rpc_set("Recording...")),
                    on_record_end=lambda: (_bridge.post(lambda: status_var.set(_hold_label)), _rpc_set("Listening...")),
                )
                status_var.set(_hold_label)
                _rpc_set("Listening...")
            elif mode.get() == "toggle":
                _runtime_mode["value"] = "toggle"
                _toggle_label = f"Listening (toggle {hotkey.get()})"
                listener.start_toggle(
                    hotkey.get(),
                    model_path=_model_dir(),
                    confirm_fn=_confirm_prompt,
                    on_text=lambda t: _bridge.post(lambda _t=t: _update_transcript(_t)),
                    restart_fn=_do_restart,
                    on_record_start=lambda: (_bridge.post(lambda: status_var.set("Recording...")), _rpc_set("Recording...")),
                    on_record_end=lambda: (_bridge.post(lambda: status_var.set(_toggle_label)), _rpc_set("Listening...")),
                )
                status_var.set(_toggle_label)
                _rpc_set("Listening...")
            elif mode.get() == "wake":
                _runtime_mode["value"] = "wake"
                _start_wake_word()
                status_var.set("Wake word active (say 'vera')")
            else:
                _runtime_mode["value"] = "idle"
                status_var.set("Timed mic mode (manual Run Now)")
        except Exception as exc:
            _runtime_mode["value"] = "idle"
            status_var.set("Listener failed to start")
            _show_inline_notice(f"Listener failed to start: {exc}", tone="error")
        _reset_idle_timer()

    def _stop_background():
        listener.stop()
        _stop_wake_word()
        _runtime_mode["value"] = "idle"
        status_var.set("Idle")

    def _mute_status_update(msg) -> None:
        """Called by skills when mute state changes. None = restore real status."""
        def _do():
            if msg == "Muted":
                status_var.set("Muted")
                def _hold_muted():
                    from skills import is_muted
                    if is_muted():
                        status_var.set("Muted")
                        QTimer.singleShot(500, _hold_muted)
                QTimer.singleShot(500, _hold_muted)
            else:
                m = _runtime_mode.get("value", "idle")
                if m == "hold":
                    status_var.set(f"Listening (hold {holdkey.get()})")
                elif m == "toggle":
                    status_var.set(f"Listening (toggle {hotkey.get()})")
                elif m == "wake":
                    status_var.set("Wake word active (say 'vera')")
                else:
                    status_var.set("Idle")
        _bridge.post(_do)

    from skills import set_mute_status_callback, set_groq_flash_callback
    set_mute_status_callback(_mute_status_update)

    _groq_flash_timer = {"handle": None}

    def _groq_flash() -> None:
        """Flash 'AI response' in the status bar for 2 seconds then restore."""
        from skills import is_muted
        if is_muted():
            return
        def _do():
            prev = status_var.get()
            status_var.set("AI response")
            if _groq_flash_timer["handle"] is not None:
                try:
                    _groq_flash_timer["handle"].stop()
                except Exception:
                    pass
            def _restore():
                if status_var.get() == "AI response":
                    status_var.set(prev)
            t = QTimer()
            t.setSingleShot(True)
            t.timeout.connect(_restore)
            t.start(2000)
            _groq_flash_timer["handle"] = t
        _bridge.post(lambda: QTimer.singleShot(150, _do))

    set_groq_flash_callback(_groq_flash)

    # --- Reminder checker ---
    def _check_reminders():
        try:
            from skills import check_due_reminders, _tts_speak
            for msg in check_due_reminders():
                _tts_speak(f"Reminder: {msg}", bypass_mute=True)
        except Exception:
            pass
        QTimer.singleShot(30000, _check_reminders)
    QTimer.singleShot(30000, _check_reminders)

    # --- Wake Word ---
    _WAKE_PHRASES = {"vera"}
    _wake_stop = threading.Event()

    def _wake_word_loop():
        try:
            import sounddevice as sd  # type: ignore
            import numpy as np  # type: ignore
            from app import _get_whisper_model

            samplerate = 16000
            chunk_seconds = 1.5  # listen in 1.5s chunks for wake word
            chunk_samples = int(samplerate * chunk_seconds)

            model = _get_whisper_model()

            q: queue.Queue = queue.Queue()

            def _cb(indata, frames, time_info, status):
                q.put(indata.copy())

            with sd.InputStream(samplerate=samplerate, channels=1, dtype="float32", callback=_cb):
                audio_buf = np.zeros(0, dtype="float32")
                while not _wake_stop.is_set():
                    try:
                        chunk = q.get(timeout=0.3)
                        audio_buf = np.concatenate([audio_buf, chunk.flatten()])
                    except Exception:
                        continue

                    if len(audio_buf) < chunk_samples:
                        continue

                    # Transcribe the buffer and check for wake phrase
                    segments, _ = model.transcribe(audio_buf, language="en", beam_size=1, vad_filter=True)
                    text = " ".join(seg.text.strip() for seg in segments).lower()
                    audio_buf = np.zeros(0, dtype="float32")

                    if any(p in text for p in _WAKE_PHRASES) and not _wake_stop.is_set():
                        from personality import get_wake_ack  # type: ignore
                        from skills import _kokoro_tts_play  # type: ignore
                        _kokoro_tts_play(get_wake_ack())  # blocks until done
                        # Flush audio captured during TTS playback
                        while not q.empty():
                            try:
                                q.get_nowait()
                            except Exception:
                                break
                        audio_buf = np.zeros(0, dtype="float32")
                        # Beep to signal mic is open and ready
                        _ptt_beep(880, 150, load_config().get("ptt_beep_volume", 80))
                        # Record command
                        cmd_chunks = []
                        cmd_end = time.time() + 5
                        while time.time() < cmd_end and not _wake_stop.is_set():
                            try:
                                cmd_chunks.append(q.get(timeout=0.3).flatten())
                            except Exception:
                                continue
                        if cmd_chunks:
                            cmd_audio = np.concatenate(cmd_chunks)
                            segs, _ = model.transcribe(cmd_audio, language="en", beam_size=1, vad_filter=True)
                            command = " ".join(seg.text.strip() for seg in segs).strip()
                            if command:
                                _bridge.post(lambda t=command: _update_transcript(t))
                                if not handle_transcript(command, allow_prompt=True, confirm_fn=_confirm_prompt, restart_fn=_do_restart):
                                    log_unmatched(command)
        except Exception as exc:
            _runtime_mode["value"] = "idle"
            _bridge.post(lambda e=str(exc): (
                status_var.set("Wake word listener failed"),
                _show_inline_notice(f"Wake word listener failed: {e}", tone="error")
            ))

    _wake_thread: list = [None]  # mutable container so inner functions can update it

    def _start_wake_word():
        # Stop any existing wake word thread first
        _wake_stop.set()
        if _wake_thread[0] is not None and _wake_thread[0].is_alive():
            _wake_thread[0].join(timeout=2.0)
        _wake_stop.clear()
        t = threading.Thread(target=_wake_word_loop, daemon=True)
        _wake_thread[0] = t
        t.start()

    def _stop_wake_word():
        _wake_stop.set()
        if _wake_thread[0] is not None and _wake_thread[0].is_alive():
            _wake_thread[0].join(timeout=2.0)
        _wake_thread[0] = None

    # --- Setup Wizard ---
    def _run_wizard():
        state = {
            "mode": mode,
            "language": language,
            "seconds": seconds,
            "hotkey": hotkey,
            "holdkey": holdkey,
            "hotkey_display": hotkey_display,
            "holdkey_display": holdkey_display,
            "spotify_media": spotify_media,
            "spotify_requires": spotify_requires,
        }
        callbacks = {
            "model_present": _model_present,
            "record_hotkey": _record_hotkey,
            "record_hold_key": _record_hold_key,
            "import_steam": _import_steam,
            "build_config": _build_config,
            "save_config": save_config,
            "start_background": _start_background,
        }
        constants = {
            "HOTKEY_CHOICES": HOTKEY_CHOICES,
            "LANG_CHOICES": LANG_CHOICES,
        }
        wizard.run_wizard(root, state, callbacks, constants, {})
    # --- System Tray ---
    def _create_tray_icon():
        try:
            from pystray import pystray  # type: ignore
            from PIL import Image, ImageDraw  # type: ignore
        except Exception:
            return None

        def _make_image():
            asset_path = os.path.join(os.path.dirname(__file__), "data", "assets", "ipa_tray.png")
            try:
                return Image.open(asset_path)
            except Exception:
                img = Image.new("RGB", (64, 64), (30, 30, 30))
                d = ImageDraw.Draw(img)
                d.ellipse((8, 8, 56, 56), fill=(0, 200, 90))
                d.ellipse((24, 20, 40, 44), fill=(30, 30, 30))
                d.rectangle((30, 44, 34, 56), fill=(0, 200, 90))
                return img

        def _show_window(_=None):
            _bridge.post(lambda: (root.show(), root.raise_(), root.activateWindow()))

        def _hide_window(_=None):
            _bridge.post(root.hide)

        def _exit_app(_=None):
            try:
                _rpc_close()
                listener.stop()
                if tray_icon["icon"] is not None:
                    tray_icon["icon"].stop()
                _release_mutex()
            except Exception:
                pass
            finally:
                os._exit(0)

        def _restart_app(_=None):
            try:
                listener.stop()
                if tray_icon["icon"] is not None:
                    tray_icon["icon"].stop()
                _rpc_close()
                _release_mutex()
                script_path = os.path.abspath(__file__)
                subprocess.Popen([sys.executable, script_path])
            except Exception as exc:
                print(f"Failed to restart: {exc}")
            finally:
                os._exit(0)

        menu = pystray.Menu(
            pystray.MenuItem("Show", _show_window, default=True),
            pystray.MenuItem("Hide", _hide_window),
            pystray.MenuItem("Start Background", lambda _: _start_background()),
            pystray.MenuItem("Stop Background", lambda _: _stop_background()),
            pystray.MenuItem("Restart", _restart_app),
            pystray.MenuItem("Exit", _exit_app),
        )

        icon = pystray.Icon("vera", _make_image(), "VERA", menu)
        return icon

    def _start_tray():
        icon = _create_tray_icon()
        if icon is None:
            tray_ready["ok"] = False
            return
        tray_icon["icon"] = icon
        tray_ready["ok"] = True
        threading.Thread(target=icon.run, daemon=True).start()

    def _on_close():
        if tray_ready["ok"]:
            root.hide()
        else:
            _notify_info("Tray Unavailable", "System tray support isn't available. Install deps and restart.")

    def _install_deps():
        deps = ["sounddevice", "faster-whisper", "pynput", "pystray", "pillow", "PySide6", "pyttsx3"]
        status_var.set("Installing dependencies...")

        def _run():
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", *deps])
                status_var.set("Dependencies installed.")
                _notify_info("Done", "Dependencies installed.")
            except Exception as exc:
                status_var.set("Install failed.")
                _notify_error("Install Error", str(exc))

        threading.Thread(target=_run, daemon=True).start()

    def _create_bug_report():
        # ── Description dialog ────────────────────────────────────────────────
        description, ok = QInputDialog.getText(root, "Bug Report", "Describe the bug (what went wrong?):")
        if not ok:
            return
        description = description.strip()
        if not description:
            _notify_info("Bug Report", "Description is required.")
            return

        discord_username, _ = QInputDialog.getText(root, "Bug Report", "Your Discord username (optional — press Enter to skip):")
        discord_username = (discord_username or "").strip()

        # ── Zip logs ──────────────────────────────────────────────────────────
        base_dir = os.path.dirname(__file__)
        data_dir = os.path.join(base_dir, "data")
        logs_dir = os.path.join(data_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)

        config_path = os.path.join(data_dir, "config.json")
        log_path = os.path.join(logs_dir, "assistant.log")
        transcripts_path = os.path.join(logs_dir, "transcripts.log")
        ts = time.strftime("%Y%m%d_%H%M%S")
        zip_path = os.path.join(logs_dir, f"bug_report_{ts}.zip")

        files_added = 0
        try:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                if os.path.exists(config_path):
                    zf.write(config_path, arcname="config.json")
                    files_added += 1
                if os.path.exists(log_path):
                    zf.write(log_path, arcname="assistant.log")
                    files_added += 1
                if os.path.exists(transcripts_path):
                    zf.write(transcripts_path, arcname="transcripts.log")
                    files_added += 1
            if files_added == 0:
                try:
                    os.remove(zip_path)
                except Exception:
                    pass
                _notify_info("Bug Report", "No config or log file found yet.")
                return
        except Exception as exc:
            _notify_error("Bug Report Error", str(exc))
            return

        # ── Submit to Discord bot ─────────────────────────────────────────────
        _BUG_REPORT_URL    = "http://5.175.181.139:8080/report"
        _BUG_REPORT_SECRET = bug_report_secret_var.get()

        ticket_url = None
        if _BUG_REPORT_SECRET:
            try:
                import requests as _req
                version_path = os.path.join(base_dir, "VERSION")
                version = open(version_path).read().strip() if os.path.exists(version_path) else "unknown"
                with open(zip_path, "rb") as zf:
                    r = _req.post(
                        _BUG_REPORT_URL,
                        data={
                            "version": version,
                            "description": description,
                            "discord_username": discord_username,
                        },
                        files={"log_zip": (os.path.basename(zip_path), zf, "application/zip")},
                        headers={"X-VERA-Token": _BUG_REPORT_SECRET},
                        timeout=15,
                    )
                if r.ok:
                    ticket_url = r.json().get("thread_url")
            except Exception:
                pass

        if ticket_url:
            _notify_info(
                "Bug Report Submitted",
                f"Ticket created! Follow up here:\n{ticket_url}\n\nLog saved locally:\n{zip_path}"
            )
        else:
            _notify_info("Bug Report", f"Saved locally:\n{zip_path}")
            try:
                os.startfile(logs_dir)
            except Exception:
                pass

        if _confirm_dialog("Bug Report", "Would you like to clear the current logs to save space?"):
            try:
                for log_file in (log_path, transcripts_path):
                    if os.path.exists(log_file):
                        open(log_file, "w").close()
            except Exception:
                pass

    def _export_transcripts():
        src = os.path.join(os.path.dirname(__file__), "data", "logs", "transcripts.log")
        if not os.path.exists(src):
            _notify_info("Export Transcripts", "No transcript log found yet.")
            return
        dest, _ = QFileDialog.getSaveFileName(
            root,
            "Export Transcripts",
            "transcripts.log",
            "Log files (*.log);;Text files (*.txt);;All files (*.*)",
        )
        if not dest:
            return
        import shutil
        shutil.copy2(src, dest)
        _notify_info("Export Transcripts", f"Saved to:\n{dest}")

    def _clear_pycache():
        base_dir = os.path.dirname(__file__)
        removed = 0
        for root_dir, dirnames, _ in os.walk(base_dir):
            for name in list(dirnames):
                if name == "__pycache__":
                    cache_path = os.path.join(root_dir, name)
                    try:
                        shutil.rmtree(cache_path)
                        removed += 1
                    except Exception:
                        pass
        if removed:
            _notify_info("Cache Cleared", f"Removed {removed} __pycache__ folder(s).")
        else:
            _notify_info("Cache Cleared", "No __pycache__ folders found.")

    def _toggle_wake_word():
        if mode.get() == "wake":
            listener.stop()
            _start_wake_word()
            status_var.set("Wake word active (say 'vera')")
        else:
            _stop_wake_word()

    def _create_shortcuts():
        threading.Thread(target=_create_shortcuts_worker, daemon=True).start()

    def _create_shortcuts_worker():
        base_dir = os.path.dirname(os.path.abspath(__file__))
        target = os.path.join(base_dir, "launcher_out", "VERA.exe")
        icon = os.path.join(base_dir, "data", "assets", "ipa.ico")
        desktop = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop", "VERA.lnk")
        start_menu_dir = os.path.join(
            os.environ.get("APPDATA", ""),
            "Microsoft", "Windows", "Start Menu", "Programs", "VERA"
        )
        os.makedirs(start_menu_dir, exist_ok=True)
        start_menu = os.path.join(start_menu_dir, "VERA.lnk")

        def _make_lnk(dest):
            ps = (
                f'$ws = New-Object -ComObject WScript.Shell; '
                f'$s = $ws.CreateShortcut("{dest}"); '
                f'$s.TargetPath = "{target}"; '
                f'$s.WorkingDirectory = "{base_dir}"; '
                f'$s.IconLocation = "{target}, 0"; '
                f'$s.Save()'
            )
            return subprocess.run(["powershell", "-Command", ps], capture_output=True).returncode == 0

        desktop_ok = _make_lnk(desktop)
        start_ok = _make_lnk(start_menu)

        if desktop_ok or start_ok:
            parts = []
            if desktop_ok:
                parts.append("Desktop shortcut created.")
            if start_ok:
                parts.append("Start Menu shortcut created.")
            parts.append("\nTo pin VERA to Start: search for VERA, look under the 'Apps' section (not 'Best match'), right-click it, and select 'Pin to Start'.")
            _notify_info("Shortcuts Created", "\n".join(parts))
        else:
            _notify_error("Shortcut Failed", "Could not create shortcuts. Try creating them manually.")

    # =========================================================================
    # =========================================================================
    #  LAYOUT — the modern CustomTkinter UI (modularized)
    # =========================================================================

    state = {
        "mode": mode,
        "language": language,
        "seconds": seconds,
        "hotkey": hotkey,
        "holdkey": holdkey,
        "hotkey_display": hotkey_display,
        "holdkey_display": holdkey_display,
        "search_engine": search_engine,
        "confirm_actions": confirm_actions,
        "ptt_beep_volume": ptt_beep_volume,
        "tts_output_device": tts_output_device,
        "tts_device_choices": tts_device_choices,
        "tts_voice": tts_voice,
        "tts_voice_choices": tts_voice_choices,
        "personality_mode": personality_mode,
        "spotify_media": spotify_media,
        "spotify_requires": spotify_requires,
        "spotify_keywords": spotify_keywords,
        "news_source": news_source,
        "birthday_month": birthday_month,
        "birthday_day": birthday_day,
        "status_var": status_var,
        "transcript_var": transcript_var,
        "app_name_var": app_name_var,
        "app_cmd_var": app_cmd_var,
        "alias_var": alias_var,
        "alias_target_var": alias_target_var,
        "phrase_var": phrase_var,
        "command_var": command_var,
        "discord_ch_name_var": discord_ch_name_var,
        "discord_ch_url_var": discord_ch_url_var,
        "discord_ch_server_var": discord_ch_server_var,
        "discord_srv_nickname_var": discord_srv_nickname_var,
        "discord_srv_id_var": discord_srv_id_var,
        "discord_bot_token_var": discord_bot_token_var,
        "discord_server_id_var": discord_server_id_var,
        "gemini_api_key_var": gemini_api_key_var,
        "keybind_phrase_var": keybind_phrase_var,
        "keybind_key_var": keybind_key_var,
        "keybind_count_var": keybind_count_var,
    }

    callbacks_ui = {
        "load_logo": _load_logo,
        "save": _save,
        "run_now": _run_now,
        "install_deps": _install_deps,
        "start_background": _start_background,
        "stop_background": _stop_background,
        "check_for_updates": _check_for_updates,
        "create_bug_report": _create_bug_report,
        "export_transcripts": _export_transcripts,
        "mode_changed": _on_mode_change,
        "toggle_wake_word": _toggle_wake_word,
        "clear_pycache": _clear_pycache,
        "create_shortcuts": _create_shortcuts,
        "add_app": _add_app,
        "remove_app": _remove_app,
        "test_app": _test_app,
        "import_steam": _import_steam,
        "add_alias": _add_alias,
        "remove_alias": _remove_alias,
        "add_action": _add_action,
        "remove_action": _remove_action,
        "record_hotkey": _record_hotkey,
        "record_hold_key": _record_hold_key,
        "add_discord_channel": _add_discord_channel,
        "remove_discord_channel": _remove_discord_channel,
        "add_discord_server": _add_discord_server,
        "remove_discord_server": _remove_discord_server,
        "add_keybind": _add_keybind,
        "remove_keybind": _remove_keybind,
        "record_keybind_key": _record_keybind_step,
    }

    constants = {
        "HOTKEY_CHOICES": HOTKEY_CHOICES,
        "LANG_CHOICES": LANG_CHOICES,
    }

    widgets = ui.build_ui(window=root, state=state, callbacks=callbacks_ui, constants=constants)
    apps_textbox = widgets.get("apps_textbox")
    aliases_textbox = widgets.get("aliases_textbox")
    actions_textbox = widgets.get("actions_textbox")
    history_textbox = widgets.get("history_textbox")
    discord_channels_textbox = widgets.get("discord_channels_textbox")
    discord_servers_textbox = widgets.get("discord_servers_textbox")
    keybinds_textbox = widgets.get("keybinds_textbox")
    save_button = widgets.get("save_button")
    notice_frame = widgets.get("notice_frame")
    notice_label = widgets.get("notice_label")
    notice_action_button = widgets.get("notice_action_button")
    notice_close_button = widgets.get("notice_close_button")
    update_frame = widgets.get("update_frame")
    update_label = widgets.get("update_label")
    update_action_button = widgets.get("update_action_button")
    update_close_button = widgets.get("update_close_button")
    loading_overlay = widgets.get("loading_overlay")
    loading_progress = widgets.get("loading_progress")
    record_backdrop = widgets.get("record_backdrop")
    record_overlay = widgets.get("record_overlay")
    record_title_label = widgets.get("record_title_label")
    record_message_label = widgets.get("record_message_label")
    record_status_label = widgets.get("record_status_label")
    transcript_history = []

    if save_button is not None:
        class _SaveHoverFilter(QObject):
            def eventFilter(self, obj, event):
                from PySide6.QtCore import QEvent
                if obj is save_button:
                    if event.type() == QEvent.Enter:
                        save_button.setText("Save changes")
                    elif event.type() == QEvent.Leave:
                        save_button.setText("Unsaved changes")
                return False
        _save_hover_filter = _SaveHoverFilter(save_button)
        save_button.installEventFilter(_save_hover_filter)

    def _update_transcript(text: str):
        transcript_var.set(text)
        _reset_idle_timer()
        transcript_history.append(f"{time.strftime('%H:%M:%S')}  {text}")
        if len(transcript_history) > 10:
            transcript_history.pop(0)
        if history_textbox is not None:
            history_textbox.setReadOnly(False)
            history_textbox.clear()
            for line in reversed(transcript_history):
                history_textbox.append(line)
            history_textbox.setReadOnly(True)
    # =========================================================================
    #  Init
    # =========================================================================
    _refresh_actions()
    _refresh_apps()
    _refresh_aliases()
    _refresh_discord_channels()
    _refresh_discord_servers()
    _refresh_keybinds()
    _saved_config_signature[0] = _config_signature()
    for _var in (
        mode,
        language,
        seconds,
        hotkey,
        holdkey,
        search_engine,
        ptt_beep_volume,
        tts_output_device,
        tts_voice,
        personality_mode,
        premium,
        confirm_actions,
        spotify_media,
        spotify_requires,
        spotify_keywords,
        news_source,
        birthday_month,
        birthday_day,
        discord_bot_token_var,
        discord_server_id_var,
        gemini_api_key_var,
    ):
        _var.trace_add("write", _refresh_save_prompt)
    _refresh_save_prompt()

    if loading_overlay is not None:
        loading_overlay.show_over()

    def _animate_launch_reveal(on_done) -> None:
        if loading_overlay is not None:
            loading_overlay.hide_over()
        on_done()

    def _finish_launch():
        if loading_progress is not None:
            try:
                loading_progress.setRange(0, 1)
                loading_progress.setValue(1)
            except Exception:
                pass

        def _after_reveal():
            root.raise_()
            root.activateWindow()
            threading.Thread(target=_startup_update_check, daemon=True).start()
            if _test_update_alert:
                QTimer.singleShot(500, lambda: _show_update_notice("TEST", test=True))
            if not cfg.get("wizard_done"):
                _run_wizard()
            else:
                _start_background()
                if cfg.get("idle_chatter", True):
                    def _do_startup_greeting():
                        import time as _t
                        _t.sleep(2.0)
                        from skills import _tts_speak
                        from personality import get_startup_greeting
                        _tts_speak(get_startup_greeting())
                    threading.Thread(target=_do_startup_greeting, daemon=True).start()

        _animate_launch_reveal(_after_reveal)

    QTimer.singleShot(500, _finish_launch)

    root.show()
    _start_tray()
    sys.exit(app.exec())


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log_dir = os.path.join(os.path.dirname(__file__), "data", "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "assistant.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("\n=== Assistant Crash ===\n")
            f.write(traceback.format_exc())
            f.write("\n")
        try:
            _crash_app = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(None, "Assistant Error", f"The assistant crashed. See log:\n{log_path}")
        except Exception:
            pass
