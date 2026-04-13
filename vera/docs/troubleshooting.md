# Troubleshooting

Common issues and how to fix them. If your problem isn't listed here, submit a bug report via **Settings → Utilities → Bug Report**.

---

## VERA Won't Start

**"Run_ipa.cmd opens and closes immediately"**
- Open a terminal, navigate to your VERA folder, and run `python assistant.py` directly to see the full error message
- Make sure Python 3.11 or newer is installed and added to PATH
- Run `setup_installer.cmd` to reinstall dependencies

**"Missing dependency" error on launch**
- Run `setup_installer.cmd` from your VERA folder — it reinstalls all required packages
- If the error persists, check that your Python version is 3.11 or newer: open a terminal and run `python --version`

---

## Microphone / Not Hearing Commands

**"VERA doesn't respond to anything I say"**
- Check Windows microphone permissions: **Settings → Privacy & Security → Microphone** — make sure microphone access is on
- Open the VERA UI and check **Last Transcript** in the status bar — if it's blank, VERA isn't hearing you
- Go to **Settings → Recording** and make sure the correct input device is selected
- Try speaking closer to your microphone or increasing your mic volume in Windows Sound settings

**"VERA hears me but gets the words wrong"**
- Check **Last Transcript** in the VERA UI to see what was transcribed
- Speak more slowly and clearly
- Use the **Training** tab to add corrections for commonly misheard words
- Try a different listening mode — Hold-to-talk reduces background noise compared to Wake Word

**"Wake word isn't triggering"**
- Make sure you're saying "vera" clearly before your command
- Background noise can prevent wake word detection — try Hold-to-talk mode instead
- Check that your microphone input level is sufficient in Windows Sound settings

---

## Commands Not Working

**"VERA says she doesn't understand"**
- Check **Last Transcript** to see what was heard — the issue may be a mishearing
- Say **"what can I say"** to review all available commands
- Make sure the command you're using matches the format in the [Command Reference](commands.md)

**"Open \<app\> doesn't work"**
- The app may not be in VERA's list — check the **Apps** tab in the UI
- If it's a Steam game, run **Import Steam** in the Apps tab
- If it's not on Steam, add it manually — see [Adding Apps](adding-apps.md)
- Spotify and Discord are not auto-discovered and must be added manually

**"Close this hung up VERA"**
- This was fixed in v0.97.7.1 — update VERA via **Settings → Utilities → Check Updates**

**"Key binds aren't working in my game"**
- Some games with anti-cheat (EasyAntiCheat, BattlEye) block synthetic keypresses — see [Key Binds](keybinds.md) for details
- Make sure the game window is focused when the command fires

**"Macros aren't triggering"**
- Command Macros require Premium — check that Premium is enabled in Settings
- Make sure the macro is listed under Command Macros in the Integrations tab

---

## Audio / TTS

**"VERA isn't speaking"**
- Check that your output device is correct in **Settings → TTS Output Device**
- Make sure your speakers or headset aren't muted
- Try a different TTS voice in **Settings → Voice**

**"VERA's voice sounds wrong or robotic"**
- Try a different voice in **Settings → Voice** — there are 11 Kokoro voices available
- Make sure espeak-ng was installed correctly — run `setup_installer.cmd` if unsure

---

## AI / Ask Command

**"VERA says it can't reach the AI"**
- Check your API key in **Integrations → AI API Key** — make sure there are no extra spaces
- Make sure you have an active internet connection
- If using Groq, check you haven't exceeded the free tier daily limit (14,400 requests/day)

**"My Anthropic key isn't being recognized"**
- Make sure the key starts with `sk-ant-` — if it doesn't, it may be an OpenAI or Groq key
- Re-paste the key from your Anthropic console to avoid clipboard artifacts

---

## Discord

**"Messages aren't sending"**
- Check that your webhook URL is correct and hasn't been deleted from Discord
- Make sure you have an active internet connection
- See [Discord Setup](discord.md) to verify your configuration

**"Read discord isn't working"**
- Reading messages requires a bot token — webhook alone is not enough
- Make sure your bot is a member of the server and has access to the channel
- See [Discord Setup](discord.md) for full bot setup instructions

---

## Overlay

**"The overlay isn't showing"**
- Say "show overlay" or press your assigned hotkey
- If it's off-screen, change the position in **Settings → Game Overlay** to Top Left

**"The overlay is interfering with my game"**
- The overlay is click-through by design and should not block input
- If you're having issues, try repositioning it or hiding it with "hide overlay"

---

## Updates

**"Check Updates says I'm up to date but I'm not on the latest version"**
- VERA compares versions against the GitHub releases page — make sure you have an internet connection
- You can always download the latest installer manually from the [releases page](https://github.com/copenhagenay-spec/Vera-beta/releases)

---

## Crash Logs

If VERA crashes, logs are saved to:
```
%LocalAppData%\VERA\data\logs\assistant.log
```
You can include this file when submitting a bug report via **Settings → Utilities → Bug Report**.
