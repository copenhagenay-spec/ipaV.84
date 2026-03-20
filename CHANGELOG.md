# Changelog

## 0.84.7
- Added text-to-speech (TTS): say `read out <text>` to have IPA speak any text aloud.
- Added Discord integration: send messages to a Discord channel via voice command (`discord <channel> <message>`).
- Added Discord bot support: say `read discord <channel>` to hear the last message from a channel read aloud.
- Added Discord credentials section in the Apps tab (Bot Token, Server ID, per-channel webhook URLs).
- Added pyttsx3 to setup.cmd dependencies.

## 0.84.6.4
- Added "restart assistant" voice command — restarts IPA instantly.
- Added "type <text>" voice command — simulates keyboard input of any text.
- Added mouse side button (back/forward) support for push-to-talk — record via the Hold key Record button.

## 0.84.6.3
- Fixed YouTube commands not triggering due to mishear map corrupting the word "youtube".
- Added "start you do" and "start you tube" as YouTube mishear variants.
- Removed false positive mishear entries that were corrupting normal speech.

## 0.84.6.2
- Added transcript history — last 10 transcripts shown live in the UI (newest first).
- All raw transcripts now logged to `data/logs/transcripts.log`.
- Bug reports now include `transcripts.log`.

## 0.84.6.1
- Added "start youtube", "start you tube", and "start your job" as YouTube trigger phrases.

## 0.84.6
- Expanded mishear corrections with additional Scottish English accent variants for YouTube and other commands.
- General fix for "open the <app>" — leading "the" is now stripped before app lookup.

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
