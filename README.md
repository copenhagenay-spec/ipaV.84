# VERA — Voice Enabled Response Assistant

Personal voice assistant for Windows. Speech recognition and TTS run locally — cloud AI is optional.

---

## Installation

1. Download the latest **VERA_Setup** installer from the [Releases](../../releases) page
2. Run it — the installer handles everything automatically
3. Python dependencies, the voice engine (espeak-ng), and the voice model (~310MB) are downloaded and installed silently
4. Launch VERA from the desktop shortcut or Start Menu

> **Requires Python 3.11 or newer.** Download from [python.org](https://www.python.org/downloads/) — check **"Add Python to PATH"** during install.

---

## First Run

The setup wizard opens automatically on first launch:

1. Choose **Language** (English or Spanish)
2. Choose **Listening Mode** — Wake Word, Hold-to-talk, or Push to Toggle
3. Optional: **Import Steam Apps** to add your games as voice commands
4. Click **Finish** — VERA starts listening in the background

---

## Voice Commands

Say `what can I say` at any time to hear all available commands.

| Category | Examples |
|---|---|
| Apps | `open spotify`, `close discord` |
| Search | `search for <query>`, `youtube <query>` |
| Media | `play`, `pause`, `skip`, `volume up` |
| Weather & Date | `weather in <city>`, `what's the date` |
| News | `give me the news` |
| Timers & Reminders | `set a timer 5 minutes`, `remind me to <thing> at <time>` |
| Notes & Memory | `note <text>`, `remember <fact>` |
| Key Binds | `reload` → presses R (configured in Integrations tab) |
| Command Macros | say a phrase → runs a chain of commands (Premium) |
| Discord | `discord <channel> <message>`, `read discord <channel>` |
| Gaming | `start gaming mode`, `show overlay` |
| System | `sleep computer`, `restart computer`, `shut down computer` |
| Conversation | `tell me a joke`, `good morning` |

> **Note:** Key binds may be blocked by anti-cheat software (EAC/BattlEye) in protected games. Use at your own risk.

---

## Key Binds

Map a spoken phrase to a keypress or sequence of keys in the **Integrations** tab:

- Single key: `reload` → `r`
- Combo: `quick save` → `ctrl+s`
- Macro sequence: `eject` → `f1 > space > enter`
- Mouse side buttons supported as push-to-talk key

---

## Command Macros (Premium)

Chain multiple voice commands into one phrase — configured in the **Integrations** tab.

> **Example:** Say "good morning" → VERA opens Spotify, reads the weather, and checks your reminders in sequence.

---

## Steam Import

Click **Import Steam** in the Apps tab to automatically add your installed games as voice commands.

---

## AI Setup (Optional)

The `ask <question>` command supports on-demand AI responses. Paste your key in **Integrations → AI API Key**.

| Provider | Key prefix | Notes |
|---|---|---|
| Groq | `gsk_` | Free — 14,400 requests/day, no credit card |
| OpenAI | `sk-` | Paid — uses gpt-4o-mini |
| Anthropic | `sk-ant-` | Paid — uses Claude Haiku |

VERA detects which provider to use automatically based on your key format.

---

## Troubleshooting

- **Nothing transcribed** — check Windows microphone permissions and your input device in Settings
- **App won't open** — run `run_ipa.cmd` directly to see errors in the terminal
- **Command not triggering** — check **Last Transcript** in the UI for misheard words; use the Training tab to add corrections
- **Crash logs** — saved to `%LocalAppData%\VERA\data\logs\assistant.log`

---

## Uninstall

Use **Add or Remove Programs** → search for VERA, or run the uninstaller from the Start Menu.

Your settings (`config.json`) and memory (`memory.json`) are preserved after uninstall in case you reinstall later.

---

## Manual / Source Install

If you prefer to run from source instead of using the installer:

1. Clone the repo
2. Run `setup_installer.cmd` to install dependencies
3. Run `run_ipa.cmd` to start VERA

---

## Legal

By using VERA you agree to the [Terms of Service](vera/docs/terms.md).

VERA uses open source libraries. See [THIRD-PARTY-LICENSES.md](THIRD-PARTY-LICENSES.md) for full details and LGPL compliance information.
