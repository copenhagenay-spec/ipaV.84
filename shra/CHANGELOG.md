# Changelog

## 0.99.8.9 — Hotfix
- Fixed: SH|RA crashing on launch after 0.99.8.8 update — license.py was incorrectly removed from the installer package.

## 0.99.8.8 — Hotfix
- Fixed: SH|RA not launching on machines without a system Python install — launcher now correctly uses the bundled embedded Python.
- Changed: Spotify / media controls now enabled by default on fresh installs.
- Improved: Updates no longer re-download voice models if they are already present (~310 MB saved per update).

## 0.99.8
- Added: Start Menu auto-discovery — SH|RA now scans the Windows Start Menu on startup and adds installed apps automatically. Spotify, Discord, and other store apps are found this way.
- Added: Weather and news commands — "what's the weather in [city]" and "give me the news".
- Added: Per-app volume control — "set [app] volume [0-100]".
- Fixed: Administrative Tools shortcuts (Event Viewer, Registry Editor, Task Scheduler, etc.) no longer appear in the app list.
- Changed: Python is no longer required as a separate install — it is now bundled with the installer.
- Changed: Save and Revert buttons use rounded corners consistent with the rest of the UI.

## 0.99.7.2 — Hotfix
- Fixed: SH|RA would not launch after a fresh install — tour.py was missing from the installer package.

## 0.99.7 — Steam Integration, Conversational AI & Stability
- Fixed: Animated MP4 video background was continuously decoding frames and flooding the Qt event queue, causing severe input lag and audio delays in CPU/GPU-heavy games (Rust, Gray Zone Warfare). Gaming mode now pauses the video player entirely.
- Fixed: Memory leak root cause identified — QPixmap accumulation and Qt event queue flooding from the video background caused memory growth under game load. Pausing video in gaming mode resolves this.
- Fixed: PortAudio stream leak in the "read out" TTS path — was leaking a stream on every call. Now correctly delegates to the shared output stream context manager.
- Fixed: Caps lock suppression restored after keyboard polling migration — toggle correction now fires on physical key release, completing in microseconds without interfering with push-to-talk.
- Fixed: Home theme (Emerald, Particle Network, etc.) was resetting to Particle Network on restart after any settings save. The UI and settings save paths used separate config instances, so theme changes were silently overwritten.
- Added: Freeze watchdog — detects Qt main thread freezes (heartbeat stale >10s), logs memory/thread diagnostics to data/logs/freeze_watchdog.log, and automatically restarts SH|RA.
- Added: Dismiss button on info notifications — blue notification panels can now be closed without restarting SH|RA.
- Added: Revert Changes button — appears alongside the Unsaved Changes button in the status bar; rolls back all unsaved settings changes to the last saved state.
- Added: Spotlight tour for new users — a 4-step guided overlay that highlights the PTT key field and listening mode selector, then returns to the Home tab. Navigates automatically between tabs. Dismisses with Skip or Done and does not appear again after completion.
- Added: Steam library auto-sync on startup — runs in a background thread, adds newly installed games and removes uninstalled ones from the apps list. Only touches Steam-sourced entries. Saves silently with no unsaved changes prompt.
- Added: Steam auto gaming mode — detects when a Steam game is launched via registry and automatically enables gaming mode. Disables silently when the game closes, but only if SH|RA was the one that enabled it.
- Added: Conversational memory — LLM responses now carry context across follow-up questions within the same session. History is shared across both the personality fallback and the ask command. Clears on restart, holds up to 5 exchanges.
- Changed: Toggle key and Hold key settings merged into a single PTT Key field. All listening modes now share one key binding. Existing configs migrate automatically on first launch. If a mouse or joystick button is set and Toggle mode is selected, SH|RA automatically falls back to caps_lock and notifies the user.
- Removed: Setup wizard removed. First-time experience is now handled by the guided spotlight tour.
- Removed: Import Steam Games button — replaced by auto-sync.
- Removed: Discord Rich Presence integration — was not working as intended.
- Removed: pypresence and espeak-ng dependencies — no longer needed.

## 0.99.6
- Fixed: Memory leak causing SH|RA to consume 9-16GB of RAM during long sessions — status bar was allocating Qt style objects on every update without releasing them
- Fixed: Status updates now throttled to prevent burst allocation during rapid state changes
- Fixed: SH|RA now automatically restarts cleanly on system wake from sleep using a direct Windows power notification callback — eliminates memory spike caused by audio device reconnection on wake

## 0.99.5
- Added: About tab — shows version number and Forjem Software LLC copyright; info icon in sidebar rail; card follows active theme
- Added: Installer banner — custom branded sidebar image with SH|RA logo and Forjem Software LLC copyright
- Added: EULA — license agreement page added to installer with "I Agree" step
- Added: Install progress — progress bar now builds meaningfully through each install step with step count labels
- Fixed: "What can I say" / "Show help" now opens correctly and shows the SH|RA icon in the title bar
- Fixed: Help dialog window stays open — was being garbage collected immediately after opening

## 0.99.4
- Fixed: "What can I say" / "Show help" now opens correctly — was silently failing after the PySide6 migration
- Fixed: Help dialog now shows the SH|RA icon in the title bar

## 0.99.3
- Added: HMAC-signed license key system — cryptographically validated, no server required
- Added: Premium settings consolidated into a dedicated section — license key, wake phrase, and theme all in one place
- Added: Premium onboarding card on first launch — points you to exactly where everything lives
- Fixed: Onboarding dismissed state now persists correctly through settings saves
- Added: Animated video backgrounds for premium themes (Particle Network, Emerald)
- Added: Sidebar icon rail replaces tab bar — collapsible via hamburger toggle
- Added: Per-theme color system — buttons, slider, cards, and icons follow the active theme
- Added: Per-theme logos — each theme has its own logo
- Added: Default theme — available to free tier and as a clean premium option
- Added: Cinzel font bundled — used for the SH|RA / SH|RA+ title across all tiers
- Changed: Theme assets organized into structured folders

## 0.99.2
- Added: New pill knob control (Premium) — replaces the rotating knob with a sleek pill-shaped control
- Added: Start Listening / Stop Listening labels sit directly on the black panels
- Added: Knob color matches your selected theme — gold for Particle Network, emerald for Emerald
- Fixed: Theme swap now updates both the background and the knob simultaneously

## 0.99.1
- Fixed: Scroll wheel no longer accidentally changes dropdowns and sliders on hover — must click first
- Fixed: "search when is the next X" no longer triggers media skip instead of opening a browser search
- Added: SH|RA now confirms web searches with a spoken response

## 0.99
- Added: PyArmor obfuscation — source code is now protected in all installer builds
- Fixed: Dev-only files (smoke_test.py, sync_public.py, discord_post.py, etc.) no longer ship to users; old copies removed automatically on next install
- Added: Premium UI identity — gold theme, deeper background, SH|RA+ title bar and home screen title, SH|RA+/PREMIUM TIER watermarks
- Added: Premium knob control — replaces Start/Stop buttons in Hold to Talk and Toggle modes for premium users; click toggles listening state

## 0.98.0.1
- Fixed: "type" and "send message" commands failing with "cannot import name KbController" — public build import was broken after sync

## 0.98
- Added: Fuzzy intent routing — SH|RA now catches misheard commands that slip past exact matching; high-confidence mishears fire silently, mid-confidence triggers a "Did you mean X?" confirmation; confirmed matches auto-log to mishear training
- Added: Custom wake phrase (Premium) — set your own trigger word alongside "shira" in Settings → Personality; updates live without restart
- Added: First-launch onboarding card — new users see a prompt to try "show help" or "what can I say"; dismissed permanently with "Got it"

## 0.97.8.4
- Fixed: "Downloading update..." status now shows immediately after confirming so it's clear the update is in progress
- Fixed: update error messages now display correctly if the download fails

## 0.97.8.3
- Fixed: clicking "Check Updates" no longer freezes SH|RA — update check and download now run in the background

## 0.97.8.2
- Fixed: cancel/clear/delete reminders now recognized with more natural phrasings ("cancel reminders", "delete my reminders", "get rid of reminders", etc.)
- Improved: Discord username is now required when submitting a bug report — you'll receive a ping in the server when your bug is confirmed and when it's fixed

## 0.97.8.1
- Fixed: numpad keys (Num0–Num9, NumDecimal, NumMultiply, NumAdd, NumSubtract, NumDivide) now record and fire correctly in keybinds
- Fixed: reminder list queries ("what's my reminder set to", "what are my reminders", etc.) were being misrouted to the AI and returning fabricated answers; now handled correctly by the local intent system

## 0.97.8
- Added: weather shown on game overlay — say "weather in <city>" with the overlay visible to see current conditions pinned at the top in amber (city, temp, description on line 1; high/low/rain chance on line 2)
- Improved: game overlay rebuilt with Qt layout system — cleaner rendering, better visual hierarchy, separator between weather and exchanges, foundation for future pinnable widget cards
- Docs: full documentation pass — fixed factual errors, added missing commands (time, clipboard, per-app volume, aliases), added overlay guide, macros guide, personality guide, and comprehensive troubleshooting guide

## 0.97.7.1
- Fixed: "close this" command could hang SH|RA indefinitely if the target process was in a protected or unresponsive state; taskkill now has a 5-second timeout and SH|RA stays responsive regardless of the result

## 0.97.7
- Added: Command Macros (Premium) — chain multiple commands into one phrase; each step runs in sequence, waiting for SH|RA to finish speaking before starting the next; configure in Integrations tab
- Fixed: Ctrl+Scroll text scaling now works on all tabs — collapsible list headers and description labels throughout the UI all scale correctly (moved from 0.97.6.2)

## 0.97.6.2
- Fixed: Ctrl+Scroll text scaling now works on all tabs — collapsible list headers (Registered Apps, App Aliases, Voice Actions, Key Binds) and description labels throughout the UI now scale correctly

## 0.97.6.1
- Added: idle chatter toggle — "Enable idle chatter" checkbox in Settings → Personality; checked by default; uncheck to stop SH|RA from speaking unless spoken to

## 0.97.6
- Added: collapsible list sections — Voice Actions, Key Binds, Registered Apps, and App Aliases now collapse by default with item count shown in header
- Added: Setup wizard redesign — accent header bar, card layout, blue Finish Setup button
- Added: Ctrl+Scroll to scale text size across the UI (Normal → Large → X-Large); resets on restart
- Added: Secondary PTT — record any keyboard key, mouse button, or joystick button as a second push-to-talk alongside your primary hold key; moved to Recording Settings
- Changed: Input mode labels updated — "Timed mic" → "Wake Word", "Hotkey" → "Push to Toggle" (wizard was out of sync with main UI)
- Removed: Seconds field from Recording Settings (unused since timed mic mode was replaced)

## 0.97.5
- Jarvis personality mode — formal, composed, dry British wit; free tier alongside Professional
- Game overlay — transparent always-on-top bar showing last 3 You/SH|RA exchanges; say "show overlay" / "hide overlay" or set a hotkey; position configurable in Settings (Top Left default)
- Gaming mode — say "start gaming mode" to strip responses to ultra-short, silence idle chatter, and suppress unrecognized command feedback; status bar shows "Gaming Mode" while active; say "stop gaming mode" to exit

## 0.97.4
- Fixed: note command ignored when transcript starts with "notes." followed by a remember-pattern word
- Added: date command — "what's the date" / "what day is it" returns current date without requiring Groq
- Added: install path display in Settings Utilities — shows SH|RA's install folder with Open and Copy buttons
- Fixed: voice restart command leaving old instance alive with a dead listener
- Help command updated — Reminders, mute/unmute, and date added

## 0.97.3
- Added: mouse side button support — extra mouse buttons (x1/x2) can now be recorded as hold-to-talk or toggle keys
- Fixed: Record button for toggle key and hold key not updating the text field after recording

## 0.97.2
- Fixed: keybind "+ Step" key field not updating after recording a key
- Fixed: modifier key combos (alt+n, ctrl+shift+f, etc.) not captured
- Fixed: hold-to-talk occasionally freezing
- Fixed: tray icon not recovering after Windows Explorer restart

## 0.97.1
- Fixed: SH|RA not launching on Python 3.11/3.12/3.13 installs
- Fixed: `run_ipa.cmd` hardcoded to Python 3.14 only

## 0.97.0
- UI rebuilt on PySide6/Qt6 — eliminates scroll tearing, uses native OS rendering
- Silent installer — pip, espeak-ng, and Kokoro model files all download and install automatically with progress shown in the installer UI (no terminal window)
- Listening mode redesigned as a segmented pill control — all three modes visible without scrolling
- Dark mode only — light mode removed
- Fixed: dual process on voice restart — old instance now hard-exits cleanly
- Fixed: AI response status bar not flashing after Groq responses
- Fixed: record overlay getting stuck when triggered from background thread
- Fixed: list widget scroll bleeding into parent scroll area
- Key bind display: angle brackets stripped from key names (e.g. `caps_lock` instead of `<caps_lock>`)
- Utilities section: all buttons unified to secondary style

## 0.90.1.1
- "close shira" now kills only the SH|RA process — PID written to `data/shra.pid` on startup; targeted kill instead of matching by exe name

## 0.90.0
- UI overhaul — inline notifications replace popups, smooth scrolling, unsaved changes indicator, loading overlay, styled listboxes (thepyro-dev)
- Inline key recording overlay — record hotkeys and hold keys directly inside the window instead of a separate dialog
- Fixed hold-to-talk with Caps Lock — releasing the key no longer restarts recording due to synthetic keybd_event from caps lock state restore
- New logo, tray icon, and app icon — refreshed visual design

## 0.89.0
- Bug report now submits to Discord automatically — creates a private ticket with description, SH|RA version, and full log zip attached
- Description and Discord username prompts added to bug report flow
- Ticket thread named after user's Discord handle if provided
- `requests` added to dependencies

## 0.88.0
- Multi-server Discord support — add servers with nicknames; use 'discord <server> <channel> <message>' to target specific servers
- Discord tab — dedicated tab for all Discord config; moved out of Integrations
- Toggle-to-talk mode — press once to start, press again to stop; replaces timed mic mode

## 0.87.0
- Mishear Training UI — new Training tab shows transcripts SH|RA didn't understand; click one, type what you meant, save; corrections apply immediately without restart
- PTT beep volume — slider in Settings (0–100%) controls how loud the push-to-talk beeps are
- Single instance enforcement — opening SH|RA a second time shows a warning and exits instead of opening a duplicate window
- Voice Output device — select a virtual audio device (e.g. VB-Cable) in Settings; "read out" routes TTS through it so it plays through Discord as your mic

## 0.86.4
- Updater now automatically replaces SH|RA.exe — no more manual reinstalls needed for launcher updates

## 0.86.3
- Fixed desktop and Start Menu shortcuts not launching SH|RA
- Media keys (play, pause, skip, previous) now work with any player — Apple Music, YouTube, etc. — not just Spotify

## 0.86.2
- Fixed SH|RA.exe not launching after fresh install — launcher was spawning itself recursively instead of finding the real Python interpreter

## 0.86.1
- Pinned all Python dependencies to exact versions with SHA256 hashes — prevents supply chain attacks
- Fixed SH|RA.exe crash on fresh install (corrupted release build replaced with clean build)

## 0.86
- Discord delete — "discord delete <channel>" removes the last message (requires MANAGE_MESSAGES)
- Discord purge — "discord purge <channel> <n>" bulk deletes up to 100 messages
- Voice Actions list now clickable — select any entry and Remove Selected instead of only removing last
- Punctuation stripping in transcript preprocessing — fixes faster-whisper adding periods/commas/question marks that broke command matching
- Mishear corrections for purge (perch/perge/merge → purge)

## 0.85.5
- New brand assets — low-poly plant icon and SH|RA figure logo with transparent backgrounds
- Status indicator dot in status bar (gray=idle, green=listening, red=recording, blue=processing)
- faster-whisper replaces Vosk — MIT licensed, auto-downloads on first run (~150MB), better accuracy
- kokoro-onnx replaces kokoro — compatible with Python 3.14, uses offline model files
- SH|RA.exe launcher — no console window on startup
- Add Desktop Shortcut button in Settings → Utilities

## 0.85.2
- Intent-based command router — decorator-based priority system replacing if/elif chain
- preprocess_transcript() pipeline — filler strip, mishear corrections, leading/trailing noise removal
- Memory system — long-term (memory.json) + short-term session context
- Conversational depth — mood/activity detection, session-aware responses, name-aware greetings

## 0.85.1
- Personality system — moved all response pools into `personality.py` for cleaner separation
- Wake acknowledgments — 15 random lines when wake word triggers
- Command confirmations — per-category response pools (open, close, volume, note, timer, search, send)
- Social responses — SH|RA responds to greetings, thanks, compliments, good morning/night, how are you, and more
- Fallback response — SH|RA speaks when a command isn't recognized instead of going silent
- Wake word simplified — trigger with just "shira" instead of requiring "hey shira"
- Wake word audio fix — mic reuses existing stream so no startup delay on command capture
- Ready beep — short tone signals mic is open after wake ack
- Edge TTS — replaced pyttsx3 with Microsoft neural TTS (en-US-JennyNeural) for a much cleaner voice; falls back to pyttsx3 if offline

## 0.84.8.6
- UI refactor — improved layout consistency, button styles, card sections, and section headers (thepyro-dev)
- Added .gitignore to prevent user data and models from being committed
- Added custom CTk theme file

## 0.84.8.5
- Restart PC — say "restart computer" or "reboot computer" (5 second delay)
- Shutdown PC — say "shut down computer" or "power off computer" (5 second delay)

## 0.84.8.4
- AI now knows the current time as well as the date
- Bug report now offers to clear logs after zipping

## 0.84.8.3
- Caps Lock suppression now included in public build — when using Caps Lock as PTT, it no longer toggles caps lock state while recording

## 0.84.8.2
- Fixed crash on launch: gemini_api_key_var missing from assistant.py state dict

## 0.84.8.1
- AI now injects today's date into the prompt so it knows the current date
- Switched default Groq model to llama-3.3-70b-versatile (December 2023 cutoff, smarter responses)
- Added Claude / Anthropic API support — paste a `sk-ant-` key and SH|RA uses Claude Haiku automatically
- README note added about AI knowledge cutoff

## 0.84.8
- AI voice query — say "ask <question>" to get a spoken answer powered by Groq (free API, get key at console.groq.com)
- Key Binds — map a spoken phrase to a keypress with optional repeat count (Actions tab); note: blocked by EAC/BattlEye in protected games
- Send Message — "send message <text>" types text and presses Enter to send

## 0.84.7
- TTS — "read out <text>" speaks text aloud
- Discord send — "discord <channel> <message>" posts to a webhook channel
- Discord read — "read discord <channel>" reads the last message aloud via TTS
- Discord credentials UI (bot token + server ID fields in Apps tab)
- pyttsx3 added as TTS dependency
