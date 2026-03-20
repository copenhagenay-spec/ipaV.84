# Changelog

## 0.84.5
- Added mishear corrections for common speech recognition variants (e.g. "your job" → "youtube").

## 0.84.4
- Added `setup.cmd` for installing dependencies without needing the UI (fixes fresh install bootstrapping).
- Updated README with clearer install steps including standalone Python and PATH instructions.

## 0.84.3
- Fixed update check failing silently — now shows the actual error message.
- Fixed VERSION URL pointing to wrong path on GitHub.
- Update failures are now logged to `assistant.log`.

## 0.84.2
- Added "What can I say?" voice command — shows a scrollable popup of all available commands including custom apps and actions.

## 0.84.1
- Added scrollable setup wizard to prevent cut-off.
- Added hotkey and hold-key record buttons.
- Added system audio mute/unmute voice commands.
- Added "Check for Updates" with prompt-to-install.
- Added bug report button (zips logs + config).
- Improved tray behavior (left-click shows window).
- Set IPA window icon and AppUserModelID.
- Added VBS launcher to run without terminal.
- UI layout cleanup and sectioning.
