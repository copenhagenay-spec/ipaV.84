"""Setup wizard UI for VERA (PySide6)."""

from __future__ import annotations

import threading
import subprocess
import sys
import os
import zipfile
import urllib.request

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QScrollArea, QWidget,
    QLabel, QLineEdit, QPushButton, QCheckBox, QRadioButton,
    QButtonGroup, QComboBox, QProgressBar, QFrame, QMessageBox,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon


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
        shortcut_path = os.path.join(desktop, "VERA.lnk")
        start_path = os.path.join(start_menu, "VERA.lnk")

        for stale in [
            os.path.join(start_menu, "VERA.lnk"),
            os.path.join(start_menu, "VERA (2).lnk"),
            os.path.join(desktop, "VERA (2).lnk"),
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
    parent,
    state: dict,
    callbacks: dict,
    constants: dict,
    model_urls: dict,
):
    HOTKEY_CHOICES = constants["HOTKEY_CHOICES"]
    LANG_CHOICES = constants["LANG_CHOICES"]

    _record_hotkey = callbacks["record_hotkey"]
    _record_hold_key = callbacks["record_hold_key"]
    _import_steam = callbacks["import_steam"]
    _build_config = callbacks["build_config"]
    _save_config = callbacks["save_config"]
    _start_background = callbacks["start_background"]

    dialog = QDialog(parent)
    dialog.setWindowTitle("VERA Setup Wizard")
    dialog.resize(560, 520)
    dialog.setModal(True)

    try:
        icon_path = os.path.join(os.path.dirname(__file__), "data", "assets", "ipa.ico")
        if os.path.exists(icon_path):
            dialog.setWindowIcon(QIcon(icon_path))
    except Exception:
        pass

    # --- Outer layout ---
    outer_layout = QVBoxLayout(dialog)
    outer_layout.setContentsMargins(0, 0, 0, 0)

    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setFrameShape(QFrame.NoFrame)
    outer_layout.addWidget(scroll_area)

    content = QWidget()
    scroll_area.setWidget(content)
    layout = QVBoxLayout(content)
    layout.setContentsMargins(14, 14, 14, 14)
    layout.setSpacing(8)

    def _add_label(text, bold=False, color=None):
        lbl = QLabel(text)
        if bold:
            lbl.setStyleSheet("font-weight: bold; font-size: 14px;")
        if color:
            lbl.setStyleSheet(lbl.styleSheet() + f" color: {color};")
        lbl.setWordWrap(True)
        layout.addWidget(lbl)
        return lbl

    def _add_row(*widgets):
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        for w in widgets:
            row_layout.addWidget(w)
        row_layout.addStretch()
        layout.addWidget(row)
        return row

    # --- Header ---
    _add_label("Welcome to VERA!", bold=True)
    _add_label("Speech model: auto-downloads on first use (~150MB)", color="#888888")

    # --- Language ---
    lang_label = QLabel("Language")
    lang_combo = QComboBox()
    lang_combo.addItems(LANG_CHOICES)
    current_lang = state["language"].get()
    if current_lang in LANG_CHOICES:
        lang_combo.setCurrentText(current_lang)
    _add_row(lang_label, lang_combo)

    # --- Mode ---
    _add_label("Mode", bold=True)
    mode_group = QButtonGroup(dialog)
    mode_row = QWidget()
    mode_row_layout = QHBoxLayout(mode_row)
    mode_row_layout.setContentsMargins(0, 0, 0, 0)
    radio_mic = QRadioButton("Timed mic")
    radio_hold = QRadioButton("Hold-to-talk")
    radio_hotkey = QRadioButton("Hotkey")
    mode_group.addButton(radio_mic)
    mode_group.addButton(radio_hold)
    mode_group.addButton(radio_hotkey)
    mode_row_layout.addWidget(radio_mic)
    mode_row_layout.addWidget(radio_hold)
    mode_row_layout.addWidget(radio_hotkey)
    mode_row_layout.addStretch()
    layout.addWidget(mode_row)

    current_mode = state["mode"].get()
    if current_mode == "mic":
        radio_mic.setChecked(True)
    elif current_mode == "hotkey":
        radio_hotkey.setChecked(True)
    else:
        radio_hold.setChecked(True)

    # --- Seconds ---
    sec_label = QLabel("Seconds (timed/hotkey)")
    sec_label.setFixedWidth(160)
    sec_entry = QLineEdit(state["seconds"].get())
    sec_entry.setFixedWidth(80)
    _add_row(sec_label, sec_entry)

    # --- Hotkey ---
    hk_label = QLabel("Hotkey")
    hk_label.setFixedWidth(160)
    hk_entry = QLineEdit(state["hotkey"].get())
    hk_entry.setFixedWidth(160)
    hk_btn = QPushButton("Record")

    def _do_record_hotkey():
        _record_hotkey(state["hotkey"])
        hk_entry.setText(state["hotkey"].get())

    hk_btn.clicked.connect(_do_record_hotkey)
    _add_row(hk_label, hk_entry, hk_btn)

    # --- Hold key ---
    hold_label = QLabel("Hold key")
    hold_label.setFixedWidth(160)
    hold_entry = QLineEdit(state["holdkey"].get())
    hold_entry.setFixedWidth(160)
    hold_btn = QPushButton("Record")

    def _do_record_hold():
        _record_hold_key(state["holdkey"])
        hold_entry.setText(state["holdkey"].get())

    hold_btn.clicked.connect(_do_record_hold)
    _add_row(hold_label, hold_entry, hold_btn)

    # --- Spotify ---
    spotify_chk = QCheckBox("Enable Spotify media controls")
    spotify_chk.setChecked(bool(state["spotify_media"].get()))
    layout.addWidget(spotify_chk)

    spotify_req_chk = QCheckBox("Require word 'spotify' in command")
    spotify_req_chk.setChecked(bool(state["spotify_requires"].get()))
    layout.addWidget(spotify_req_chk)

    # --- Model info ---
    _add_label(
        "VERA uses Whisper for speech recognition. The model (~150MB) will download automatically\n"
        "the first time you speak — no manual setup needed.",
        color="#888888",
    )

    # --- Buttons row ---
    btn_row = QWidget()
    btn_layout = QHBoxLayout(btn_row)
    btn_layout.setContentsMargins(0, 0, 0, 0)
    import_btn = QPushButton("Import Steam Apps")
    install_btn = QPushButton("Install Dependencies")
    import_btn.clicked.connect(lambda: _import_steam())
    install_btn.clicked.connect(lambda: _install_deps_wizard(dialog))
    btn_layout.addWidget(import_btn)
    btn_layout.addWidget(install_btn)
    btn_layout.addStretch()
    layout.addWidget(btn_row)

    # --- Download progress (hidden until download starts) ---
    dl_frame = QWidget()
    dl_layout = QVBoxLayout(dl_frame)
    dl_layout.setContentsMargins(0, 4, 0, 0)
    dl_status_label = QLabel("")
    dl_progress = QProgressBar()
    dl_progress.setRange(0, 1000)
    dl_progress.setValue(0)
    dl_layout.addWidget(dl_status_label)
    dl_layout.addWidget(dl_progress)
    dl_frame.setVisible(False)
    layout.addWidget(dl_frame)

    # --- Shortcut checkbox ---
    shortcut_chk = QCheckBox("Create desktop shortcut")
    shortcut_chk.setChecked(True)
    layout.addWidget(shortcut_chk)

    # --- Finish button ---
    finish_btn = QPushButton("Finish Setup")
    finish_btn.setFixedHeight(40)
    finish_btn.setStyleSheet("font-size: 14px; font-weight: bold;")
    layout.addWidget(finish_btn)

    def _finish():
        # Write entries back into state vars before building config
        state["seconds"].set(sec_entry.text())
        state["hotkey"].set(hk_entry.text())
        state["holdkey"].set(hold_entry.text())
        state["language"].set(lang_combo.currentText())
        if radio_mic.isChecked():
            state["mode"].set("mic")
        elif radio_hotkey.isChecked():
            state["mode"].set("hotkey")
        else:
            state["mode"].set("hold")
        state["spotify_media"].set(spotify_chk.isChecked())
        state["spotify_requires"].set(spotify_req_chk.isChecked())

        data = _build_config(wizard_done=True)
        _save_config(data)
        if shortcut_chk.isChecked():
            _create_shortcut()
        dialog.accept()
        _start_background()
        QMessageBox.information(None, "Done", "Setup complete. VERA is ready.")

    finish_btn.clicked.connect(_finish)

    dialog.exec()


def _install_deps_wizard(parent):
    deps = ["sounddevice", "faster-whisper", "pynput", "pystray", "pillow", "PySide6"]

    def _run():
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *deps])
            QTimer.singleShot(0, lambda: QMessageBox.information(parent, "Done", "Dependencies installed."))
        except Exception as exc:
            QTimer.singleShot(0, lambda: QMessageBox.critical(parent, "Install Error", str(exc)))

    threading.Thread(target=_run, daemon=True).start()
