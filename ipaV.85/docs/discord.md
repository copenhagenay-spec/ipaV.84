# Discord Setup Guide

This guide explains how to set up the Discord voice commands in IPA.

---

## Overview

IPA can send and read Discord messages by voice using Discord webhooks. This feature is intended for **server owners and administrators** as it requires the ability to create webhooks in your server.

| What to say | What happens |
|---|---|
| `discord <channel> <message>` | Sends a message to a channel |
| `read discord <channel>` | Reads the last message in a channel aloud |

---

## Requirements

- You must have **Administrator** or **Manage Webhooks** permission in the Discord server
- The channels you want to use must have webhooks created for them

---

## Step 1 — Create a Webhook

For each channel you want IPA to send messages to:

1. Open Discord and go to your server
2. Right-click the channel → **Edit Channel**
3. Go to the **Integrations** tab
4. Click **Webhooks** → **New Webhook**
5. Give it a name (e.g. "IPA") and click **Copy Webhook URL**
6. Click **Save**

---

## Step 2 — Get Your Server and Channel IDs

To enable the **read discord** command you'll need your Server ID and Channel ID.

**Enable Developer Mode first:**
1. Open Discord → **User Settings** → **Advanced**
2. Toggle on **Developer Mode**

**Get your Server ID:**
- Right-click your server icon → **Copy Server ID**

**Channel name:**
- IPA uses the channel name directly — just use the name as it appears in Discord (e.g. "general", "announcements")

---

## Step 3 — Configure IPA

1. Open the IPA UI
2. Go to the **Settings** tab
3. Fill in the following fields:
   - **Discord Webhook URL** — the webhook URL you copied in Step 1
   - **Server ID** — your Discord server ID
   - **Bot Token** — required for reading messages (see below)
   - Channel names are used directly in the voice command — no ID needed
4. Click **Save**

---

## Bot Token (for Read Discord)

Reading messages requires a Discord bot token. This is an advanced feature intended for server owners, administrators, and developers — the send command works with just the webhook and does not require a bot token.

To get a bot token:
1. Go to [discord.com/developers/applications](https://discord.com/developers/applications)
2. Click **New Application** and give it a name
3. Go to the **Bot** tab → click **Add Bot**
4. Under **Token** click **Copy**
5. Paste it into the **Bot Token** field in IPA settings

> ⚠️ **Important:** Your bot token grants full access to your bot — treat it like a password. Never share it publicly, post it in a Discord server, or commit it to a public repository. If your token is ever leaked, reset it immediately in the Discord Developer Portal.

---

## Troubleshooting

**"IPA said the message failed to send"**
- Double check your webhook URL is correct and hasn't been deleted
- Make sure you have an active internet connection

**"Read discord isn't working"**
- Make sure your bot token is entered correctly
- Verify the Server ID and Channel ID are correct
- The bot must be a member of your server to read messages
