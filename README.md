# VERA — Voice Enabled Response Assistant

Offline personal voice assistant for Windows. No cloud, no API key required — everything runs locally on your machine.

---

## Installation

1. Download the latest **VERA_Setup_x.x.x.exe** from the [Releases](../../releases) page
2. Run it — Windows will ask for admin permission (needed to install a voice component)
3. The installer will automatically download Python dependencies and the voice model (~310MB, one-time)
4. Launch VERA from the desktop shortcut or Start Menu

> **Requires Python 3.11 or newer.** Download from [python.org](https://www.python.org/downloads/) — check **"Add Python to PATH"** during install.

---

## First Run

The setup wizard opens automatically on first launch:

1. Choose **Language** (English or Spanish)
2. Choose **Mode** — Hold-to-talk, Hotkey, or Timed
3. Download a speech model if prompted (English model is bundled, Spanish downloads separately)
4. Optional: **Import Steam Apps** to add your games as voice commands
5. Click **Finish** — VERA starts listening in the background

---

## Voice Commands

Say `what can I say` at any time to hear all available commands.

| Category | Examples |
|---|---|
| Apps | `open spotify`, `close discord` |
| Search | `search for <query>`, `youtube <query>` |
| Media | `play`, `pause`, `skip`, `volume up`, `mute` |
| Timers | `set a timer 5 minutes`, `cancel timer` |
| Notes | `note <text>`, `open notes`, `delete last note` |
| Clipboard | `copy that`, `read clipboard`, `clear clipboard` |
| Keybinds | `reload` → presses R (configured in Actions tab) |
| Discord | `discord <channel> <message>`, `read discord <channel>`, `discord delete <channel>`, `discord purge <channel> <n>` |
| System | `sleep computer`, `restart assistant` |
| Conversation | `tell me a joke`, `what's your name`, `good morning` |

> **Note:** Keybinds may be blocked by anti-cheat software (EAC/BattlEye) in protected games. Use at your own risk.

---

## Keybinds & Macros

Map a spoken phrase to a keypress or sequence of keys in the **Actions** tab:

- Single key: `reload` → `r`
- Combo: `quick save` → `ctrl+s`
- Macro sequence: `eject` → `f1 > space > enter`
- Mouse side buttons supported as push-to-talk key

---

## Steam Import

Click **Import Steam** in the Apps tab to automatically add your installed games as voice commands.

---

## AI Setup (Optional)

The `ask <question>` command supports on-demand AI responses. Paste your key in **Apps → AI API Key**.

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
- **Command not triggering** — check **Last Transcript** in the UI for misheard words, add a mishear correction
- **Crash logs** — saved to `%LocalAppData%\VERA\data\logs\assistant.log`

---

## Uninstall

Use **Add or Remove Programs** → search for VERA, or run the uninstaller from the Start Menu.

Your settings (`config.json`) and memory (`memory.json`) are preserved after uninstall in case you reinstall later.

---

## Manual / Source Install

If you prefer to run from source instead of using the installer:

1. Clone the repo
2. Run `setup.cmd` to install dependencies
3. Run `run_ipa.cmd` to start VERA
