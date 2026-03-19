# IPA Assistant

Offline personal assistant for Windows using Vosk (speech to text).

## Quick Start

1. Install Python 3.10+:
   https://www.python.org/downloads/
2. Double-click:
   `run_ipa.vbs` (no terminal)
3. The first-run wizard will open:
   - Choose **Language** (English or Spanish)
   - Choose **Mode** (Hold-to-talk, Hotkey, or Timed)
   - Click **Install Dependencies** (one-time)
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

- Open apps: say `open <app>`
- App aliases: say an alias to open a target app
- Custom actions: phrase -> command
- Web search: say `search for <query>`
- YouTube: open, search, play/pause/next/back
- Spotify media controls: `play`, `pause`, `skip`, `back`
- Timers: say `set a timer 5 minutes`
- Notes: `note ...`, `open notes`, `delete last note`, `clear all notes`
- Sleep PC: `sleep computer`
- System audio mute/unmute: `sound on`, `sound off`
- Tray controls: show/hide/start/stop/restart/exit
- Bug report button (zips log + settings)
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

## Tips

- If audio isn't detected, check Windows microphone permissions.
- If a command doesn't trigger, check **Last Transcript** for misheard words and add aliases.
