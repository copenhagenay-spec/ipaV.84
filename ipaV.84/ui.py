"""Main UI layout for IPA (CustomTkinter)."""

from __future__ import annotations

import customtkinter as ctk


def build_ui(root, state: dict, callbacks: dict, constants: dict):
    HOTKEY_CHOICES = constants["HOTKEY_CHOICES"]
    LANG_CHOICES = constants["LANG_CHOICES"]

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

    def _toggle_theme():
        new_mode = "dark" if state["theme_var"].get() else "light"
        ctk.set_appearance_mode(new_mode)

    # --- Tabview ---
    tabview = ctk.CTkTabview(root)
    tabview.pack(fill="both", expand=True, padx=10, pady=(10, 0))
    tabview.add("Main")
    tabview.add("Apps")
    tabview.add("Actions")
    tabview.set("Main")

    # ---- MAIN TAB ----
    main_scroll = ctk.CTkScrollableFrame(tabview.tab("Main"))
    main_scroll.pack(fill="both", expand=True)

    logo_img = _load_logo()
    if logo_img is not None:
        logo_label = ctk.CTkLabel(main_scroll, image=logo_img, text="")
        logo_label.pack(pady=(6, 2))

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
    ctk.CTkRadioButton(mode_row, text="Hotkey", variable=mode, value="hotkey").pack(side="left")

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
    ctk.CTkEntry(rec_row2, textvariable=hotkey, width=160).pack(side="left", padx=(0, 10))
    ctk.CTkButton(rec_row2, text="Record", command=lambda: _record_hotkey(hotkey), width=90).pack(
        side="left"
    )

    rec_row3 = ctk.CTkFrame(rec_card, fg_color="transparent")
    rec_row3.pack(fill="x", padx=12, pady=(4, 8))
    ctk.CTkLabel(rec_row3, text="Hold key", width=120).pack(side="left")
    ctk.CTkEntry(rec_row3, textvariable=holdkey, width=160).pack(side="left", padx=(0, 10))
    ctk.CTkButton(rec_row3, text="Record", command=lambda: _record_hold_key(holdkey), width=90).pack(
        side="left"
    )

    rec_row4 = ctk.CTkFrame(rec_card, fg_color="transparent")
    rec_row4.pack(fill="x", padx=12, pady=(4, 8))
    ctk.CTkLabel(rec_row4, text="Search Engine", width=120).pack(side="left")
    ctk.CTkEntry(rec_row4, textvariable=search_engine, width=340).pack(side="left")

    ctk.CTkLabel(main_scroll, text="Options", font=("Segoe UI", 13, "bold")).pack(
        anchor="w", padx=12, pady=(14, 4)
    )
    opt_card = ctk.CTkFrame(main_scroll)
    opt_card.pack(fill="x", padx=12, pady=4)

    ctk.CTkCheckBox(opt_card, text="Confirm before running actions", variable=confirm_actions).pack(
        anchor="w", padx=16, pady=(10, 4)
    )
    ctk.CTkCheckBox(opt_card, text="Dark mode", variable=state["theme_var"], command=_toggle_theme).pack(
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
    ctk.CTkButton(ctrl_row2, text="Check Updates", command=_check_for_updates, width=130).pack(
        side="left", padx=4
    )
    ctk.CTkButton(ctrl_row2, text="Bug Report", command=_create_bug_report, width=130,
                   fg_color=("gray60", "gray30"), hover_color=("gray50", "gray40")).pack(
        side="left", padx=4
    )

    ctrl_row3 = ctk.CTkFrame(ctrl_card, fg_color="transparent")
    ctrl_row3.pack(fill="x", padx=12, pady=(4, 8))
    ctk.CTkButton(ctrl_row3, text="Delete Cache", command=_clear_pycache, width=130,
                   fg_color=("gray60", "gray30"), hover_color=("gray50", "gray40")).pack(
        side="left", padx=4
    )

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

    ctk.CTkLabel(apps_scroll, text="App Aliases", font=("Segoe UI", 13, "bold")).pack(
        anchor="w", padx=12, pady=(16, 4)
    )
    ctk.CTkLabel(apps_scroll, text="Say the alias to launch the target app.").pack(
        anchor="w", padx=12, pady=(0, 6)
    )

    aliases_textbox = ctk.CTkTextbox(apps_scroll, height=80)
    aliases_textbox.pack(fill="x", padx=12, pady=4)

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
    ctk.CTkEntry(act_r2, textvariable=command_var, width=300,
                 placeholder_text="e.g. rundll32.exe user32.dll,LockWorkStation").pack(
        side="left", padx=(0, 10)
    )

    action_btn_row = ctk.CTkFrame(actions_scroll, fg_color="transparent")
    action_btn_row.pack(fill="x", padx=12, pady=4)
    ctk.CTkButton(action_btn_row, text="Add Action", command=_add_action, width=130).pack(side="left", padx=4)
    ctk.CTkButton(action_btn_row, text="Remove Last", command=_remove_action, width=130,
                   fg_color=("#cc3333", "#cc3333"), hover_color=("#aa2222", "#aa2222")).pack(
        side="left", padx=4
    )

    return {
        "apps_textbox": apps_textbox,
        "aliases_textbox": aliases_textbox,
        "actions_textbox": actions_textbox,
        "tabview": tabview,
    }
