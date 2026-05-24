# VERA Assistant

Voice-controlled personal assistant for Windows.

## Quick Start

1. Download the latest `VERA_Setup_x.x.x.exe` from the [releases page](https://github.com/copenhagenay-spec/Vera-beta/releases)
2. Run the installer — it handles Python packages and voice model files automatically
3. On first launch a short spotlight tour walks you through setting your PTT key and listening mode
4. VERA starts listening in the background — look for the icon in your system tray

Say **"what can I say"** to see everything VERA can do.

## Troubleshooting

- If the app doesn't open, run `run_ipa.cmd` to see errors in the terminal
- If nothing is transcribed, check Windows microphone permissions and your input device
- Crash logs are saved to `data/logs/assistant.log`
- Use the **Bug Report** button in the UI to zip and submit logs automatically

## Uninstall

Run the uninstaller from Add/Remove Programs, or double-click `uninstall.cmd` in the VERA folder.

## Files

- `data/models/` — voice model files (kokoro TTS, faster-whisper STT)
- `data/assets/` — icons and UI assets
- `data/logs/` — crash and event logs
- `data/config.json` — your settings (preserved on reinstall)
- `data/memory.json` — things VERA remembers about you (preserved on reinstall)
- `data/macros.json` — command macros (preserved on reinstall)

## Features

- **Help:** say `what can I say` to show available voice commands
- **Open apps:** say `open <app>` or `close <app>`
- **App aliases:** create shortcut names for apps
- **Custom actions:** map a phrase to any shell command (Integrations tab)
- **Key binds:** map a phrase to a keypress or key sequence (Integrations tab)
- **Command macros:** chain multiple commands into one phrase (Integrations tab, Premium)
- **Web search:** say `search for <query>`
- **Weather:** say `weather in <city>`
- **Date:** say `what's the date` or `what day is it`
- **News:** say `give me the news`
- **Timers:** say `set a timer 5 minutes`
- **Reminders:** say `remind me to <thing> at <time>`
- **Notes:** `note <text>`, `open notes`, `list notes`
- **Memory:** `my name is <name>`, `remember <fact>`, `what do you know about me`
- **Spotify:** `play`, `pause`, `skip`, `back`; or `spotify <query>` to search
- **Volume:** `volume up`, `volume down`, `set volume 50`
- **System:** `sleep computer`, `restart computer`, `shut down computer`
- **Type/send:** `type <text>`, `send message <text>`
- **TTS:** `read out <text>`
- **Mute VERA:** `mute` / `be quiet` / `unmute`
- **Gaming mode:** `start gaming mode` — strips responses to ultra-short, silences idle chatter; activates automatically when a Steam game is launched
- **Steam auto-sync:** Steam library is synced on every launch — new installs added, uninstalled games removed automatically
- **Game overlay:** transparent always-on-top bar showing last 3 voice exchanges
- **AI query:** `ask <question>` — spoken answer via Groq, Claude, or OpenAI; remembers conversation context within the session (see AI Setup)
- **Discord:** send messages, read channels, delete/purge via webhook
- **Personalities:** Default, Professional, Jarvis (free); Offensive (Premium)
- **Idle chatter:** VERA speaks unprompted after inactivity (toggle in Settings)
- **Mishear training:** correct misheard transcripts in the Training tab
- **Tray controls:** show/hide, start/stop, restart, exit
- **Check for updates** — compares version against latest release
- **Bug report** — zips logs and submits automatically to Discord

## AI Setup

The `ask <question>` command supports three providers — VERA detects which to use from your key prefix.

### Groq (free, recommended)

1. Go to [console.groq.com](https://console.groq.com) and sign in
2. Navigate to **API Keys** → **Create API Key**
3. Copy the key (starts with `gsk_`)
4. In VERA → **Integrations tab** → paste it into the **API Key** field → **Save**

### Claude / Anthropic (paid)

Paste your `sk-ant-` key into the same **API Key** field. VERA uses Claude Haiku automatically.

### OpenAI (paid)

Paste your `sk-` key into the **API Key** field. VERA uses gpt-4o-mini.

> **Note:** AI responses reflect the provider's training data and may not include very recent events.
