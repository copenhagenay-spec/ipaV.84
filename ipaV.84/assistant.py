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

    def start_hotkey(self, hotkey: str, seconds: int, model_path: str, confirm_fn, on_text=None):
        from pynput import keyboard  # type: ignore

        def _record():
            text = _run_mic(seconds, model_path, confirm_fn=confirm_fn, allow_prompt=False)
            if on_text and text:
                on_text(text)

        def _on_activate():
            threading.Thread(target=_record, daemon=True).start()

        self.stop()
        self.mode = "hotkey"
        self.listener = keyboard.GlobalHotKeys({str(hotkey): _on_activate})
        self.listener.start()

    def start_hold(self, hold_key: str, model_path: str, confirm_fn, on_text=None):
        from pynput import keyboard  # type: ignore

        key_obj = _resolve_hold_key(hold_key, keyboard)
        if not key_obj:
            raise ValueError("Invalid hold key")

        def _record():
            text = _run_hold(self.stop_event, hold_key, model_path, confirm_fn=confirm_fn)
            if on_text and text:
                on_text(text)
            self.recording_flag.clear()
            self.stop_event.clear()

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


def _run_mic(seconds: int, model_path: str, confirm_fn=None, allow_prompt: bool = True):
    try:
        text = transcribe_mic(seconds=seconds, model_path=model_path)
        if text:
            handle_transcript(text, allow_prompt=allow_prompt, confirm_fn=confirm_fn)
        return text
    except MissingDependencyError as exc:
        messagebox.showerror("Missing Dependency", str(exc))
    except Exception as exc:
        messagebox.showerror("Error", str(exc))
    return ""


def _run_hold(stop_event: threading.Event, hold_key: str, model_path: str, confirm_fn=None):
    try:
        text = transcribe_mic_hold(stop_event=stop_event, model_path=model_path)
        if text:
            handle_transcript(text, allow_prompt=False, confirm_fn=confirm_fn)
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

    status_var = tk.StringVar(value="Idle")
    transcript_var = tk.StringVar(value="")
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
        }
        if wizard_done is not None:
            data["wizard_done"] = bool(wizard_done)
        return data

    def _confirm_prompt(prompt: str) -> bool:
        if not confirm_actions.get():
            return True
        return messagebox.askyesno("Confirm", prompt)

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
        url = "https://raw.githubusercontent.com/copenhagenay-spec/IPA-alpha/main/VERSION"
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                return resp.read().decode("utf-8").strip()
        except Exception:
            return None

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

    def _check_for_updates():
        current = _read_local_version()
        latest = _fetch_latest_version()
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
        except Exception:
            messagebox.showerror("Missing Dependency", "pynput is required to record keys.")
            return

        dialog = tk.Toplevel(root)
        dialog.title("Record Hold Key")
        dialog.geometry("320x120")
        dialog.resizable(False, False)
        dialog.transient(root)
        dialog.grab_set()

        info = tk.Label(dialog, text="Press a single key (Esc to cancel)")
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

        def _finish(value: str | None):
            if value:
                target_var.set(value)
                status.set(f"Captured: {value}")
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
                return
            name = _key_name(key)
            if name:
                _finish(name)
            else:
                _finish(None)
            return False

        listener = keyboard.Listener(on_press=_on_press)
        listener.start()

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
        apps_textbox.configure(state="normal")
        apps_textbox.delete("1.0", "end")
        for a in apps:
            name = a.get("name", "")
            command = a.get("command", "")
            apps_textbox.insert("end", f"{name}  ->  {command}\n")
        apps_textbox.configure(state="disabled")

    def _refresh_aliases():
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
                text = _run_mic(secs, _model_dir(), confirm_fn=_confirm_prompt, allow_prompt=True)
                if text:
                    root.after(0, lambda: transcript_var.set(text))
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
                    on_text=lambda t: root.after(0, lambda: transcript_var.set(t)),
                )
                status_var.set(f"Listening (hold {holdkey.get()})")
            elif mode.get() == "hotkey":
                listener.start_hotkey(
                    hotkey.get(),
                    secs,
                    model_path=_model_dir(),
                    confirm_fn=_confirm_prompt,
                    on_text=lambda t: root.after(0, lambda: transcript_var.set(t)),
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
        wizard = ctk.CTkToplevel(root)
        wizard.title("IPA Setup Wizard")
        wizard.geometry("520x480")
        wizard.resizable(False, False)
        wizard.transient(root)
        wizard.grab_set()
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "data", "assets", "ipa.ico")
            if os.path.exists(icon_path):
                wizard.after(200, lambda: wizard.iconbitmap(icon_path))
        except Exception:
            pass

        scroll = ctk.CTkScrollableFrame(wizard)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(scroll, text="Welcome to IPA!", font=("Segoe UI", 18, "bold")).pack(
            anchor="w", padx=10, pady=(10, 4)
        )

        status_text = "Found" if _model_present() else "Not found"
        ctk.CTkLabel(scroll, text=f"Voice model status: {status_text}").pack(
            anchor="w", padx=10, pady=(0, 10)
        )

        # Language
        lang_frame = ctk.CTkFrame(scroll)
        lang_frame.pack(fill="x", padx=10, pady=6)
        ctk.CTkLabel(lang_frame, text="Language").pack(side="left", padx=10, pady=8)
        ctk.CTkOptionMenu(lang_frame, variable=language, values=LANG_CHOICES, width=160).pack(
            side="right", padx=10, pady=8
        )

        # Mode
        ctk.CTkLabel(scroll, text="Listening Mode", font=("Segoe UI", 12, "bold")).pack(
            anchor="w", padx=10, pady=(10, 4)
        )
        mode_frame = ctk.CTkFrame(scroll)
        mode_frame.pack(fill="x", padx=10, pady=6)
        ctk.CTkRadioButton(mode_frame, text="Timed mic", variable=mode, value="mic").pack(
            anchor="w", padx=20, pady=4
        )
        ctk.CTkRadioButton(mode_frame, text="Hold-to-talk", variable=mode, value="hold").pack(
            anchor="w", padx=20, pady=4
        )
        ctk.CTkRadioButton(mode_frame, text="Hotkey", variable=mode, value="hotkey").pack(
            anchor="w", padx=20, pady=(4, 8)
        )

        # Recording settings
        rec_frame = ctk.CTkFrame(scroll)
        rec_frame.pack(fill="x", padx=10, pady=6)
        ctk.CTkLabel(rec_frame, text="Seconds").pack(side="left", padx=10, pady=8)
        ctk.CTkEntry(rec_frame, textvariable=seconds, width=80).pack(side="left", padx=10, pady=8)
        ctk.CTkLabel(rec_frame, text="Hotkey").pack(side="left", padx=10, pady=8)
        ctk.CTkOptionMenu(rec_frame, variable=hotkey, values=HOTKEY_CHOICES, width=160).pack(
            side="left", padx=10, pady=8
        )

        hold_frame = ctk.CTkFrame(scroll)
        hold_frame.pack(fill="x", padx=10, pady=6)
        ctk.CTkLabel(hold_frame, text="Hold key").pack(side="left", padx=10, pady=8)
        ctk.CTkOptionMenu(hold_frame, variable=holdkey, values=HOLD_CHOICES, width=160).pack(
            side="left", padx=10, pady=8
        )

        # Spotify
        ctk.CTkCheckBox(scroll, text="Enable Spotify media controls", variable=spotify_media).pack(
            anchor="w", padx=20, pady=4
        )
        ctk.CTkCheckBox(scroll, text="Require word 'spotify' in command", variable=spotify_requires).pack(
            anchor="w", padx=20, pady=4
        )

        # Download buttons
        def _download_model(lang: str, url: str):
            dest_root = os.path.join(os.path.dirname(__file__), "data", "model")
            os.makedirs(dest_root, exist_ok=True)
            zip_path = os.path.join(dest_root, f"{lang}.zip")
            extract_dir = os.path.join(dest_root, lang)
            os.makedirs(extract_dir, exist_ok=True)

            def _run():
                try:
                    import urllib.request

                    urllib.request.urlretrieve(url, zip_path)
                    with zipfile.ZipFile(zip_path, "r") as zf:
                        zf.extractall(extract_dir)
                    messagebox.showinfo("Done", f"{lang.upper()} model downloaded.")
                except Exception as exc:
                    messagebox.showerror("Download Error", str(exc))

            threading.Thread(target=_run, daemon=True).start()

        btn_frame = ctk.CTkFrame(scroll)
        btn_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkButton(btn_frame, text="Download English Model", command=lambda: _download_model(
            "en",
            "https://github.com/copenhagenay-spec/ipaV.84/releases/download/dependency/vosk-model-small-en-us-0.15.zip",
        )).pack(side="left", padx=6, pady=8)
        ctk.CTkButton(btn_frame, text="Download Spanish Model", command=lambda: _download_model(
            "es",
            "https://github.com/copenhagenay-spec/ipaV.84/releases/download/dependency2/vosk-model-small-es-0.42.zip",
        )).pack(side="left", padx=6, pady=8)

        btn_frame2 = ctk.CTkFrame(scroll)
        btn_frame2.pack(fill="x", padx=10, pady=6)
        ctk.CTkButton(btn_frame2, text="Import Steam Apps", command=_import_steam).pack(
            side="left", padx=6, pady=8
        )

        def _install_deps_wizard():
            deps = ["sounddevice", "vosk", "pynput", "pystray", "pillow", "customtkinter"]

            def _run():
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", *deps])
                    messagebox.showinfo("Done", "Dependencies installed.")
                except Exception as exc:
                    messagebox.showerror("Install Error", str(exc))

            threading.Thread(target=_run, daemon=True).start()

        ctk.CTkButton(btn_frame2, text="Install Dependencies", command=_install_deps_wizard).pack(
            side="left", padx=6, pady=8
        )

        def _finish():
            data = _build_config(wizard_done=True)
            save_config(data)
            wizard.destroy()
            _start_background()
            messagebox.showinfo("Done", "Setup complete. IPA is ready.")

        ctk.CTkButton(scroll, text="Finish Setup", command=_finish, height=40,
                       font=("Segoe UI", 14, "bold")).pack(padx=10, pady=16, fill="x")

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
        deps = ["sounddevice", "vosk", "pynput", "pystray", "pillow", "customtkinter"]
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

    # =========================================================================
    #  LAYOUT — the modern CustomTkinter UI
    # =========================================================================

    # --- Tabview (replaces ttk.Notebook) ---
    tabview = ctk.CTkTabview(root)
    tabview.pack(fill="both", expand=True, padx=10, pady=(10, 0))
    tabview.add("Main")
    tabview.add("Apps")
    tabview.add("Actions")
    tabview.set("Main")

    # ---- MAIN TAB ----
    main_scroll = ctk.CTkScrollableFrame(tabview.tab("Main"))
    main_scroll.pack(fill="both", expand=True)

    # Logo
    logo_img = _load_logo()
    if logo_img is not None:
        logo_label = ctk.CTkLabel(main_scroll, image=logo_img, text="")
        logo_label.pack(pady=(6, 2))

    # -- Mode section --
    ctk.CTkLabel(main_scroll, text="Listening Mode", font=("Segoe UI", 13, "bold")).pack(
        anchor="w", padx=12, pady=(10, 4)
    )
    mode_card = ctk.CTkFrame(main_scroll)
    mode_card.pack(fill="x", padx=12, pady=4)

    mode_row = ctk.CTkFrame(mode_card, fg_color="transparent")
    mode_row.pack(fill="x", padx=12, pady=8)
    ctk.CTkRadioButton(mode_row, text="Timed mic", variable=mode, value="mic").pack(
        side="left", padx=(0, 16)
    )
    ctk.CTkRadioButton(mode_row, text="Hold-to-talk", variable=mode, value="hold").pack(
        side="left", padx=(0, 16)
    )
    ctk.CTkRadioButton(mode_row, text="Hotkey", variable=mode, value="hotkey").pack(
        side="left"
    )

    # -- Recording section --
    ctk.CTkLabel(main_scroll, text="Recording Settings", font=("Segoe UI", 13, "bold")).pack(
        anchor="w", padx=12, pady=(14, 4)
    )
    rec_card = ctk.CTkFrame(main_scroll)
    rec_card.pack(fill="x", padx=12, pady=4)

    rec_row1 = ctk.CTkFrame(rec_card, fg_color="transparent")
    rec_row1.pack(fill="x", padx=12, pady=(8, 4))
    ctk.CTkLabel(rec_row1, text="Seconds", width=120).pack(side="left")
    ctk.CTkEntry(rec_row1, textvariable=seconds, width=80).pack(side="left", padx=(0, 20))
    ctk.CTkLabel(rec_row1, text="Language", width=80).pack(side="left")
    ctk.CTkOptionMenu(rec_row1, variable=language, values=LANG_CHOICES, width=140).pack(side="left")

    rec_row2 = ctk.CTkFrame(rec_card, fg_color="transparent")
    rec_row2.pack(fill="x", padx=12, pady=4)
    ctk.CTkLabel(rec_row2, text="Hotkey", width=120).pack(side="left")
    ctk.CTkOptionMenu(rec_row2, variable=hotkey, values=HOTKEY_CHOICES, width=180).pack(
        side="left", padx=(0, 20)
    )

    rec_row3 = ctk.CTkFrame(rec_card, fg_color="transparent")
    rec_row3.pack(fill="x", padx=12, pady=(4, 8))
    ctk.CTkLabel(rec_row3, text="Hold key", width=120).pack(side="left")
    ctk.CTkOptionMenu(rec_row3, variable=holdkey, values=HOLD_CHOICES, width=180).pack(side="left")

    rec_row4 = ctk.CTkFrame(rec_card, fg_color="transparent")
    rec_row4.pack(fill="x", padx=12, pady=(4, 8))
    ctk.CTkLabel(rec_row4, text="Search Engine", width=120).pack(side="left")
    ctk.CTkEntry(rec_row4, textvariable=search_engine, width=340).pack(side="left")

    # -- Options section --
    ctk.CTkLabel(main_scroll, text="Options", font=("Segoe UI", 13, "bold")).pack(
        anchor="w", padx=12, pady=(14, 4)
    )
    opt_card = ctk.CTkFrame(main_scroll)
    opt_card.pack(fill="x", padx=12, pady=4)

    ctk.CTkCheckBox(opt_card, text="Confirm before running actions", variable=confirm_actions).pack(
        anchor="w", padx=16, pady=(10, 4)
    )

    def _toggle_theme():
        new_mode = "dark" if theme_var.get() else "light"
        ctk.set_appearance_mode(new_mode)

    ctk.CTkCheckBox(opt_card, text="Dark mode", variable=theme_var, command=_toggle_theme).pack(
        anchor="w", padx=16, pady=4
    )
    ctk.CTkCheckBox(opt_card, text="Enable Spotify media controls", variable=spotify_media).pack(
        anchor="w", padx=16, pady=4
    )
    ctk.CTkCheckBox(opt_card, text="Require word 'spotify' in command", variable=spotify_requires).pack(
        anchor="w", padx=16, pady=4
    )

    spot_row = ctk.CTkFrame(opt_card, fg_color="transparent")
    spot_row.pack(fill="x", padx=16, pady=(4, 10))
    ctk.CTkLabel(spot_row, text="Spotify keywords").pack(side="left")
    ctk.CTkEntry(spot_row, textvariable=spotify_keywords, width=240).pack(side="left", padx=(10, 0))

    # -- Controls section --
    ctk.CTkLabel(main_scroll, text="Controls", font=("Segoe UI", 13, "bold")).pack(
        anchor="w", padx=12, pady=(14, 4)
    )
    ctrl_card = ctk.CTkFrame(main_scroll)
    ctrl_card.pack(fill="x", padx=12, pady=4)

    ctrl_row1 = ctk.CTkFrame(ctrl_card, fg_color="transparent")
    ctrl_row1.pack(fill="x", padx=12, pady=(8, 4))
    ctk.CTkButton(ctrl_row1, text="Save Config", command=_save, width=130).pack(side="left", padx=4)
    ctk.CTkButton(ctrl_row1, text="Run Now", command=_run_now, width=130).pack(side="left", padx=4)
    ctk.CTkButton(ctrl_row1, text="Install Deps", command=_install_deps, width=130).pack(side="left", padx=4)

    ctrl_row2 = ctk.CTkFrame(ctrl_card, fg_color="transparent")
    ctrl_row2.pack(fill="x", padx=12, pady=(4, 8))
    ctk.CTkButton(ctrl_row2, text="Start Background", command=_start_background, width=130).pack(
        side="left", padx=4
    )
    ctk.CTkButton(ctrl_row2, text="Stop Background", command=_stop_background, width=130,
                   fg_color=("#cc3333", "#cc3333"), hover_color=("#aa2222", "#aa2222")).pack(
        side="left", padx=4
    )
    ctk.CTkButton(ctrl_row2, text="Bug Report", command=_create_bug_report, width=130,
                   fg_color=("gray60", "gray30"), hover_color=("gray50", "gray40")).pack(
        side="left", padx=4
    )

    # -- Status section (bottom bar) --
    status_frame = ctk.CTkFrame(root)
    status_frame.pack(fill="x", padx=10, pady=(4, 10))

    status_left = ctk.CTkFrame(status_frame, fg_color="transparent")
    status_left.pack(fill="x", padx=12, pady=8)
    ctk.CTkLabel(status_left, text="Status:", font=("Segoe UI", 11, "bold")).pack(side="left")
    ctk.CTkLabel(status_left, textvariable=status_var).pack(side="left", padx=(8, 20))
    ctk.CTkLabel(status_left, text="Last:", font=("Segoe UI", 11, "bold")).pack(side="left")
    ctk.CTkEntry(status_left, textvariable=transcript_var, width=260).pack(side="left", padx=(8, 0))

    # ---- APPS TAB ----
    apps_scroll = ctk.CTkScrollableFrame(tabview.tab("Apps"))
    apps_scroll.pack(fill="both", expand=True)

    ctk.CTkLabel(apps_scroll, text="Registered Apps", font=("Segoe UI", 13, "bold")).pack(
        anchor="w", padx=12, pady=(10, 4)
    )
    ctk.CTkLabel(apps_scroll, text="Say \"open <app name>\" to launch an app.").pack(
        anchor="w", padx=12, pady=(0, 6)
    )

    apps_textbox = ctk.CTkTextbox(apps_scroll, height=120)
    apps_textbox.pack(fill="x", padx=12, pady=4)

    app_name_var = tk.StringVar()
    app_cmd_var = tk.StringVar()

    app_input_card = ctk.CTkFrame(apps_scroll)
    app_input_card.pack(fill="x", padx=12, pady=6)

    app_r1 = ctk.CTkFrame(app_input_card, fg_color="transparent")
    app_r1.pack(fill="x", padx=12, pady=(8, 4))
    ctk.CTkLabel(app_r1, text="App name", width=100).pack(side="left")
    ctk.CTkEntry(app_r1, textvariable=app_name_var, width=240, placeholder_text="e.g. notepad").pack(
        side="left", padx=(0, 10)
    )

    app_r2 = ctk.CTkFrame(app_input_card, fg_color="transparent")
    app_r2.pack(fill="x", padx=12, pady=(4, 8))
    ctk.CTkLabel(app_r2, text="App command", width=100).pack(side="left")
    ctk.CTkEntry(app_r2, textvariable=app_cmd_var, width=240, placeholder_text="e.g. notepad.exe").pack(
        side="left", padx=(0, 10)
    )

    app_btn_row = ctk.CTkFrame(apps_scroll, fg_color="transparent")
    app_btn_row.pack(fill="x", padx=12, pady=4)
    ctk.CTkButton(app_btn_row, text="Add App", command=_add_app, width=110).pack(side="left", padx=4)
    ctk.CTkButton(app_btn_row, text="Remove Last", command=_remove_app, width=110,
                   fg_color=("#cc3333", "#cc3333"), hover_color=("#aa2222", "#aa2222")).pack(
        side="left", padx=4
    )
    ctk.CTkButton(app_btn_row, text="Test App", command=_test_app, width=110,
                   fg_color=("gray60", "gray30"), hover_color=("gray50", "gray40")).pack(
        side="left", padx=4
    )
    ctk.CTkButton(app_btn_row, text="Import Steam", command=_import_steam, width=110,
                   fg_color=("gray60", "gray30"), hover_color=("gray50", "gray40")).pack(
        side="left", padx=4
    )

    # Aliases section
    ctk.CTkLabel(apps_scroll, text="App Aliases", font=("Segoe UI", 13, "bold")).pack(
        anchor="w", padx=12, pady=(16, 4)
    )
    ctk.CTkLabel(apps_scroll, text="Say the alias to launch the target app.").pack(
        anchor="w", padx=12, pady=(0, 6)
    )

    aliases_textbox = ctk.CTkTextbox(apps_scroll, height=80)
    aliases_textbox.pack(fill="x", padx=12, pady=4)

    alias_var = tk.StringVar()
    alias_target_var = tk.StringVar()

    alias_input_card = ctk.CTkFrame(apps_scroll)
    alias_input_card.pack(fill="x", padx=12, pady=6)

    alias_r1 = ctk.CTkFrame(alias_input_card, fg_color="transparent")
    alias_r1.pack(fill="x", padx=12, pady=(8, 4))
    ctk.CTkLabel(alias_r1, text="Alias", width=100).pack(side="left")
    ctk.CTkEntry(alias_r1, textvariable=alias_var, width=240, placeholder_text="e.g. browser").pack(
        side="left", padx=(0, 10)
    )

    alias_r2 = ctk.CTkFrame(alias_input_card, fg_color="transparent")
    alias_r2.pack(fill="x", padx=12, pady=(4, 8))
    ctk.CTkLabel(alias_r2, text="Target app", width=100).pack(side="left")
    ctk.CTkEntry(alias_r2, textvariable=alias_target_var, width=240, placeholder_text="e.g. chrome").pack(
        side="left", padx=(0, 10)
    )

    alias_btn_row = ctk.CTkFrame(apps_scroll, fg_color="transparent")
    alias_btn_row.pack(fill="x", padx=12, pady=4)
    ctk.CTkButton(alias_btn_row, text="Add Alias", command=_add_alias, width=110).pack(side="left", padx=4)
    ctk.CTkButton(alias_btn_row, text="Remove Last", command=_remove_alias, width=110,
                   fg_color=("#cc3333", "#cc3333"), hover_color=("#aa2222", "#aa2222")).pack(
        side="left", padx=4
    )

    # ---- ACTIONS TAB ----
    actions_scroll = ctk.CTkScrollableFrame(tabview.tab("Actions"))
    actions_scroll.pack(fill="both", expand=True)

    ctk.CTkLabel(actions_scroll, text="Voice Actions", font=("Segoe UI", 13, "bold")).pack(
        anchor="w", padx=12, pady=(10, 4)
    )
    ctk.CTkLabel(actions_scroll, text="Map a spoken phrase to a shell command.").pack(
        anchor="w", padx=12, pady=(0, 6)
    )

    actions_textbox = ctk.CTkTextbox(actions_scroll, height=160)
    actions_textbox.pack(fill="x", padx=12, pady=4)

    phrase_var = tk.StringVar()
    command_var = tk.StringVar()

    action_input_card = ctk.CTkFrame(actions_scroll)
    action_input_card.pack(fill="x", padx=12, pady=6)

    act_r1 = ctk.CTkFrame(action_input_card, fg_color="transparent")
    act_r1.pack(fill="x", padx=12, pady=(8, 4))
    ctk.CTkLabel(act_r1, text="Phrase", width=100).pack(side="left")
    ctk.CTkEntry(act_r1, textvariable=phrase_var, width=300, placeholder_text="e.g. lock my computer").pack(
        side="left", padx=(0, 10)
    )

    act_r2 = ctk.CTkFrame(action_input_card, fg_color="transparent")
    act_r2.pack(fill="x", padx=12, pady=(4, 8))
    ctk.CTkLabel(act_r2, text="Command", width=100).pack(side="left")
    ctk.CTkEntry(act_r2, textvariable=command_var, width=300, placeholder_text="e.g. rundll32.exe user32.dll,LockWorkStation").pack(
        side="left", padx=(0, 10)
    )

    action_btn_row = ctk.CTkFrame(actions_scroll, fg_color="transparent")
    action_btn_row.pack(fill="x", padx=12, pady=4)
    ctk.CTkButton(action_btn_row, text="Add Action", command=_add_action, width=130).pack(side="left", padx=4)
    ctk.CTkButton(action_btn_row, text="Remove Last", command=_remove_action, width=130,
                   fg_color=("#cc3333", "#cc3333"), hover_color=("#aa2222", "#aa2222")).pack(
        side="left", padx=4
    )

    # =========================================================================
    #  Init
    # =========================================================================
    _refresh_actions()
    _refresh_apps()
    _refresh_aliases()
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
