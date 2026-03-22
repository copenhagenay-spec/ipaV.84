# Adding Apps to IPA

This guide covers the different ways to add apps to IPA so you can open them by voice.

---

## How It Works

When you say **"open \<app name\>"**, IPA looks up that name in its app list and launches whatever is assigned to it. There are four ways apps get added to that list:

1. **Auto-discovered** — common apps IPA finds automatically on startup
2. **Steam Import** — your entire Steam library added in one click
3. **Voice alias** — you define a shortcut name for any app by voice
4. **Manually via the UI** — type in an app name and path directly in the IPA settings

---

## Auto-Discovered Apps

On every startup IPA scans your PC for common apps and adds any it finds automatically. These include:

- Chrome, Firefox, Edge, Opera GX
- Discord, Spotify, Steam
- Notepad, Calculator, Task Manager, VLC, OBS

You don't need to do anything — if the app is installed it will just work.

---

## Steam Library Import

To add all your Steam games at once:

1. Open the IPA UI
2. Go to the **Apps** tab
3. Click **Import Steam**

IPA will scan your Steam installation and add every game in your library. Once imported, say **"open \<game name\>"** to launch any of them.

> **Example:** "open hell divers 2", "open rust", "open grey hack"

> **Note:** The game name you say should match the Steam title. If a game has a long or unusual name and IPA doesn't recognize it, try adding an alias for it (see below).

---

## Adding an App Manually via the UI

If an app wasn't auto-discovered and isn't on Steam, you can add it manually:

1. Open the IPA UI
2. Go to the **Apps** tab
3. Fill in **App name** — this is what you'll say out loud
4. Fill in **App command** — the full path to the executable or a launch command
5. Click **Add App**

> **Example:** App name: `signal` — App command: `C:\Users\You\AppData\Local\Signal\signal.exe`

Once added, say **"open \<name\>"** to launch it. You can also click **Test App** to verify it opens correctly before using it by voice.

---

## Adding an Alias by Voice

If an app name is hard to say, too long, or keeps getting misheard, you can create a shorter alias for it.

**Say:** `add alias <your shortcut> for <app name>`

> **Examples:**
> - "add alias hell divers for helldivers 2"
> - "add alias music for spotify"
> - "add alias browser for opera gx"

After adding an alias, **restart IPA** for it to take effect. You can then say **"open \<your shortcut\>"** to launch the app.

---

## Troubleshooting

**"IPA opened the wrong app"**
The app name you said was too close to another app in the list. Try adding an alias with a more unique name.

**"IPA didn't open anything"**
- The app may not be in the list — check if it's a Steam game (run Steam Import) or a common app (restart IPA to trigger auto-discovery)
- Try saying the name more clearly or add an alias

**"My game isn't showing up after Steam Import"**
- Make sure the game is fully installed, not just in your library
- Run Steam Import again after installing the game
