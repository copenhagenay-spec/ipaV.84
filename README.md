# IPA Assistant

Offline personal assistant for Windows using Vosk speech recognition.

---

## Quick Start

1. Install Python 3.10+ from [python.org](https://www.python.org/downloads/) — check **"Add Python to PATH"** during install
2. Double-click **`setup.cmd`** to install dependencies (one-time)
3. Double-click **`run_ipa.cmd`** to launch IPA
4. The setup wizard will open — follow the steps to configure IPA and download a language model

IPA will run in the background after the wizard finishes. Look for the icon in your system tray.

For a detailed walkthrough see the [Setup Guide](ipaV.85/docs/setup.md).

---

## Documentation

| Guide | Description |
|---|---|
| [Setup Guide](ipaV.85/docs/setup.md) | Full installation and first-time setup walkthrough |
| [Voice Commands](ipaV.85/docs/commands.md) | Complete list of voice commands with examples |
| [Adding Apps](ipaV.85/docs/adding-apps.md) | How to add apps, import Steam games, and create aliases |
| [AI Setup](ipaV.85/docs/ai-setup.md) | Setting up Groq, Claude, or OpenAI for the ask command |
| [Discord Setup](ipaV.85/docs/discord.md) | Configuring Discord send and read commands |

---

## Features

- Say **"what can I say"** to see all available commands inside the app
- Open apps and games by voice — `open <app>` / `open <game>`
- Full Steam library import — add all your games in one click
- App aliases — create short voice shortcuts for any app
- Web search — `search for <query>`
- YouTube — search and media controls by voice
- Spotify — search by voice, play/pause/skip controls
- Timers — `set a timer 10 minutes`
- Notes — save, open, and delete notes by voice
- Type text — `type <text>` simulates keyboard input
- Send message — `send message <text>` types and hits Enter
- Text-to-speech — `read out <text>`
- AI query — `ask <question>` — answered aloud via Groq, Claude, or OpenAI
- Discord — send and read messages by voice via webhook
- Restart/shutdown PC by voice
- Close apps by voice — `close <app>` / `close this`
- Mouse side button support for push-to-talk
- Bug report button — zips logs and settings for easy sharing
- Check for updates from the UI

---

## Files

| Path | Description |
|---|---|
| `data/config.json` | Your settings |
| `data/model/en/` | English language model |
| `data/model/es/` | Spanish language model |
| `data/logs/` | Crash logs and transcripts |
| `data/assets/` | Icons |

---

## Troubleshooting

- If nothing is transcribed, check Windows microphone permissions and your selected input device
- If a command doesn't trigger, check **Last Transcript** in the UI for misheard words — add an alias if needed
- If the app won't open, run `run_ipa.cmd` to see errors in the terminal
- Crash logs are saved to `data/logs/assistant.log`

---

## Uninstall

Double-click **`uninstall.cmd`**. You'll be asked whether to remove your settings and language model. To fully remove IPA, delete the IPA folder after running the uninstaller.
