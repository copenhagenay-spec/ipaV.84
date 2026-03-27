# Mishear Training

VERA isn't perfect — sometimes it hears the wrong thing, especially with different accents or microphones. The Training tab lets you teach VERA what you actually said so it gets it right next time.

---

## How it works

When VERA doesn't recognize a command, it logs the raw transcript to a file called `data/unmatched.json`. The Training tab shows you everything in that list.

---

## Step by step

1. Open VERA and go to the **Training** tab
2. You'll see a list of phrases VERA didn't understand
3. Click one to select it — it will appear in the **Correct to** field below
4. Clear the field and type what you actually meant (e.g. `open youtube`)
5. Click **Save Correction**

The correction is saved immediately and takes effect right away — no restart needed.

---

## Buttons

| Button | What it does |
|---|---|
| **Save Correction** | Saves the selected phrase as a mishear correction and removes it from the list |
| **Dismiss** | Removes the phrase from the list without saving a correction (use for gibberish or noise) |
| **Refresh** | Reloads the list in case new unmatched transcripts came in while the tab was open |

---

## Where corrections are stored

Your corrections are saved to `data/user_mishears.json` inside the VERA install folder. This file is kept on uninstall so your corrections survive reinstalls.

---

## Tips

- Use **Dismiss** to clear out noise, breathing sounds, or random words VERA picked up that aren't real commands
- Corrections are case-insensitive and punctuation is handled automatically — just type naturally
- If VERA keeps mishearing the same thing, add a correction once and it will work every time going forward
