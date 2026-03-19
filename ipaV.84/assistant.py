"""All-in-one UI + background listener for the standalone assistant."""

from __future__ import annotations

import threading
import subprocess
import sys
import traceback
import os
import time
import zipfile
import tkinter as tk
from tkinter import messagebox, ttk

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
    mapping = {
        "caps_lock": keyboard.Key.caps_lock,
    }
    return mapping.get(str(key_name).lower())


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

    root = tk.Tk()
    root.title("IPA Assistant")
    root.geometry("560x520")
    root.minsize(560, 420)
    root.resizable(True, True)

    theme_var = tk.BooleanVar(value=(cfg.get("theme", "dark") == "dark"))

    def _apply_theme(is_dark: bool) -> None:
        if is_dark:
            bg = "#1e1f22"
            fg = "#e6e6e6"
            entry_bg = "#2b2d31"
            accent = "#22c55e"
            select_fg = "#0b0b0b"
        else:
            bg = "#f6f6f6"
            fg = "#111111"
            entry_bg = "#ffffff"
            accent = "#0ea5e9"
            select_fg = "#ffffff"

        root.configure(bg=bg)
        root.option_add("*Background", bg)
        root.option_add("*Foreground", fg)
        root.option_add("*EntryBackground", entry_bg)
        root.option_add("*ListboxBackground", entry_bg)
        root.option_add("*ListboxForeground", fg)
        root.option_add("*insertBackground", fg)
        root.option_add("*selectBackground", accent)
        root.option_add("*selectForeground", select_fg)

        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("TFrame", background=bg)
        style.configure("TLabel", background=bg, foreground=fg)
        style.configure("TButton", background=entry_bg, foreground=fg)
        style.configure("TCheckbutton", background=bg, foreground=fg)
        style.configure("TRadiobutton", background=bg, foreground=fg)
        style.configure("TNotebook", background=bg)
        style.configure("TNotebook.Tab", background=entry_bg, foreground=fg)
        style.map(
            "TNotebook.Tab",
            background=[("selected", bg)],
            foreground=[("selected", fg)],
        )

    _apply_theme(theme_var.get())

    notebook = ttk.Notebook(root)
    main_tab = ttk.Frame(notebook)
    apps_tab = ttk.Frame(notebook)
    actions_tab = ttk.Frame(notebook)
    notebook.add(main_tab, text="Main")
    notebook.add(apps_tab, text="Apps")
    notebook.add(actions_tab, text="Actions")
    notebook.pack(fill="both", expand=True)

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

    def _load_logo():
        logo_path = os.path.join(os.path.dirname(__file__), "data", "assets", "ipa_logo.png")
        try:
            img = tk.PhotoImage(file=logo_path)
            # Scale down for UI (keep it compact)
            img = img.subsample(6, 6)
            return img
        except Exception:
            return None

    def _save():
        data = _build_config()
        save_config(data)
        messagebox.showinfo("Saved", "Configuration saved.")

    def _refresh_actions():
        actions_list.delete(0, tk.END)
        for a in actions:
            phrase = a.get("phrase", "")
            command = a.get("command", "")
            actions_list.insert(tk.END, f"{phrase} -> {command}")

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
        sel = actions_list.curselection()
        if not sel:
            return
        idx = sel[0]
        actions.pop(idx)
        _refresh_actions()

    def _refresh_apps():
        apps_list.delete(0, tk.END)
        for a in apps:
            name = a.get("name", "")
            command = a.get("command", "")
            apps_list.insert(tk.END, f"{name} -> {command}")

    def _refresh_aliases():
        aliases_list.delete(0, tk.END)
        for a in aliases:
            aliases_list.insert(tk.END, f"{a.get('alias')} -> {a.get('target')}")

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
        sel = aliases_list.curselection()
        if not sel:
            return
        idx = sel[0]
        aliases.pop(idx)
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
        sel = apps_list.curselection()
        if not sel:
            return
        idx = sel[0]
        apps.pop(idx)
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

    def _run_wizard():
        wizard = tk.Toplevel(root)
        wizard.title("IPA Setup Wizard")
        wizard.geometry("520x420")
        wizard.resizable(False, False)
        wizard.transient(root)
        wizard.grab_set()

        wizard_canvas = tk.Canvas(wizard, borderwidth=0, highlightthickness=0)
        wizard_scroll = tk.Scrollbar(wizard, orient="vertical", command=wizard_canvas.yview)
        wizard_canvas.configure(yscrollcommand=wizard_scroll.set)
        wizard_scroll.pack(side="right", fill="y")
        wizard_canvas.pack(side="left", fill="both", expand=True)

        wizard_content = tk.Frame(wizard_canvas)
        wizard_window = wizard_canvas.create_window((0, 0), window=wizard_content, anchor="nw")

        def _on_wizard_configure(_event):
            wizard_canvas.configure(scrollregion=wizard_canvas.bbox("all"))

        def _on_wizard_canvas_configure(event):
            wizard_canvas.itemconfigure(wizard_window, width=event.width)

        wizard_content.bind("<Configure>", _on_wizard_configure)
        wizard_canvas.bind("<Configure>", _on_wizard_canvas_configure)

        def _on_wizard_mousewheel(event):
            wizard_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        wizard_canvas.bind_all("<MouseWheel>", _on_wizard_mousewheel)

        w_pad = {"padx": 10, "pady": 6, "sticky": "w"}

        status_text = "Found" if _model_present() else "Not found"
        tk.Label(wizard_content, text="Welcome to IPA!").grid(row=0, column=0, columnspan=2, **w_pad)
        tk.Label(wizard_content, text=f"Model status: {status_text}").grid(row=1, column=0, columnspan=2, **w_pad)

        tk.Label(wizard_content, text="Language").grid(row=2, column=0, **w_pad)
        tk.OptionMenu(wizard_content, language, *LANG_CHOICES).grid(row=2, column=1, **w_pad)

        tk.Label(wizard_content, text="Mode").grid(row=3, column=0, **w_pad)
        tk.Radiobutton(wizard_content, text="Timed mic", variable=mode, value="mic").grid(row=3, column=1, **w_pad)
        tk.Radiobutton(wizard_content, text="Hold-to-talk", variable=mode, value="hold").grid(row=4, column=1, **w_pad)
        tk.Radiobutton(wizard_content, text="Hotkey", variable=mode, value="hotkey").grid(row=5, column=1, **w_pad)

        tk.Label(wizard_content, text="Seconds (timed/hotkey)").grid(row=6, column=0, **w_pad)
        tk.Entry(wizard_content, textvariable=seconds, width=10).grid(row=6, column=1, **w_pad)

        tk.Label(wizard_content, text="Hotkey").grid(row=7, column=0, **w_pad)
        tk.OptionMenu(wizard_content, hotkey, *HOTKEY_CHOICES).grid(row=7, column=1, **w_pad)

        tk.Label(wizard_content, text="Hold key").grid(row=8, column=0, **w_pad)
        tk.OptionMenu(wizard_content, holdkey, *HOLD_CHOICES).grid(row=8, column=1, **w_pad)

        tk.Checkbutton(wizard_content, text="Enable Spotify media controls", variable=spotify_media).grid(
            row=9, column=0, columnspan=2, padx=10, pady=2, sticky="w"
        )
        tk.Checkbutton(wizard_content, text="Require word 'spotify' in command", variable=spotify_requires).grid(
            row=10, column=0, columnspan=2, padx=10, pady=2, sticky="w"
        )

        def _download_model(lang: str, url: str):
            dest_root = os.path.join(os.path.dirname(__file__), "data", "model")
            os.makedirs(dest_root, exist_ok=True)
            zip_path = os.path.join(dest_root, f"{lang}.zip")
            extract_dir = os.path.join(dest_root, lang)
            os.makedirs(extract_dir, exist_ok=True)

            def _run():
                try:
                    import urllib.request
                    import zipfile

                    urllib.request.urlretrieve(url, zip_path)
                    with zipfile.ZipFile(zip_path, "r") as zf:
                        zf.extractall(extract_dir)
                    messagebox.showinfo("Done", f"{lang.upper()} model downloaded.")
                except Exception as exc:
                    messagebox.showerror("Download Error", str(exc))

            threading.Thread(target=_run, daemon=True).start()

        tk.Button(wizard_content, text="Download English Model", command=lambda: _download_model(
            "en",
            "https://github.com/copenhagenay-spec/ipaV.84/releases/download/dependency/vosk-model-small-en-us-0.15.zip",
        )).grid(row=11, column=0, padx=10, pady=6, sticky="w")

        tk.Button(wizard_content, text="Download Spanish Model", command=lambda: _download_model(
            "es",
            "https://github.com/copenhagenay-spec/ipaV.84/releases/download/dependency2/vosk-model-small-es-0.42.zip",
        )).grid(row=11, column=1, padx=10, pady=6, sticky="w")

        tk.Button(wizard_content, text="Import Steam Apps", command=_import_steam).grid(
            row=12, column=0, padx=10, pady=6, sticky="w"
        )

        def _install_deps_wizard():
            deps = ["sounddevice", "vosk", "pynput", "pystray", "pillow"]

            def _run():
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", *deps])
                    messagebox.showinfo("Done", "Dependencies installed.")
                except Exception as exc:
                    messagebox.showerror("Install Error", str(exc))

            threading.Thread(target=_run, daemon=True).start()

        tk.Button(wizard_content, text="Install Dependencies", command=_install_deps_wizard).grid(
            row=12, column=1, padx=10, pady=6, sticky="w"
        )

        def _finish():
            data = _build_config(wizard_done=True)
            save_config(data)
            wizard.destroy()
            _start_background()
            messagebox.showinfo("Done", "Setup complete. IPA is ready.")

        tk.Button(wizard_content, text="Finish", command=_finish).grid(
            row=13, column=0, padx=10, pady=10, sticky="w"
        )

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
            pystray.MenuItem("Show", _show_window),
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
        # Minimize to tray instead of exiting.
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
        deps = ["sounddevice", "vosk", "pynput", "pystray", "pillow"]
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

    # Layout
    pad = {"padx": 10, "pady": 6, "sticky": "w"}

    # Main tab
    main_canvas = tk.Canvas(main_tab, borderwidth=0, highlightthickness=0)
    main_scroll = tk.Scrollbar(main_tab, orient="vertical", command=main_canvas.yview)
    main_canvas.configure(yscrollcommand=main_scroll.set)
    main_scroll.pack(side="right", fill="y")
    main_canvas.pack(side="left", fill="both", expand=True)

    main_content = ttk.Frame(main_canvas)
    main_window = main_canvas.create_window((0, 0), window=main_content, anchor="nw")

    def _on_main_configure(_event):
        main_canvas.configure(scrollregion=main_canvas.bbox("all"))

    def _on_main_canvas_configure(event):
        main_canvas.itemconfigure(main_window, width=event.width)

    main_content.bind("<Configure>", _on_main_configure)
    main_canvas.bind("<Configure>", _on_main_canvas_configure)

    def _on_main_mousewheel(event):
        main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    main_canvas.bind_all("<MouseWheel>", _on_main_mousewheel)

    logo_img = _load_logo()
    if logo_img is not None:
        logo_label = tk.Label(main_content, image=logo_img)
        logo_label.image = logo_img  # keep reference
        logo_label.grid(row=0, column=2, rowspan=6, padx=10, pady=6, sticky="e")

    tk.Label(main_content, text="Mode").grid(row=0, column=0, **pad)
    tk.Radiobutton(main_content, text="Timed mic", variable=mode, value="mic").grid(row=0, column=1, **pad)
    tk.Radiobutton(main_content, text="Hold-to-talk", variable=mode, value="hold").grid(row=1, column=1, **pad)
    tk.Radiobutton(main_content, text="Hotkey", variable=mode, value="hotkey").grid(row=2, column=1, **pad)

    tk.Label(main_content, text="Seconds (timed/hotkey)").grid(row=3, column=0, **pad)
    tk.Entry(main_content, textvariable=seconds, width=10).grid(row=3, column=1, **pad)

    tk.Label(main_content, text="Language").grid(row=4, column=0, **pad)
    tk.OptionMenu(main_content, language, *LANG_CHOICES).grid(row=4, column=1, **pad)

    tk.Label(main_content, text="Hotkey").grid(row=5, column=0, **pad)
    tk.OptionMenu(main_content, hotkey, *HOTKEY_CHOICES).grid(row=5, column=1, **pad)

    tk.Label(main_content, text="Hold key").grid(row=6, column=0, **pad)
    tk.OptionMenu(main_content, holdkey, *HOLD_CHOICES).grid(row=6, column=1, **pad)

    tk.Label(main_content, text="Search Engine URL").grid(row=7, column=0, **pad)
    tk.Entry(main_content, textvariable=search_engine, width=45).grid(row=7, column=1, **pad)

    tk.Checkbutton(main_content, text="Confirm before running actions", variable=confirm_actions).grid(
        row=8, column=0, columnspan=2, padx=10, pady=6, sticky="w"
    )
    tk.Checkbutton(main_content, text="Dark mode (restart to apply)", variable=theme_var).grid(
        row=9, column=0, columnspan=2, padx=10, pady=2, sticky="w"
    )
    tk.Checkbutton(main_content, text="Enable Spotify media controls", variable=spotify_media).grid(
        row=10, column=0, columnspan=2, padx=10, pady=2, sticky="w"
    )
    tk.Checkbutton(main_content, text="Require word 'spotify' in command", variable=spotify_requires).grid(
        row=11, column=0, columnspan=2, padx=10, pady=2, sticky="w"
    )

    tk.Label(main_content, text="Spotify keywords (comma-separated)").grid(row=12, column=0, **pad)
    tk.Entry(main_content, textvariable=spotify_keywords, width=45).grid(row=12, column=1, **pad)

    tk.Button(main_content, text="Save Config", command=_save).grid(row=13, column=0, padx=10, pady=6, sticky="w")
    tk.Button(main_content, text="Run Now", command=_run_now).grid(row=13, column=1, padx=10, pady=6, sticky="w")
    tk.Button(main_content, text="Install Deps", command=_install_deps).grid(row=14, column=0, padx=10, pady=6, sticky="w")
    tk.Button(main_content, text="Create Bug Report", command=_create_bug_report).grid(
        row=14, column=1, padx=10, pady=6, sticky="w"
    )
    tk.Button(main_content, text="Start Background", command=_start_background).grid(
        row=15, column=0, padx=10, pady=6, sticky="w"
    )
    tk.Button(main_content, text="Stop Background", command=_stop_background).grid(
        row=15, column=1, padx=10, pady=6, sticky="w"
    )

    tk.Label(main_content, text="Status").grid(row=16, column=0, **pad)
    tk.Label(main_content, textvariable=status_var).grid(row=16, column=1, **pad)

    tk.Label(main_content, text="Last Transcript").grid(row=17, column=0, **pad)
    tk.Entry(main_content, textvariable=transcript_var, width=45).grid(row=17, column=1, **pad)

    tk.Label(
        main_content,
        text="Tip: Start Background to enable hotkey/hold listening.",
        wraplength=380,
        justify="left",
    ).grid(row=18, column=0, columnspan=2, padx=10, pady=8, sticky="w")

    app_name_var = tk.StringVar()
    app_cmd_var = tk.StringVar()

    # Apps tab
    tk.Label(apps_tab, text="Apps (say: open <app>)").grid(row=0, column=0, **pad)
    apps_list = tk.Listbox(apps_tab, width=60, height=6)
    apps_list.grid(row=1, column=0, columnspan=3, padx=10, pady=6, sticky="w")

    tk.Label(apps_tab, text="App name").grid(row=2, column=0, **pad)
    tk.Entry(apps_tab, textvariable=app_name_var, width=30).grid(row=2, column=1, **pad)
    tk.Button(apps_tab, text="Add App", command=_add_app).grid(row=2, column=2, padx=10, pady=6, sticky="w")

    tk.Label(apps_tab, text="App command").grid(row=3, column=0, **pad)
    tk.Entry(apps_tab, textvariable=app_cmd_var, width=30).grid(row=3, column=1, **pad)
    tk.Button(apps_tab, text="Remove App", command=_remove_app).grid(row=3, column=2, padx=10, pady=6, sticky="w")

    tk.Button(apps_tab, text="Test App", command=_test_app).grid(row=4, column=0, padx=10, pady=6, sticky="w")
    tk.Button(apps_tab, text="Import Steam", command=_import_steam).grid(row=4, column=1, padx=10, pady=6, sticky="w")

    tk.Label(apps_tab, text="App Aliases (say alias to open target)").grid(row=5, column=0, **pad)
    aliases_list = tk.Listbox(apps_tab, width=60, height=4)
    aliases_list.grid(row=6, column=0, columnspan=3, padx=10, pady=6, sticky="w")

    alias_var = tk.StringVar()
    alias_target_var = tk.StringVar()

    tk.Label(apps_tab, text="Alias").grid(row=7, column=0, **pad)
    tk.Entry(apps_tab, textvariable=alias_var, width=30).grid(row=7, column=1, **pad)
    tk.Button(apps_tab, text="Add Alias", command=_add_alias).grid(row=7, column=2, padx=10, pady=6, sticky="w")

    tk.Label(apps_tab, text="Target app").grid(row=8, column=0, **pad)
    tk.Entry(apps_tab, textvariable=alias_target_var, width=30).grid(row=8, column=1, **pad)
    tk.Button(apps_tab, text="Remove Alias", command=_remove_alias).grid(row=8, column=2, padx=10, pady=6, sticky="w")

    # Actions tab
    tk.Label(actions_tab, text="Voice Actions").grid(row=0, column=0, **pad)
    actions_list = tk.Listbox(actions_tab, width=60, height=8)
    actions_list.grid(row=1, column=0, columnspan=2, padx=10, pady=6, sticky="w")

    phrase_var = tk.StringVar()
    command_var = tk.StringVar()

    tk.Label(actions_tab, text="Phrase").grid(row=2, column=0, **pad)
    tk.Entry(actions_tab, textvariable=phrase_var, width=30).grid(row=2, column=1, **pad)

    tk.Label(actions_tab, text="Command").grid(row=3, column=0, **pad)
    tk.Entry(actions_tab, textvariable=command_var, width=30).grid(row=3, column=1, **pad)

    tk.Button(actions_tab, text="Add Action", command=_add_action).grid(row=4, column=0, padx=10, pady=6, sticky="w")
    tk.Button(actions_tab, text="Remove Selected", command=_remove_action).grid(
        row=4, column=1, padx=10, pady=6, sticky="w"
    )

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
