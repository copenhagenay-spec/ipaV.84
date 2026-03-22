# IPA Setup Guide

This guide walks you through everything you need to get IPA up and running from scratch.

---

## Step 1 — Download IPA

1. Go to the [IPA GitHub releases page](https://github.com/copenhagenay-spec/IPA-alpha/releases)
2. Download the latest version zip
3. Extract it to a folder you won't move — IPA runs from wherever you put it

> **Tip:** A good place is somewhere like `C:\IPA\` or your Desktop. Avoid putting it inside Program Files.

---

## Step 2 — Install Dependencies

Double-click **`setup.cmd`** first. This installs all the Python packages IPA needs to run. A command prompt window will open and close automatically when done.

> If you see any errors here, make sure Python is installed on your PC. Download it from [python.org](https://python.org) — make sure to check **"Add Python to PATH"** during install.

> You only need to run `setup.cmd` once.

---

## Step 3 — Run the Setup Wizard

Once dependencies are installed, double-click **`run_ipa.cmd`**. The setup wizard will open automatically.

The wizard walks you through the rest of the setup — language model download, push to talk configuration, Steam import, and shortcut creation. Work through each section top to bottom and click **Finish** when done. IPA will launch immediately after.

---

## Step 4 — Download a Language Model

IPA needs a voice recognition model to understand what you say. There are two options:

| Model | Size | Best For |
|---|---|---|
| **English (Small)** | ~40MB | Fast download, decent accuracy |
| **English (Standard)** | ~128MB | Better accuracy, handles accents well |

Click the button for your preferred model and wait for the download to complete. A confirmation message will appear when it's done.

> **Recommendation:** If you have a non-standard accent or find the small model misses words, go with the Standard model.

---

## Step 5 — Configure Your Settings

### Push to Talk
IPA uses **Hold mode** — hold your assigned key or mouse button while speaking and release when done. A beep will signal when IPA is ready to listen.

Click **Record** to assign your key or button.

### AI Assistant (optional)
If you want to use the **"ask \<question\>"** command, you'll need an API key. See the [AI Setup Guide](ai-setup.md) for details.

---

## Step 6 — Import Your Steam Library (optional)

Click **Import Steam Apps** to automatically add all your Steam games to IPA. Once imported you can open any game by saying **"open \<game name\>"**.

> This scans your Steam installation automatically — no manual entry needed.

---

## Step 7 — Desktop Shortcut

Make sure **Create desktop shortcut** is checked before finishing. This puts an IPA shortcut on your desktop that you can also pin to your taskbar or Start menu.

---

## Step 8 — Finish

Click **Finish**. IPA will start running in the background — look for the IPA icon in your system tray.

You're ready to go. Say **"what can I say"** at any time to see a full list of available commands.

---

## Updating IPA

IPA does not automatically notify you of updates. To check manually, open the IPA UI and click **Check for Updates** — it will compare your version against the latest release and prompt you to update if one is available.

Your settings and data are preserved during updates.

---

## Uninstalling IPA

Run **`uninstall.cmd`** in the IPA folder. You'll be asked if you want to remove your settings and language model as well. Choosing **Y** does a full clean wipe. Choosing **N** keeps your data in case you reinstall later.
