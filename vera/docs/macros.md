# Command Macros

Command Macros let you chain multiple voice commands into one phrase. Each step runs in order, waiting for VERA to finish speaking before moving to the next.

> **Command Macros are a Premium feature.**

---

## How It Works

You define a trigger phrase and a list of steps. When you say the phrase, VERA runs each step in sequence — opening apps, reading the weather, checking reminders, whatever you set up.

> **Example:** Say "good morning" → VERA opens Spotify, reads the weather, then lists your reminders — each one finishing before the next starts.

---

## Setting Up a Macro

1. Open the VERA UI
2. Go to the **Integrations** tab
3. Scroll to **Command Macros**
4. Enter a **Phrase** — what you'll say to trigger the macro (e.g. `good morning`)
5. Enter a **Step** — any voice command VERA understands (e.g. `open spotify`)
6. Click **Add Step** — the step appears in the pending list
7. Repeat steps 5–6 to add more steps
8. Click **Add Macro** to save it

The macro appears in the list and is active immediately — no restart needed.

---

## What You Can Use as Steps

Any command VERA understands can be a macro step:

- `open <app>` — opens an app
- `weather in <city>` — reads the weather
- `what are my reminders` — lists reminders
- `give me the news` — reads headlines
- `set volume <number>` — sets volume
- `spotify play <query>` — plays music

> **Tip:** Steps run in the order you add them. VERA waits for TTS to finish before starting the next step, so nothing overlaps.

---

## Managing Macros

- Click a macro in the list to select it
- Click **Remove Selected** to delete it

---

## Troubleshooting

**"VERA says the phrase but nothing happens"**
- Make sure Premium is enabled in your settings
- Check that the macro is in the list under Command Macros

**"Steps are running out of order"**
- Steps always run top to bottom in the order they were added — remove the macro and re-add it with the steps in the correct order

**"One step interrupted another"**
- This can happen if a step triggers a long background process — try reordering so longer steps come last
