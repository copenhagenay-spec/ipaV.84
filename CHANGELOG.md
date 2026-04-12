# Changelog

## 0.97.7
- Added: Command Macros (Premium) — chain multiple commands into one phrase; each step runs in sequence, waiting for VERA to finish speaking before starting the next; configure in Integrations tab
- Fixed: Ctrl+Scroll text scaling now works on all tabs — collapsible list headers and description labels throughout the UI all scale correctly (moved from 0.97.6.2)

## 0.97.6.2
- Fixed: Ctrl+Scroll text scaling now works on all tabs — collapsible list headers (Registered Apps, App Aliases, Voice Actions, Key Binds) and description labels throughout the UI now scale correctly

## 0.97.6.1
- Added: idle chatter toggle — "Enable idle chatter" checkbox in Settings → Personality; checked by default; uncheck to stop VERA from speaking unless spoken to

## 0.97.6
- Added: collapsible list sections — Voice Actions, Key Binds, Registered Apps, and App Aliases now collapse by default with item count shown in header
- Added: Setup wizard redesign — accent header bar, card layout, blue Finish Setup button
- Added: Ctrl+Scroll to scale text size across the UI (Normal → Large → X-Large); resets on restart
- Added: Secondary PTT — record any keyboard key, mouse button, or joystick button as a second push-to-talk alongside your primary hold key; moved to Recording Settings
- Changed: Input mode labels updated — "Timed mic" → "Wake Word", "Hotkey" → "Push to Toggle" (wizard was out of sync with main UI)
- Removed: Seconds field from Recording Settings (unused since timed mic mode was replaced)

## 0.97.5
- Jarvis personality mode — formal, composed, dry British wit; free tier alongside Professional
- Game overlay — transparent always-on-top bar showing last 3 You/VERA exchanges; say "show overlay" / "hide overlay" or set a hotkey; position configurable in Settings (Top Left default)
- Gaming mode — say "start gaming mode" to strip responses to ultra-short, silence idle chatter, and suppress unrecognized command feedback; status bar shows "Gaming Mode" while active; say "stop gaming mode" to exit

## 0.97.4
- Fixed: note command ignored when transcript starts with "notes." followed by a remember-pattern word
- Added: date command — "what's the date" / "what day is it" returns current date without requiring Groq
- Added: install path display in Settings Utilities — shows VERA's install folder with Open and Copy buttons
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
- Fixed: VERA not launching on Python 3.11/3.12/3.13 installs
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
- "close vera" now kills only the VERA process — PID written to `data/vera.pid` on startup; targeted kill instead of matching by exe name

## 0.90.0
- UI overhaul — inline notifications replace popups, smooth scrolling, unsaved changes indicator, loading overlay, styled listboxes (thepyro-dev)
- Inline key recording overlay — record hotkeys and hold keys directly inside the window instead of a separate dialog
- Fixed hold-to-talk with Caps Lock — releasing the key no longer restarts recording due to synthetic keybd_event from caps lock state restore
- New logo, tray icon, and app icon — refreshed visual design

## 0.89.0
- Bug report now submits to Discord automatically — creates a private ticket with description, VERA version, and full log zip attached
- Description and Discord username prompts added to bug report flow
- Ticket thread named after user's Discord handle if provided
- `requests` added to dependencies

## 0.88.0
- Multi-server Discord support — add servers with nicknames; use 'discord <server> <channel> <message>' to target specific servers
- Discord tab — dedicated tab for all Discord config; moved out of Integrations
- Toggle-to-talk mode — press once to start, press again to stop; replaces timed mic mode

## 0.87.0
- Mishear Training UI — new Training tab shows transcripts VERA didn't understand; click one, type what you meant, save; corrections apply immediately without restart
- PTT beep volume — slider in Settings (0–100%) controls how loud the push-to-talk beeps are
- Single instance enforcement — opening VERA a second time shows a warning and exits instead of opening a duplicate window
- Voice Output device — select a virtual audio device (e.g. VB-Cable) in Settings; "read out" routes TTS through it so it plays through Discord as your mic

## 0.86.4
- Updater now automatically replaces VERA.exe — no more manual reinstalls needed for launcher updates

## 0.86.3
- Fixed desktop and Start Menu shortcuts not launching VERA
- Media keys (play, pause, skip, previous) now work with any player — Apple Music, YouTube, etc. — not just Spotify

## 0.86.2
- Fixed VERA.exe not launching after fresh install — launcher was spawning itself recursively instead of finding the real Python interpreter

## 0.86.1
- Pinned all Python dependencies to exact versions with SHA256 hashes — prevents supply chain attacks
- Fixed VERA.exe crash on fresh install (corrupted release build replaced with clean build)

## 0.86
- Discord delete — "discord delete <channel>" removes the last message (requires MANAGE_MESSAGES)
- Discord purge — "discord purge <channel> <n>" bulk deletes up to 100 messages
- Voice Actions list now clickable — select any entry and Remove Selected instead of only removing last
- Punctuation stripping in transcript preprocessing — fixes faster-whisper adding periods/commas/question marks that broke command matching
- Mishear corrections for purge (perch/perge/merge → purge)

## 0.85.5
- New brand assets — low-poly plant icon and VERA figure logo with transparent backgrounds
- Status indicator dot in status bar (gray=idle, green=listening, red=recording, blue=processing)
- faster-whisper replaces Vosk — MIT licensed, auto-downloads on first run (~150MB), better accuracy
- kokoro-onnx replaces kokoro — compatible with Python 3.14, uses offline model files
- VERA.exe launcher — no console window on startup
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
- Social responses — VERA responds to greetings, thanks, compliments, good morning/night, how are you, and more
- Fallback response — VERA speaks when a command isn't recognized instead of going silent
- Wake word simplified — trigger with just "vera" instead of requiring "hey vera"
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
- Added Claude / Anthropic API support — paste a `sk-ant-` key and VERA uses Claude Haiku automatically
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
