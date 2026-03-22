# AI Setup Guide

This guide explains how to set up the **"ask \<question\>"** voice command in IPA.

---

## How It Works

When you say **"ask \<question\>"**, IPA sends your question to an AI provider and reads the answer aloud via text-to-speech. You need an API key from one of the supported providers to use this feature.

---

## Supported Providers

IPA automatically detects which provider to use based on your API key — no extra configuration needed.

| Provider | Key Prefix | Free Tier | Notes |
|---|---|---|---|
| **Groq** | `gsk_...` | Yes — 14,400 requests/day | Recommended |
| **Anthropic (Claude)** | `sk-ant-...` | No — paid | High quality |
| **OpenAI (ChatGPT)** | `sk-...` | No — paid | Requires billing |

> **Recommendation:** Groq is the easiest to get started with — it's free, fast, and requires no payment details.

---

## Setting Up Groq (Free — Recommended)

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up for a free account
3. Navigate to **API Keys** in the left sidebar
4. Click **Create API Key** and copy it
5. Open the IPA UI → **Settings** tab → paste your key into the **API Key** field
6. Click **Save**

That's it. Say **"ask what is the weather today"** to test it.

---

## Setting Up Anthropic / Claude

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign up and add a payment method
3. Navigate to **API Keys** and create a new key
4. Copy the key — it will start with `sk-ant-`
5. Open the IPA UI → **Settings** tab → paste your key into the **API Key** field
6. Click **Save**

---

## Setting Up OpenAI / ChatGPT

1. Go to [platform.openai.com](https://platform.openai.com)
2. Sign up and add a payment method
3. Navigate to **API Keys** and create a new key
4. Copy the key — it will start with `sk-`
5. Open the IPA UI → **Settings** tab → paste your key into the **API Key** field
6. Click **Save**

---

## Notes

- IPA keeps AI answers short — 2 to 3 sentences maximum
- The AI knows the current date and time so you can ask time-sensitive questions
- AI responses may not reflect the very latest news or events depending on the provider's knowledge cutoff
- You only need one API key — IPA will detect the provider automatically

---

## Troubleshooting

**"IPA said it couldn't reach the AI"**
- Check your API key is correct and has no extra spaces
- Make sure you have an active internet connection
- If using Groq, check you haven't exceeded the free tier daily limit

**"The answer seems outdated"**
- This is normal — AI models have a knowledge cutoff date and may not know about very recent events
