# Adding Apps to VERA

This guide covers the different ways to add apps to VERA so you can open them by voice.

---

## How It Works

When you say **"open \<app name\>"**, VERA looks up that name in its app list and launches whatever is assigned to it. There are four ways apps get added to that list:

1. **Auto-discovered** — common apps VERA finds automatically on startup
2. **Steam Import** — your entire Steam library added in one click
3. **Voice alias** — you define a shortcut name for any app by voice
4. **Manually via the UI** — type in an app name and path directly in the VERA settings

---

## Auto-Discovered Apps

On every startup VERA scans your PC for common apps and adds any it finds automatically. These include:

- Chrome, Firefox, Edge, Opera, Opera GX
- Steam, VLC, OBS
- Notepad, Calculator, Task Manager, File Explorer

You don't need to do anything — if the app is installed it will just work.

> **Note:** Spotify and Discord are **not** auto-discovered. To open them by voice you need to add them manually — see below for common paths.

---

## Steam Library Import

To add all your Steam games at once:

1. Open the VERA UI
2. Go to the **Apps** tab
3. Click **Import Steam**

VERA will scan your Steam installation and add every game in your library. Once imported, say **"open \<game name\>"** to launch any of them.

> **Example:** "open hell divers 2", "open rust", "open grey hack"

> **Note:** The game name you say should match the Steam title. If a game has a long or unusual name and VERA doesn't recognize it, try adding an alias for it (see below).

---

## Adding an App Manually via the UI

If an app wasn't auto-discovered and isn't on Steam, you can add it manually:

1. Open the VERA UI
2. Go to the **Apps** tab
3. Fill in **App name** — this is what you'll say out loud
4. Fill in **App command** — the full path to the executable or a launch command
5. Click **Add App**

> **Example:** App name: `signal` — App command: `C:\Users\You\AppData\Local\Signal\signal.exe`

**Common paths for apps not auto-discovered:**

| App | App command |
|---|---|
| Spotify | `C:\Users\<YourName>\AppData\Roaming\Spotify\Spotify.exe` |
| Discord | `C:\Users\<YourName>\AppData\Local\Discord\Update.exe --processStart Discord.exe` |

Replace `<YourName>` with your Windows username.

You can also use this to open websites by voice — just put a URL as the app command:

> **Example:** App name: `reddit` — App command: `https://www.reddit.com`

Say **"open reddit"** and VERA will open it in your default browser.

Once added, say **"open \<name\>"** to launch it. You can also click **Test App** to verify it opens correctly before using it by voice.

---

## Adding an Alias by Voice

If an app name is hard to say, too long, or keeps getting misheard, you can create a shorter alias for it.

**Say:** `add alias <your shortcut> for <app name>`

> **Examples:**
> - "add alias hell divers for helldivers 2"
> - "add alias music for spotify"
> - "add alias browser for opera gx"

You can then say **"open \<your shortcut\>"** to launch the app — no restart needed.

---

## Troubleshooting

**"VERA opened the wrong app"**
The app name you said was too close to another app in the list. Try adding an alias with a more unique name.

**"VERA didn't open anything"**
- The app may not be in the list — check if it's a Steam game (run Steam Import) or a common app (restart VERA to trigger auto-discovery)
- Try saying the name more clearly or add an alias

**"My game isn't showing up after Steam Import"**
- Make sure the game is fully installed, not just in your library
- Run Steam Import again after installing the game
