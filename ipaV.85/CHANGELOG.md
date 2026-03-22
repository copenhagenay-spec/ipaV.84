# Changelog

## 0.85.0
- Close app by voice — "close <app name>" or "close this"
- Auto-discover common apps on startup (Chrome, Firefox, Edge, Opera GX, Discord, Steam, VLC, OBS, and more)
- Spotify search by voice — "spotify <query>" or "spotify play <query>"
- "What can I say" UI overhauled — dark themed, section cards, colored placeholders
- Help window now opens in background thread — PTT stays active while it's open
- App list in "What Can I Say" now shows only relevant discovered apps, not full Steam library
- Open last app again — "open that again"
- Full documentation added — setup, commands, adding apps, AI setup, Discord setup
- Key binds (keypress commands) temporarily disabled pending reliability improvements
- Wizard shortcut creation fixed — no more duplicate Start Menu entries

## 0.84.9.0
- Switched AI backend to Groq (free, no quota issues) — also auto-detects Claude and OpenAI API keys
- Added standard English model option in wizard (vosk-model-en-us-0.22-lgraph, ~128MB, better accuracy)
- Vosk model now cached in memory — no longer reloads on every keypress
- Add alias voice command — say "add alias [name] for [app]" to create custom app shortcuts
- PTT audio cues — beep on press signals when to start talking, beep on release confirms end
- Improved hold-to-talk timing — reduced audio cutoff at start and end of speech
- Mishear corrections expanded for "restart assistant"
- Wizard: desktop shortcut creation option added
- Removed unused VBS launcher

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
- Added Claude / Anthropic API support — paste a `sk-ant-` key and IPA uses Claude Haiku automatically
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
