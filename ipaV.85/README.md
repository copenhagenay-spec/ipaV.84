# IPA Assistant

Offline personal assistant for Windows using Vosk (speech to text).

## Quick Start

1. Install Python 3.10+ (standalone installer):
   https://www.python.org/downloads/
   - Make sure to check **"Add Python to PATH"** during install
2. Double-click `setup.cmd` to install dependencies (one-time)
3. Double-click `run_ipa.vbs` (no terminal)
4. The first-run wizard will open:
   - Choose **Language** (English or Spanish)
   - Choose **Mode** (Hold-to-talk, Hotkey, or Timed)
   - If you don't have a model yet, click **Download English/Spanish Model**
   - Optional: **Import Steam Apps**
   - Click **Finish**

IPA will start listening in the background after the wizard finishes.

## Troubleshooting

- If the app doesn't open, run `run_ipa.cmd` to see errors in the terminal.
- If nothing is transcribed, check Windows microphone permissions and input device.
- If hotkey/hold doesn't work, make sure dependencies are installed and restart IPA.
- Crash logs are saved to `data/logs/assistant.log`.

## Uninstall

Double-click:
`uninstall.cmd`

This removes the `data` folder (model, logs, settings). To fully remove IPA,
delete the IPA folder.

## Files

- `data/model` holds the Vosk models
- `data/model/en` English model
- `data/model/es` Spanish model (if installed)
- `data/assets` holds icons
- `data/logs` holds crash logs
- `data/config.json` holds your settings

## Features

- Help: say `what can I say` to show all available voice commands
- Open apps: say `open <app>`
- App aliases: say an alias to open a target app
- Custom actions: phrase -> command
- Web search: say `search for <query>`
- YouTube: open, search, play/pause/next/back
- Spotify media controls: `play`, `pause`, `skip`, `back`
- Timers: say `set a timer 5 minutes`
- Notes: `note ...`, `open notes`, `delete last note`, `clear all notes`
- Sleep PC: `sleep computer`
- Restart IPA: `restart assistant`
- Type text: `type <text>` (simulates keyboard input)
- Send message: `send message <text>` — types text and presses Enter to send
- System audio mute/unmute: `sound on`, `sound off`
- Text-to-speech: `read out <text>` (offline TTS via pyttsx3)
- AI query: `ask <question>` — spoken answer powered by Groq (free, see **AI Setup** below)
- Key binds: map a spoken phrase to a keypress (e.g. say "reload" → presses R); configured in the Actions tab. ⚠ Blocked by EAC/BattlEye anti-cheat in protected games.
- Discord: `discord <channel> <message>` — posts to a webhook channel; `read discord <channel>` — reads last message aloud
- Discord setup: add Bot Token + Server ID + per-channel webhook URLs in the Apps tab
- Mouse side buttons supported as push-to-talk key (record via Hold key button)
- Tray controls: show/hide/start/stop/restart/exit
- Bug report button (zips log + settings)
- Check for updates (downloads latest from GitHub)
- English and Spanish recognition (per-language models)

## Steam Import

Use the **Import Steam** button in the Apps section to auto-add games
from your Steam library as voice commands.

## Models

Place models in:

```
data/model/en/<model-folder>
data/model/es/<model-folder>
```

Small English model example:
`vosk-model-small-en-us-0.15`

Small Spanish model example:
`vosk-model-small-es-0.42`

## AI Setup

The `ask <question>` command supports two providers — IPA detects which one to use automatically based on your key.

### Option 1 — Groq (free, recommended)

No credit card needed. 14,400 requests/day on the free tier.

1. Go to **console.groq.com** and sign in
2. Navigate to **API Keys** → **Create API Key**
3. Copy the key (starts with `gsk_`)
4. In IPA → **Apps tab** → paste it into the **AI API Key** field → **Save Config**

### Option 2 — OpenAI (paid)

If you already have an OpenAI API key, IPA will use it automatically — no extra setup needed.

1. In IPA → **Apps tab** → paste your OpenAI key (starts with `sk-`) into the **AI API Key** field → **Save Config**

IPA will use **gpt-4o-mini** which is OpenAI's cheapest model. Typical voice queries cost a fraction of a cent each.

### Option 3 — Claude / Anthropic (paid)

If you have an Anthropic API key, IPA will detect it automatically.

1. In IPA → **Apps tab** → paste your Anthropic key (starts with `sk-ant-`) into the **AI API Key** field → **Save Config**

IPA will use **Claude Haiku**, Anthropic's fastest and most affordable model.

Say `ask what's the weather like on Mars` to test whichever key you set up.

> **Note:** AI responses are based on training data and may not reflect recent events, releases, or news.

## Tips

- If audio isn't detected, check Windows microphone permissions.
- If a command doesn't trigger, check **Last Transcript** for misheard words and add aliases.
- You can use **Delete Cache** in the UI if you ever want to remove Python `__pycache__` folders.
