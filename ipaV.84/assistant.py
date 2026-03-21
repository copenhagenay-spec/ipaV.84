"""All-in-one UI + background listener for the standalone assistant."""

from __future__ import annotations

import threading
import subprocess
import sys
import traceback
import os
import time
import zipfile
import shutil
import tempfile
import urllib.request
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

import ui
import wizard

from app import MissingDependencyError, transcribe_mic, transcribe_mic_hold
from config import load_config, save_config
from skills import handle_transcript
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

    def start_hotkey(self, hotkey: str, seconds: int, model_path: str, confirm_fn, on_text=None, restart_fn=None):
        from pynput import keyboard  # type: ignore

        def _record():
            text = _run_mic(seconds, model_path, confirm_fn=confirm_fn, allow_prompt=False, restart_fn=restart_fn)
            if on_text and text:
                on_text(text)

        def _on_activate():
            threading.Thread(target=_record, daemon=True).start()

        self.stop()
        self.mode = "hotkey"
        self.listener = keyboard.GlobalHotKeys({str(hotkey): _on_activate})
        self.listener.start()

    def start_hold(self, hold_key: str, model_path: str, confirm_fn, on_text=None, restart_fn=None):
        from pynput import keyboard  # type: ignore

        def _record():
            text = _run_hold(self.stop_event, hold_key, model_path, confirm_fn=confirm_fn, restart_fn=restart_fn)
            if on_text and text:
                on_text(text)
            self.recording_flag.clear()
            self.stop_event.clear()

        if _is_mouse_button(hold_key):
            from pynput import mouse  # type: ignore
            button_obj = _resolve_mouse_button(hold_key, mouse)
            if not button_obj:
                raise ValueError("Invalid mouse button")

            def _on_click(x, y, button, pressed):
                if button != button_obj:
                    return
                if pressed and not self.recording_flag.is_set():
                    self.recording_flag.set()
                    threading.Thread(target=_record, daemon=True).start()
                elif not pressed and self.recording_flag.is_set():
                    self.stop_event.set()

            self.stop()
            self.mode = "hold"
            self.listener = mouse.Listener(on_click=_on_click)
            self.listener.start()

        else:
            key_obj = _resolve_hold_key(hold_key, keyboard)
            if not key_obj:
                raise ValueError("Invalid hold key")

            def _on_press(key):
                if key == key_obj and not self.recording_flag.is_set():
                    self.recording_flag.set()
                    threading.Thread(target=_record, daemon=True).start()

            def _on_release(key):
                if key == key_obj and self.recording_flag.is_set():
                    self.stop_event.set()

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
    return str(key_name).strip().lower() in ("x1", "x2")


def _resolve_mouse_button(key_name: str, mouse):
    raw = str(key_name).strip().lower()
    if raw == "x1":
        return mouse.Button.x1
    if raw == "x2":
        return mouse.Button.x2
    return None


def _run_mic(seconds: int, model_path: str, confirm_fn=None, allow_prompt: bool = True, restart_fn=None):
    try:
        text = transcribe_mic(seconds=seconds, model_path=model_path)
        if text:
            handle_transcript(text, allow_prompt=allow_prompt, confirm_fn=confirm_fn, restart_fn=restart_fn)
        return text
    except MissingDependencyError as exc:
        messagebox.showerror("Missing Dependency", str(exc))
    except Exception as exc:
        messagebox.showerror("Error", str(exc))
    return ""


def _run_hold(stop_event: threading.Event, hold_key: str, model_path: str, confirm_fn=None, restart_fn=None):
    try:
        text = transcribe_mic_hold(stop_event=stop_event, model_path=model_path)
        if text:
            handle_transcript(text, allow_prompt=False, confirm_fn=confirm_fn, restart_fn=restart_fn)
        return text
    except MissingDependencyError as exc:
        messagebox.showerror("Missing Dependency", str(exc))
    except Exception as exc:
        messagebox.showerror("Error", str(exc))
    return ""


def main() -> None:
    cfg = load_config()
    if cfg and "wizard_done" not in cfg:
        cfg["wizard_done"] = True
        save_config(cfg)

    try:
        import ctypes  # type: ignore
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("IPA.Assistant")
    except Exception:
        pass

    # --- CustomTkinter setup ---
    theme_path = os.path.join(os.path.dirname(__file__), "data", "assets", "ipa_theme.json")
    if os.path.exists(theme_path):
        ctk.set_default_color_theme(theme_path)

    is_dark = cfg.get("theme", "dark") == "dark"
    ctk.set_appearance_mode("dark" if is_dark else "light")

    root = ctk.CTk()
    root.title("IPA Assistant")
    root.geometry("620x560")
    root.minsize(580, 460)
    root.resizable(True, True)
    try:
        icon_path = os.path.join(os.path.dirname(__file__), "data", "assets", "ipa.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    except Exception:
        pass

    # --- Tk variables (these still use tkinter StringVar/BooleanVar) ---
    theme_var = tk.BooleanVar(value=is_dark)
    mode = tk.StringVar(value=cfg.get("mode", "mic"))
    language = tk.StringVar(value=cfg.get("language", "English"))
    seconds = tk.StringVar(value=str(cfg.get("seconds", 5)))
    hotkey = tk.StringVar(value=cfg.get("hotkey", HOTKEY_CHOICES[0]))
    holdkey = tk.StringVar(value=cfg.get("hold_key", HOLD_CHOICES[0]))
    search_engine = tk.StringVar(
        value=cfg.get("search_engine", "https://www.google.com/search?q={query}")
    )
    confirm_actions = tk.BooleanVar(value=bool(cfg.get("confirm_actions", False)))
    spotify_media = tk.BooleanVar(value=bool(cfg.get("spotify_media", False)))
    spotify_requires = tk.BooleanVar(value=bool(cfg.get("spotify_requires_keyword", False)))
    spotify_keywords = tk.StringVar(value=str(cfg.get("spotify_keywords", "spotify")))

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
        for name, url in discord_cfg.items():
            discord_channels.append({"name": str(name).lower(), "url": str(url)})

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

    status_var = tk.StringVar(value="Idle")
    transcript_var = tk.StringVar(value="")
    app_name_var = tk.StringVar()
    app_cmd_var = tk.StringVar()
    alias_var = tk.StringVar()
    alias_target_var = tk.StringVar()
    phrase_var = tk.StringVar()
    command_var = tk.StringVar()
    discord_ch_name_var = tk.StringVar()
    discord_ch_url_var = tk.StringVar()
    discord_bot_token_var = tk.StringVar(value=cfg.get("discord_bot_token", ""))
    discord_server_id_var = tk.StringVar(value=cfg.get("discord_server_id", ""))
    keybind_phrase_var = tk.StringVar()
    keybind_key_var = tk.StringVar()
    keybind_count_var = tk.StringVar(value="1")
    apps_textbox = None
    aliases_textbox = None
    actions_textbox = None
    discord_channels_textbox = None
    keybinds_textbox = None
    listener = BackgroundListener()
    tray_icon = {"icon": None}
    tray_ready = {"ok": False}

    # --- Helper functions (logic unchanged) ---

    def _model_dir() -> str:
        lang = language.get().lower()
        if lang.startswith("span"):
            return os.path.join(os.path.dirname(__file__), "data", "model", "es")
        return os.path.join(os.path.dirname(__file__), "data", "model", "en")

    def _model_present() -> bool:
        model_dir = _model_dir()
        if not os.path.isdir(model_dir):
            return False
        try:
            entries = [os.path.join(model_dir, n) for n in os.listdir(model_dir)]
            return any(os.path.isdir(p) for p in entries)
        except Exception:
            return False

    def _build_config(wizard_done: bool | None = None) -> dict:
        try:
            secs = int(seconds.get())
            if secs <= 0:
                secs = 5
        except Exception:
            secs = 5
        data = {
            "theme": "dark" if theme_var.get() else "light",
            "mode": mode.get(),
            "language": language.get(),
            "seconds": secs,
            "hotkey": hotkey.get(),
            "hold_key": holdkey.get(),
            "search_engine": search_engine.get().strip(),
            "confirm_actions": bool(confirm_actions.get()),
            "spotify_media": bool(spotify_media.get()),
            "spotify_requires_keyword": bool(spotify_requires.get()),
            "spotify_keywords": spotify_keywords.get().strip(),
            "actions": [a for a in actions if a.get("phrase") and a.get("command")],
            "apps": {a.get("name"): a.get("command") for a in apps if a.get("name") and a.get("command")},
            "app_aliases": {a.get("alias"): a.get("target") for a in aliases if a.get("alias") and a.get("target")},
            "discord_channels": {a.get("name"): a.get("url") for a in discord_channels if a.get("name") and a.get("url")},
            "discord_bot_token": discord_bot_token_var.get().strip(),
            "discord_server_id": discord_server_id_var.get().strip(),
            "keybinds": [k for k in keybinds if k.get("phrase") and k.get("key")],
        }
        if wizard_done is not None:
            data["wizard_done"] = bool(wizard_done)
        return data

    def _confirm_prompt(prompt: str) -> bool:
        if not confirm_actions.get():
            return True
        return messagebox.askyesno("Confirm", prompt)

    def _do_restart():
        try:
            listener.stop()
            if tray_icon["icon"] is not None:
                tray_icon["icon"].stop()
            script_path = os.path.abspath(__file__)
            subprocess.Popen([sys.executable, script_path])
            root.after(0, root.destroy)
        except Exception as exc:
            print(f"Restart failed: {exc}")

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
        url = "https://raw.githubusercontent.com/copenhagenay-spec/IPA-alpha/main/ipaV.84/VERSION"
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
        tmp_dir = tempfile.mkdtemp(prefix="ipa_update_")
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
            messagebox.showerror("Update Failed", f"Could not check for updates.\n\n{exc}")
            return
        if not latest:
            messagebox.showinfo("Update", "Could not check for updates (no connection).")
            return
        if _parse_version(latest) <= _parse_version(current):
            messagebox.showinfo("Update", f"You're up to date (v{current}).")
            return

        if not messagebox.askyesno("Update Available", f"Update to v{latest}?"):
            return

        try:
            base_dir = os.path.dirname(__file__)
            data_dir = os.path.join(base_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            backup_dir = os.path.join(data_dir, f"backup_{time.strftime('%Y%m%d_%H%M%S')}")
            _backup_current_app(backup_dir)

            zip_url = "https://github.com/copenhagenay-spec/IPA-alpha/archive/refs/heads/main.zip"
            zip_path = os.path.join(data_dir, "update.zip")
            urllib.request.urlretrieve(zip_url, zip_path)
            _apply_update_from_zip(zip_path)
            try:
                os.remove(zip_path)
            except Exception:
                pass

            messagebox.showinfo("Update", "Update installed. Restarting IPA...")
            script_path = os.path.abspath(__file__)
            subprocess.Popen([sys.executable, script_path])
            root.destroy()
        except Exception as exc:
            messagebox.showerror("Update Failed", str(exc))

    def _record_hotkey(target_var: tk.StringVar) -> None:
        try:
            from pynput import keyboard  # type: ignore
        except Exception:
            messagebox.showerror("Missing Dependency", "pynput is required to record hotkeys.")
            return

        dialog = tk.Toplevel(root)
        dialog.title("Record Hotkey")
        dialog.geometry("320x120")
        dialog.resizable(False, False)
        dialog.transient(root)
        dialog.grab_set()

        info = tk.Label(dialog, text="Press a key combo (Esc to cancel)")
        info.pack(padx=10, pady=(12, 6))
        status = tk.StringVar(value="Waiting...")
        tk.Label(dialog, textvariable=status).pack(padx=10, pady=(0, 10))

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
        listener.start()

    def _record_hold_key(target_var: tk.StringVar) -> None:
        try:
            from pynput import keyboard  # type: ignore
            from pynput import mouse as pynput_mouse  # type: ignore
        except Exception:
            messagebox.showerror("Missing Dependency", "pynput is required to record keys.")
            return

        dialog = tk.Toplevel(root)
        dialog.title("Record Hold Key")
        dialog.geometry("340x130")
        dialog.resizable(False, False)
        dialog.transient(root)
        dialog.grab_set()

        info = tk.Label(dialog, text="Press a key or side mouse button (Esc to cancel)")
        info.pack(padx=10, pady=(12, 6))
        status = tk.StringVar(value="Waiting...")
        tk.Label(dialog, textvariable=status).pack(padx=10, pady=(0, 10))

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
        active["kb"].start()
        active["ms"] = pynput_mouse.Listener(on_click=_on_click)
        active["ms"].start()

    def _load_logo():
        logo_path = os.path.join(os.path.dirname(__file__), "data", "assets", "ipa_logo.png")
        try:
            from PIL import Image  # type: ignore
            pil_img = Image.open(logo_path)
            w, h = pil_img.size
            new_w, new_h = w // 6, h // 6
            img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(new_w, new_h))
            return img
        except Exception:
            return None

    def _save():
        data = _build_config()
        save_config(data)
        messagebox.showinfo("Saved", "Configuration saved.")

    # --- Actions list helpers ---
    def _refresh_actions():
        if actions_textbox is None:
            return
        actions_textbox.configure(state="normal")
        actions_textbox.delete("1.0", "end")
        for a in actions:
            phrase = a.get("phrase", "")
            command = a.get("command", "")
            actions_textbox.insert("end", f"{phrase}  ->  {command}\n")
        actions_textbox.configure(state="disabled")

    def _add_action():
        phrase = phrase_var.get().strip()
        command = command_var.get().strip()
        if not phrase or not command:
            messagebox.showerror("Invalid", "Phrase and command are required.")
            return
        actions.append({"phrase": phrase, "command": command})
        phrase_var.set("")
        command_var.set("")
        _refresh_actions()

    def _remove_action():
        if not actions:
            return
        actions.pop(-1)
        _refresh_actions()

    # --- Apps list helpers ---
    def _refresh_apps():
        if apps_textbox is None:
            return
        apps_textbox.configure(state="normal")
        apps_textbox.delete("1.0", "end")
        for a in apps:
            name = a.get("name", "")
            command = a.get("command", "")
            apps_textbox.insert("end", f"{name}  ->  {command}\n")
        apps_textbox.configure(state="disabled")

    def _refresh_aliases():
        if aliases_textbox is None:
            return
        aliases_textbox.configure(state="normal")
        aliases_textbox.delete("1.0", "end")
        for a in aliases:
            aliases_textbox.insert("end", f"{a.get('alias')}  ->  {a.get('target')}\n")
        aliases_textbox.configure(state="disabled")

    def _add_alias():
        alias = alias_var.get().strip().lower()
        target = alias_target_var.get().strip().lower()
        if not alias or not target:
            messagebox.showerror("Invalid", "Alias and target app are required.")
            return
        aliases.append({"alias": alias, "target": target})
        alias_var.set("")
        alias_target_var.set("")
        _refresh_aliases()

    def _remove_alias():
        if not aliases:
            return
        aliases.pop(-1)
        _refresh_aliases()

    def _add_app():
        name = app_name_var.get().strip().lower()
        command = app_cmd_var.get().strip()
        if not name or not command:
            messagebox.showerror("Invalid", "App name and command are required.")
            return
        apps.append({"name": name, "command": command})
        app_name_var.set("")
        app_cmd_var.set("")
        _refresh_apps()

    def _test_app():
        command = app_cmd_var.get().strip()
        if not command:
            messagebox.showerror("Invalid", "App command is required to test.")
            return
        try:
            subprocess.Popen(command, shell=True)
        except Exception as exc:
            messagebox.showerror("Test Failed", str(exc))

    def _remove_app():
        if not apps:
            return
        apps.pop(-1)
        _refresh_apps()

    # --- Discord channels helpers ---
    def _refresh_discord_channels():
        if discord_channels_textbox is None:
            return
        discord_channels_textbox.configure(state="normal")
        discord_channels_textbox.delete("1.0", "end")
        for ch in discord_channels:
            discord_channels_textbox.insert("end", f"#{ch.get('name')}  ->  {ch.get('url')}\n")
        discord_channels_textbox.configure(state="disabled")

    def _add_discord_channel():
        name = discord_ch_name_var.get().strip().lower()
        url = discord_ch_url_var.get().strip()
        if not name or not url:
            messagebox.showerror("Invalid", "Channel name and webhook URL are required.")
            return
        discord_channels.append({"name": name, "url": url})
        discord_ch_name_var.set("")
        discord_ch_url_var.set("")
        _refresh_discord_channels()

    def _remove_discord_channel():
        if not discord_channels:
            return
        discord_channels.pop(-1)
        _refresh_discord_channels()

    # --- Keybinds helpers ---
    def _refresh_keybinds():
        if keybinds_textbox is None:
            return
        keybinds_textbox.configure(state="normal")
        keybinds_textbox.delete("1.0", "end")
        for kb in keybinds:
            count = kb.get("count", 1)
            suffix = f" x{count}" if int(count) > 1 else ""
            keybinds_textbox.insert("end", f"{kb.get('phrase')}  ->  {kb.get('key')}{suffix}\n")
        keybinds_textbox.configure(state="disabled")

    def _add_keybind():
        phrase = keybind_phrase_var.get().strip().lower()
        key = keybind_key_var.get().strip()
        try:
            count = max(1, int(keybind_count_var.get().strip()))
        except Exception:
            count = 1
        if not phrase or not key:
            messagebox.showerror("Invalid", "Phrase and key are required.")
            return
        keybinds.append({"phrase": phrase, "key": key, "count": count})
        keybind_phrase_var.set("")
        keybind_key_var.set("")
        keybind_count_var.set("1")
        _refresh_keybinds()

    def _remove_keybind():
        if not keybinds:
            return
        keybinds.pop(-1)
        _refresh_keybinds()

    def _import_steam():
        try:
            found = find_steam_apps()
        except Exception as exc:
            messagebox.showerror("Steam Import Error", str(exc))
            return
        if not found:
            messagebox.showinfo("Steam Import", "No Steam apps found.")
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
        messagebox.showinfo("Steam Import", f"Added {added} apps.")

    def _run_now():
        try:
            secs = int(seconds.get())
        except Exception:
            secs = 5
        if mode.get() == "mic":
            def _run():
                text = _run_mic(secs, _model_dir(), confirm_fn=_confirm_prompt, allow_prompt=True, restart_fn=_do_restart)
                if text:
                    root.after(0, lambda: _update_transcript(text))
            threading.Thread(target=_run, daemon=True).start()
        elif mode.get() == "hold":
            messagebox.showinfo("Hold Mode", "Hold mode only runs in the background.")
        else:
            messagebox.showinfo("Hotkey Mode", "Hotkey mode only runs in the background.")

    def _start_background():
        try:
            secs = int(seconds.get())
        except Exception:
            secs = 5
        try:
            if mode.get() == "hold":
                listener.start_hold(
                    holdkey.get(),
                    model_path=_model_dir(),
                    confirm_fn=_confirm_prompt,
                    on_text=lambda t: root.after(0, lambda: _update_transcript(t)),
                    restart_fn=_do_restart,
                )
                status_var.set(f"Listening (hold {holdkey.get()})")
            elif mode.get() == "hotkey":
                listener.start_hotkey(
                    hotkey.get(),
                    secs,
                    model_path=_model_dir(),
                    confirm_fn=_confirm_prompt,
                    on_text=lambda t: root.after(0, lambda: _update_transcript(t)),
                    restart_fn=_do_restart,
                )
                status_var.set(f"Listening (hotkey {hotkey.get()})")
            else:
                status_var.set("Timed mic mode (manual Run Now)")
        except Exception as exc:
            messagebox.showerror("Listener Error", str(exc))

    def _stop_background():
        listener.stop()
        status_var.set("Idle")

    # --- Setup Wizard ---
    def _run_wizard():
        model_urls = {
            "en": "https://github.com/copenhagenay-spec/IPA-alpha/releases/download/dependency/vosk-model-small-en-us-0.15.zip",
            "es": "https://github.com/copenhagenay-spec/IPA-alpha/releases/download/dependency2/vosk-model-small-es-0.42.zip",
        }
        state = {
            "mode": mode,
            "language": language,
            "seconds": seconds,
            "hotkey": hotkey,
            "holdkey": holdkey,
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
        wizard.run_wizard(root, state, callbacks, constants, model_urls)
    # --- System Tray ---
    def _create_tray_icon():
        try:
            import pystray  # type: ignore
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
            root.after(0, lambda: (root.deiconify(), root.lift(), root.focus_force()))

        def _hide_window(_=None):
            root.after(0, root.withdraw)

        def _exit_app(_=None):
            listener.stop()
            if tray_icon["icon"] is not None:
                tray_icon["icon"].stop()
            root.after(0, root.destroy)

        def _restart_app(_=None):
            try:
                listener.stop()
                if tray_icon["icon"] is not None:
                    tray_icon["icon"].stop()
                script_path = os.path.abspath(__file__)
                subprocess.Popen([sys.executable, script_path])
                root.destroy()
            except Exception as exc:
                print(f"Failed to restart: {exc}")

        menu = pystray.Menu(
            pystray.MenuItem("Show", _show_window, default=True),
            pystray.MenuItem("Hide", _hide_window),
            pystray.MenuItem("Start Background", lambda _: _start_background()),
            pystray.MenuItem("Stop Background", lambda _: _stop_background()),
            pystray.MenuItem("Restart", _restart_app),
            pystray.MenuItem("Exit", _exit_app),
        )

        icon = pystray.Icon("ipa-assistant", _make_image(), "IPA Assistant", menu)
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
            root.withdraw()
        else:
            messagebox.showinfo(
                "Tray Unavailable",
                "System tray support isn't available. Install deps and restart.",
            )

    def _on_minimize(event):
        if root.state() == "iconic":
            if tray_ready["ok"]:
                root.withdraw()

    def _poll_minimize():
        if root.state() == "iconic" and tray_ready["ok"]:
            root.withdraw()
        root.after(400, _poll_minimize)

    def _install_deps():
        deps = ["sounddevice", "vosk", "pynput", "pystray", "pillow", "customtkinter", "pyttsx3"]
        status_var.set("Installing dependencies...")

        def _run():
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", *deps])
                status_var.set("Dependencies installed.")
                messagebox.showinfo("Done", "Dependencies installed.")
            except Exception as exc:
                status_var.set("Install failed.")
                messagebox.showerror("Install Error", str(exc))

        threading.Thread(target=_run, daemon=True).start()

    def _create_bug_report():
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
                messagebox.showinfo("Bug Report", "No config or log file found yet.")
                return
        except Exception as exc:
            messagebox.showerror("Bug Report Error", str(exc))
            return

        messagebox.showinfo("Bug Report", f"Created:\n{zip_path}")
        try:
            os.startfile(logs_dir)
        except Exception:
            pass

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
            messagebox.showinfo("Cache Cleared", f"Removed {removed} __pycache__ folder(s).")
        else:
            messagebox.showinfo("Cache Cleared", "No __pycache__ folders found.")

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
        "search_engine": search_engine,
        "confirm_actions": confirm_actions,
        "theme_var": theme_var,
        "spotify_media": spotify_media,
        "spotify_requires": spotify_requires,
        "spotify_keywords": spotify_keywords,
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
        "discord_bot_token_var": discord_bot_token_var,
        "discord_server_id_var": discord_server_id_var,
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
        "clear_pycache": _clear_pycache,
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
        "add_keybind": _add_keybind,
        "remove_keybind": _remove_keybind,
        "record_keybind_key": _record_hold_key,
    }

    constants = {
        "HOTKEY_CHOICES": HOTKEY_CHOICES,
        "LANG_CHOICES": LANG_CHOICES,
    }

    widgets = ui.build_ui(root=root, state=state, callbacks=callbacks_ui, constants=constants)
    apps_textbox = widgets.get("apps_textbox")
    aliases_textbox = widgets.get("aliases_textbox")
    actions_textbox = widgets.get("actions_textbox")
    history_textbox = widgets.get("history_textbox")
    discord_channels_textbox = widgets.get("discord_channels_textbox")
    keybinds_textbox = widgets.get("keybinds_textbox")
    transcript_history = []

    def _update_transcript(text: str):
        transcript_var.set(text)
        transcript_history.append(f"{time.strftime('%H:%M:%S')}  {text}")
        if len(transcript_history) > 10:
            transcript_history.pop(0)
        if history_textbox is not None:
            history_textbox.configure(state="normal")
            history_textbox.delete("1.0", "end")
            for line in reversed(transcript_history):
                history_textbox.insert("end", line + "\n")
            history_textbox.configure(state="disabled")
    # =========================================================================
    #  Init
    # =========================================================================
    _refresh_actions()
    _refresh_apps()
    _refresh_aliases()
    _refresh_discord_channels()
    _refresh_keybinds()
    if not cfg.get("wizard_done"):
        _run_wizard()
    else:
        _start_background()

    root.protocol("WM_DELETE_WINDOW", _on_close)
    root.bind("<Unmap>", _on_minimize)
    _start_tray()
    _poll_minimize()
    root.mainloop()


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
            import tkinter as tk
            from tkinter import messagebox

            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Assistant Error",
                f"The assistant crashed. See log:\n{log_path}",
            )
            root.destroy()
        except Exception:
            pass








