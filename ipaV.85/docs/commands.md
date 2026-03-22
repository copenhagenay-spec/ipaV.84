# IPA Voice Command Reference

A full list of everything you can say to IPA. Say **"what can I say"** at any time to see a summary inside the app.

---

## Apps

| What to say | What happens |
|---|---|
| `open <app name>` | Opens the app |
| `launch <app name>` | Same as open |
| `open that again` | Reopens the last app you opened with IPA |
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

## Timers

| What to say | What happens |
|---|---|
| `set a timer <n> minutes` | Sets a timer for n minutes |
| `set a timer <n> seconds` | Sets a timer for n seconds |
| `set a timer <n> hours` | Sets a timer for n hours |

> **Example:** "set a timer 10 minutes"

---

## Notes

| What to say | What happens |
|---|---|
| `note <text>` | Saves a note |
| `open notes` | Opens your notes |
| `delete last note` | Deletes the most recent note |
| `clear all notes` | Deletes all notes |

> **Example:** "note pick up milk on the way home"

---

## System

| What to say | What happens |
|---|---|
| `type <text>` | Types the text as keyboard input |
| `send message <text>` | Types the text and presses Enter |
| `read out <text>` | Reads the text aloud via text-to-speech |

> **Important:** For `type` and `send message` to work, you must have your cursor clicked into a text field first — IPA types into whatever is currently focused on screen.
| `sleep computer` | Puts your PC to sleep |
| `restart computer` | Restarts your PC after a 5 second delay |
| `shut down computer` | Shuts down your PC after a 5 second delay |
| `restart assistant` | Restarts IPA |

> **Examples:** "type hello world", "send message on my way", "shut down computer"

---

## Discord

| What to say | What happens |
|---|---|
| `discord <channel> <message>` | Sends a message to a Discord channel via webhook |
| `read discord <channel>` | Reads the last message in a channel aloud |

> Requires Discord webhook setup in the IPA settings. See the [Discord Setup Guide](discord.md) for details.
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

## Aliases

| What to say | What happens |
|---|---|
| `add alias <name> for <app>` | Creates a voice shortcut for an app |

> **Example:** "add alias music for spotify" — after this you can say "open music" to open Spotify.
>
> Restart IPA after adding an alias for it to take effect.

---

## Key Binds

Custom phrases mapped to keypresses — configured in the **Actions** tab of the IPA UI.

> **Example:** You could bind "push to talk" to your in-game PTT key so IPA triggers it on command.

---

## Help

| What to say | What happens |
|---|---|
| `what can I say` | Opens the command reference window |
| `show commands` | Same as above |
| `show help` | Same as above |
