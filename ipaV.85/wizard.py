"""Setup wizard UI for IPA."""

from __future__ import annotations

import threading
import subprocess
import sys
import os
import zipfile
import urllib.request
from tkinter import messagebox

import customtkinter as ctk


def _create_shortcut():
    try:
        base = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base, "data", "assets", "ipa.ico")
        script_path = os.path.join(base, "assistant.py")
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        start_menu = os.path.join(
            os.environ.get("APPDATA", ""),
            "Microsoft", "Windows", "Start Menu", "Programs",
        )
        shortcut_path = os.path.join(desktop, "IPA.lnk")
        start_path = os.path.join(start_menu, "IPA.lnk")

        # Remove stale entries to prevent "(2)" duplicates
        for stale in [
            os.path.join(start_menu, "IPA.lnk"),
            os.path.join(start_menu, "IPA (2).lnk"),
            os.path.join(desktop, "IPA (2).lnk"),
        ]:
            try:
                os.remove(stale)
            except FileNotFoundError:
                pass

        pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
        if not os.path.exists(pythonw):
            pythonw = sys.executable

        ps = (
            f'$lnk="{shortcut_path}";'
            f'$s=(New-Object -COM WScript.Shell).CreateShortcut($lnk);'
            f'$s.TargetPath="{pythonw}";'
            f'$s.Arguments=\'"{script_path}"\';'
            f'$s.IconLocation="{icon_path}";'
            f'$s.WorkingDirectory="{base}";'
            f'$s.Save();'
            f'Copy-Item $lnk "{start_path}" -Force'
        )
        subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps], check=True)
    except Exception:
        pass


def run_wizard(
    root,
    state: dict,
    callbacks: dict,
    constants: dict,
    model_urls: dict,
):
    wizard = ctk.CTkToplevel(root)
    wizard.title("IPA Setup Wizard")
    wizard.geometry("560x520")
    wizard.resizable(True, True)
    wizard.transient(root)
    wizard.grab_set()
    try:
        icon_path = os.path.join(os.path.dirname(__file__), "data", "assets", "ipa.ico")
        if os.path.exists(icon_path):
            wizard.iconbitmap(icon_path)
            wizard.after(200, lambda: wizard.iconbitmap(icon_path))
    except Exception:
        pass

    # Scrollable content
    scroll = ctk.CTkScrollableFrame(wizard)
    scroll.pack(fill="both", expand=True, padx=10, pady=10)

    HOTKEY_CHOICES = constants["HOTKEY_CHOICES"]
    LANG_CHOICES = constants["LANG_CHOICES"]

    import tkinter as tk
    create_shortcut_var = tk.IntVar(value=1)

    mode = state["mode"]
    language = state["language"]
    seconds = state["seconds"]
    hotkey = state["hotkey"]
    holdkey = state["holdkey"]
    spotify_media = state["spotify_media"]
    spotify_requires = state["spotify_requires"]

    _model_present = callbacks["model_present"]
    _record_hotkey = callbacks["record_hotkey"]
    _record_hold_key = callbacks["record_hold_key"]
    _import_steam = callbacks["import_steam"]
    _build_config = callbacks["build_config"]
    _save_config = callbacks["save_config"]
    _start_background = callbacks["start_background"]

    def _download_model(lang: str, url: str):
        dest_root = os.path.join(os.path.dirname(__file__), "data", "model")
        os.makedirs(dest_root, exist_ok=True)
        zip_path = os.path.join(dest_root, f"{lang}.zip")
        extract_dir = os.path.join(dest_root, lang)
        os.makedirs(extract_dir, exist_ok=True)

        def _run():
            try:
                urllib.request.urlretrieve(url, zip_path)
                import shutil
                for item in os.listdir(extract_dir):
                    item_path = os.path.join(extract_dir, item)
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                with zipfile.ZipFile(zip_path, "r") as zf:
                    zf.extractall(extract_dir)
                messagebox.showinfo("Done", f"{lang.upper()} model downloaded.")
            except Exception as exc:
                messagebox.showerror("Download Error", str(exc))

        threading.Thread(target=_run, daemon=True).start()

    def _install_deps_wizard():
        deps = ["sounddevice", "vosk", "pynput", "pystray", "pillow", "customtkinter"]

        def _run():
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", *deps])
                messagebox.showinfo("Done", "Dependencies installed.")
            except Exception as exc:
                messagebox.showerror("Install Error", str(exc))

        threading.Thread(target=_run, daemon=True).start()

    def _finish():
        data = _build_config(wizard_done=True)
        _save_config(data)
        if create_shortcut_var.get():
            _create_shortcut()
        wizard.destroy()
        _start_background()
        messagebox.showinfo("Done", "Setup complete. IPA is ready.")

    # Header
    ctk.CTkLabel(scroll, text="Welcome to IPA!", font=("Segoe UI", 16, "bold")).pack(
        anchor="w", padx=10, pady=(6, 4)
    )
    status_text = "Found" if _model_present() else "Not found"
    ctk.CTkLabel(scroll, text=f"Model status: {status_text}").pack(anchor="w", padx=10, pady=(0, 8))

    # Language
    lang_row = ctk.CTkFrame(scroll, fg_color="transparent")
    lang_row.pack(fill="x", padx=10, pady=4)
    ctk.CTkLabel(lang_row, text="Language", width=120).pack(side="left")
    ctk.CTkOptionMenu(lang_row, variable=language, values=LANG_CHOICES, width=200).pack(side="left")

    # Mode
    ctk.CTkLabel(scroll, text="Mode", font=("Segoe UI", 13, "bold")).pack(
        anchor="w", padx=10, pady=(10, 4)
    )
    mode_row = ctk.CTkFrame(scroll, fg_color="transparent")
    mode_row.pack(fill="x", padx=10, pady=4)
    ctk.CTkRadioButton(mode_row, text="Timed mic", variable=mode, value="mic").pack(side="left", padx=(0, 12))
    ctk.CTkRadioButton(mode_row, text="Hold-to-talk", variable=mode, value="hold").pack(side="left", padx=(0, 12))
    ctk.CTkRadioButton(mode_row, text="Hotkey", variable=mode, value="hotkey").pack(side="left")

    # Timing + keys
    row1 = ctk.CTkFrame(scroll, fg_color="transparent")
    row1.pack(fill="x", padx=10, pady=4)
    ctk.CTkLabel(row1, text="Seconds (timed/hotkey)", width=160).pack(side="left")
    ctk.CTkEntry(row1, textvariable=seconds, width=80).pack(side="left", padx=(0, 16))

    row2 = ctk.CTkFrame(scroll, fg_color="transparent")
    row2.pack(fill="x", padx=10, pady=4)
    ctk.CTkLabel(row2, text="Hotkey", width=160).pack(side="left")
    ctk.CTkEntry(row2, textvariable=hotkey, width=160).pack(side="left", padx=(0, 10))
    ctk.CTkButton(row2, text="Record", command=lambda: _record_hotkey(hotkey), width=90).pack(side="left")

    row3 = ctk.CTkFrame(scroll, fg_color="transparent")
    row3.pack(fill="x", padx=10, pady=4)
    ctk.CTkLabel(row3, text="Hold key", width=160).pack(side="left")
    ctk.CTkEntry(row3, textvariable=holdkey, width=160).pack(side="left", padx=(0, 10))
    ctk.CTkButton(row3, text="Record", command=lambda: _record_hold_key(holdkey), width=90).pack(side="left")

    # Spotify
    ctk.CTkCheckBox(scroll, text="Enable Spotify media controls", variable=spotify_media).pack(
        anchor="w", padx=16, pady=(10, 2)
    )
    ctk.CTkCheckBox(scroll, text="Require word 'spotify' in command", variable=spotify_requires).pack(
        anchor="w", padx=16, pady=2
    )

    # Model download buttons
    btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
    btn_frame.pack(fill="x", padx=10, pady=(10, 4))
    ctk.CTkButton(
        btn_frame,
        text="English Model - Small (faster)",
        command=lambda: _download_model("en", model_urls["en"]),
    ).pack(side="left", padx=6, pady=8)
    ctk.CTkButton(
        btn_frame,
        text="English Model - Standard (better accuracy)",
        command=lambda: _download_model("en", model_urls["en_standard"]),
    ).pack(side="left", padx=6, pady=8)
    ctk.CTkButton(
        btn_frame,
        text="Spanish Model",
        command=lambda: _download_model("es", model_urls["es"]),
    ).pack(side="left", padx=6, pady=8)

    btn_frame2 = ctk.CTkFrame(scroll, fg_color="transparent")
    btn_frame2.pack(fill="x", padx=10, pady=(0, 4))
    ctk.CTkButton(btn_frame2, text="Import Steam Apps", command=_import_steam).pack(
        side="left", padx=6, pady=8
    )
    ctk.CTkButton(btn_frame2, text="Install Dependencies", command=_install_deps_wizard).pack(
        side="left", padx=6, pady=8
    )

    ctk.CTkCheckBox(scroll, text="Create desktop shortcut", variable=create_shortcut_var).pack(
        anchor="w", padx=16, pady=(10, 2)
    )

    ctk.CTkButton(
        scroll,
        text="Finish Setup",
        command=_finish,
        height=40,
        font=("Segoe UI", 14, "bold"),
    ).pack(padx=10, pady=16, fill="x")
