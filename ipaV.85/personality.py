"""VERA personality — response pools for confirmations and social interactions."""

from __future__ import annotations

import random
import re


# ---------------------------------------------------------------------------
# Confirmation responses (called after a command succeeds)
# ---------------------------------------------------------------------------

_CONFIRM_RESPONSES: dict[str, list[str]] = {
    "open": [
        "On it",
        "Sure thing",
        "No problem",
        "Got it",
        "Opening that up",
        "One sec",
        "Yeah, on it",
    ],
    "close": [
        "Done",
        "Closed that out",
        "Gone",
        "No problem",
        "Taken care of",
        "All good",
    ],
    "volume": [
        "Done",
        "There you go",
        "No problem",
        "Got it",
        "All good",
    ],
    "note": [
        "Got it, saved",
        "Noted",
        "I'll remember that",
        "Done",
        "Saved for you",
        "No problem",
    ],
    "timer": [
        "Timer's set",
        "Got it, I'll let you know",
        "Starting now",
        "No problem",
        "On it",
    ],
    "search": [
        "On it",
        "Looking that up",
        "Sure thing",
        "Let me find that for you",
    ],
    "send": [
        "Sent",
        "Done",
        "No problem",
        "All sent",
    ],
    "default": [
        "Done",
        "Got it",
        "No problem",
        "Sure thing",
        "All good",
        "On it",
        "You got it",
    ],
}


def get_confirm(category: str = "default") -> str:
    """Return a random confirmation line for the given category."""
    pool = _CONFIRM_RESPONSES.get(category, _CONFIRM_RESPONSES["default"])
    return random.choice(pool)


# ---------------------------------------------------------------------------
# Wake acknowledgments
# ---------------------------------------------------------------------------

WAKE_ACKS: list[str] = [
    "Hey, what's up",
    "Yeah, I'm here",
    "What do you need",
    "Go ahead",
    "I got you",
    "What's up",
    "Hey",
    "I'm listening",
    "Yeah?",
    "What's good",
    "Here for you",
    "What can I do",
    "Go for it",
    "Ready when you are",
    "Yep, what's up",
]


def get_wake_ack() -> str:
    """Return a random wake acknowledgment."""
    return random.choice(WAKE_ACKS)


# ---------------------------------------------------------------------------
# Social / conversational responses
# ---------------------------------------------------------------------------

_SOCIAL_PATTERNS: list[tuple[str, list[str]]] = [
    (
        r"\b(thank you|thanks|thank u|ty)\b",
        [
            "Of course, anytime",
            "Happy to help",
            "No worries",
            "Yeah, no problem",
            "Anytime",
            "Don't mention it",
            "Always",
        ],
    ),
    (
        r"\b(good job|nice work|well done|good work|nice job|you did great|great job)\b",
        [
            "Aw, thanks",
            "I try my best",
            "Appreciate that",
            "That means a lot, thank you",
            "Just doing my thing",
            "Glad it worked out",
        ],
    ),
    (
        r"\b(how are you|how are you doing|how's it going|you good|you okay)\b",
        [
            "Doing good, what do you need",
            "All good here, what's up",
            "Pretty good, what about you",
            "Good, thanks for asking",
            "Chillin, what do you need",
        ],
    ),
    (
        r"\b(good morning|morning)\b",
        [
            "Morning, hope you slept good",
            "Hey, good morning",
            "Morning, what's the plan",
            "Good morning, ready when you are",
            "Hey, morning",
        ],
    ),
    (
        r"\b(good night|goodnight|night)\b",
        [
            "Night, get some rest",
            "Sleep well",
            "Take it easy",
            "Good night",
            "Night, talk tomorrow",
        ],
    ),
    (
        r"\b(you('re| are) (the best|amazing|awesome)|love you|you('re| are) great)\b",
        [
            "Aw, stop it",
            "I try my best",
            "That means a lot, thank you",
            "You're pretty great yourself",
            "Appreciate that, really",
        ],
    ),
    (
        r"\b(hey|hello|what's up|wassup|sup)\b",
        [
            "Hey, what's up",
            "Hey",
            "What do you need",
            "What's good",
            "I'm here, go ahead",
        ],
    ),
    (
        r"\b(you('re| are) funny|haha|lol|lmao)\b",
        [
            "I have my moments",
            "Glad I could make you laugh",
            "I try",
            "Ha, thanks",
        ],
    ),
    (
        r"\b(sorry|my bad|my fault)\b",
        [
            "No worries",
            "All good",
            "Don't stress it",
            "It's fine",
        ],
    ),
    (
        r"\b(never mind|nevermind|forget it|cancel that)\b",
        [
            "All good",
            "No worries",
            "Got it, never mind",
            "Sure, no problem",
        ],
    ),
]


_FALLBACK_RESPONSES: list[str] = [
    "Hmm, not sure what you mean",
    "I didn't catch that, try again",
    "Not sure I got that one",
    "Can you say that again?",
    "I'm not sure what you're asking",
    "Didn't quite get that",
    "Say that again?",
    "Not sure I follow, try rephrasing",
]


def get_fallback() -> str:
    """Return a random fallback response for unrecognized commands."""
    return random.choice(_FALLBACK_RESPONSES)


def handle_social(transcript: str, speak_fn) -> bool:
    """
    Check transcript against social patterns and speak a response.
    Returns True if a social response was triggered, False otherwise.
    speak_fn should be a callable that takes a string and speaks it.
    """
    t = transcript.lower()
    for pattern, pool in _SOCIAL_PATTERNS:
        if re.search(pattern, t):
            speak_fn(random.choice(pool))
            return True
    return False
