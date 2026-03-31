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

> **Examples:** "open discord", "open rust", "launch opera gx", "close steam"

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
| `sound on` / `sound off` | Unmute / mute |

> **Example:** "spotify play eye of the tiger"

---

## Volume

| What to say | What happens |
|---|---|
| `mute` / `mute audio` / `sound off` | Mutes system volume |
| `unmute` / `sound on` / `audio on` | Restores volume to previous level |
| `volume up` | Increases volume by 10% |
| `volume down` | Decreases volume by 10% |
| `set volume <number>` | Sets volume to a specific level (0–100) |
| `set volume max` | Sets volume to 100% |

> **Examples:** "mute", "set volume 50", "volume up"

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

## Notes

| What to say | What happens |
|---|---|
| `note <text>` | Saves a note |
| `open notes` | Opens your notes |
| `list notes` / `show notes` | Reads your notes aloud |
| `delete last note` | Deletes the most recent note |
| `clear all notes` | Deletes all notes |

> **Example:** "note pick up milk on the way home"

---

## Clipboard

| What to say | What happens |
|---|---|
| `read clipboard` | Reads your clipboard aloud |
| `copy <text>` | Copies text to clipboard |
| `paste clipboard` / `paste that` / `paste it` | Pastes clipboard contents |
| `clear clipboard` | Clears the clipboard |

> **Examples:** "copy hello world", "read clipboard", "paste that"

---

## System

| What to say | What happens |
|---|---|
| `type <text>` | Types the text as keyboard input |
| `send message <text>` | Types the text and presses Enter |
| `read out <text>` | Reads the text aloud via text-to-speech |
| `sleep computer` | Puts your PC to sleep |
| `restart computer` | Restarts your PC after a 5 second delay |
| `shut down computer` | Shuts down your PC after a 5 second delay |
| `restart assistant` | Restarts VERA |

> **Important:** For `type` and `send message` to work, you must have your cursor clicked into a text field first — VERA types into whatever is currently focused on screen.
>
> **Examples:** "type hello world", "send message on my way", "shut down computer"

---

## Discord

| What to say | What happens |
|---|---|
| `discord <channel> <message>` | Sends a message to a Discord channel via webhook |
| `read discord <channel>` | Reads the last message in a channel aloud |

> Requires Discord webhook setup in the VERA settings. See the [Discord Setup Guide](discord.md) for details.
>
> **Note:** To create a webhook you must have **Administrator** or **Manage Webhooks** permission in the Discord server. This feature is intended for server owners and administrators.

---

## AI

| What to say | What happens |
|---|---|
| `ask <question>` | Sends your question to the AI and reads the answer aloud |

> Requires an API key. See the [AI Setup Guide](ai-setup.md) for details.
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

## Aliases

| What to say | What happens |
|---|---|
| `add alias <name> for <app>` | Creates a voice shortcut for an app |

> **Example:** "add alias music for spotify" — after this you can say "open music" to open Spotify.
>
> Restart VERA after adding an alias for it to take effect.

---

## Key Binds

Custom phrases mapped to keypresses — configured in the **Actions** tab of the VERA UI.

> **Example:** You could bind "push to talk" to your in-game PTT key so VERA triggers it on command.

---

## Conversation

| What to say | What happens |
|---|---|
| `I'm tired` / `I'm stressed` / `I'm happy` | VERA responds to your mood |
| `I'm playing <game>` | Sets your activity so VERA is context-aware |
| `tell me a joke` / `joke` | VERA tells you a joke |

---

## Help

| What to say | What happens |
|---|---|
| `what can I say` | Opens the command reference window |
| `show commands` | Same as above |
| `show help` | Same as above |

---

## Mishear Training

VERA didn't understand something? The Training tab lets you correct it so it works next time.

> See the [Mishear Training Guide](training.md) for details.
