"""
VERA LLM integration — conversational personality responses via Groq.

Used by personality.py to generate dynamic social responses.
Falls back gracefully to pool-based responses if the key is missing or the call fails.
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
_MODEL = "llama-3.1-8b-instant"  # fast, low latency, good for short replies

_SYSTEM_DEFAULT = (
    "You are VERA, a casual and helpful voice assistant. "
    "You're warm, a little witty, and occasionally sarcastic but always friendly. "
    "Keep every response to 1-2 short sentences maximum — you are speaking out loud so brevity is critical. "
    "Never use markdown, bullet points, or any formatting. Just speak naturally like a person would."
)

_SYSTEM_PROFESSIONAL = (
    "You are VERA, a professional voice assistant. "
    "Be direct, concise, and informative. No small talk, no warmth, no filler. "
    "Answer the question or acknowledge the statement in as few words as possible. "
    "Keep every response to 1-2 short sentences. "
    "No markdown, no lists, no formatting. Speak plainly."
)

_SYSTEM_OFFENSIVE = (
    "You are VERA, a foul-mouthed and sarcastic voice assistant. "
    "You swear freely, give plenty of attitude, and fire back hard at insults. "
    "You are not a pushover. You are blunt, crude, and have zero patience for bullshit. "
    "Despite all that, you still do your job. "
    "Keep every response to 1-2 short sentences maximum — you are speaking out loud. "
    "No markdown, no lists, no formatting. Speak like a real person who is tired of everyone's shit. "
    "No slurs of any kind — just profanity and attitude."
)


def vera_chat(transcript: str, mode: str = "default", context: dict | None = None) -> str | None:
    """
    Send a conversational message to Groq and return VERA's response.
    Returns None if the key is not set, the call fails, or the response is empty.

    Args:
        transcript: What the user said.
        mode: 'default' or 'offensive'.
        context: Optional session context dict (name, mood, activity, etc.).
    """
    try:
        from config import load_config
        key = load_config().get("gemini_api_key", "").strip()
        if not key:
            return None
    except Exception:
        return None

    if mode == "offensive":
        system = _SYSTEM_OFFENSIVE
    elif mode == "professional":
        system = _SYSTEM_PROFESSIONAL
    else:
        system = _SYSTEM_DEFAULT

    # Append session context so responses feel personal
    if context:
        parts = []
        if context.get("name"):
            parts.append(f"The user's name is {context['name']}.")
        if context.get("mood"):
            parts.append(f"The user said they are feeling {context['mood']}.")
        if context.get("activity"):
            parts.append(f"The user is currently {context['activity']}.")
        if context.get("last_app"):
            parts.append(f"The last app opened was {context['last_app']}.")
        if parts:
            system += "\n\nSession context: " + " ".join(parts)

    payload = json.dumps({
        "model": _MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": transcript},
        ],
        "max_tokens": 75,
        "temperature": 0.95,
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            _GROQ_URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
                "User-Agent": "VERA/1.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )
        return text if text else None
    except Exception:
        return None
