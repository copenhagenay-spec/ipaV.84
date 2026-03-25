# Changelog

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
