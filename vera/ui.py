"""Main UI layout for VERA (CustomTkinter)."""

from __future__ import annotations

import tkinter as tk
import customtkinter as ctk


# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------
PAD_SECTION = 16
PAD_CARD = 16
PAD_OUTER = 16
CORNER_R = 10
FONT_HEADER = ("Segoe UI", 14, "bold")
FONT_BODY = ("Segoe UI", 12)
FONT_HELP = ("Segoe UI", 11)
COLOR_HELP = ("gray50", "gray60")
COLOR_WARN = ("#cc7700", "#ffaa00")


# ---------------------------------------------------------------------------
# Button helper factories
# ---------------------------------------------------------------------------

def _primary_btn(parent, **kw):
    """Blue primary action button (default CTk accent)."""
    defaults = dict(height=36, corner_radius=8)
    defaults.update(kw)
    return ctk.CTkButton(parent, **defaults)


def _secondary_btn(parent, **kw):
    """Gray secondary action button."""
    defaults = dict(
        fg_color=("gray70", "gray30"),
        hover_color=("gray60", "gray40"),
        height=32,
        corner_radius=6,
    )
    defaults.update(kw)
    return ctk.CTkButton(parent, **defaults)


def _danger_btn(parent, **kw):
    """Red destructive action button."""
    defaults = dict(
        fg_color=("#c0392b", "#c0392b"),
        hover_color=("#a93226", "#a93226"),
        height=32,
        corner_radius=6,
    )
    defaults.update(kw)
    return ctk.CTkButton(parent, **defaults)


def _muted_btn(parent, **kw):
    """Outline-only utility button."""
    defaults = dict(
        fg_color="transparent",
        border_width=1,
        border_color=("gray60", "gray40"),
        text_color=("gray30", "gray70"),
        hover_color=("gray85", "gray25"),
        height=30,
        corner_radius=6,
    )
    defaults.update(kw)
    return ctk.CTkButton(parent, **defaults)


# ---------------------------------------------------------------------------
# Section helpers
# ---------------------------------------------------------------------------

def _section_header(parent, title, help_text=None):
    """Add a bold section title with optional help text."""
    ctk.CTkLabel(parent, text=title, font=FONT_HEADER).pack(
        anchor="w", padx=PAD_OUTER, pady=(PAD_SECTION, 4)
    )
    if help_text:
        ctk.CTkLabel(
            parent, text=help_text, font=FONT_HELP, text_color=COLOR_HELP,
            wraplength=520,
        ).pack(anchor="w", padx=PAD_OUTER, pady=(0, 6))


def _card(parent):
    """Create a styled card frame."""
    frame = ctk.CTkFrame(parent, corner_radius=CORNER_R)
    frame.pack(fill="x", padx=PAD_OUTER - 2, pady=4)
    return frame


def _card_row(card, transparent=True):
    """Create a row inside a card."""
    row = ctk.CTkFrame(card, fg_color="transparent" if transparent else None)
    row.pack(fill="x", padx=PAD_CARD, pady=4)
    return row


def _btn_row(parent):
    """Create a transparent frame for a row of buttons."""
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", padx=PAD_OUTER, pady=(6, PAD_SECTION))
    return row


def _make_scrollable(parent):
    frame = ctk.CTkScrollableFrame(
        parent,
        fg_color="transparent",
        corner_radius=0,
    )
    frame.pack(fill="both", expand=True)
    return frame


def _scroll_canvas(scrollable):
    return getattr(scrollable, "_parent_canvas", None)


def _queue_native_scroll(canvas, delta: int) -> None:
    if canvas is None:
        return
    pending = int(getattr(canvas, "_vera_scroll_pending", 0)) + int(delta)
    canvas._vera_scroll_pending = pending
    if getattr(canvas, "_vera_scroll_scheduled", False):
        return

    canvas._vera_scroll_scheduled = True

    def _flush():
        canvas._vera_scroll_scheduled = False
        pending_delta = int(getattr(canvas, "_vera_scroll_pending", 0))
        canvas._vera_scroll_pending = 0
        if pending_delta == 0:
            return
        direction = -1 if pending_delta > 0 else 1
        steps = max(1, min(8, int(abs(pending_delta) / 120) + 1))
        try:
            canvas.yview_scroll(direction * steps, "units")
        except Exception:
            pass

    canvas.after(12, _flush)


def install_smooth_scrolling(root, *scrollables) -> None:
    registered = list(getattr(root, "_vera_scrollables", []))
    for scrollable in scrollables:
        if scrollable not in registered:
            registered.append(scrollable)
    root._vera_scrollables = registered
    if getattr(root, "_vera_scroll_bound", False):
        return

    def _find_scrollable(widget):
        current = widget
        while current is not None:
            for scrollable in root._vera_scrollables:
                if current is scrollable:
                    return scrollable
            current = getattr(current, "master", None)
        return None

    def _on_mousewheel(event):
        import tkinter as _tk_chk
        widget = root.winfo_containing(event.x_root, event.y_root)
        # If hovering over a Listbox, let it scroll itself — don't hijack
        if isinstance(widget, _tk_chk.Listbox):
            widget.yview_scroll(-1 * (event.delta // 120), "units")
            return "break"
        scrollable = _find_scrollable(widget)
        if scrollable is None:
            return
        canvas = _scroll_canvas(scrollable)
        if canvas is None:
            return "break"
        delta = event.delta
        if delta == 0 and getattr(event, "num", None) == 4:
            delta = 120
        elif delta == 0 and getattr(event, "num", None) == 5:
            delta = -120
        if delta == 0:
            return "break"
        _queue_native_scroll(canvas, delta)
        return "break"

    root.bind_all("<MouseWheel>", _on_mousewheel, add="+")
    root.bind_all("<Button-4>", _on_mousewheel, add="+")
    root.bind_all("<Button-5>", _on_mousewheel, add="+")
    root._vera_scroll_bound = True


# ---------------------------------------------------------------------------
# Main build function
# ---------------------------------------------------------------------------

def build_ui(root, state: dict, callbacks: dict, constants: dict):
    HOTKEY_CHOICES = constants["HOTKEY_CHOICES"]
    LANG_CHOICES = constants["LANG_CHOICES"]

    # -- Unpack state (identical to original) --
    mode = state["mode"]
    language = state["language"]
    seconds = state["seconds"]
    hotkey = state["hotkey"]
    holdkey = state["holdkey"]
    hotkey_display = state["hotkey_display"]
    holdkey_display = state["holdkey_display"]
    search_engine = state["search_engine"]
    confirm_actions = state["confirm_actions"]
    ptt_beep_volume = state["ptt_beep_volume"]
    tts_output_device = state["tts_output_device"]
    tts_device_choices = state["tts_device_choices"]
    tts_voice = state["tts_voice"]
    tts_voice_choices = state["tts_voice_choices"]
    personality_mode = state["personality_mode"]
    spotify_media = state["spotify_media"]
    spotify_requires = state["spotify_requires"]
    spotify_keywords = state["spotify_keywords"]
    status_var = state["status_var"]
    transcript_var = state["transcript_var"]

    app_name_var = state["app_name_var"]
    app_cmd_var = state["app_cmd_var"]
    alias_var = state["alias_var"]
    alias_target_var = state["alias_target_var"]
    phrase_var = state["phrase_var"]
    command_var = state["command_var"]
    discord_ch_name_var = state["discord_ch_name_var"]
    discord_ch_url_var = state["discord_ch_url_var"]
    discord_ch_server_var = state["discord_ch_server_var"]
    discord_srv_nickname_var = state["discord_srv_nickname_var"]
    discord_srv_id_var = state["discord_srv_id_var"]
    discord_bot_token_var = state["discord_bot_token_var"]
    discord_server_id_var = state["discord_server_id_var"]
    gemini_api_key_var = state["gemini_api_key_var"]
    keybind_phrase_var = state["keybind_phrase_var"]
    keybind_key_var = state["keybind_key_var"]
    keybind_count_var = state["keybind_count_var"]

    # -- Unpack callbacks (identical to original) --
    _load_logo = callbacks["load_logo"]
    _save = callbacks["save"]
    _run_now = callbacks["run_now"]
    _install_deps = callbacks["install_deps"]
    _start_background = callbacks["start_background"]
    _stop_background = callbacks["stop_background"]
    _check_for_updates = callbacks["check_for_updates"]
    _create_bug_report = callbacks["create_bug_report"]
    _export_transcripts = callbacks["export_transcripts"]
    _clear_pycache = callbacks["clear_pycache"]
    _create_shortcuts = callbacks["create_shortcuts"]
    _add_app = callbacks["add_app"]
    _remove_app = callbacks["remove_app"]
    _test_app = callbacks["test_app"]
    _import_steam = callbacks["import_steam"]
    _add_alias = callbacks["add_alias"]
    _remove_alias = callbacks["remove_alias"]
    _add_action = callbacks["add_action"]
    _remove_action = callbacks["remove_action"]
    _record_hotkey = callbacks["record_hotkey"]
    _record_hold_key = callbacks["record_hold_key"]
    _add_discord_channel = callbacks["add_discord_channel"]
    _remove_discord_channel = callbacks["remove_discord_channel"]
    _add_discord_server = callbacks["add_discord_server"]
    _remove_discord_server = callbacks["remove_discord_server"]
    _add_keybind = callbacks["add_keybind"]
    _remove_keybind = callbacks["remove_keybind"]
    _record_keybind_key = callbacks["record_keybind_key"]
    _on_mode_change = callbacks["mode_changed"]

    def _toggle_theme():
        new_mode = "dark" if state["theme_var"].get() else "light"
        ctk.set_appearance_mode(new_mode)

    # =====================================================================
    # TABVIEW  (4 tabs)
    # =====================================================================
    tabview = ctk.CTkTabview(root)
    tabview.pack(fill="both", expand=True, padx=10, pady=(10, 0))
    tabview.add("Home")
    tabview.add("Settings")
    tabview.add("Apps")
    tabview.add("Integrations")
    tabview.add("Discord")
    tabview.add("Training")
    tabview.set("Home")

    # =====================================================================
    # HOME TAB
    # =====================================================================
    home_scroll = _make_scrollable(tabview.tab("Home"))

    # -- Logo --
    logo_img = _load_logo()
    if logo_img is not None:
        logo_label = ctk.CTkLabel(home_scroll, image=logo_img, text="", bg_color="transparent")
        logo_label.pack(pady=(10, 2))
        ctk.CTkLabel(home_scroll, text="V  E  R  A", font=("Segoe UI", 24, "bold"), text_color=("#4a7c59", "#a8d5b5"), bg_color="transparent").pack(pady=(0, 6))

    # -- Primary Controls (swap based on mode) --
    _section_header(home_scroll, "Controls")
    ctrl_card = _card(home_scroll)

    # Background controls (hold-to-talk / hotkey modes)
    bg_ctrl_row = _card_row(ctrl_card)
    _primary_btn(bg_ctrl_row, text="Start Listening", command=_start_background,
                 width=160).pack(side="left", padx=4)
    _danger_btn(bg_ctrl_row, text="Stop Listening", command=_stop_background,
                width=140).pack(side="left", padx=4)

    # Timed mic controls
    mic_ctrl_row = _card_row(ctrl_card)
    _primary_btn(mic_ctrl_row, text="Run Now", command=_run_now,
                 width=160).pack(side="left", padx=4)

    def _update_controls(*_args):
        current = mode.get()
        if current == "mic":
            bg_ctrl_row.pack_forget()
            mic_ctrl_row.pack(fill="x", padx=PAD_CARD, pady=4)
        elif current == "wake":
            bg_ctrl_row.pack_forget()
            mic_ctrl_row.pack_forget()
        else:
            mic_ctrl_row.pack_forget()
            bg_ctrl_row.pack(fill="x", padx=PAD_CARD, pady=4)

    mode.trace_add("write", _update_controls)
    _update_controls()

    # -- Transcript History --
    _section_header(home_scroll, "Transcript History",
                    "Recent voice commands you've spoken.")
    history_textbox = ctk.CTkTextbox(home_scroll, height=180, state="disabled",
                                     corner_radius=8)
    history_textbox.pack(fill="x", padx=PAD_OUTER, pady=(0, 10))

    # -- Community --
    _section_header(home_scroll, "Community", "Join the VERA Discord server.")
    community_card = _card(home_scroll)
    community_row = _card_row(community_card)
    _primary_btn(
        community_row,
        text="Join the Discord",
        command=lambda: __import__("webbrowser").open("https://discord.gg/DCdHVEchet"),
        width=160,
    ).pack(side="left", padx=4)

    # =====================================================================
    # SETTINGS TAB
    # =====================================================================
    settings_scroll = _make_scrollable(tabview.tab("Settings"))

    # -- Listening Mode --
    _section_header(settings_scroll, "Listening Mode",
                    "Choose how VERA listens for your voice commands.")
    mode_card = _card(settings_scroll)

    mode_row = _card_row(mode_card)
    ctk.CTkRadioButton(mode_row, text="Hold-to-talk", variable=mode,
                       value="hold", command=_on_mode_change).pack(side="left", padx=(0, 16))
    ctk.CTkRadioButton(mode_row, text="Toggle-to-talk", variable=mode,
                       value="toggle", command=_on_mode_change).pack(side="left", padx=(0, 16))
    ctk.CTkRadioButton(mode_row, text="Wake word", variable=mode,
                       value="wake",
                       command=_on_mode_change).pack(side="left")

    # -- Recording Settings --
    _section_header(settings_scroll, "Recording Settings",
                    "Configure timing, language, and activation keys.")
    rec_card = _card(settings_scroll)

    rec_r1 = _card_row(rec_card)
    ctk.CTkLabel(rec_r1, text="Seconds", width=120).pack(side="left")
    ctk.CTkEntry(rec_r1, textvariable=seconds, width=80).pack(
        side="left", padx=(0, 20))
    ctk.CTkLabel(rec_r1, text="Language", width=80).pack(side="left")
    ctk.CTkOptionMenu(rec_r1, variable=language, values=LANG_CHOICES,
                      width=140).pack(side="left")

    rec_r2 = _card_row(rec_card)
    ctk.CTkLabel(rec_r2, text="Toggle key", width=120).pack(side="left")
    ctk.CTkEntry(rec_r2, textvariable=hotkey_display, width=160).pack(
        side="left", padx=(0, 10))
    _secondary_btn(rec_r2, text="Record",
                   command=lambda: _record_hotkey(hotkey),
                   width=90).pack(side="left")

    rec_r3 = _card_row(rec_card)
    ctk.CTkLabel(rec_r3, text="Hold key", width=120).pack(side="left")
    ctk.CTkEntry(rec_r3, textvariable=holdkey_display, width=160).pack(
        side="left", padx=(0, 10))
    _secondary_btn(rec_r3, text="Record",
                   command=lambda: _record_hold_key(holdkey),
                   width=90).pack(side="left")

    rec_r4 = _card_row(rec_card)
    ctk.CTkLabel(rec_r4, text="Search Engine", width=120).pack(side="left")
    ctk.CTkEntry(rec_r4, textvariable=search_engine, width=340).pack(
        side="left")

    rec_r5 = _card_row(rec_card)
    ctk.CTkLabel(rec_r5, text="Beep Volume", width=120).pack(side="left")
    beep_vol_label = ctk.CTkLabel(rec_r5, text=f"{ptt_beep_volume.get()}%", width=40)
    ctk.CTkSlider(rec_r5, from_=0, to=100, number_of_steps=100,
                  variable=ptt_beep_volume,
                  command=lambda v: beep_vol_label.configure(text=f"{int(v)}%"),
                  width=200).pack(side="left", padx=(0, 8))
    beep_vol_label.pack(side="left")

    rec_r6 = _card_row(rec_card)
    ctk.CTkLabel(rec_r6, text="Voice Output", width=120).pack(side="left")
    ctk.CTkOptionMenu(rec_r6, variable=tts_output_device,
                      values=tts_device_choices, width=260).pack(side="left")
    ctk.CTkLabel(rec_r6, text="  Select your virtual mic (e.g. VB-Cable) to route TTS to Discord",
                 font=FONT_HELP, text_color=COLOR_HELP).pack(side="left", padx=(8, 0))

    rec_r7 = _card_row(rec_card)
    ctk.CTkLabel(rec_r7, text="Voice", width=120).pack(side="left")
    ctk.CTkOptionMenu(rec_r7, variable=tts_voice,
                      values=tts_voice_choices, width=160).pack(side="left")
    ctk.CTkLabel(rec_r7, text="  Choose VERA's voice (takes effect immediately)",
                 font=FONT_HELP, text_color=COLOR_HELP).pack(side="left", padx=(8, 0))

    # -- General Options --
    _section_header(settings_scroll, "General Options")
    opt_card = _card(settings_scroll)

    ctk.CTkCheckBox(opt_card, text="Confirm before running actions",
                    variable=confirm_actions).pack(
        anchor="w", padx=PAD_CARD, pady=(10, 4))
    ctk.CTkCheckBox(opt_card, text="Dark mode", variable=state["theme_var"],
                    command=_toggle_theme).pack(
        anchor="w", padx=PAD_CARD, pady=(4, 10))

    # -- Personality --
    _section_header(settings_scroll, "Personality",
                    "Choose how VERA speaks to you.")
    personality_card = _card(settings_scroll)
    personality_row = _card_row(personality_card)
    ctk.CTkLabel(personality_row, text="Mode", width=120).pack(side="left")
    try:
        from license import is_premium as _is_premium
        _premium = _is_premium()
    except Exception:
        _premium = False
    if _premium:
        ctk.CTkOptionMenu(
            personality_row,
            variable=personality_mode,
            values=["default", "professional", "offensive"],
            width=160,
        ).pack(side="left")
    else:
        ctk.CTkOptionMenu(
            personality_row,
            variable=personality_mode,
            values=["default", "professional"],
            width=160,
        ).pack(side="left")
        ctk.CTkLabel(
            personality_row,
            text="  Offensive mode requires a Premium license",
            font=FONT_HELP,
            text_color=COLOR_HELP,
        ).pack(side="left", padx=(8, 0))

    # -- Spotify --
    _section_header(settings_scroll, "Spotify",
                    "Control Spotify playback with voice commands like "
                    "'play', 'pause', 'next'.")
    spot_card = _card(settings_scroll)

    ctk.CTkCheckBox(spot_card, text="Enable Spotify media controls",
                    variable=spotify_media).pack(
        anchor="w", padx=PAD_CARD, pady=(10, 4))
    ctk.CTkCheckBox(spot_card, text="Require word 'spotify' in command",
                    variable=spotify_requires).pack(
        anchor="w", padx=PAD_CARD, pady=4)

    spot_kw_row = _card_row(spot_card)
    ctk.CTkLabel(spot_kw_row, text="Spotify keywords").pack(side="left")
    ctk.CTkEntry(spot_kw_row, textvariable=spotify_keywords,
                 width=240).pack(side="left", padx=(10, 0))

    # -- News --
    _section_header(settings_scroll, "News",
                    "Choose your preferred news source for 'give me the news'.")
    news_source = state["news_source"]
    news_card = _card(settings_scroll)
    news_row = _card_row(news_card)
    ctk.CTkLabel(news_row, text="Source", width=120).pack(side="left")
    ctk.CTkOptionMenu(
        news_row,
        variable=news_source,
        values=["BBC", "Reuters", "NPR", "AP News", "The Guardian", "Al Jazeera"],
        width=160,
    ).pack(side="left")

    # -- Birthday --
    _section_header(settings_scroll, "Birthday",
                    "VERA will wish you happy birthday on startup. "
                    "You can also say 'my birthday is October 15th'.")
    birthday_month = state["birthday_month"]
    birthday_day = state["birthday_day"]
    bday_card = _card(settings_scroll)
    bday_row = _card_row(bday_card)
    ctk.CTkLabel(bday_row, text="Month", width=80).pack(side="left")
    ctk.CTkOptionMenu(
        bday_row,
        variable=birthday_month,
        values=["", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"],
        width=80,
    ).pack(side="left", padx=(0, 16))
    ctk.CTkLabel(bday_row, text="Day", width=40).pack(side="left")
    ctk.CTkOptionMenu(
        bday_row,
        variable=birthday_day,
        values=[""] + [str(d) for d in range(1, 32)],
        width=80,
    ).pack(side="left")
    ctk.CTkLabel(bday_row, text="  Leave blank to disable",
                 font=FONT_HELP, text_color=COLOR_HELP).pack(side="left", padx=(12, 0))

    # -- Utilities --
    _section_header(settings_scroll, "Utilities")
    util_card = _card(settings_scroll)

    util_row1 = _card_row(util_card)
    _secondary_btn(util_row1, text="Check Updates", command=_check_for_updates,
                   width=130).pack(side="left", padx=4)
    _secondary_btn(util_row1, text="Install Deps", command=_install_deps,
                   width=130).pack(side="left", padx=4)

    util_row2 = _card_row(util_card)
    _muted_btn(util_row2, text="Bug Report", command=_create_bug_report,
               width=130).pack(side="left", padx=4)
    _muted_btn(util_row2, text="Export Transcripts", command=_export_transcripts,
               width=150).pack(side="left", padx=4)
    _danger_btn(util_row2, text="Delete Cache", command=_clear_pycache,
                width=130).pack(side="left", padx=4)

    util_row3 = _card_row(util_card)
    _secondary_btn(util_row3, text="Add Desktop Shortcut", command=_create_shortcuts,
                   width=180).pack(side="left", padx=4)

    # =====================================================================
    # APPS TAB
    # =====================================================================
    apps_scroll = _make_scrollable(tabview.tab("Apps"))

    # -- Registered Apps --
    _section_header(apps_scroll, "Registered Apps",
                    "Say 'open <app name>' to launch an app. "
                    "Add them manually or import from Steam.")

    import tkinter as _tk_apps
    apps_frame = ctk.CTkFrame(apps_scroll, corner_radius=8)
    apps_frame.pack(fill="x", padx=PAD_OUTER, pady=(2, 2))
    apps_textbox = _tk_apps.Listbox(
        apps_frame,
        height=6,
        selectmode="single",
        activestyle="none",
        exportselection=False,
        bg="#262626",
        fg="white",
        selectbackground="#2563eb",
        selectforeground="white",
        relief="flat",
        borderwidth=0,
        highlightthickness=1,
        highlightbackground="#404040",
        highlightcolor="#2563eb",
        font=("Segoe UI Semibold", 11),
    )
    apps_textbox.pack(fill="x", padx=8, pady=8)
    def _apps_scroll(e):
        apps_textbox.yview_scroll(-1 * (e.delta // 120), "units")
        return "break"
    apps_textbox.bind("<MouseWheel>", _apps_scroll)

    app_input_card = _card(apps_scroll)

    app_r1 = _card_row(app_input_card)
    ctk.CTkLabel(app_r1, text="App name", width=100).pack(side="left")
    ctk.CTkEntry(app_r1, textvariable=app_name_var, width=240,
                 placeholder_text="e.g. notepad").pack(
        side="left", padx=(0, 10))

    app_r2 = _card_row(app_input_card)
    ctk.CTkLabel(app_r2, text="App command", width=100).pack(side="left")
    ctk.CTkEntry(app_r2, textvariable=app_cmd_var, width=240,
                 placeholder_text="e.g. notepad.exe").pack(
        side="left", padx=(0, 10))

    app_btns = _btn_row(apps_scroll)
    _primary_btn(app_btns, text="Add App", command=_add_app,
                 width=110).pack(side="left", padx=4)
    _secondary_btn(app_btns, text="Test App", command=_test_app,
                   width=110).pack(side="left", padx=4)
    _secondary_btn(app_btns, text="Import Steam", command=_import_steam,
                   width=110).pack(side="left", padx=4)
    _danger_btn(app_btns, text="Remove Selected", command=_remove_app,
                width=130).pack(side="right", padx=4)

    # -- App Aliases --
    _section_header(apps_scroll, "App Aliases",
                    "Create shortcuts \u2014 say the alias to launch "
                    "the target app.")

    import tkinter as _tk_alias
    aliases_frame = ctk.CTkFrame(apps_scroll, corner_radius=8)
    aliases_frame.pack(fill="x", padx=PAD_OUTER, pady=(2, 2))
    aliases_textbox = _tk_alias.Listbox(
        aliases_frame,
        height=4,
        selectmode="single",
        activestyle="none",
        exportselection=False,
        bg="#262626",
        fg="white",
        selectbackground="#2563eb",
        selectforeground="white",
        relief="flat",
        borderwidth=0,
        highlightthickness=1,
        highlightbackground="#404040",
        highlightcolor="#2563eb",
        font=("Segoe UI Semibold", 11),
    )
    aliases_textbox.pack(fill="x", padx=8, pady=8)
    def _alias_scroll(e):
        aliases_textbox.yview_scroll(-1 * (e.delta // 120), "units")
        return "break"
    aliases_textbox.bind("<MouseWheel>", _alias_scroll)

    alias_input_card = _card(apps_scroll)

    alias_r1 = _card_row(alias_input_card)
    ctk.CTkLabel(alias_r1, text="Alias", width=100).pack(side="left")
    ctk.CTkEntry(alias_r1, textvariable=alias_var, width=240,
                 placeholder_text="e.g. browser").pack(
        side="left", padx=(0, 10))

    alias_r2 = _card_row(alias_input_card)
    ctk.CTkLabel(alias_r2, text="Target app", width=100).pack(side="left")
    ctk.CTkEntry(alias_r2, textvariable=alias_target_var, width=240,
                 placeholder_text="e.g. chrome").pack(
        side="left", padx=(0, 10))

    alias_btns = _btn_row(apps_scroll)
    _primary_btn(alias_btns, text="Add Alias", command=_add_alias,
                 width=110).pack(side="left", padx=4)
    _danger_btn(alias_btns, text="Remove Selected", command=_remove_alias,
                width=130).pack(side="right", padx=4)

    # =====================================================================
    # INTEGRATIONS TAB
    # =====================================================================
    integ_scroll = _make_scrollable(tabview.tab("Integrations"))

    # -- AI (Groq) --
    _section_header(
        integ_scroll,
        "AI Assistant",
        "Use `ask <question>` to query AI.\nGet your free key at console.groq.com -> API Keys.",
    )
    ai_card = _card(integ_scroll)

    ai_row = _card_row(ai_card)
    ctk.CTkLabel(ai_row, text="API Key", width=120).pack(side="left")
    ctk.CTkEntry(ai_row, textvariable=gemini_api_key_var, width=320,
                 show="*",
                 placeholder_text="Groq API key").pack(
        side="left", padx=(0, 10))

    # -- Voice Actions --
    _section_header(
        integ_scroll,
        "Voice Actions",
        "Map a spoken phrase to a shell command.\nExample: `lock my computer` -> `rundll32.exe user32.dll,LockWorkStation`",
    )

    import tkinter as _tk_act
    actions_frame = ctk.CTkFrame(integ_scroll, corner_radius=8)
    actions_frame.pack(fill="x", padx=PAD_OUTER, pady=(2, 2))
    actions_textbox = _tk_act.Listbox(
        actions_frame,
        height=6,
        selectmode="single",
        activestyle="none",
        exportselection=False,
        bg="#262626",
        fg="white",
        selectbackground="#2563eb",
        selectforeground="white",
        relief="flat",
        borderwidth=0,
        highlightthickness=1,
        highlightbackground="#404040",
        highlightcolor="#2563eb",
        font=("Segoe UI Semibold", 11),
    )
    actions_textbox.pack(fill="x", padx=8, pady=8)

    action_input_card = _card(integ_scroll)
    action_input_card.pack_configure(pady=(2, 4))

    act_r1 = _card_row(action_input_card)
    ctk.CTkLabel(act_r1, text="Phrase", width=100).pack(side="left")
    ctk.CTkEntry(act_r1, textvariable=phrase_var, width=300,
                 placeholder_text="e.g. lock my computer").pack(
        side="left", padx=(0, 10))

    act_r2 = _card_row(action_input_card)
    ctk.CTkLabel(act_r2, text="Command", width=100).pack(side="left")
    ctk.CTkEntry(
        act_r2, textvariable=command_var, width=300,
        placeholder_text="e.g. rundll32.exe user32.dll,LockWorkStation"
    ).pack(side="left", padx=(0, 10))

    action_btns = _btn_row(integ_scroll)
    action_btns.pack_configure(pady=(4, PAD_SECTION))
    _primary_btn(action_btns, text="Add Action", command=_add_action,
                 width=130).pack(side="left", padx=4)
    _danger_btn(action_btns, text="Remove Selected", command=_remove_action,
                width=130).pack(side="right", padx=4)

    # -- Key Binds --
    _section_header(integ_scroll, "Key Binds",
                    "Say a phrase to press a key (e.g. 'reload' \u2192 r).")
    ctk.CTkLabel(
        integ_scroll,
        text="\u26a0 Do not use in games protected by EAC or BattlEye "
             "\u2014 synthetic input may be flagged.",
        text_color=COLOR_WARN,
        font=FONT_HELP,
        wraplength=520,
    ).pack(anchor="w", padx=PAD_OUTER, pady=(0, 4))

    import tkinter as _tk_kb
    keybinds_frame = ctk.CTkFrame(integ_scroll, corner_radius=8)
    keybinds_frame.pack(fill="x", padx=PAD_OUTER, pady=(2, 2))
    keybinds_textbox = _tk_kb.Listbox(
        keybinds_frame,
        height=6,
        selectmode="single",
        activestyle="none",
        exportselection=False,
        bg="#262626",
        fg="white",
        selectbackground="#2563eb",
        selectforeground="white",
        relief="flat",
        borderwidth=0,
        highlightthickness=1,
        highlightbackground="#404040",
        highlightcolor="#2563eb",
        font=("Segoe UI Semibold", 11),
    )
    keybinds_textbox.pack(fill="x", padx=8, pady=8)

    kb_input_card = _card(integ_scroll)
    kb_input_card.pack_configure(pady=(2, 4))

    kb_r1 = _card_row(kb_input_card)
    ctk.CTkLabel(kb_r1, text="Phrase", width=100).pack(side="left")
    ctk.CTkEntry(kb_r1, textvariable=keybind_phrase_var, width=240,
                 placeholder_text="e.g. reload").pack(
        side="left", padx=(0, 10))

    kb_r2 = _card_row(kb_input_card)
    ctk.CTkLabel(kb_r2, text="Key", width=100).pack(side="left")
    ctk.CTkEntry(kb_r2, textvariable=keybind_key_var, width=180,
                 placeholder_text="e.g. alt+n or x1 > q").pack(side="left", padx=(0, 10))
    _secondary_btn(
        kb_r2, text="+ Step",
        command=lambda: _record_keybind_key(keybind_key_var),
        width=90
    ).pack(side="left")

    kb_r3 = _card_row(kb_input_card)
    ctk.CTkLabel(kb_r3, text="Count", width=100).pack(side="left")
    ctk.CTkEntry(kb_r3, textvariable=keybind_count_var, width=60,
                 placeholder_text="1").pack(side="left", padx=(0, 10))
    ctk.CTkLabel(kb_r3, text="(how many times to press)",
                 text_color=COLOR_HELP).pack(side="left")

    kb_btns = _btn_row(integ_scroll)
    kb_btns.pack_configure(pady=(4, PAD_SECTION))
    _primary_btn(kb_btns, text="Add Key Bind", command=_add_keybind,
                 width=130).pack(side="left", padx=4)
    _danger_btn(kb_btns, text="Remove Selected", command=_remove_keybind,
                width=130).pack(side="right", padx=4)

    # =====================================================================
    # DISCORD TAB
    # =====================================================================
    discord_scroll = _make_scrollable(tabview.tab("Discord"))

    # -- Bot Credentials --
    _section_header(
        discord_scroll,
        "Bot Credentials",
        "Required for `read discord`.\nGet your bot token from discord.dev.",
    )
    creds_card = _card(discord_scroll)

    creds_r1 = _card_row(creds_card)
    ctk.CTkLabel(creds_r1, text="Bot Token", width=120).pack(side="left")
    ctk.CTkEntry(creds_r1, textvariable=discord_bot_token_var, width=320,
                 show="*",
                 placeholder_text="Bot token from Discord Developer Portal"
                 ).pack(side="left", padx=(0, 10))

    creds_r2 = _card_row(creds_card)
    ctk.CTkLabel(creds_r2, text="Default Server ID", width=120).pack(side="left")
    ctk.CTkEntry(creds_r2, textvariable=discord_server_id_var, width=220,
                 placeholder_text="Right-click server \u2192 Copy Server ID"
                 ).pack(side="left", padx=(0, 10))

    # -- Servers --
    _section_header(
        discord_scroll,
        "Servers",
        "Add servers with a nickname.\nExample: `discord <nickname> <channel> <message>`",
    )

    import tkinter as _tk_disc
    discord_servers_frame = ctk.CTkFrame(discord_scroll, corner_radius=8)
    discord_servers_frame.pack(fill="x", padx=PAD_OUTER, pady=(2, 2))
    discord_servers_textbox = _tk_disc.Listbox(
        discord_servers_frame,
        height=4,
        selectmode="single",
        activestyle="none",
        exportselection=False,
        bg="#262626",
        fg="white",
        selectbackground="#2563eb",
        selectforeground="white",
        relief="flat",
        borderwidth=0,
        highlightthickness=1,
        highlightbackground="#404040",
        highlightcolor="#2563eb",
        font=("Segoe UI Semibold", 11),
    )
    discord_servers_textbox.pack(fill="x", padx=8, pady=8)

    srv_input_card = _card(discord_scroll)
    srv_input_card.pack_configure(pady=(2, 4))
    srv_r1 = _card_row(srv_input_card)
    ctk.CTkLabel(srv_r1, text="Nickname", width=120).pack(side="left")
    ctk.CTkEntry(srv_r1, textvariable=discord_srv_nickname_var, width=160,
                 placeholder_text="e.g. baddie").pack(side="left", padx=(0, 10))

    srv_r2 = _card_row(srv_input_card)
    ctk.CTkLabel(srv_r2, text="Server ID", width=120).pack(side="left")
    ctk.CTkEntry(srv_r2, textvariable=discord_srv_id_var, width=220,
                 placeholder_text="Right-click server \u2192 Copy Server ID"
                 ).pack(side="left", padx=(0, 10))

    srv_btns = _btn_row(discord_scroll)
    srv_btns.pack_configure(pady=(4, PAD_SECTION))
    _primary_btn(srv_btns, text="Add Server", command=_add_discord_server, width=120).pack(side="left", padx=4)
    _danger_btn(srv_btns, text="Remove Selected", command=_remove_discord_server, width=140).pack(side="left", padx=4)

    # -- Channels --
    _section_header(
        discord_scroll,
        "Channels",
        "Webhook channels.\nOptionally tag a server so `discord <server> <channel>` works.",
    )

    discord_channels_frame = ctk.CTkFrame(discord_scroll, corner_radius=8)
    discord_channels_frame.pack(fill="x", padx=PAD_OUTER, pady=(2, 2))
    discord_channels_textbox = _tk_disc.Listbox(
        discord_channels_frame,
        height=5,
        selectmode="single",
        activestyle="none",
        exportselection=False,
        bg="#262626",
        fg="white",
        selectbackground="#2563eb",
        selectforeground="white",
        relief="flat",
        borderwidth=0,
        highlightthickness=1,
        highlightbackground="#404040",
        highlightcolor="#2563eb",
        font=("Segoe UI Semibold", 11),
    )
    discord_channels_textbox.pack(fill="x", padx=8, pady=8)

    ch_input_card = _card(discord_scroll)
    ch_input_card.pack_configure(pady=(2, 4))
    ch_r1 = _card_row(ch_input_card)
    ctk.CTkLabel(ch_r1, text="Channel name", width=120).pack(side="left")
    ctk.CTkEntry(ch_r1, textvariable=discord_ch_name_var, width=180,
                 placeholder_text="e.g. general").pack(side="left", padx=(0, 10))

    ch_r2 = _card_row(ch_input_card)
    ctk.CTkLabel(ch_r2, text="Server nickname", width=120).pack(side="left")
    ctk.CTkEntry(ch_r2, textvariable=discord_ch_server_var, width=180,
                 placeholder_text="optional — e.g. baddie").pack(side="left", padx=(0, 10))

    ch_r3 = _card_row(ch_input_card)
    ctk.CTkLabel(ch_r3, text="Webhook URL", width=120).pack(side="left")
    ctk.CTkEntry(ch_r3, textvariable=discord_ch_url_var, width=320,
                 placeholder_text="https://discord.com/api/webhooks/..."
                 ).pack(side="left", padx=(0, 10))

    ch_btns = _btn_row(discord_scroll)
    ch_btns.pack_configure(pady=(4, PAD_SECTION))
    _primary_btn(ch_btns, text="Add Channel", command=_add_discord_channel, width=120).pack(side="left", padx=4)
    _danger_btn(ch_btns, text="Remove Selected", command=_remove_discord_channel, width=140).pack(side="left", padx=4)

    ctk.CTkLabel(
        discord_scroll,
        text=(
            "Commands\n"
            "discord <channel> <message>\n"
            "discord <server> <channel> <message>\n"
            "read discord <server> <channel>"
        ),
        font=FONT_HELP,
        text_color=COLOR_HELP,
        justify="left",
        wraplength=560,
    ).pack(anchor="w", padx=PAD_OUTER, pady=(8, 0))

    # =====================================================================
    # TRAINING TAB
    # =====================================================================
    from skills import load_unmatched, save_user_mishear, dismiss_unmatched, load_groq_handled, dismiss_groq_handled

    training_scroll = _make_scrollable(tabview.tab("Training"))

    _section_header(training_scroll, "Mishear Training",
                    "Transcripts VERA didn't understand. Select one, type what you meant, and save.")

    # List frame
    unmatched_list_frame = ctk.CTkFrame(training_scroll, corner_radius=8)
    unmatched_list_frame.pack(fill="x", padx=PAD_OUTER, pady=(2, 4))

    unmatched_listbox_var = tk.StringVar(value=[])
    unmatched_listbox = tk.Listbox(
        unmatched_list_frame,
        listvariable=unmatched_listbox_var,
        height=8,
        selectmode="single",
        font=("Segoe UI Semibold", 11),
        activestyle="none",
        exportselection=False,
        bg="#262626",
        fg="white",
        selectbackground="#2563eb",
        selectforeground="white",
        relief="flat",
        borderwidth=0,
        highlightthickness=1,
        highlightbackground="#404040",
        highlightcolor="#2563eb",
    )
    unmatched_listbox.pack(fill="both", expand=True, padx=8, pady=8)

    _selected_mishear = [None]  # mutable container so closures can write to it

    def _refresh_unmatched():
        entries = load_unmatched()
        unmatched_listbox_var.set(entries)

    _refresh_unmatched()

    def _on_unmatched_select(event=None):
        sel = unmatched_listbox.curselection()
        if sel:
            text = unmatched_listbox.get(sel[0])
            _selected_mishear[0] = text
            correction_entry.delete(0, "end")
            correction_entry.insert(0, text)

    unmatched_listbox.bind("<<ListboxSelect>>", _on_unmatched_select)

    # Correction row
    correction_frame = ctk.CTkFrame(training_scroll, fg_color="transparent")
    correction_frame.pack(fill="x", padx=PAD_OUTER, pady=(0, 2))

    ctk.CTkLabel(correction_frame, text="Correct to:", font=FONT_BODY).pack(side="left", padx=(0, 8))
    correction_entry = ctk.CTkEntry(correction_frame, placeholder_text="what you actually said", width=260)
    correction_entry.pack(side="left", fill="x", expand=True)

    def _save_correction():
        mishear = _selected_mishear[0]
        if not mishear:
            return
        correction = correction_entry.get().strip()
        if not correction:
            return
        save_user_mishear(mishear, correction)
        dismiss_unmatched(mishear)
        _selected_mishear[0] = None
        correction_entry.delete(0, "end")
        _refresh_unmatched()

    def _dismiss_selected():
        mishear = _selected_mishear[0]
        if not mishear:
            return
        dismiss_unmatched(mishear)
        _selected_mishear[0] = None
        correction_entry.delete(0, "end")
        _refresh_unmatched()

    btn_row = _btn_row(training_scroll)
    _primary_btn(btn_row, text="Save Correction", command=_save_correction, width=140).pack(side="left", padx=4)
    _secondary_btn(btn_row, text="Dismiss", command=_dismiss_selected, width=100).pack(side="left", padx=4)
    _muted_btn(btn_row, text="Refresh", command=_refresh_unmatched, width=90).pack(side="left", padx=4)

    ctk.CTkLabel(training_scroll,
                 text="Saved corrections take effect immediately — no restart needed.",
                 font=FONT_HELP, text_color=COLOR_HELP).pack(anchor="w", padx=PAD_OUTER, pady=(4, 0))

    # -- Groq Handled --
    _section_header(training_scroll, "Groq Handled",
                    "Things VERA answered via AI that could become real skills. "
                    "Use these to spot patterns worth adding as commands.")

    groq_list_frame = ctk.CTkFrame(training_scroll, corner_radius=8)
    groq_list_frame.pack(fill="x", padx=PAD_OUTER, pady=(2, 4))

    groq_listbox = tk.Listbox(
        groq_list_frame,
        height=8,
        selectmode="single",
        activestyle="none",
        exportselection=False,
        bg="#262626",
        fg="white",
        selectbackground="#2563eb",
        selectforeground="white",
        relief="flat",
        borderwidth=0,
        highlightthickness=1,
        highlightbackground="#404040",
        highlightcolor="#2563eb",
        font=("Segoe UI Semibold", 11),
    )
    groq_listbox.pack(fill="x", padx=8, pady=8)
    groq_listbox.bind("<MouseWheel>", lambda e: (groq_listbox.yview_scroll(-1 * (e.delta // 120), "units"), "break")[1])

    _selected_groq = [None]

    def _refresh_groq_handled():
        entries = load_groq_handled()
        groq_listbox.delete(0, "end")
        for e in entries:
            groq_listbox.insert("end", e)

    _refresh_groq_handled()

    def _on_groq_select(event=None):
        sel = groq_listbox.curselection()
        if sel:
            _selected_groq[0] = groq_listbox.get(sel[0])

    groq_listbox.bind("<<ListboxSelect>>", _on_groq_select)

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

    groq_btn_row = _btn_row(training_scroll)
    _secondary_btn(groq_btn_row, text="Dismiss Selected", command=_dismiss_groq, width=140).pack(side="left", padx=4)
    _danger_btn(groq_btn_row, text="Clear All", command=_clear_all_groq, width=100).pack(side="left", padx=4)
    _muted_btn(groq_btn_row, text="Refresh", command=_refresh_groq_handled, width=90).pack(side="left", padx=4)

    # =====================================================================
    # STATUS BAR  (persistent, outside tabview)
    # =====================================================================
    status_frame = ctk.CTkFrame(root)
    status_frame.pack(fill="x", padx=10, pady=(4, 10))
    status_frame.grid_columnconfigure(0, weight=1)
    status_frame.grid_columnconfigure(1, weight=0)
    status_left = ctk.CTkFrame(status_frame, fg_color="transparent")
    status_left.grid(row=0, column=0, sticky="ew", padx=12, pady=8)
    ctk.CTkLabel(status_left, text="Status:",
                 font=("Segoe UI", 11, "bold")).pack(side="left")

    # Indicator dot — color reflects current state
    _indicator = ctk.CTkLabel(status_left, text="●", font=("Segoe UI", 14), text_color="gray")
    _indicator.pack(side="left", padx=(8, 4))

    def _update_indicator(status: str):
        s = status.lower()
        if "recording" in s:
            _indicator.configure(text_color="#e74c3c")   # red — mic is hot
        elif "listening" in s or "wake" in s:
            _indicator.configure(text_color="#2ecc71")   # green — active
        elif "processing" in s or "installing" in s or "downloading" in s:
            _indicator.configure(text_color="#3498db")   # blue — busy
        else:
            _indicator.configure(text_color="gray")      # idle

    status_var.trace_add("write", lambda *_: _update_indicator(status_var.get()))

    ctk.CTkLabel(status_left, textvariable=status_var).pack(
        side="left", padx=(4, 20))
    ctk.CTkLabel(status_left, text="Last:",
                 font=("Segoe UI", 11, "bold")).pack(side="left")
    ctk.CTkEntry(status_left, textvariable=transcript_var,
                 width=260).pack(side="left", padx=(8, 0))
    save_button = ctk.CTkButton(
        status_frame,
        text="Unsaved changes",
        command=_save,
        width=150,
        height=32,
        corner_radius=999,
        fg_color=("#d97706", "#d97706"),
        hover_color=("#b45309", "#b45309"),
        font=("Segoe UI", 11, "bold"),
    )
    notice_frame = ctk.CTkFrame(status_frame, corner_radius=8, fg_color=("#fdecea", "#4a1f1f"))
    notice_content = ctk.CTkFrame(notice_frame, fg_color="transparent")
    notice_content.pack(fill="x", padx=10, pady=8)
    notice_label = ctk.CTkLabel(
        notice_content,
        text="",
        anchor="w",
        justify="left",
        text_color=("#8a1c1c", "#ffb4b4"),
        wraplength=500,
        font=("Segoe UI", 11),
    )
    notice_label.pack(side="left", fill="x", expand=True)
    notice_action_button = ctk.CTkButton(notice_content, text="Action", width=120, height=28)
    notice_close_button = ctk.CTkButton(notice_content, text="Close", width=84, height=28)
    update_frame = ctk.CTkFrame(status_frame, corner_radius=8, fg_color=("#fff4db", "#4a3a1f"))
    update_content = ctk.CTkFrame(update_frame, fg_color="transparent")
    update_content.pack(fill="x", padx=10, pady=8)
    update_label = ctk.CTkLabel(
        update_content,
        text="",
        anchor="w",
        justify="left",
        text_color=("#8a6116", "#ffd67d"),
        wraplength=500,
        font=("Segoe UI", 11),
    )
    update_label.pack(side="left", fill="x", expand=True)
    update_action_button = ctk.CTkButton(update_content, text="Check Updates", width=120, height=28)
    update_close_button = ctk.CTkButton(update_content, text="Close", width=84, height=28)

    loading_overlay = ctk.CTkFrame(root, corner_radius=0, fg_color=("gray96", "gray12"))
    loading_card = ctk.CTkFrame(loading_overlay, corner_radius=18, fg_color=("gray92", "gray18"))
    loading_card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.72, relheight=0.48)
    loading_logo = _load_logo()
    if loading_logo is not None:
        loading_logo_label = ctk.CTkLabel(loading_card, image=loading_logo, text="")
        loading_logo_label.pack(pady=(22, 4))
    else:
        loading_logo_label = None
    ctk.CTkLabel(
        loading_card,
        text="VERA",
        font=("Segoe UI", 24, "bold"),
    ).pack(pady=(0, 6))
    ctk.CTkLabel(
        loading_card,
        text="Loading your workspace...",
        font=("Segoe UI", 12),
        text_color=COLOR_HELP,
    ).pack()
    loading_progress = ctk.CTkProgressBar(loading_card, mode="indeterminate", width=240)
    loading_progress.pack(pady=(18, 10))
    loading_progress.start()
    loading_overlay.place_forget()

    record_backdrop = ctk.CTkFrame(
        root,
        corner_radius=0,
        fg_color=("#f3f4f6", "#111827"),
    )
    record_overlay = ctk.CTkFrame(
        record_backdrop,
        corner_radius=14,
        border_width=1,
        border_color=("gray70", "gray30"),
        fg_color=("gray95", "gray18"),
    )
    record_overlay.grid_columnconfigure(0, weight=1)
    record_title_label = ctk.CTkLabel(
        record_overlay,
        text="",
        anchor="w",
        justify="left",
        font=("Segoe UI", 16, "bold"),
    )
    record_title_label.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 6))
    record_message_label = ctk.CTkLabel(
        record_overlay,
        text="",
        anchor="w",
        justify="left",
        wraplength=340,
        font=("Segoe UI", 12),
    )
    record_message_label.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 10))
    record_status_label = ctk.CTkLabel(
        record_overlay,
        text="Listening for your input...",
        anchor="w",
        justify="left",
        text_color=("gray40", "gray75"),
        font=("Segoe UI", 11),
    )
    record_status_label.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 6))
    record_hint_label = ctk.CTkLabel(
        record_overlay,
        text="Press Esc to cancel.",
        anchor="w",
        justify="left",
        text_color=("gray50", "gray65"),
        font=("Segoe UI", 11),
    )
    record_hint_label.grid(row=3, column=0, sticky="ew", padx=18, pady=(0, 16))
    record_overlay.pack(expand=True)
    record_backdrop.place_forget()
    record_overlay.place_forget()

    install_smooth_scrolling(
        root,
        home_scroll,
        settings_scroll,
        apps_scroll,
        integ_scroll,
        discord_scroll,
        training_scroll,
    )

    # =====================================================================
    # RETURN DICT  (identical keys to original)
    # =====================================================================
    return {
        "apps_textbox": apps_textbox,
        "aliases_textbox": aliases_textbox,
        "actions_textbox": actions_textbox,
        "history_textbox": history_textbox,
        "discord_channels_textbox": discord_channels_textbox,
        "discord_servers_textbox": discord_servers_textbox,
        "keybinds_textbox": keybinds_textbox,
        "tabview": tabview,
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
    }
