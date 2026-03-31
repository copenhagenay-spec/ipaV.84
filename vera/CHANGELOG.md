# Changelog

## 0.95
- Premium tier foundation — `license.py` gate controls access to premium features; `premium` flag persists through config saves
- Offensive personality mode (Premium) — alternate response pools across all response types: confirmations, wake acks, fallbacks, failures, and social interactions; unlocked via premium license
- Offensive startup greetings — VERA greets differently at startup based on active personality mode
- LLM-powered personality — `llm.py` hooks VERA's conversational responses into Groq (llama-3.1-8b-instant) for dynamic, context-aware replies; falls back to pools if key not set or call fails; uses existing Groq API key from settings
- Personality mode selector — Settings UI shows a mode dropdown (Default / Offensive); locked with a message when premium is not active
- TTS voice selection — dropdown in Settings to choose from 11 Kokoro voices; takes effect immediately
- Conversational prefix stripping — natural phrases like "can you", "could you", "hey vera" stripped before command matching so commands work conversationally
- Expanded social patterns — VERA now responds to: direct insults, "fuck you", "shut up", "don't talk to me like that", "what did you say", "huh", "sounds good", "pretty good", "dude", "yes/yeah", and more
- Insult comebacks — in offensive mode VERA fires back at insults instead of giving polite responses
- Discord community button — Join the Discord button on the Home tab
- Session context in responses — mood, activity, last app, and name now influence personality responses
- Repeat detection — VERA notices when the same phrase is said multiple times without success and suggests rephrasing
- `premium` key preserved on config save — no longer wiped when settings are saved from the UI

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

## 0.85.2
- Key binds: mouse side button support (x1/x2) fixed — was silently failing
- Key binds: combo support fixed (alt+n, ctrl+shift+f etc.) — bracket parsing bug resolved
- Key binds: macro sequences — chain multiple keypresses with > separator (e.g. x1 > q)
- Key binds: remove specific bind by clicking to select then clicking Remove Selected
- Vosk noise filter — "the", "a", "an" and other artifacts silently dropped instead of triggering fallback
- Leading "the" stripped globally — "the open map" → "open map" before command matching
- keybinds.md updated with full usage guide and anti-cheat warning

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
