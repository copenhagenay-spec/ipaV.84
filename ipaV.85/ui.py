"""Main UI layout for IPA (CustomTkinter)."""

from __future__ import annotations

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
    search_engine = state["search_engine"]
    confirm_actions = state["confirm_actions"]
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
    _clear_pycache = callbacks["clear_pycache"]
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
    _add_keybind = callbacks["add_keybind"]
    _remove_keybind = callbacks["remove_keybind"]
    _record_keybind_key = callbacks["record_keybind_key"]

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
    tabview.set("Home")

    # =====================================================================
    # HOME TAB
    # =====================================================================
    home_scroll = ctk.CTkScrollableFrame(tabview.tab("Home"))
    home_scroll.pack(fill="both", expand=True)

    # -- Logo --
    logo_img = _load_logo()
    if logo_img is not None:
        logo_label = ctk.CTkLabel(home_scroll, image=logo_img, text="")
        logo_label.pack(pady=(10, 6))

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

    # =====================================================================
    # SETTINGS TAB
    # =====================================================================
    settings_scroll = ctk.CTkScrollableFrame(tabview.tab("Settings"))
    settings_scroll.pack(fill="both", expand=True)

    # -- Save Config (top of page) --
    save_row = ctk.CTkFrame(settings_scroll, fg_color="transparent")
    save_row.pack(fill="x", padx=PAD_OUTER, pady=(10, 4))
    _primary_btn(save_row, text="Save Config", command=_save,
                 width=200).pack(side="left", padx=4)

    # -- Listening Mode --
    _section_header(settings_scroll, "Listening Mode",
                    "Choose how IPA listens for your voice commands.")
    mode_card = _card(settings_scroll)

    mode_row = _card_row(mode_card)
    ctk.CTkRadioButton(mode_row, text="Timed mic", variable=mode,
                       value="mic").pack(side="left", padx=(0, 16))
    ctk.CTkRadioButton(mode_row, text="Hold-to-talk", variable=mode,
                       value="hold").pack(side="left", padx=(0, 16))
    ctk.CTkRadioButton(mode_row, text="Hotkey", variable=mode,
                       value="hotkey").pack(side="left")

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
    ctk.CTkLabel(rec_r2, text="Hotkey", width=120).pack(side="left")
    ctk.CTkEntry(rec_r2, textvariable=hotkey, width=160).pack(
        side="left", padx=(0, 10))
    _secondary_btn(rec_r2, text="Record",
                   command=lambda: _record_hotkey(hotkey),
                   width=90).pack(side="left")

    rec_r3 = _card_row(rec_card)
    ctk.CTkLabel(rec_r3, text="Hold key", width=120).pack(side="left")
    ctk.CTkEntry(rec_r3, textvariable=holdkey, width=160).pack(
        side="left", padx=(0, 10))
    _secondary_btn(rec_r3, text="Record",
                   command=lambda: _record_hold_key(holdkey),
                   width=90).pack(side="left")

    rec_r4 = _card_row(rec_card)
    ctk.CTkLabel(rec_r4, text="Search Engine", width=120).pack(side="left")
    ctk.CTkEntry(rec_r4, textvariable=search_engine, width=340).pack(
        side="left")

    # -- General Options --
    _section_header(settings_scroll, "General Options")
    opt_card = _card(settings_scroll)

    ctk.CTkCheckBox(opt_card, text="Confirm before running actions",
                    variable=confirm_actions).pack(
        anchor="w", padx=PAD_CARD, pady=(10, 4))
    ctk.CTkCheckBox(opt_card, text="Dark mode", variable=state["theme_var"],
                    command=_toggle_theme).pack(
        anchor="w", padx=PAD_CARD, pady=(4, 10))

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
    _danger_btn(util_row2, text="Delete Cache", command=_clear_pycache,
                width=130).pack(side="left", padx=4)

    # =====================================================================
    # APPS TAB
    # =====================================================================
    apps_scroll = ctk.CTkScrollableFrame(tabview.tab("Apps"))
    apps_scroll.pack(fill="both", expand=True)

    # -- Registered Apps --
    _section_header(apps_scroll, "Registered Apps",
                    "Say 'open <app name>' to launch an app. "
                    "Add them manually or import from Steam.")

    apps_textbox = ctk.CTkTextbox(apps_scroll, height=140, corner_radius=8)
    apps_textbox.pack(fill="x", padx=PAD_OUTER, pady=4)

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
    _danger_btn(app_btns, text="Remove Last", command=_remove_app,
                width=110).pack(side="right", padx=4)

    # -- App Aliases --
    _section_header(apps_scroll, "App Aliases",
                    "Create shortcuts \u2014 say the alias to launch "
                    "the target app.")

    aliases_textbox = ctk.CTkTextbox(apps_scroll, height=90, corner_radius=8)
    aliases_textbox.pack(fill="x", padx=PAD_OUTER, pady=4)

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
    _danger_btn(alias_btns, text="Remove Last", command=_remove_alias,
                width=110).pack(side="right", padx=4)

    # =====================================================================
    # INTEGRATIONS TAB
    # =====================================================================
    integ_scroll = ctk.CTkScrollableFrame(tabview.tab("Integrations"))
    integ_scroll.pack(fill="both", expand=True)

    # -- AI (Groq) --
    _section_header(integ_scroll, "AI Assistant",
                    "Say 'ask <question>' to query AI. "
                    "Get your free key at console.groq.com \u2192 API Keys.")
    ai_card = _card(integ_scroll)

    ai_row = _card_row(ai_card)
    ctk.CTkLabel(ai_row, text="API Key", width=120).pack(side="left")
    ctk.CTkEntry(ai_row, textvariable=gemini_api_key_var, width=320,
                 show="*",
                 placeholder_text="Groq API key").pack(
        side="left", padx=(0, 10))

    # -- Discord Credentials --
    _section_header(integ_scroll, "Discord",
                    "Connect a Discord bot to post messages by voice.")
    discord_card = _card(integ_scroll)

    disc_r1 = _card_row(discord_card)
    ctk.CTkLabel(disc_r1, text="Bot Token", width=120).pack(side="left")
    ctk.CTkEntry(disc_r1, textvariable=discord_bot_token_var, width=320,
                 show="*",
                 placeholder_text="Bot token from Discord Developer Portal"
                 ).pack(side="left", padx=(0, 10))

    disc_r2 = _card_row(discord_card)
    ctk.CTkLabel(disc_r2, text="Server ID", width=120).pack(side="left")
    ctk.CTkEntry(disc_r2, textvariable=discord_server_id_var, width=220,
                 placeholder_text="Right-click server \u2192 Copy Server ID"
                 ).pack(side="left", padx=(0, 10))

    # -- Discord Channels --
    _section_header(integ_scroll, "Discord Channels",
                    "Say 'discord <channel> <message>' to post to a channel.")

    discord_channels_textbox = ctk.CTkTextbox(integ_scroll, height=80,
                                               corner_radius=8)
    discord_channels_textbox.pack(fill="x", padx=PAD_OUTER, pady=4)

    discord_input_card = _card(integ_scroll)

    disc_ch_r1 = _card_row(discord_input_card)
    ctk.CTkLabel(disc_ch_r1, text="Channel name", width=120).pack(
        side="left")
    ctk.CTkEntry(disc_ch_r1, textvariable=discord_ch_name_var, width=220,
                 placeholder_text="e.g. general").pack(
        side="left", padx=(0, 10))

    disc_ch_r2 = _card_row(discord_input_card)
    ctk.CTkLabel(disc_ch_r2, text="Webhook URL", width=120).pack(
        side="left")
    ctk.CTkEntry(disc_ch_r2, textvariable=discord_ch_url_var, width=320,
                 placeholder_text="https://discord.com/api/webhooks/..."
                 ).pack(side="left", padx=(0, 10))

    discord_btns = _btn_row(integ_scroll)
    _primary_btn(discord_btns, text="Add Channel",
                 command=_add_discord_channel, width=120).pack(
        side="left", padx=4)
    _danger_btn(discord_btns, text="Remove Last",
                command=_remove_discord_channel, width=120).pack(
        side="right", padx=4)

    # -- Voice Actions --
    _section_header(integ_scroll, "Voice Actions",
                    "Map any spoken phrase to a shell command.")

    actions_textbox = ctk.CTkTextbox(integ_scroll, height=160,
                                      corner_radius=8)
    actions_textbox.pack(fill="x", padx=PAD_OUTER, pady=4)

    action_input_card = _card(integ_scroll)

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
    _primary_btn(action_btns, text="Add Action", command=_add_action,
                 width=130).pack(side="left", padx=4)
    _danger_btn(action_btns, text="Remove Last", command=_remove_action,
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
    ).pack(anchor="w", padx=PAD_OUTER, pady=(0, 6))

    keybinds_textbox = ctk.CTkTextbox(integ_scroll, height=100,
                                       corner_radius=8)
    keybinds_textbox.pack(fill="x", padx=PAD_OUTER, pady=4)

    kb_input_card = _card(integ_scroll)

    kb_r1 = _card_row(kb_input_card)
    ctk.CTkLabel(kb_r1, text="Phrase", width=100).pack(side="left")
    ctk.CTkEntry(kb_r1, textvariable=keybind_phrase_var, width=240,
                 placeholder_text="e.g. reload").pack(
        side="left", padx=(0, 10))

    kb_r2 = _card_row(kb_input_card)
    ctk.CTkLabel(kb_r2, text="Key", width=100).pack(side="left")
    ctk.CTkEntry(kb_r2, textvariable=keybind_key_var, width=120,
                 placeholder_text="e.g. r").pack(side="left", padx=(0, 10))
    _secondary_btn(
        kb_r2, text="Record",
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
    _primary_btn(kb_btns, text="Add Key Bind", command=_add_keybind,
                 width=130).pack(side="left", padx=4)
    _danger_btn(kb_btns, text="Remove Last", command=_remove_keybind,
                width=130).pack(side="right", padx=4)

    # =====================================================================
    # STATUS BAR  (persistent, outside tabview)
    # =====================================================================
    status_frame = ctk.CTkFrame(root)
    status_frame.pack(fill="x", padx=10, pady=(4, 10))
    status_left = ctk.CTkFrame(status_frame, fg_color="transparent")
    status_left.pack(fill="x", padx=12, pady=8)
    ctk.CTkLabel(status_left, text="Status:",
                 font=("Segoe UI", 11, "bold")).pack(side="left")
    ctk.CTkLabel(status_left, textvariable=status_var).pack(
        side="left", padx=(8, 20))
    ctk.CTkLabel(status_left, text="Last:",
                 font=("Segoe UI", 11, "bold")).pack(side="left")
    ctk.CTkEntry(status_left, textvariable=transcript_var,
                 width=260).pack(side="left", padx=(8, 0))

    # =====================================================================
    # RETURN DICT  (identical keys to original)
    # =====================================================================
    return {
        "apps_textbox": apps_textbox,
        "aliases_textbox": aliases_textbox,
        "actions_textbox": actions_textbox,
        "history_textbox": history_textbox,
        "discord_channels_textbox": discord_channels_textbox,
        "keybinds_textbox": keybinds_textbox,
        "tabview": tabview,
    }
