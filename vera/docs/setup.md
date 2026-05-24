# VERA Setup Guide

This guide walks you through getting VERA up and running from scratch.

---

## Step 1 — Download the Installer

1. Go to the [VERA releases page](https://github.com/copenhagenay-spec/Vera-beta/releases)
2. Download the latest `VERA_Setup_x.x.x.exe`

---

## Step 2 — Run the Installer

Double-click the installer and follow the prompts. The installer handles everything automatically:

- Python package dependencies
- Kokoro TTS model files (~310MB, downloaded once)

A progress screen shows each step. This takes a minute or two depending on your connection.

> **Note:** You do not need to install Python manually — VERA's installer finds your existing Python installation. If Python is not installed, get it from [python.org](https://python.org) (3.11 or newer, check **"Add Python to PATH"**).

---

## Step 3 — Guided Tour

On first launch VERA walks you through the basics with a short spotlight tour:

1. **PTT Key** — click Record and press any key, mouse button, or controller button
2. **Listening Mode** — choose Hold-to-talk, Toggle, or Wake Word
3. You're done — say **"what can I say"** to see everything VERA can do

You can skip the tour and configure everything later in **Settings**.

---

## Step 4 — Start Using VERA

VERA starts listening in the background automatically — look for the icon in your system tray.

> **Steam users:** Your Steam library is imported automatically on every launch. Games you install or uninstall are kept in sync with no manual action needed. Gaming mode also activates automatically when a Steam game is running.

---

## Running from Source

If you're running VERA from source instead of the installer, use `setup_installer.cmd` to install dependencies manually, then `run_ipa.cmd` to launch.

---

## Updating VERA

Open the VERA UI and click **Check for Updates** in Settings → Utilities. VERA will compare your version against the latest release and prompt you if an update is available.

Your settings, memory, and macros are preserved during updates.

---

## Uninstalling VERA

Use **Add/Remove Programs** in Windows Settings, or run `uninstall.cmd` in the VERA folder. Your `config.json` and `memory.json` are left behind so your settings are preserved if you reinstall.
