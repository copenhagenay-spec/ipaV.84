# VERA Voice Command Reference

A full list of everything you can say to VERA. Say **"what can I say"** at any time to see a summary inside the app.

---

## Apps

| What to say | What happens |
|---|---|
| `open <app name>` | Opens the app |
| `launch <app name>` | Same as open |
| `open that again` | Reopens the last app you opened with VERA |
| `close <app name>` | Closes the app |
| `close this` | Closes the currently active window |
| `add alias <shortcut> for <app name>` | Creates a shorter name you can use to open an app |

> **Examples:** "open discord", "open rust", "launch opera gx", "close steam"
>
> **Alias example:** "add alias music for spotify" — then say "open music" to launch Spotify

---

## Web

| What to say | What happens |
|---|---|
| `search for <query>` | Opens a Google search in your browser |
| `web search for <query>` | Same as above |

> **Example:** "search for best graphics settings for rust"

---

## YouTube

| What to say | What happens |
|---|---|
| `open youtube` | Opens YouTube homepage |
| `youtube <query>` | Searches YouTube for your query |
| `youtube play <query>` | Same as above |
| `youtube play` | Play / resume |
| `youtube pause` | Pause |
| `youtube next` / `youtube skip` | Next video |
| `youtube back` / `youtube previous` | Previous video |

> **Example:** "youtube play blinding lights"

---

## Spotify

| What to say | What happens |
|---|---|
| `spotify <query>` | Opens Spotify and searches for your query |
| `spotify play <query>` | Same as above |
| `play` / `pause` | Play or pause current track |
| `skip` / `next` | Skip to next track |
| `back` / `previous` | Go to previous track |

> **Example:** "spotify play eye of the tiger"

---

## Volume

| What to say | What happens |
|---|---|
| `volume up` | Increases system volume by 10% |
| `volume down` | Decreases system volume by 10% |
| `set volume <number>` | Sets system volume to a specific level (0–100) |
| `set volume max` | Sets system volume to 100% |
| `set <app> volume <number>` | Sets the volume for a specific app (0–100) |

> **Example:** "set spotify volume 50", "set discord volume 20"

---

## Muting VERA

| What to say | What happens |
|---|---|
| `mute` / `be quiet` | VERA stops responding to commands until unmuted |
| `unmute` / `okay vera` | VERA resumes responding |

> This mutes VERA's responses — it does not affect your system volume.

---

## Weather & Date

| What to say | What happens |
|---|---|
| `weather in <city>` | Reads the current weather for that city |
| `what's the weather in <city>` | Same as above |
| `what's the date` / `what day is it` | Reads the current date |
| `what time is it` | Reads the current time |

> **Example:** "weather in new york", "what's the date", "what time is it"

> **Tip:** If the game overlay is visible, weather results are also pinned to the top of the overlay in real time.

---

## News

| What to say | What happens |
|---|---|
| `give me the news` | Reads top headlines from your selected news source |
| `news briefing` | Same as above |

> News source is configurable in Settings.

---

## Timers

| What to say | What happens |
|---|---|
| `set a timer <n> minutes` | Sets a timer for n minutes |
| `set a timer <n> seconds` | Sets a timer for n seconds |
| `set a timer <n> hours` | Sets a timer for n hours |
| `cancel timer` / `stop timer` | Cancels all running timers |

> **Examples:** "set a timer 10 minutes", "cancel timer"

---

## Reminders

| What to say | What happens |
|---|---|
| `remind me to <thing> at <time>` | Sets a reminder |
| `remind me at <time> to <thing>` | Same as above |
| `what are my reminders` | Lists all upcoming reminders |
| `cancel all reminders` | Removes all reminders |

> **Examples:** "remind me to take my meds at 9pm", "what are my reminders"

---

## Notes

| What to say | What happens |
|---|---|
| `note <text>` | Saves a note |
| `open notes` | Opens your notes file |
| `list notes` / `show notes` | Reads your notes aloud |
| `delete last note` | Deletes the most recent note |
| `clear all notes` | Deletes all notes |

> **Example:** "note pick up milk on the way home"

---

## Clipboard

| What to say | What happens |
|---|---|
| `copy <text>` | Copies the text to your clipboard |
| `paste` / `paste that` / `paste clipboard` | Pastes whatever is in your clipboard |
| `read clipboard` | Reads your clipboard contents aloud |
| `clear clipboard` | Clears your clipboard |

> **Example:** "copy hello world", "paste that"

---

## System

| What to say | What happens |
|---|---|
| `type <text>` | Types the text as keyboard input |
| `send message <text>` | Types the text and presses Enter |
| `read out <text>` | Reads the text aloud via TTS |
| `sleep computer` | Puts your PC to sleep |
| `restart computer` | Restarts your PC after a 5 second delay |
| `shut down computer` | Shuts down your PC after a 5 second delay |
| `restart assistant` | Restarts VERA |

> **Important:** For `type` and `send message` to work, your cursor must be in a text field — VERA types into whatever is currently focused.

---

## Gaming Mode

| What to say | What happens |
|---|---|
| `start gaming mode` | Strips responses to ultra-short, silences idle chatter, suppresses unrecognized command feedback |
| `stop gaming mode` | Returns VERA to normal behavior |

> **"Gaming Mode"** appears in the status bar while active.

---

## Game Overlay

| What to say | What happens |
|---|---|
| `show overlay` | Shows the transparent always-on-top bar with your last 3 voice exchanges |
| `hide overlay` | Hides the overlay |

> Position and hotkey are configurable in Settings → Game Overlay.

---

## Discord

| What to say | What happens |
|---|---|
| `discord <channel> <message>` | Sends a message to a Discord channel via webhook |
| `discord <server> <channel> <message>` | Sends to a specific server's channel |
| `read discord <channel>` | Reads the last message in a channel aloud |
| `read discord <server> <channel>` | Reads from a specific server's channel |
| `discord delete <channel>` | Deletes the last message sent to a channel |
| `discord purge <channel> <n>` | Bulk deletes up to 100 messages |

> Requires Discord webhook setup in the Discord tab. See the [Discord Setup Guide](discord.md) for details.

---

## AI

| What to say | What happens |
|---|---|
| `ask <question>` | Sends your question to the AI and reads the answer aloud |

> Requires an API key in the Integrations tab. See the [AI Setup Guide](ai-setup.md) for details.
>
> **Example:** "ask what is the capital of France"

---

## Memory

| What to say | What happens |
|---|---|
| `my name is <name>` | Saves your name so VERA remembers it |
| `what is my name` | VERA tells you your saved name |
| `remember <fact>` | Saves a fact for later |
| `forget <thing>` | Removes a saved fact |
| `what do you know about me` | VERA reads back everything she remembers |

> **Examples:** "my name is Alex", "remember my birthday is March 5th", "forget my birthday"

---

## Key Binds

Custom phrases mapped to keypresses — configured in the **Integrations** tab.

> **Example:** Bind "reload" to R so saying "reload" presses R in-game.
>
> ⚠ May be flagged by EAC/BattlEye anti-cheat. See the [Key Binds Guide](keybinds.md).

---

## Command Macros (Premium)

Chain multiple commands into one phrase — configured in the **Integrations** tab.

> **Example:** Say "good morning" → VERA opens Spotify, reads the weather, and checks your reminders — each step waits for VERA to finish speaking before the next begins.

---

## Conversation

| What to say | What happens |
|---|---|
| `I'm tired` / `I'm stressed` / `I'm happy` | VERA responds to your mood |
| `I'm playing <game>` | Sets your activity so VERA is context-aware |
| `tell me a joke` | VERA tells you a joke |

---

## Help

| What to say | What happens |
|---|---|
| `what can I say` | Opens the command reference window |
| `show commands` | Same as above |
| `show help` | Same as above |
