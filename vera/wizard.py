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

    _WZ_ACCENT  = "#2563eb"
    _WZ_SURFACE = "#2b2b2b"
    _WZ_BG      = "#1a1a1a"
    _WZ_TEXT    = "#ffffff"
    _WZ_MUTED   = "#888888"

    _CARD_STYLE = f"""
        QFrame {{
            background-color: {_WZ_SURFACE};
            border-radius: 8px;
        }}
        QLabel {{ color: {_WZ_TEXT}; background: transparent; }}
        QCheckBox {{ color: {_WZ_TEXT}; background: transparent; }}
        QRadioButton {{ color: {_WZ_TEXT}; background: transparent; }}
        QLineEdit {{
            background-color: #333333; color: {_WZ_TEXT};
            border: 1px solid #555555; border-radius: 4px;
            padding: 4px 8px;
        }}
        QPushButton {{
            background-color: #404040; color: {_WZ_TEXT};
            border-radius: 6px; padding: 5px 12px; font-size: 12px;
        }}
        QPushButton:hover {{ background-color: #505050; }}
        QComboBox {{
            background-color: #333333; color: {_WZ_TEXT};
            border: 1px solid #555555; border-radius: 4px; padding: 4px 8px;
        }}
        QComboBox::drop-down {{ border: none; }}
        QComboBox QAbstractItemView {{
            background-color: #2b2b2b; color: {_WZ_TEXT};
            selection-background-color: {_WZ_ACCENT};
        }}
    """

    def _card(*widgets, title=None):
        frame = QFrame()
        frame.setStyleSheet(_CARD_STYLE)
        cvl = QVBoxLayout(frame)
        cvl.setContentsMargins(14, 10, 14, 10)
        cvl.setSpacing(8)
        if title:
            t = QLabel(title)
            t.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {_WZ_TEXT}; background: transparent; margin-bottom: 2px;")
            cvl.addWidget(t)
        for w in widgets:
            cvl.addWidget(w)
        return frame

    def _row(*widgets):
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(8)
        for w in widgets:
            rl.addWidget(w)
        rl.addStretch()
        return row

    def _lbl(text, muted=False, width=None):
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        if muted:
            lbl.setStyleSheet(f"color: {_WZ_MUTED}; font-size: 11px; background: transparent;")
        if width:
            lbl.setFixedWidth(width)
        return lbl

    dialog = QDialog(parent)
    dialog.setWindowTitle("VERA Setup Wizard")
    dialog.resize(500, 580)
    dialog.setModal(True)
    dialog.setStyleSheet(f"QDialog {{ background-color: {_WZ_BG}; }} QLabel {{ color: {_WZ_TEXT}; }}")

    try:
        icon_path = os.path.join(os.path.dirname(__file__), "data", "assets", "ipa.ico")
        if os.path.exists(icon_path):
            dialog.setWindowIcon(QIcon(icon_path))
    except Exception:
        pass

    outer_layout = QVBoxLayout(dialog)
    outer_layout.setContentsMargins(0, 0, 0, 0)
    outer_layout.setSpacing(0)

    # --- Accent header bar ---
    header_bar = QWidget()
    header_bar.setFixedHeight(56)
    header_bar.setStyleSheet(f"background-color: {_WZ_ACCENT};")
    hbl = QVBoxLayout(header_bar)
    hbl.setContentsMargins(16, 10, 16, 10)
    header_title = QLabel("Welcome to VERA!")
    header_title.setStyleSheet("color: #ffffff; font-size: 18px; font-weight: bold; background: transparent;")
    hbl.addWidget(header_title)
    outer_layout.addWidget(header_bar)

    subtitle_bar = QWidget()
    subtitle_bar.setStyleSheet(f"background-color: {_WZ_BG};")
    sbl = QVBoxLayout(subtitle_bar)
    sbl.setContentsMargins(16, 6, 16, 2)
    sbl.addWidget(_lbl("Speech model: auto-downloads on first use (~150MB)", muted=True))
    outer_layout.addWidget(subtitle_bar)

    # --- Scroll area ---
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setFrameShape(QFrame.NoFrame)
    scroll_area.setStyleSheet(f"background-color: {_WZ_BG};")
    outer_layout.addWidget(scroll_area)

    content = QWidget()
    content.setStyleSheet(f"background-color: {_WZ_BG};")
    scroll_area.setWidget(content)
    layout = QVBoxLayout(content)
    layout.setContentsMargins(14, 10, 14, 14)
    layout.setSpacing(10)

    # --- Language card ---
    lang_combo = QComboBox()
    lang_combo.addItems(LANG_CHOICES)
    current_lang = state["language"].get()
    if current_lang in LANG_CHOICES:
        lang_combo.setCurrentText(current_lang)
    layout.addWidget(_card(_row(_lbl("Language", width=100), lang_combo), title="Language"))

    # --- Input Mode card ---
    mode_group = QButtonGroup(dialog)
    radio_mic   = QRadioButton("Wake Word")
    radio_hold  = QRadioButton("Hold-to-talk")
    radio_hotkey = QRadioButton("Push to Toggle")
    for rb in (radio_mic, radio_hold, radio_hotkey):
        mode_group.addButton(rb)

    current_mode = state["mode"].get()
    if current_mode == "wake":
        radio_mic.setChecked(True)
    elif current_mode == "toggle":
        radio_hotkey.setChecked(True)
    else:
        radio_hold.setChecked(True)

    sec_entry  = QLineEdit(state["seconds"].get());  sec_entry.setFixedWidth(80)
    hk_entry   = QLineEdit(state["hotkey"].get());   hk_entry.setFixedWidth(160)
    hold_entry = QLineEdit(state["holdkey"].get());  hold_entry.setFixedWidth(160)

    hk_btn   = QPushButton("Record")
    hold_btn = QPushButton("Record")

    def _do_record_hotkey():
        _record_hotkey(state["hotkey"])
        hk_entry.setText(state["hotkey"].get())

    def _do_record_hold():
        _record_hold_key(state["holdkey"])
        hold_entry.setText(state["holdkey"].get())

    hk_btn.clicked.connect(_do_record_hotkey)
    hold_btn.clicked.connect(_do_record_hold)

    layout.addWidget(_card(
        _row(radio_mic, radio_hold, radio_hotkey),
        _row(_lbl("Seconds (wake word/toggle)", width=160), sec_entry),
        _row(_lbl("Toggle key", width=160), hk_entry, hk_btn),
        _row(_lbl("Hold key", width=160), hold_entry, hold_btn),
        title="Input Mode",
    ))

    # --- Spotify card ---
    spotify_chk = QCheckBox("Enable Spotify media controls")
    spotify_chk.setChecked(bool(state["spotify_media"].get()))
    spotify_req_chk = QCheckBox("Require word 'spotify' in command")
    spotify_req_chk.setChecked(bool(state["spotify_requires"].get()))
    layout.addWidget(_card(spotify_chk, spotify_req_chk, title="Spotify"))

    # --- Model info ---
    info_lbl = _lbl(
        "VERA uses Whisper for speech recognition. The model (~150MB) will download automatically "
        "the first time you speak — no manual setup needed.",
        muted=True,
    )
    layout.addWidget(info_lbl)

    # --- Utilities card ---
    import_btn  = QPushButton("Import Steam Apps")
    install_btn = QPushButton("Install Dependencies")
    import_btn.clicked.connect(lambda: _import_steam())
    install_btn.clicked.connect(lambda: _install_deps_wizard(dialog))
    layout.addWidget(_card(_row(import_btn, install_btn), title="Utilities"))

    # --- Download progress (hidden until download starts) ---
    dl_frame = QWidget()
    dl_frame.setStyleSheet(f"background: transparent;")
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

    # --- Options card ---
    shortcut_chk = QCheckBox("Create desktop shortcut")
    shortcut_chk.setChecked(True)
    layout.addWidget(_card(shortcut_chk, title="Options"))

    layout.addStretch()

    # --- Finish button ---
    finish_btn = QPushButton("Finish Setup")
    finish_btn.setFixedHeight(44)
    finish_btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {_WZ_ACCENT}; color: #ffffff;
            border-radius: 8px; font-size: 15px; font-weight: bold;
        }}
        QPushButton:hover {{ background-color: #1d4ed8; }}
        QPushButton:pressed {{ background-color: #1e40af; }}
    """)
    layout.addWidget(finish_btn)

    def _finish():
        state["seconds"].set(sec_entry.text())
        state["hotkey"].set(hk_entry.text())
        state["holdkey"].set(hold_entry.text())
        state["language"].set(lang_combo.currentText())
        if radio_mic.isChecked():
            state["mode"].set("wake")
        elif radio_hotkey.isChecked():
            state["mode"].set("toggle")
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
