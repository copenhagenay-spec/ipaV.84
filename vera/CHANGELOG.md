# Changelog

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
