"""Main UI layout for VERA (PySide6)."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QCheckBox, QRadioButton, QButtonGroup,
    QSlider, QTextEdit, QListWidget, QAbstractItemView,
    QTabWidget, QScrollArea, QFrame, QProgressBar, QSizePolicy,
    QSpacerItem,
)
from PySide6.QtCore import Qt, Signal, QObject, QSize
from PySide6.QtGui import QFont, QPixmap, QColor, QIcon


# ---------------------------------------------------------------------------
# Style helpers
# ---------------------------------------------------------------------------

# Free tier palette
_ACCENT        = "#2563eb"
_ACCENT_HOVER  = "#1d4ed8"
_ACCENT_PRESS  = "#1e40af"
_DANGER        = "#c0392b"
_SURFACE       = "#2b2b2b"
_BG            = "#1e1e1e"
_TEXT          = "#ffffff"
_MUTED         = "#888888"
_WARN_FG       = "#ffaa00"
_TITLE_COLOR   = "#a8d5b5"

# Premium gold palette
_PREM_ACCENT       = "#c9a84c"
_PREM_ACCENT_HOVER = "#b8962e"
_PREM_ACCENT_PRESS = "#a07c20"
_PREM_SURFACE      = "#1e1a14"
_PREM_BG           = "#141414"
_PREM_TITLE_COLOR  = "#c9a84c"


def _apply_premium_theme() -> None:
    """Swap color constants and recompute style strings for premium tier."""
    global _ACCENT, _ACCENT_HOVER, _ACCENT_PRESS, _SURFACE, _BG, _TITLE_COLOR
    _ACCENT        = _PREM_ACCENT
    _ACCENT_HOVER  = _PREM_ACCENT_HOVER
    _ACCENT_PRESS  = _PREM_ACCENT_PRESS
    _SURFACE       = _PREM_SURFACE
    _BG            = _PREM_BG
    _TITLE_COLOR   = _PREM_TITLE_COLOR
    _rebuild_styles()

# ---------------------------------------------------------------------------
# Text scale registry
# ---------------------------------------------------------------------------

FONT_SCALE_CHOICES = ["Normal", "Large", "X-Large"]
_FONT_SCALE_MAP    = {"Normal": 1.0, "Large": 1.25, "X-Large": 1.5}

# Each entry: (QLabel, base_px, bold)
_scalable_labels: list = []


def _make_scalable_font(px: int, bold: bool = False) -> QFont:
    f = QFont("Segoe UI")
    f.setPixelSize(px)
    f.setBold(bold)
    return f


def apply_label_scale(scale_name: str) -> None:
    """Immediately rescale all registered labels and application body font."""
    factor = _FONT_SCALE_MAP.get(scale_name, 1.0)
    for label, base_px, bold in _scalable_labels:
        label.setFont(_make_scalable_font(round(base_px * factor), bold))
    app = QApplication.instance()
    if app:
        body = QFont("Segoe UI")
        body.setPixelSize(round(12 * factor))
        app.setFont(body)

_BTN_PRIMARY   = ""
_BTN_SECONDARY = ""
_BTN_DANGER    = ""
_BTN_MUTED     = ""
_LIST_STYLE    = ""
_ENTRY_STYLE   = ""
_COMBO_STYLE   = ""
_CHECK_STYLE   = ""
_RADIO_STYLE   = ""


def _rebuild_styles() -> None:
    """Recompute all QSS style strings from the current color constants."""
    global _BTN_PRIMARY, _BTN_SECONDARY, _BTN_DANGER, _BTN_MUTED
    global _LIST_STYLE, _ENTRY_STYLE, _COMBO_STYLE, _CHECK_STYLE, _RADIO_STYLE
    _BTN_PRIMARY = f"""
        QPushButton {{
            background-color: {_ACCENT}; color: {_TEXT};
            border-radius: 8px; padding: 6px 14px;
            font-size: 13px;
        }}
        QPushButton:hover {{ background-color: {_ACCENT_HOVER}; }}
        QPushButton:pressed {{ background-color: {_ACCENT_PRESS}; }}
    """
    _BTN_SECONDARY = f"""
        QPushButton {{
            background-color: #404040; color: {_TEXT};
            border-radius: 6px; padding: 5px 12px;
            font-size: 12px;
        }}
        QPushButton:hover {{ background-color: #505050; }}
    """
    _BTN_DANGER = f"""
        QPushButton {{
            background-color: {_DANGER}; color: {_TEXT};
            border-radius: 6px; padding: 5px 12px;
            font-size: 12px;
        }}
        QPushButton:hover {{ background-color: #a93226; }}
    """
    _BTN_MUTED = f"""
        QPushButton {{
            background-color: transparent; color: #aaaaaa;
            border: 1px solid #555555; border-radius: 6px;
            padding: 5px 12px; font-size: 12px;
        }}
        QPushButton:hover {{ background-color: #333333; }}
    """
    _LIST_STYLE = f"""
        QListWidget {{
            background-color: #262626; color: {_TEXT};
            border: 1px solid #404040; border-radius: 4px;
            font-family: "Segoe UI Semibold"; font-size: 11px;
        }}
        QListWidget::item:selected {{
            background-color: {_ACCENT}; color: {_TEXT};
        }}
    """
    _ENTRY_STYLE = f"""
        QLineEdit {{
            background-color: #333333; color: {_TEXT};
            border: 1px solid #555555; border-radius: 4px;
            padding: 4px 8px;
        }}
        QLineEdit:focus {{ border: 1px solid {_ACCENT}; }}
    """
    _COMBO_STYLE = f"""
        QComboBox {{
            background-color: #333333; color: {_TEXT};
            border: 1px solid #555555; border-radius: 4px;
            padding: 4px 8px;
        }}
        QComboBox::drop-down {{ border: none; }}
        QComboBox QAbstractItemView {{
            background-color: #2b2b2b; color: {_TEXT};
            selection-background-color: {_ACCENT};
        }}
    """
    _CHECK_STYLE = f"""
        QCheckBox {{ color: {_TEXT}; }}
        QCheckBox::indicator {{ width: 16px; height: 16px; }}
    """
    _RADIO_STYLE = f"""
        QRadioButton {{ color: {_TEXT}; }}
    """


_rebuild_styles()


def _primary_btn(text, command=None) -> QPushButton:
    btn = QPushButton(text)
    btn.setStyleSheet(_BTN_PRIMARY)
    if command:
        btn.clicked.connect(command)
    return btn


def _secondary_btn(text, command=None) -> QPushButton:
    btn = QPushButton(text)
    btn.setStyleSheet(_BTN_SECONDARY)
    if command:
        btn.clicked.connect(command)
    return btn


def _danger_btn(text, command=None) -> QPushButton:
    btn = QPushButton(text)
    btn.setStyleSheet(_BTN_DANGER)
    if command:
        btn.clicked.connect(command)
    return btn


def _muted_btn(text, command=None) -> QPushButton:
    btn = QPushButton(text)
    btn.setStyleSheet(_BTN_MUTED)
    if command:
        btn.clicked.connect(command)
    return btn


def _make_entry(width=None, placeholder="", password=False) -> QLineEdit:
    e = QLineEdit()
    e.setStyleSheet(_ENTRY_STYLE)
    e.setPlaceholderText(placeholder)
    if password:
        e.setEchoMode(QLineEdit.Password)
    if width:
        e.setFixedWidth(width)
    return e


def _make_combo(choices, width=None) -> QComboBox:
    c = QComboBox()
    c.addItems(choices)
    c.setStyleSheet(_COMBO_STYLE)
    if width:
        c.setFixedWidth(width)
    return c


class _ListWidget(QListWidget):
    """QListWidget that consumes wheel events so they don't bubble to the parent scroll area."""
    def wheelEvent(self, event):
        super().wheelEvent(event)
        event.accept()


def _make_listbox(height_rows=6) -> QListWidget:
    lb = _ListWidget()
    lb.setStyleSheet(_LIST_STYLE)
    lb.setFixedHeight(height_rows * 22 + 16)
    lb.setSelectionMode(QAbstractItemView.SingleSelection)
    return lb


def _collapsible_list(title: str, height_rows: int = 6):
    """Returns (container_widget, listbox).

    The list starts collapsed. The header button shows the item count and
    toggles visibility. The count updates automatically when items are added
    or removed.
    """
    container = QWidget()
    container.setStyleSheet("background: transparent;")
    vl = QVBoxLayout(container)
    vl.setContentsMargins(0, 0, 0, 0)
    vl.setSpacing(2)

    lb = _make_listbox(height_rows)
    lb.setVisible(False)

    header = QPushButton(f"\u25b6  {title}  (0)")
    header.setStyleSheet("""
        QPushButton {
            background: transparent;
            color: #ffffff;
            font-weight: bold;
            text-align: left;
            border: none;
            padding: 4px 0px;
            margin-top: 4px;
        }
        QPushButton:hover { color: #cccccc; }
    """)
    header.setFont(_make_scalable_font(14, bold=True))
    _scalable_labels.append((header, 14, True))

    def _refresh():
        arrow = "\u25bc" if lb.isVisible() else "\u25b6"
        header.setText(f"{arrow}  {title}  ({lb.count()})")

    def _toggle():
        lb.setVisible(not lb.isVisible())
        _refresh()

    header.clicked.connect(_toggle)
    lb.model().rowsInserted.connect(lambda *_: _refresh())
    lb.model().rowsRemoved.connect(lambda *_: _refresh())

    vl.addWidget(header)
    vl.addWidget(lb)
    return container, lb


def _hint_label(text: str, color: str = _MUTED) -> QLabel:
    """Muted description label that participates in Ctrl+Scroll font scaling."""
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color: {color};")
    lbl.setFont(_make_scalable_font(11))
    _scalable_labels.append((lbl, 11, False))
    return lbl


def _section_label(text, help_text=None) -> tuple:
    spacer = QWidget()
    spacer.setFixedHeight(6)
    lbl = QLabel(text)
    lbl.setStyleSheet("font-weight: bold; color: #ffffff; margin-top: 4px;")
    lbl.setFont(_make_scalable_font(14, bold=True))
    _scalable_labels.append((lbl, 14, True))
    widgets = [spacer, lbl]
    if help_text:
        h = QLabel(help_text)
        h.setStyleSheet(f"color: {_MUTED};")
        h.setFont(_make_scalable_font(11))
        h.setWordWrap(True)
        _scalable_labels.append((h, 11, False))
        widgets.append(h)
    return widgets


def _card_frame() -> QFrame:
    f = QFrame()
    f.setStyleSheet(f"QFrame {{ background-color: {_SURFACE}; border-radius: 10px; }}")
    return f


def _hrow(*widgets) -> QWidget:
    row = QWidget()
    row.setStyleSheet("background: transparent;")
    rl = QHBoxLayout(row)
    rl.setContentsMargins(0, 0, 0, 0)
    rl.setSpacing(8)
    for w in widgets:
        rl.addWidget(w)
    rl.addStretch()
    return row


def _scrollable_tab() -> tuple[QScrollArea, QWidget, QVBoxLayout]:
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setFrameShape(QFrame.NoFrame)
    area.setStyleSheet("QScrollArea { background: transparent; border: none; }")
    inner = QWidget()
    inner.setStyleSheet("background: transparent;")
    vl = QVBoxLayout(inner)
    vl.setContentsMargins(12, 12, 12, 12)
    vl.setSpacing(6)
    area.setWidget(inner)
    return area, inner, vl


# ---------------------------------------------------------------------------
# Overlay widget — covers the full parent, shown/hidden as a blocking splash
# ---------------------------------------------------------------------------

class _OverlayWidget(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setVisible(False)
        parent.installEventFilter(self)

    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        if obj is self.parent() and event.type() == QEvent.Resize:
            self.setGeometry(0, 0, obj.width(), obj.height())
        return False

    def show_over(self):
        self.setGeometry(0, 0, self.parent().width(), self.parent().height())
        self.setVisible(True)
        self.raise_()

    def hide_over(self):
        self.setVisible(False)


# ---------------------------------------------------------------------------
# Main build function
# ---------------------------------------------------------------------------

def build_ui(window, state: dict, callbacks: dict, constants: dict):
    from license import is_premium
    if is_premium():
        _apply_premium_theme()

    _scalable_labels.clear()

    HOTKEY_CHOICES      = constants["HOTKEY_CHOICES"]
    LANG_CHOICES        = constants["LANG_CHOICES"]
    FONT_SCALE_CHOICES  = constants.get("FONT_SCALE_CHOICES", ["Normal", "Large", "X-Large"])
    _install_path       = constants.get("install_path", "")

    # -- Unpack state --
    mode            = state["mode"]
    language        = state["language"]
    hotkey          = state["hotkey"]
    holdkey         = state["holdkey"]
    hotkey_display  = state["hotkey_display"]
    holdkey_display = state["holdkey_display"]
    search_engine   = state["search_engine"]
    confirm_actions = state["confirm_actions"]
    idle_chatter    = state["idle_chatter"]
    ptt_beep_volume = state["ptt_beep_volume"]
    tts_output_device = state["tts_output_device"]
    tts_device_choices = state["tts_device_choices"]
    tts_voice       = state["tts_voice"]
    tts_voice_choices = state["tts_voice_choices"]
    personality_mode = state["personality_mode"]
    overlay_position = state["overlay_position"]
    overlay_hotkey   = state["overlay_hotkey"]
    overlay_hotkey_display = state["overlay_hotkey_display"]
    joy_ptt_button  = state["joy_ptt_button"]
    font_scale      = state["font_scale"]
    spotify_media   = state["spotify_media"]
    spotify_requires = state["spotify_requires"]
    spotify_keywords = state["spotify_keywords"]
    status_var      = state["status_var"]
    transcript_var  = state["transcript_var"]
    news_source     = state["news_source"]
    birthday_month  = state["birthday_month"]
    birthday_day    = state["birthday_day"]

    app_name_var    = state["app_name_var"]
    app_cmd_var     = state["app_cmd_var"]
    alias_var       = state["alias_var"]
    alias_target_var = state["alias_target_var"]
    phrase_var      = state["phrase_var"]
    command_var     = state["command_var"]
    discord_ch_name_var  = state["discord_ch_name_var"]
    discord_ch_url_var   = state["discord_ch_url_var"]
    discord_ch_server_var = state["discord_ch_server_var"]
    discord_srv_nickname_var = state["discord_srv_nickname_var"]
    discord_srv_id_var   = state["discord_srv_id_var"]
    discord_bot_token_var = state["discord_bot_token_var"]
    discord_server_id_var = state["discord_server_id_var"]
    gemini_api_key_var   = state["gemini_api_key_var"]
    keybind_phrase_var   = state["keybind_phrase_var"]
    keybind_key_var      = state["keybind_key_var"]
    keybind_count_var    = state["keybind_count_var"]
    macro_phrase_var     = state["macro_phrase_var"]
    macro_step_var       = state["macro_step_var"]

    # -- Unpack callbacks --
    _load_logo           = callbacks["load_logo"]
    _save                = callbacks["save"]
    _do_restart          = callbacks.get("do_restart")
    _run_now             = callbacks["run_now"]
    _install_deps        = callbacks["install_deps"]
    _start_background    = callbacks["start_background"]
    _stop_background     = callbacks["stop_background"]
    _check_for_updates   = callbacks["check_for_updates"]
    _create_bug_report   = callbacks["create_bug_report"]
    _export_transcripts  = callbacks["export_transcripts"]
    _clear_pycache         = callbacks["clear_pycache"]
    _create_shortcuts      = callbacks["create_shortcuts"]
    _open_install_folder   = callbacks["open_install_folder"]
    _add_app             = callbacks["add_app"]
    _remove_app          = callbacks["remove_app"]
    _test_app            = callbacks["test_app"]
    _import_steam        = callbacks["import_steam"]
    _add_alias           = callbacks["add_alias"]
    _remove_alias        = callbacks["remove_alias"]
    _add_action          = callbacks["add_action"]
    _remove_action       = callbacks["remove_action"]
    _record_hotkey       = callbacks["record_hotkey"]
    _record_hold_key     = callbacks["record_hold_key"]
    _add_discord_channel    = callbacks["add_discord_channel"]
    _remove_discord_channel = callbacks["remove_discord_channel"]
    _add_discord_server     = callbacks["add_discord_server"]
    _remove_discord_server  = callbacks["remove_discord_server"]
    _add_keybind         = callbacks["add_keybind"]
    _remove_keybind      = callbacks["remove_keybind"]
    _record_keybind_key  = callbacks["record_keybind_key"]
    _add_macro_step      = callbacks["add_macro_step"]
    _remove_macro_step   = callbacks["remove_macro_step"]
    _add_macro           = callbacks["add_macro"]
    _remove_macro        = callbacks["remove_macro"]
    _on_mode_change      = callbacks["mode_changed"]

    # =====================================================================
    # Central widget + outer layout
    # =====================================================================
    central = QWidget()
    central.setStyleSheet(f"background-color: {_BG};")
    window.setCentralWidget(central)
    outer_vl = QVBoxLayout(central)
    outer_vl.setContentsMargins(0, 0, 0, 0)
    outer_vl.setSpacing(0)

    # =====================================================================
    # TAB WIDGET
    # =====================================================================
    tabs = QTabWidget()
    tabs.setStyleSheet(f"""
        QTabWidget::pane {{ border: none; background: {_BG}; }}
        QTabBar::tab {{
            background: #2b2b2b; color: #aaaaaa;
            padding: 8px 16px; border: none;
        }}
        QTabBar::tab:selected {{ background: {_BG}; color: #ffffff; border-bottom: 2px solid {_ACCENT}; }}
        QTabBar::tab:hover {{ background: #333333; }}
    """)
    outer_vl.addWidget(tabs, stretch=1)

    # =====================================================================
    # HOME TAB
    # =====================================================================
    home_area, home_inner, home_vl = _scrollable_tab()
    tabs.addTab(home_area, "Home")

    # Premium watermarks
    if is_premium():
        _wm_row = QHBoxLayout()
        _wm_row.setContentsMargins(6, 4, 6, 0)
        _wm_left = QLabel("VERA+")
        _wm_left.setStyleSheet("color: rgba(201,168,76,55); font-size: 9px; letter-spacing: 4px; background: transparent;")
        _wm_right = QLabel("PREMIUM TIER")
        _wm_right.setStyleSheet("color: rgba(201,168,76,55); font-size: 9px; letter-spacing: 3px; background: transparent;")
        _wm_right.setAlignment(Qt.AlignRight)
        _wm_row.addWidget(_wm_left)
        _wm_row.addWidget(_wm_right)
        _wm_widget = QWidget()
        _wm_widget.setLayout(_wm_row)
        _wm_widget.setStyleSheet("background: transparent;")
        home_vl.addWidget(_wm_widget)

    # Logo
    logo_path = _load_logo()
    if logo_path:
        logo_lbl = QLabel()
        px = QPixmap(logo_path)
        if not px.isNull():
            logo_lbl.setPixmap(px.scaled(140, 140, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            logo_lbl.setAlignment(Qt.AlignCenter)
            home_vl.addWidget(logo_lbl)
    title_lbl = QLabel("V  E  R  A  +" if is_premium() else "V  E  R  A")
    title_lbl.setAlignment(Qt.AlignCenter)
    title_lbl.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {_TITLE_COLOR};")
    home_vl.addWidget(title_lbl)

    # Controls section
    for w in _section_label("Controls"):
        home_vl.addWidget(w)

    ctrl_card = _card_frame()
    ctrl_vl = QVBoxLayout(ctrl_card)
    ctrl_vl.setContentsMargins(12, 8, 12, 8)

    bg_ctrl_row = _hrow(
        _primary_btn("Start Listening", _start_background),
        _danger_btn("Stop Listening", _stop_background),
    )
    ctrl_vl.addWidget(bg_ctrl_row)

    mic_ctrl_row = _hrow(_primary_btn("Run Now", _run_now))
    ctrl_vl.addWidget(mic_ctrl_row)

    knob_row = None

    def _update_controls():
        m = mode.get()
        if m == "mic":
            ctrl_card.setVisible(True)
            bg_ctrl_row.setVisible(False)
            mic_ctrl_row.setVisible(True)
            if knob_row: knob_row.setVisible(False)
        elif m == "wake":
            ctrl_card.setVisible(False)
            bg_ctrl_row.setVisible(False)
            mic_ctrl_row.setVisible(False)
            if knob_row: knob_row.setVisible(False)
        elif m in ("hold", "toggle") and knob_row is not None:
            ctrl_card.setVisible(False)
            bg_ctrl_row.setVisible(False)
            mic_ctrl_row.setVisible(False)
            knob_row.setVisible(True)
        else:
            ctrl_card.setVisible(True)
            mic_ctrl_row.setVisible(False)
            bg_ctrl_row.setVisible(True)
            if knob_row: knob_row.setVisible(False)

    mode.trace_add("write", lambda *_: _update_controls())
    _update_controls()
    home_vl.addWidget(ctrl_card)

    # Premium knob — floats below controls card, no card background
    knob_row = None
    if is_premium():
        import os as _os
        _knob_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "data", "assets", "ptt_knob.png")
        _knob_px = QPixmap(_knob_path)
        if not _knob_px.isNull():
            from PySide6.QtGui import QPainter, QTransform

            _knob_sized = _knob_px.scaled(90, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)

            def _make_knob_icon(angle: float) -> QIcon:
                out = QPixmap(_knob_sized.size())
                out.fill(QColor(_BG))
                p = QPainter(out)
                cx, cy = _knob_sized.width() / 2, _knob_sized.height() / 2
                t = QTransform()
                t.translate(cx, cy)
                t.rotate(angle)
                t.translate(-cx, -cy)
                p.setTransform(t)
                p.drawPixmap(0, 0, _knob_sized)
                p.end()
                return QIcon(out)

            # Angle pointing toward top label (Start), bottom label (Stop)
            knob_btn = QPushButton()
            knob_btn.setFixedSize(90, 90)
            knob_btn.setIcon(_make_knob_icon(0))
            knob_btn.setIconSize(QSize(90, 90))
            knob_btn.setStyleSheet("QPushButton { background: transparent; border: none; } QPushButton:pressed { margin: 2px; }")
            knob_btn.setToolTip("Click to start / stop listening")

            _knob_lbl = QLabel("Start Listening")
            _knob_lbl.setStyleSheet(f"color: {_ACCENT}; font-size: 13px; font-weight: bold; background: transparent;")

            _knob_active = [False]
            def _knob_clicked():
                if _knob_active[0]:
                    _stop_background()
                    _knob_lbl.setText("Start Listening")
                    _knob_lbl.setStyleSheet(f"color: {_ACCENT}; font-size: 13px; font-weight: bold; background: transparent;")
                    _knob_active[0] = False
                else:
                    _start_background()
                    _knob_lbl.setText("Stop Listening")
                    _knob_lbl.setStyleSheet("color: #c0392b; font-size: 13px; font-weight: bold; background: transparent;")
                    _knob_active[0] = True
            knob_btn.clicked.connect(_knob_clicked)

            knob_row = QWidget()
            knob_row.setStyleSheet("background: transparent;")
            _knob_hl = QHBoxLayout(knob_row)
            _knob_hl.setContentsMargins(8, 4, 8, 4)
            _knob_hl.setSpacing(16)
            _knob_hl.addWidget(knob_btn)
            _knob_hl.addWidget(_knob_lbl)
            _knob_hl.addStretch()
            home_vl.addWidget(knob_row)
            _update_controls()  # re-run now that knob_row is assigned

    # Transcript History
    for w in _section_label("Transcript History", "Recent voice commands you've spoken."):
        home_vl.addWidget(w)
    history_textbox = QTextEdit()
    history_textbox.setReadOnly(True)
    history_textbox.setFixedHeight(180)
    history_textbox.setStyleSheet(
        f"background-color: #262626; color: {_TEXT}; border-radius: 8px; font-size: 12px;"
    )
    home_vl.addWidget(history_textbox)

    # Community
    for w in _section_label("Community", "Join the VERA Discord server."):
        home_vl.addWidget(w)
    comm_card = _card_frame()
    comm_vl = QVBoxLayout(comm_card)
    comm_vl.setContentsMargins(12, 8, 12, 8)
    comm_vl.addWidget(_hrow(_primary_btn("Join the Discord",
        lambda: __import__("webbrowser").open("https://discord.gg/DCdHVEchet"))))
    home_vl.addWidget(comm_card)
    home_vl.addStretch()

    # =====================================================================
    # SETTINGS TAB
    # =====================================================================
    settings_area, _, settings_vl = _scrollable_tab()
    tabs.addTab(settings_area, "Settings")

    # Listening Mode
    for w in _section_label("Listening Mode", "Choose how VERA listens for your voice commands."):
        settings_vl.addWidget(w)
    mode_card = _card_frame()
    mode_cl = QVBoxLayout(mode_card)
    mode_cl.setContentsMargins(12, 10, 12, 10)

    _SEG_ACTIVE = f"""
        QPushButton {{
            background-color: {_ACCENT}; color: #ffffff;
            border: none; padding: 6px 18px; font-size: 12px; font-weight: bold;
        }}
    """
    _SEG_INACTIVE = """
        QPushButton {
            background-color: transparent; color: #aaaaaa;
            border: none; padding: 6px 18px; font-size: 12px;
        }
        QPushButton:hover { color: #ffffff; background-color: #383838; }
    """

    seg_container = QWidget()
    seg_container.setStyleSheet("background-color: #1a1a1a; border-radius: 8px;")
    seg_container.setFixedHeight(34)
    seg_container.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    seg_layout = QHBoxLayout(seg_container)
    seg_layout.setContentsMargins(3, 2, 3, 2)
    seg_layout.setSpacing(2)

    seg_hold   = QPushButton("Hold-to-talk")
    seg_toggle = QPushButton("Toggle-to-talk")
    seg_wake   = QPushButton("Wake word")
    for btn in (seg_hold, seg_toggle, seg_wake):
        btn.setFlat(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        seg_layout.addWidget(btn)

    def _seg_select(active_mode: str):
        for btn, m in ((seg_hold, "hold"), (seg_toggle, "toggle"), (seg_wake, "wake")):
            btn.setStyleSheet(_SEG_ACTIVE if m == active_mode else _SEG_INACTIVE)

    def _sync_mode_radios():
        _seg_select(mode.get())

    _sync_mode_radios()

    def _on_radio_hold():
        mode.set("hold")
        _seg_select("hold")
        _on_mode_change()

    def _on_radio_toggle():
        mode.set("toggle")
        _seg_select("toggle")
        _on_mode_change()

    def _on_radio_wake():
        mode.set("wake")
        _seg_select("wake")
        _on_mode_change()

    seg_hold.clicked.connect(_on_radio_hold)
    seg_toggle.clicked.connect(_on_radio_toggle)
    seg_wake.clicked.connect(_on_radio_wake)

    seg_row = QHBoxLayout()
    seg_row.setContentsMargins(0, 0, 0, 0)
    seg_row.addWidget(seg_container)
    seg_row.addStretch()
    seg_row_w = QWidget()
    seg_row_w.setLayout(seg_row)
    mode_cl.addWidget(seg_row_w)
    settings_vl.addWidget(mode_card)

    # Recording Settings
    for w in _section_label("Recording Settings", "Configure timing, language, and activation keys."):
        settings_vl.addWidget(w)
    rec_card = _card_frame()
    rec_vl = QVBoxLayout(rec_card)
    rec_vl.setContentsMargins(12, 8, 12, 8)
    rec_vl.setSpacing(6)

    # Language row
    lang_lbl = QLabel("Language")
    lang_lbl.setFixedWidth(120)
    lang_lbl.setStyleSheet(f"color: {_TEXT};")
    lang_combo = _make_combo(LANG_CHOICES, 140)
    lang_combo.setCurrentText(language.get())
    lang_combo.currentTextChanged.connect(language.set)
    rec_vl.addWidget(_hrow(lang_lbl, lang_combo))

    # Hotkey row
    hk_lbl = QLabel("Toggle key")
    hk_lbl.setFixedWidth(120)
    hk_lbl.setStyleSheet(f"color: {_TEXT};")
    hk_edit = _make_entry(160)
    hk_edit.setText(hotkey_display.get())

    def _on_hk_text_changed(text):
        hotkey_display.set(text)

    hk_edit.textChanged.connect(_on_hk_text_changed)

    def _hk_record():
        _record_hotkey(hotkey, on_done=lambda: hk_edit.setText(hotkey_display.get()))

    hk_rec_btn = _secondary_btn("Record", _hk_record)
    rec_vl.addWidget(_hrow(hk_lbl, hk_edit, hk_rec_btn))

    # Hold key row
    hold_lbl = QLabel("Hold key")
    hold_lbl.setFixedWidth(120)
    hold_lbl.setStyleSheet(f"color: {_TEXT};")
    hold_edit = _make_entry(160)
    hold_edit.setText(holdkey_display.get())

    def _on_hold_text_changed(text):
        holdkey_display.set(text)

    hold_edit.textChanged.connect(_on_hold_text_changed)

    def _hold_record():
        _record_hold_key(holdkey, on_done=lambda: hold_edit.setText(holdkey_display.get()))

    hold_rec_btn = _secondary_btn("Record", _hold_record)
    rec_vl.addWidget(_hrow(hold_lbl, hold_edit, hold_rec_btn))

    # Secondary PTT row
    _record_secondary_ptt_fn = callbacks.get("record_secondary_ptt")
    joy_ptt_edit = _make_entry(160)
    joy_ptt_edit.setReadOnly(True)
    joy_ptt_edit.setPlaceholderText("None")
    joy_ptt_edit.setText(joy_ptt_button.get())
    joy_ptt_button.trace_add("write", lambda *_: joy_ptt_edit.setText(joy_ptt_button.get()))

    def _do_record_secondary():
        if _record_secondary_ptt_fn:
            _record_secondary_ptt_fn(
                joy_ptt_button,
                on_done=lambda: (_save(), _do_restart()),
            )

    joy_ptt_btn = _secondary_btn("Record", _do_record_secondary)
    joy_ptt_row = _hrow(QLabel("Secondary PTT"), joy_ptt_edit, joy_ptt_btn)
    joy_ptt_row.findChildren(QLabel)[0].setStyleSheet(f"color: {_TEXT}; min-width: 120px;")
    rec_vl.addWidget(joy_ptt_row)

    # Search engine row
    se_lbl = QLabel("Search Engine")
    se_lbl.setFixedWidth(120)
    se_lbl.setStyleSheet(f"color: {_TEXT};")
    se_edit = _make_entry(340)
    se_edit.setText(search_engine.get())
    se_edit.textChanged.connect(search_engine.set)
    rec_vl.addWidget(_hrow(se_lbl, se_edit))

    # Beep volume row
    bv_lbl = QLabel("Beep Volume")
    bv_lbl.setFixedWidth(120)
    bv_lbl.setStyleSheet(f"color: {_TEXT};")
    bv_slider = QSlider(Qt.Horizontal)
    bv_slider.setRange(0, 100)
    bv_slider.setValue(int(ptt_beep_volume.get()))
    bv_slider.setFixedWidth(200)
    bv_slider.setStyleSheet(f"QSlider::groove:horizontal {{ height: 4px; background: #444; border-radius: 2px; }}"
                             f"QSlider::handle:horizontal {{ background: {_ACCENT}; width: 14px; height: 14px; border-radius: 7px; margin: -5px 0; }}"
                             f"QSlider::sub-page:horizontal {{ background: {_ACCENT}; border-radius: 2px; }}")
    bv_val_lbl = QLabel(f"{ptt_beep_volume.get()}%")
    bv_val_lbl.setStyleSheet(f"color: {_TEXT}; min-width: 40px;")

    def _on_bv_change(v):
        ptt_beep_volume.set(v)
        bv_val_lbl.setText(f"{v}%")

    bv_slider.valueChanged.connect(_on_bv_change)
    rec_vl.addWidget(_hrow(bv_lbl, bv_slider, bv_val_lbl))

    # Voice output row
    vo_lbl = QLabel("Voice Output")
    vo_lbl.setFixedWidth(120)
    vo_lbl.setStyleSheet(f"color: {_TEXT};")
    vo_combo = _make_combo(tts_device_choices, 260)
    vo_combo.setCurrentText(tts_output_device.get() or "Default")
    vo_combo.currentTextChanged.connect(tts_output_device.set)
    vo_hint = _hint_label("  Select your virtual mic (e.g. VB-Cable) to route TTS to Discord")
    rec_vl.addWidget(_hrow(vo_lbl, vo_combo, vo_hint))

    # Voice row
    voice_lbl = QLabel("Voice")
    voice_lbl.setFixedWidth(120)
    voice_lbl.setStyleSheet(f"color: {_TEXT};")
    voice_combo = _make_combo(tts_voice_choices, 160)
    voice_combo.setCurrentText(tts_voice.get())
    voice_combo.currentTextChanged.connect(tts_voice.set)
    voice_hint = _hint_label("  Choose VERA's voice (takes effect immediately)")
    rec_vl.addWidget(_hrow(voice_lbl, voice_combo, voice_hint))
    settings_vl.addWidget(rec_card)

    # General Options
    for w in _section_label("General Options"):
        settings_vl.addWidget(w)
    opt_card = _card_frame()
    opt_vl = QVBoxLayout(opt_card)
    opt_vl.setContentsMargins(12, 8, 12, 8)
    confirm_row = QWidget()
    confirm_row_l = QHBoxLayout(confirm_row)
    confirm_row_l.setContentsMargins(0, 0, 0, 0)
    confirm_row_l.setSpacing(10)
    confirm_chk = QCheckBox("Confirm before running actions")
    confirm_chk.setStyleSheet(_CHECK_STYLE)
    confirm_chk.setChecked(bool(confirm_actions.get()))
    confirm_chk.stateChanged.connect(lambda s: confirm_actions.set(s == Qt.Checked.value))
    confirm_desc = _hint_label("VERA will ask you to confirm before opening apps or running commands.")
    confirm_desc.setWordWrap(True)
    confirm_row_l.addWidget(confirm_chk)
    confirm_row_l.addWidget(confirm_desc, 1)
    opt_vl.addWidget(confirm_row)
    settings_vl.addWidget(opt_card)

    # Personality
    for w in _section_label("Personality", "Choose how VERA speaks to you."):
        settings_vl.addWidget(w)
    pers_card = _card_frame()
    pers_vl = QVBoxLayout(pers_card)
    pers_vl.setContentsMargins(12, 8, 12, 8)
    try:
        from license import is_premium as _is_premium
        _premium = _is_premium()
    except Exception:
        _premium = False
    pers_choices = ["default", "professional", "jarvis", "offensive"] if _premium else ["default", "professional", "jarvis"]
    pers_combo = _make_combo(pers_choices, 160)
    pers_combo.setCurrentText(personality_mode.get())
    pers_combo.currentTextChanged.connect(personality_mode.set)
    pers_row = _hrow(QLabel("Mode"), pers_combo)
    pers_row.findChildren(QLabel)[0].setStyleSheet(f"color: {_TEXT}; min-width: 120px;")
    if not _premium:
        pers_note = _hint_label("  Offensive mode requires a Premium license")
        pers_row.layout().addWidget(pers_note)
    pers_vl.addWidget(pers_row)

    chatter_chk = QCheckBox("Enable idle chatter")
    chatter_chk.setChecked(bool(idle_chatter.get()))
    chatter_chk.stateChanged.connect(lambda v: idle_chatter.set(bool(v)))
    chatter_desc = _hint_label("VERA will speak unprompted after periods of inactivity")
    chatter_row = QWidget()
    chatter_row_l = QHBoxLayout(chatter_row)
    chatter_row_l.setContentsMargins(0, 4, 0, 0)
    chatter_row_l.setSpacing(8)
    chatter_row_l.addWidget(chatter_chk)
    chatter_row_l.addWidget(chatter_desc, 1)
    pers_vl.addWidget(chatter_row)

    gaming_mode_chk = QCheckBox("Gaming mode")
    try:
        from skills import _gaming_mode as _gm_ui
        gaming_mode_chk.setChecked(bool(_gm_ui["value"]))
    except Exception:
        gaming_mode_chk.setChecked(False)
    def _toggle_gaming_mode(v):
        try:
            from skills import _gaming_mode as _gm_ui2
            _gm_ui2["value"] = bool(v)
            fn = _gm_ui2.get("status_fn")
            if fn:
                fn(bool(v))
        except Exception:
            pass
    gaming_mode_chk.stateChanged.connect(_toggle_gaming_mode)
    gaming_desc = _hint_label("Ultra-short responses, no idle chatter, silent on mishears")
    gaming_row = QWidget()
    gaming_row_l = QHBoxLayout(gaming_row)
    gaming_row_l.setContentsMargins(0, 4, 0, 0)
    gaming_row_l.setSpacing(8)
    gaming_row_l.addWidget(gaming_mode_chk)
    gaming_row_l.addWidget(gaming_desc, 1)
    pers_vl.addWidget(gaming_row)

    # Custom wake phrase (premium)
    from config import load_config as _load_cfg
    _cfg_wake = _load_cfg().get("custom_wake_phrase", "")
    wake_lbl = QLabel("Custom wake phrase")
    wake_lbl.setStyleSheet(f"color: {_TEXT}; min-width: 120px;")
    wake_entry = QLineEdit()
    wake_entry.setFixedWidth(140)
    wake_entry.setPlaceholderText("e.g. friday")
    wake_entry.setText(_cfg_wake)
    wake_entry.setEnabled(_premium)
    wake_save = QPushButton("Save")
    wake_save.setFixedWidth(60)
    wake_save.setEnabled(_premium)
    if _premium:
        wake_save.clicked.connect(lambda: callbacks["set_custom_wake_phrase"](wake_entry.text()))
    wake_row = QWidget()
    wake_row_l = QHBoxLayout(wake_row)
    wake_row_l.setContentsMargins(0, 4, 0, 0)
    wake_row_l.setSpacing(8)
    wake_row_l.addWidget(wake_lbl)
    wake_row_l.addWidget(wake_entry)
    wake_row_l.addWidget(wake_save)
    if not _premium:
        wake_row_l.addWidget(_hint_label("  Premium feature"))
    wake_row_l.addStretch()
    pers_vl.addWidget(wake_row)

    settings_vl.addWidget(pers_card)

    # Game Overlay
    for w in _section_label("Game Overlay", "A transparent always-on-top bar showing your last 3 voice exchanges. Say 'show overlay' / 'hide overlay' or use a hotkey."):
        settings_vl.addWidget(w)
    ovl_card = _card_frame()
    ovl_vl = QVBoxLayout(ovl_card)
    ovl_vl.setContentsMargins(12, 8, 12, 8)
    ovl_vl.setSpacing(6)

    from overlay import POSITION_CHOICES as _OVL_POSITIONS
    ovl_pos_combo = _make_combo(_OVL_POSITIONS, 160)
    ovl_pos_combo.setCurrentText(overlay_position.get())
    ovl_pos_combo.currentTextChanged.connect(overlay_position.set)
    ovl_pos_row = _hrow(QLabel("Position"), ovl_pos_combo)
    ovl_pos_row.findChildren(QLabel)[0].setStyleSheet(f"color: {_TEXT}; min-width: 120px;")
    ovl_vl.addWidget(ovl_pos_row)

    ovl_hk_edit = _make_entry(160)
    ovl_hk_edit.setReadOnly(True)
    ovl_hk_edit.setPlaceholderText("None")
    ovl_hk_edit.setText(overlay_hotkey_display.get())
    overlay_hotkey_display.trace_add("write", lambda *_: ovl_hk_edit.setText(overlay_hotkey_display.get()))

    _record_overlay_hotkey = callbacks.get("record_overlay_hotkey")

    def _ovl_hk_record():
        if _record_overlay_hotkey:
            _record_overlay_hotkey()

    ovl_hk_btn = _secondary_btn("Record", _ovl_hk_record)
    ovl_hk_row = _hrow(QLabel("Toggle Hotkey"), ovl_hk_edit, ovl_hk_btn)
    ovl_hk_row.findChildren(QLabel)[0].setStyleSheet(f"color: {_TEXT}; min-width: 120px;")
    ovl_vl.addWidget(ovl_hk_row)

    settings_vl.addWidget(ovl_card)

    # Spotify
    for w in _section_label("Spotify", "Control Spotify playback with voice commands like 'play', 'pause', 'next'."):
        settings_vl.addWidget(w)
    spot_card = _card_frame()
    spot_vl = QVBoxLayout(spot_card)
    spot_vl.setContentsMargins(12, 8, 12, 8)
    spot_media_chk = QCheckBox("Enable Spotify media controls")
    spot_media_chk.setStyleSheet(_CHECK_STYLE)
    spot_media_chk.setChecked(bool(spotify_media.get()))
    spot_media_chk.stateChanged.connect(lambda s: spotify_media.set(s == Qt.Checked.value))
    spot_vl.addWidget(spot_media_chk)
    spot_req_chk = QCheckBox("Require word 'spotify' in command")
    spot_req_chk.setStyleSheet(_CHECK_STYLE)
    spot_req_chk.setChecked(bool(spotify_requires.get()))
    spot_req_chk.stateChanged.connect(lambda s: spotify_requires.set(s == Qt.Checked.value))
    spot_vl.addWidget(spot_req_chk)
    spot_kw_lbl = QLabel("Spotify keywords")
    spot_kw_lbl.setStyleSheet(f"color: {_TEXT};")
    spot_kw_edit = _make_entry(240)
    spot_kw_edit.setText(spotify_keywords.get())
    spot_kw_edit.textChanged.connect(spotify_keywords.set)
    spot_vl.addWidget(_hrow(spot_kw_lbl, spot_kw_edit))
    settings_vl.addWidget(spot_card)

    # News
    for w in _section_label("News", "Choose your preferred news source for 'give me the news'."):
        settings_vl.addWidget(w)
    news_card = _card_frame()
    news_vl = QVBoxLayout(news_card)
    news_vl.setContentsMargins(12, 8, 12, 8)
    news_src_lbl = QLabel("Source")
    news_src_lbl.setStyleSheet(f"color: {_TEXT}; min-width: 120px;")
    news_combo = _make_combo(["BBC", "Reuters", "NPR", "AP News", "The Guardian", "Al Jazeera"], 160)
    news_combo.setCurrentText(news_source.get())
    news_combo.currentTextChanged.connect(news_source.set)
    news_vl.addWidget(_hrow(news_src_lbl, news_combo))
    settings_vl.addWidget(news_card)

    # Birthday
    for w in _section_label("Birthday", "VERA will wish you happy birthday on startup."):
        settings_vl.addWidget(w)
    bday_card = _card_frame()
    bday_vl = QVBoxLayout(bday_card)
    bday_vl.setContentsMargins(12, 8, 12, 8)
    bday_month_lbl = QLabel("Month")
    bday_month_lbl.setStyleSheet(f"color: {_TEXT}; min-width: 80px;")
    bday_month_combo = _make_combo([""] + [str(i) for i in range(1, 13)], 80)
    bday_month_combo.setCurrentText(birthday_month.get())
    bday_month_combo.currentTextChanged.connect(birthday_month.set)
    bday_day_lbl = QLabel("Day")
    bday_day_lbl.setStyleSheet(f"color: {_TEXT}; min-width: 40px;")
    bday_day_combo = _make_combo([""] + [str(d) for d in range(1, 32)], 80)
    bday_day_combo.setCurrentText(birthday_day.get())
    bday_day_combo.currentTextChanged.connect(birthday_day.set)
    bday_hint = _hint_label("  Leave blank to disable")
    bday_vl.addWidget(_hrow(bday_month_lbl, bday_month_combo, bday_day_lbl, bday_day_combo, bday_hint))
    settings_vl.addWidget(bday_card)

    # Utilities
    for w in _section_label("Utilities"):
        settings_vl.addWidget(w)
    util_card = _card_frame()
    util_vl = QVBoxLayout(util_card)
    util_vl.setContentsMargins(12, 8, 12, 8)

    # Install path row
    path_lbl = QLabel("Install Path")
    path_lbl.setStyleSheet(f"color: {_TEXT}; min-width: 100px;")
    path_edit = _make_entry(0, _install_path)
    path_edit.setReadOnly(True)
    path_edit.setStyleSheet(path_edit.styleSheet() + f"color: {_MUTED};")
    path_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def _copy_path():
        QApplication.clipboard().setText(_install_path)

    util_vl.addWidget(_hrow(
        path_lbl,
        path_edit,
        _secondary_btn("Open", _open_install_folder),
        _secondary_btn("Copy", _copy_path),
    ))

    util_vl.addWidget(_hrow(
        _secondary_btn("Check Updates", _check_for_updates),
        _secondary_btn("Install Deps", _install_deps),
        _secondary_btn("Add Desktop Shortcut", _create_shortcuts),
    ))
    util_vl.addWidget(_hrow(
        _secondary_btn("Bug Report", _create_bug_report),
        _secondary_btn("Export Transcripts", _export_transcripts),
        _secondary_btn("Delete Cache", _clear_pycache),
    ))
    settings_vl.addWidget(util_card)
    settings_vl.addStretch()

    # =====================================================================
    # APPS TAB
    # =====================================================================
    apps_area, _, apps_vl = _scrollable_tab()
    tabs.addTab(apps_area, "Apps")

    _ra_spacer = QWidget(); _ra_spacer.setFixedHeight(6)
    apps_vl.addWidget(_ra_spacer)
    _ra_help = _hint_label("Say 'open <app name>' to launch an app.")
    apps_vl.addWidget(_ra_help)
    _ra_container, apps_textbox = _collapsible_list("Registered Apps", 6)
    apps_vl.addWidget(_ra_container)

    app_card = _card_frame()
    app_cvl = QVBoxLayout(app_card)
    app_cvl.setContentsMargins(12, 8, 12, 8)
    app_name_lbl = QLabel("App name")
    app_name_lbl.setStyleSheet(f"color: {_TEXT}; min-width: 100px;")
    app_name_edit = _make_entry(240, "e.g. notepad")
    app_name_edit.textChanged.connect(app_name_var.set)
    app_cvl.addWidget(_hrow(app_name_lbl, app_name_edit))
    app_cmd_lbl = QLabel("App command")
    app_cmd_lbl.setStyleSheet(f"color: {_TEXT}; min-width: 100px;")
    app_cmd_edit = _make_entry(240, "e.g. notepad.exe")
    app_cmd_edit.textChanged.connect(app_cmd_var.set)
    app_cvl.addWidget(_hrow(app_cmd_lbl, app_cmd_edit))
    apps_vl.addWidget(app_card)
    apps_vl.addWidget(_hrow(
        _primary_btn("Add App", _add_app),
        _secondary_btn("Test App", _test_app),
        _secondary_btn("Import Steam", _import_steam),
        _danger_btn("Remove Selected", _remove_app),
    ))

    _aa_spacer = QWidget(); _aa_spacer.setFixedHeight(6)
    apps_vl.addWidget(_aa_spacer)
    _aa_help = _hint_label("Create shortcuts — say the alias to launch the target app.")
    apps_vl.addWidget(_aa_help)
    _aa_container, aliases_textbox = _collapsible_list("App Aliases", 4)
    apps_vl.addWidget(_aa_container)

    alias_card = _card_frame()
    alias_cvl = QVBoxLayout(alias_card)
    alias_cvl.setContentsMargins(12, 8, 12, 8)
    alias_lbl = QLabel("Alias")
    alias_lbl.setStyleSheet(f"color: {_TEXT}; min-width: 100px;")
    alias_edit = _make_entry(240, "e.g. browser")
    alias_edit.textChanged.connect(alias_var.set)
    alias_cvl.addWidget(_hrow(alias_lbl, alias_edit))
    alias_tgt_lbl = QLabel("Target app")
    alias_tgt_lbl.setStyleSheet(f"color: {_TEXT}; min-width: 100px;")
    alias_tgt_edit = _make_entry(240, "e.g. chrome")
    alias_tgt_edit.textChanged.connect(alias_target_var.set)
    alias_cvl.addWidget(_hrow(alias_tgt_lbl, alias_tgt_edit))
    apps_vl.addWidget(alias_card)
    apps_vl.addWidget(_hrow(
        _primary_btn("Add Alias", _add_alias),
        _danger_btn("Remove Selected", _remove_alias),
    ))
    apps_vl.addStretch()

    # =====================================================================
    # INTEGRATIONS TAB
    # =====================================================================
    integ_area, _, integ_vl = _scrollable_tab()
    tabs.addTab(integ_area, "Integrations")

    for w in _section_label("AI Assistant", "Use `ask <question>` to query AI.\nGet your free key at console.groq.com -> API Keys."):
        integ_vl.addWidget(w)
    ai_card = _card_frame()
    ai_cvl = QVBoxLayout(ai_card)
    ai_cvl.setContentsMargins(12, 8, 12, 8)
    ai_lbl = QLabel("API Key")
    ai_lbl.setStyleSheet(f"color: {_TEXT}; min-width: 120px;")
    ai_edit = _make_entry(320, "Groq API key", password=True)
    ai_edit.setText(gemini_api_key_var.get())
    ai_edit.textChanged.connect(gemini_api_key_var.set)
    ai_cvl.addWidget(_hrow(ai_lbl, ai_edit))
    integ_vl.addWidget(ai_card)

    _va_spacer = QWidget(); _va_spacer.setFixedHeight(6)
    integ_vl.addWidget(_va_spacer)
    _va_help = _hint_label("Map a spoken phrase to a shell command.\nExample: `lock my computer` -> `rundll32.exe user32.dll,LockWorkStation`")
    _va_help.setWordWrap(True)
    integ_vl.addWidget(_va_help)
    _va_container, actions_textbox = _collapsible_list("Voice Actions", 6)
    integ_vl.addWidget(_va_container)

    act_card = _card_frame()
    act_cvl = QVBoxLayout(act_card)
    act_cvl.setContentsMargins(12, 8, 12, 8)
    phrase_lbl = QLabel("Phrase")
    phrase_lbl.setStyleSheet(f"color: {_TEXT}; min-width: 100px;")
    phrase_edit = _make_entry(300, "e.g. lock my computer")
    phrase_edit.textChanged.connect(phrase_var.set)
    act_cvl.addWidget(_hrow(phrase_lbl, phrase_edit))
    cmd_lbl = QLabel("Command")
    cmd_lbl.setStyleSheet(f"color: {_TEXT}; min-width: 100px;")
    cmd_edit = _make_entry(300, "e.g. rundll32.exe user32.dll,LockWorkStation")
    cmd_edit.textChanged.connect(command_var.set)
    act_cvl.addWidget(_hrow(cmd_lbl, cmd_edit))
    integ_vl.addWidget(act_card)
    integ_vl.addWidget(_hrow(
        _primary_btn("Add Action", _add_action),
        _danger_btn("Remove Selected", _remove_action),
    ))

    _kb_spacer = QWidget(); _kb_spacer.setFixedHeight(6)
    integ_vl.addWidget(_kb_spacer)
    _kb_help = _hint_label("Say a phrase to press a key (e.g. 'reload' → r).")
    integ_vl.addWidget(_kb_help)
    warn_lbl = _hint_label("⚠ Do not use in games protected by EAC or BattlEye — synthetic input may be flagged.", color=_WARN_FG)
    warn_lbl.setWordWrap(True)
    integ_vl.addWidget(warn_lbl)
    _kb_container, keybinds_textbox = _collapsible_list("Key Binds", 6)
    integ_vl.addWidget(_kb_container)

    kb_card = _card_frame()
    kb_cvl = QVBoxLayout(kb_card)
    kb_cvl.setContentsMargins(12, 8, 12, 8)
    kb_phrase_lbl = QLabel("Phrase")
    kb_phrase_lbl.setStyleSheet(f"color: {_TEXT}; min-width: 100px;")
    kb_phrase_edit = _make_entry(240, "e.g. reload")
    kb_phrase_edit.textChanged.connect(keybind_phrase_var.set)
    kb_cvl.addWidget(_hrow(kb_phrase_lbl, kb_phrase_edit))
    kb_key_lbl = QLabel("Key")
    kb_key_lbl.setStyleSheet(f"color: {_TEXT}; min-width: 100px;")
    kb_key_edit = _make_entry(180, "e.g. alt+n or x1 > q")
    kb_key_edit.textChanged.connect(keybind_key_var.set)

    def _do_record_keybind():
        _record_keybind_key(keybind_key_var, on_done=lambda v: kb_key_edit.setText(v))

    kb_step_btn = _secondary_btn("+ Step", _do_record_keybind)
    kb_cvl.addWidget(_hrow(kb_key_lbl, kb_key_edit, kb_step_btn))
    kb_cnt_lbl = QLabel("Count")
    kb_cnt_lbl.setStyleSheet(f"color: {_TEXT}; min-width: 100px;")
    kb_cnt_edit = _make_entry(60, "1")
    kb_cnt_edit.setText(keybind_count_var.get())
    kb_cnt_edit.textChanged.connect(keybind_count_var.set)
    kb_cnt_hint = QLabel("(how many times to press)")
    kb_cnt_hint.setStyleSheet(f"color: {_MUTED};")
    kb_cvl.addWidget(_hrow(kb_cnt_lbl, kb_cnt_edit, kb_cnt_hint))
    integ_vl.addWidget(kb_card)
    integ_vl.addWidget(_hrow(
        _primary_btn("Add Key Bind", _add_keybind),
        _danger_btn("Remove Selected", _remove_keybind),
    ))
    # --- Command Macros ---
    _cm_spacer = QWidget(); _cm_spacer.setFixedHeight(6)
    integ_vl.addWidget(_cm_spacer)
    _cm_help = _hint_label("Chain multiple commands into one phrase. Each step runs in sequence with a 1.5s delay. Premium only.")
    _cm_help.setWordWrap(True)
    integ_vl.addWidget(_cm_help)
    _cm_container, macros_textbox = _collapsible_list("Command Macros", 4)
    integ_vl.addWidget(_cm_container)

    cm_card = _card_frame()
    cm_cvl = QVBoxLayout(cm_card)
    cm_cvl.setContentsMargins(12, 8, 12, 8)

    cm_phrase_lbl = QLabel("Phrase")
    cm_phrase_lbl.setStyleSheet(f"color: {_TEXT}; min-width: 100px;")
    cm_phrase_edit = _make_entry(260, "e.g. good morning")
    cm_phrase_edit.textChanged.connect(macro_phrase_var.set)
    cm_cvl.addWidget(_hrow(cm_phrase_lbl, cm_phrase_edit))

    cm_step_lbl = QLabel("Step")
    cm_step_lbl.setStyleSheet(f"color: {_TEXT}; min-width: 100px;")
    cm_step_edit = _make_entry(260, "e.g. open spotify")
    cm_step_edit.textChanged.connect(macro_step_var.set)
    cm_step_edit.returnPressed.connect(_add_macro_step)
    cm_cvl.addWidget(_hrow(cm_step_lbl, cm_step_edit, _secondary_btn("Add Step", _add_macro_step)))

    cm_pending_lbl = QLabel("Steps")
    cm_pending_lbl.setStyleSheet(f"color: {_TEXT}; min-width: 100px;")
    macro_pending_textbox = _make_listbox(4)
    cm_cvl.addWidget(_hrow(cm_pending_lbl, macro_pending_textbox))
    cm_cvl.addWidget(_hrow(
        _secondary_btn("Remove Step", _remove_macro_step),
    ))
    integ_vl.addWidget(cm_card)
    integ_vl.addWidget(_hrow(
        _primary_btn("Add Macro", _add_macro),
        _danger_btn("Remove Selected", _remove_macro),
    ))

    integ_vl.addStretch()

    # =====================================================================
    # DISCORD TAB
    # =====================================================================
    discord_area, _, discord_vl = _scrollable_tab()
    tabs.addTab(discord_area, "Discord")

    for w in _section_label("Bot Credentials", "Required for `read discord`.\nGet your bot token from discord.dev."):
        discord_vl.addWidget(w)
    creds_card = _card_frame()
    creds_cvl = QVBoxLayout(creds_card)
    creds_cvl.setContentsMargins(12, 8, 12, 8)
    token_lbl = QLabel("Bot Token")
    token_lbl.setStyleSheet(f"color: {_TEXT}; min-width: 120px;")
    token_edit = _make_entry(320, "Bot token from Discord Developer Portal", password=True)
    token_edit.setText(discord_bot_token_var.get())
    token_edit.textChanged.connect(discord_bot_token_var.set)
    creds_cvl.addWidget(_hrow(token_lbl, token_edit))
    srv_id_lbl = QLabel("Default Server ID")
    srv_id_lbl.setStyleSheet(f"color: {_TEXT}; min-width: 120px;")
    srv_id_edit = _make_entry(220, "Right-click server → Copy Server ID")
    srv_id_edit.setText(discord_server_id_var.get())
    srv_id_edit.textChanged.connect(discord_server_id_var.set)
    creds_cvl.addWidget(_hrow(srv_id_lbl, srv_id_edit))
    discord_vl.addWidget(creds_card)

    for w in _section_label("Servers", "Add servers with a nickname.\nExample: `discord <nickname> <channel> <message>`"):
        discord_vl.addWidget(w)
    discord_servers_textbox = _make_listbox(4)
    discord_vl.addWidget(discord_servers_textbox)
    srv_card = _card_frame()
    srv_cvl = QVBoxLayout(srv_card)
    srv_cvl.setContentsMargins(12, 8, 12, 8)
    srv_nick_lbl = QLabel("Nickname")
    srv_nick_lbl.setStyleSheet(f"color: {_TEXT}; min-width: 120px;")
    srv_nick_edit = _make_entry(160, "e.g. baddie")
    srv_nick_edit.textChanged.connect(discord_srv_nickname_var.set)
    srv_cvl.addWidget(_hrow(srv_nick_lbl, srv_nick_edit))
    srv_sid_lbl = QLabel("Server ID")
    srv_sid_lbl.setStyleSheet(f"color: {_TEXT}; min-width: 120px;")
    srv_sid_edit = _make_entry(220, "Right-click server → Copy Server ID")
    srv_sid_edit.textChanged.connect(discord_srv_id_var.set)
    srv_cvl.addWidget(_hrow(srv_sid_lbl, srv_sid_edit))
    discord_vl.addWidget(srv_card)
    discord_vl.addWidget(_hrow(
        _primary_btn("Add Server", _add_discord_server),
        _danger_btn("Remove Selected", _remove_discord_server),
    ))

    for w in _section_label("Channels", "Webhook channels.\nOptionally tag a server so `discord <server> <channel>` works."):
        discord_vl.addWidget(w)
    discord_channels_textbox = _make_listbox(5)
    discord_vl.addWidget(discord_channels_textbox)
    ch_card = _card_frame()
    ch_cvl = QVBoxLayout(ch_card)
    ch_cvl.setContentsMargins(12, 8, 12, 8)
    ch_name_lbl = QLabel("Channel name")
    ch_name_lbl.setStyleSheet(f"color: {_TEXT}; min-width: 120px;")
    ch_name_edit = _make_entry(180, "e.g. general")
    ch_name_edit.textChanged.connect(discord_ch_name_var.set)
    ch_cvl.addWidget(_hrow(ch_name_lbl, ch_name_edit))
    ch_srv_lbl = QLabel("Server nickname")
    ch_srv_lbl.setStyleSheet(f"color: {_TEXT}; min-width: 120px;")
    ch_srv_edit = _make_entry(180, "optional — e.g. baddie")
    ch_srv_edit.textChanged.connect(discord_ch_server_var.set)
    ch_cvl.addWidget(_hrow(ch_srv_lbl, ch_srv_edit))
    ch_url_lbl = QLabel("Webhook URL")
    ch_url_lbl.setStyleSheet(f"color: {_TEXT}; min-width: 120px;")
    ch_url_edit = _make_entry(320, "https://discord.com/api/webhooks/...")
    ch_url_edit.textChanged.connect(discord_ch_url_var.set)
    ch_cvl.addWidget(_hrow(ch_url_lbl, ch_url_edit))
    discord_vl.addWidget(ch_card)
    discord_vl.addWidget(_hrow(
        _primary_btn("Add Channel", _add_discord_channel),
        _danger_btn("Remove Selected", _remove_discord_channel),
    ))
    cmd_hint = _hint_label(
        "Commands\n"
        "discord <channel> <message>\n"
        "discord <server> <channel> <message>\n"
        "read discord <server> <channel>"
    )
    discord_vl.addWidget(cmd_hint)
    discord_vl.addStretch()

    # =====================================================================
    # TRAINING TAB
    # =====================================================================
    training_area, _, training_vl = _scrollable_tab()
    tabs.addTab(training_area, "Training")

    from skills import load_unmatched, save_user_mishear, dismiss_unmatched, load_groq_handled, dismiss_groq_handled

    for w in _section_label("Mishear Training", "Transcripts VERA didn't understand. Select one, type what you meant, and save."):
        training_vl.addWidget(w)

    unmatched_listbox = _make_listbox(8)
    training_vl.addWidget(unmatched_listbox)

    _selected_mishear = [None]

    def _refresh_unmatched():
        unmatched_listbox.clear()
        for e in load_unmatched():
            unmatched_listbox.addItem(e)

    _refresh_unmatched()

    correction_frame = QWidget()
    correction_frame.setStyleSheet("background: transparent;")
    correction_layout = QHBoxLayout(correction_frame)
    correction_layout.setContentsMargins(0, 0, 0, 0)
    correct_lbl = QLabel("Correct to:")
    correct_lbl.setStyleSheet(f"color: {_TEXT};")
    correction_entry = _make_entry(260, "what you actually said")
    correction_layout.addWidget(correct_lbl)
    correction_layout.addWidget(correction_entry)
    correction_layout.addStretch()
    training_vl.addWidget(correction_frame)

    def _on_unmatched_select():
        sel = unmatched_listbox.selectedItems()
        if sel:
            text = sel[0].text()
            _selected_mishear[0] = text
            correction_entry.setText(text)

    unmatched_listbox.itemSelectionChanged.connect(_on_unmatched_select)

    def _save_correction():
        mishear = _selected_mishear[0]
        if not mishear:
            return
        correction = correction_entry.text().strip()
        if not correction:
            return
        save_user_mishear(mishear, correction)
        dismiss_unmatched(mishear)
        _selected_mishear[0] = None
        correction_entry.clear()
        _refresh_unmatched()

    def _dismiss_selected():
        mishear = _selected_mishear[0]
        if not mishear:
            return
        dismiss_unmatched(mishear)
        _selected_mishear[0] = None
        correction_entry.clear()
        _refresh_unmatched()

    training_vl.addWidget(_hrow(
        _primary_btn("Save Correction", _save_correction),
        _secondary_btn("Dismiss", _dismiss_selected),
        _muted_btn("Refresh", _refresh_unmatched),
    ))
    saved_hint = _hint_label("Saved corrections take effect immediately — no restart needed.")
    training_vl.addWidget(saved_hint)

    for w in _section_label("Groq Handled", "Things VERA answered via AI that could become real skills."):
        training_vl.addWidget(w)
    groq_listbox = _make_listbox(8)
    training_vl.addWidget(groq_listbox)

    _selected_groq = [None]

    def _refresh_groq_handled():
        groq_listbox.clear()
        for e in load_groq_handled():
            groq_listbox.addItem(e)

    _refresh_groq_handled()

    def _on_groq_select():
        sel = groq_listbox.selectedItems()
        if sel:
            _selected_groq[0] = sel[0].text()

    groq_listbox.itemSelectionChanged.connect(_on_groq_select)

    def _dismiss_groq():
        entry = _selected_groq[0]
        if not entry:
            return
        dismiss_groq_handled(entry)
        _selected_groq[0] = None
        _refresh_groq_handled()

    def _clear_all_groq():
        import json, os as _os
        from skills import _GROQ_HANDLED_PATH
        try:
            with open(_GROQ_HANDLED_PATH, "w", encoding="utf-8") as f:
                json.dump([], f)
        except Exception:
            pass
        _selected_groq[0] = None
        _refresh_groq_handled()

    training_vl.addWidget(_hrow(
        _secondary_btn("Dismiss Selected", _dismiss_groq),
        _danger_btn("Clear All", _clear_all_groq),
        _muted_btn("Refresh", _refresh_groq_handled),
    ))
    training_vl.addStretch()

    # =====================================================================
    # STATUS BAR (bottom of window, outside tabs)
    # =====================================================================
    status_frame = QWidget()
    status_frame.setStyleSheet(f"background-color: {_SURFACE}; border-top: 1px solid #3a3a3a;")
    status_frame.setFixedHeight(56)
    status_layout = QHBoxLayout(status_frame)
    status_layout.setContentsMargins(12, 0, 12, 0)

    status_kw = QLabel("Status:")
    status_kw.setStyleSheet("font-weight: bold; font-size: 11px; color: #ffffff;")
    _indicator = QLabel("●")
    _indicator.setStyleSheet("font-size: 14px; color: gray;")
    status_label = QLabel("Idle")
    status_label.setStyleSheet(f"color: {_TEXT};")

    last_kw = QLabel("Last:")
    last_kw.setStyleSheet("font-weight: bold; font-size: 11px; color: #ffffff;")
    transcript_entry = _make_entry(260)
    transcript_entry.setReadOnly(True)

    status_layout.addWidget(status_kw)
    status_layout.addWidget(_indicator)
    status_layout.addWidget(status_label)
    status_layout.addSpacing(20)
    status_layout.addWidget(last_kw)
    status_layout.addWidget(transcript_entry)
    status_layout.addStretch()

    # Save button (hidden until dirty)
    save_button = QPushButton("Unsaved changes")
    save_button.setStyleSheet("""
        QPushButton {
            background-color: #d97706; color: white;
            border-radius: 999px; padding: 5px 16px;
            font-size: 11px; font-weight: bold;
        }
        QPushButton:hover { background-color: #b45309; }
    """)
    save_button.clicked.connect(_save)
    save_button.setVisible(False)
    status_layout.addWidget(save_button)

    outer_vl.addWidget(status_frame)

    # Wire status_var to label
    def _update_status_label(text: str):
        status_label.setText(text)
        status_var.set(text)
        s = text.lower()
        if "recording" in s:
            _indicator.setStyleSheet("font-size: 14px; color: #e74c3c;")
        elif "listening" in s or "wake" in s:
            _indicator.setStyleSheet("font-size: 14px; color: #2ecc71;")
        elif "processing" in s or "installing" in s or "downloading" in s:
            _indicator.setStyleSheet("font-size: 14px; color: #3498db;")
        else:
            _indicator.setStyleSheet("font-size: 14px; color: gray;")

    status_var._ui_update = _update_status_label
    status_var.trace_add("write", lambda *_: _update_status_label(status_var.get()))

    def _update_transcript_label(text: str):
        transcript_var.set(text)
        transcript_entry.setText(text)

    transcript_var._ui_update = _update_transcript_label
    transcript_var.trace_add("write", lambda *_: transcript_entry.setText(transcript_var.get()))

    # Notice frame (inline error/info bar, hidden by default)
    notice_frame = QWidget()
    notice_frame.setStyleSheet("background-color: #4a1f1f; border-radius: 8px;")
    notice_frame.setVisible(False)
    notice_layout = QHBoxLayout(notice_frame)
    notice_layout.setContentsMargins(10, 6, 10, 6)
    notice_label = QLabel("")
    notice_label.setStyleSheet("color: #ffb4b4; font-size: 11px;")
    notice_label.setWordWrap(True)
    notice_layout.addWidget(notice_label, stretch=1)
    notice_action_button = QPushButton("Action")
    notice_action_button.setStyleSheet(_BTN_SECONDARY)
    notice_action_button.setVisible(False)
    notice_layout.addWidget(notice_action_button)
    notice_close_button = QPushButton("Close")
    notice_close_button.setStyleSheet(_BTN_MUTED)
    notice_close_button.setVisible(False)
    notice_layout.addWidget(notice_close_button)
    outer_vl.addWidget(notice_frame)

    # Update frame (for update available notification)
    update_frame = QWidget()
    update_frame.setStyleSheet("background-color: #4a3a1f; border-radius: 8px;")
    update_frame.setVisible(False)
    update_layout = QHBoxLayout(update_frame)
    update_layout.setContentsMargins(10, 6, 10, 6)
    update_label = QLabel("")
    update_label.setStyleSheet("color: #ffd67d; font-size: 11px;")
    update_label.setWordWrap(True)
    update_layout.addWidget(update_label, stretch=1)
    update_action_button = QPushButton("Check Updates")
    update_action_button.setStyleSheet(_BTN_SECONDARY)
    update_action_button.setVisible(False)
    update_layout.addWidget(update_action_button)
    update_close_button = QPushButton("Close")
    update_close_button.setStyleSheet(_BTN_MUTED)
    update_close_button.setVisible(False)
    update_layout.addWidget(update_close_button)
    outer_vl.addWidget(update_frame)

    # =====================================================================
    # LOADING OVERLAY
    # =====================================================================
    loading_overlay = _OverlayWidget(central)
    loading_overlay.setStyleSheet(f"background-color: #1e1e1e;")
    loading_inner = QWidget(loading_overlay)
    loading_inner.setStyleSheet("background-color: #2b2b2b; border-radius: 18px;")
    loading_inner.setFixedSize(380, 220)
    load_vl = QVBoxLayout(loading_inner)
    load_vl.setAlignment(Qt.AlignCenter)

    load_logo_path = _load_logo()
    if load_logo_path:
        ll_px = QPixmap(load_logo_path)
        if not ll_px.isNull():
            ll_lbl = QLabel()
            ll_lbl.setPixmap(ll_px.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            ll_lbl.setAlignment(Qt.AlignCenter)
            load_vl.addWidget(ll_lbl)

    load_title = QLabel("VERA+" if is_premium() else "VERA")
    load_title.setAlignment(Qt.AlignCenter)
    load_title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {_TITLE_COLOR};")
    load_vl.addWidget(load_title)

    load_sub = QLabel("Loading your workspace...")
    load_sub.setAlignment(Qt.AlignCenter)
    load_sub.setStyleSheet("color: #888888; font-size: 12px;")
    load_vl.addWidget(load_sub)

    loading_progress = QProgressBar()
    loading_progress.setRange(0, 0)  # indeterminate
    loading_progress.setFixedWidth(240)
    loading_progress.setFixedHeight(6)
    loading_progress.setTextVisible(False)
    loading_progress.setStyleSheet(f"""
        QProgressBar {{ background: #444; border-radius: 3px; }}
        QProgressBar::chunk {{ background: {_ACCENT}; border-radius: 3px; }}
    """)
    load_vl.addWidget(loading_progress, alignment=Qt.AlignCenter)

    def _position_loading_inner():
        x = (loading_overlay.width() - loading_inner.width()) // 2
        y = (loading_overlay.height() - loading_inner.height()) // 2
        loading_inner.move(max(0, x), max(0, y))

    loading_overlay.resizeEvent = lambda e: _position_loading_inner()
    loading_overlay.show_over()

    # =====================================================================
    # RECORD OVERLAY
    # =====================================================================
    record_backdrop = _OverlayWidget(central)
    record_backdrop.setStyleSheet("background-color: rgba(17, 24, 39, 180);")

    record_overlay = QWidget(record_backdrop)
    record_overlay.setStyleSheet("background-color: #2a2a2a; border-radius: 14px; border: 1px solid #444444;")
    record_overlay.setFixedWidth(400)

    rec_inner_vl = QVBoxLayout(record_overlay)
    rec_inner_vl.setContentsMargins(18, 16, 18, 16)
    rec_inner_vl.setSpacing(8)

    record_title_label = QLabel("")
    record_title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
    rec_inner_vl.addWidget(record_title_label)

    record_message_label = QLabel("")
    record_message_label.setStyleSheet("font-size: 12px; color: #cccccc;")
    record_message_label.setWordWrap(True)
    rec_inner_vl.addWidget(record_message_label)

    record_status_label = QLabel("Listening for your input...")
    record_status_label.setStyleSheet(f"color: {_MUTED}; font-size: 11px;")
    rec_inner_vl.addWidget(record_status_label)

    record_hint_label = QLabel("Press Esc to cancel.")
    record_hint_label.setStyleSheet("color: #666666; font-size: 11px;")
    rec_inner_vl.addWidget(record_hint_label)
    record_overlay.adjustSize()

    def _position_record_overlay():
        if record_backdrop.width() > 0 and record_backdrop.height() > 0:
            x = (record_backdrop.width() - record_overlay.width()) // 2
            y = (record_backdrop.height() - record_overlay.height()) // 2
            record_overlay.move(max(0, x), max(0, y))

    record_backdrop.resizeEvent = lambda e: _position_record_overlay()

    # =====================================================================
    # RETURN DICT
    # =====================================================================
    return {
        "apps_textbox": apps_textbox,
        "aliases_textbox": aliases_textbox,
        "actions_textbox": actions_textbox,
        "history_textbox": history_textbox,
        "discord_channels_textbox": discord_channels_textbox,
        "discord_servers_textbox": discord_servers_textbox,
        "keybinds_textbox": keybinds_textbox,
        "macros_textbox": macros_textbox,
        "macro_pending_textbox": macro_pending_textbox,
        "tabview": tabs,
        "save_button": save_button,
        "notice_frame": notice_frame,
        "notice_label": notice_label,
        "notice_action_button": notice_action_button,
        "notice_close_button": notice_close_button,
        "update_frame": update_frame,
        "update_label": update_label,
        "update_action_button": update_action_button,
        "update_close_button": update_close_button,
        "loading_overlay": loading_overlay,
        "loading_progress": loading_progress,
        "record_backdrop": record_backdrop,
        "record_overlay": record_overlay,
        "record_title_label": record_title_label,
        "record_message_label": record_message_label,
        "record_status_label": record_status_label,
        "status_label": status_label,
        "transcript_entry": transcript_entry,
    }


def _apply_qt_theme(is_dark: bool):
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QPalette, QColor
    app = QApplication.instance()
    if app is None:
        return
    app.setStyle("Fusion")
    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window,          QColor("#1e1e1e"))
    pal.setColor(QPalette.ColorRole.WindowText,      QColor("#ffffff"))
    pal.setColor(QPalette.ColorRole.Base,            QColor("#2b2b2b"))
    pal.setColor(QPalette.ColorRole.AlternateBase,   QColor("#252525"))
    pal.setColor(QPalette.ColorRole.Text,            QColor("#ffffff"))
    pal.setColor(QPalette.ColorRole.Button,          QColor("#2b2b2b"))
    pal.setColor(QPalette.ColorRole.ButtonText,      QColor("#ffffff"))
    pal.setColor(QPalette.ColorRole.Highlight,       QColor("#2563eb"))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    pal.setColor(QPalette.ColorRole.PlaceholderText, QColor("#888888"))
    app.setPalette(pal)
    app.setStyleSheet("""
        QScrollBar:vertical { background: #2b2b2b; width: 8px; border-radius: 4px; }
        QScrollBar::handle:vertical { background: #555555; border-radius: 4px; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        QToolTip { background: #2b2b2b; color: #ffffff; border: 1px solid #555; }
    """)
