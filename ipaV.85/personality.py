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
        "Opening that now",
        "Right away",
        "Here we go",
        "Loading that up",
    ],
    "close": [
        "Done",
        "Closed that out",
        "Gone",
        "No problem",
        "Taken care of",
        "All good",
        "Closed",
        "Done, it's gone",
        "Yep, closed",
        "Out of here",
    ],
    "volume": [
        "Done",
        "There you go",
        "No problem",
        "Got it",
        "All good",
        "Adjusted",
        "Done, how's that",
        "Volume updated",
        "Sure thing",
    ],
    "note": [
        "Got it, saved",
        "Noted",
        "I'll remember that",
        "Done",
        "Saved for you",
        "No problem",
        "Locked in",
        "Written down",
        "Got it, I'll keep that",
        "Saved",
    ],
    "timer": [
        "Timer's set",
        "Got it, I'll let you know",
        "Starting now",
        "No problem",
        "On it",
        "Timer's running",
        "I'll remind you",
        "Clock's ticking",
        "Timer started",
    ],
    "search": [
        "On it",
        "Looking that up",
        "Sure thing",
        "Let me find that for you",
        "Searching now",
        "On it, one sec",
        "Let me look that up",
        "I'll find that",
    ],
    "send": [
        "Sent",
        "Done",
        "No problem",
        "All sent",
        "Message sent",
        "Delivered",
        "Sent it over",
        "Done, it's sent",
    ],
    "clipboard": [
        "Copied",
        "Done",
        "Got it",
        "In your clipboard",
        "Copied to clipboard",
        "Done, it's there",
    ],
    "default": [
        "Done",
        "Got it",
        "No problem",
        "Sure thing",
        "All good",
        "On it",
        "You got it",
        "Done and done",
        "Easy",
        "Consider it done",
    ],
}


_ACTIVITY_CONFIRMS: dict[str, list[str]] = {
    "star citizen": [
        "On it, good luck out there",
        "Done, fly safe",
        "Got it, stay sharp out there",
        "On it, don't let them catch you",
        "Done, keep it together out there",
    ],
    "gaming": [
        "On it, good luck",
        "Done, get that win",
        "Got it, stay focused",
        "On it, let's get it",
    ],
    "working": [
        "Done, stay focused",
        "On it, keep grinding",
        "Got it, you got this",
        "Done, heads down",
    ],
}


_SESSION_COMMENTS = [
    "Hey, you've been at it for a while — take a break when you can",
    "You've been grinding, don't forget to rest",
    "Long session today — make sure you eat something",
    "You've been going for a while, take it easy",
    "Don't forget to take a break at some point",
]


def get_confirm(category: str = "default") -> str:
    """Return a random confirmation line, activity-aware and occasionally session-nudging."""
    try:
        from memory import get_session as _gs, session_minutes as _sm
        activity = (_gs("activity") or "").lower()
        mins = _sm()
    except Exception:
        activity = ""
        mins = 0

    # Activity-aware confirm (1 in 4 chance when activity is known)
    if activity and random.random() < 0.25:
        for key, pool in _ACTIVITY_CONFIRMS.items():
            if key in activity:
                return random.choice(pool)

    pool = _CONFIRM_RESPONSES.get(category, _CONFIRM_RESPONSES["default"])
    base = random.choice(pool)

    # Session length nudge (1 in 5 after 60min, 1 in 4 after 90min)
    chance = 0.25 if mins >= 90 else (0.20 if mins >= 60 else 0)
    if chance and random.random() < chance:
        return f"{base}. {random.choice(_SESSION_COMMENTS)}"

    return base


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
    "Talk to me",
    "I'm all ears",
    "What's on your mind",
    "Sup",
    "Right here",
    "What do you need from me",
    "Go ahead, I'm listening",
    "Yeah, what's up",
    "What are we doing",
    "I got you, go ahead",
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
            "That's what I'm here for",
            "Glad I could help",
            "Any time, seriously",
            "Of course",
            "No problem at all",
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
            "Thanks, that's sweet",
            "I'll take it",
            "Means a lot, thank you",
            "Just here to help",
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
            "Honestly, pretty good",
            "Doing great, ready to help",
            "Can't complain, what's up",
            "Good, always good when you're around",
            "Running smooth, what do you need",
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
            "Morning! What are we getting into today",
            "Good morning, let's get it",
            "Morning, hope it's a good one",
            "Hey, good morning to you too",
        ],
    ),
    (
        r"\b(good afternoon|afternoon)\b",
        [
            "Hey, good afternoon",
            "Afternoon, how's the day going",
            "Good afternoon, what do you need",
            "Afternoon, hope the day's been good",
            "Hey, afternoon",
        ],
    ),
    (
        r"\b(good evening|evening)\b",
        [
            "Good evening",
            "Hey, good evening",
            "Evening, winding down or just getting started",
            "Good evening, what do you need",
            "Evening, hope the day treated you well",
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
            "Rest up, you earned it",
            "Good night, take care",
            "Night, catch you tomorrow",
            "Sweet dreams",
            "Night, I'll be here when you're back",
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
            "Okay now you're making me blush",
            "That's really sweet, thank you",
            "I appreciate you saying that",
            "You're too kind",
            "Honestly, right back at you",
            "That genuinely means a lot",
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
            "Hey, good to hear from you",
            "What's going on",
            "Hey there",
            "What's up",
        ],
    ),
    (
        r"\b(you('re| are) funny|haha|lol|lmao|that('s| is) funny|ha)\b",
        [
            "I have my moments",
            "Glad I could make you laugh",
            "I try",
            "Ha, thanks",
            "Comedy's a side thing for me",
            "I'll be here all week",
            "Didn't know I had it in me",
            "Hey, I surprised myself too",
            "Gotta keep it fun somehow",
            "That one surprised even me",
        ],
    ),
    (
        r"\b(sorry|my bad|my fault)\b",
        [
            "No worries",
            "All good",
            "Don't stress it",
            "It's fine",
            "Seriously, no worries",
            "All good, happens to everyone",
            "No stress, we're good",
            "Don't even worry about it",
        ],
    ),
    (
        r"\b(bored|boring|nothing to do)\b",
        [
            "Tell me about it",
            "Same honestly",
            "We could always find something",
            "Well I'm here if you think of something",
            "Boredom's rough, hope it passes",
        ],
    ),
    (
        r"\b(i('m| am) tired|so tired|exhausted|worn out)\b",
        [
            "Go rest if you can",
            "Take a break, you deserve it",
            "Yeah, sounds like you need some rest",
            "Hope you get a chance to recharge",
            "Take it easy",
        ],
    ),
    (
        r"\b(i('m| am) hungry|so hungry|starving)\b",
        [
            "Go eat, I'll be here",
            "Same, unfortunately I can't eat",
            "You should fix that",
            "Go grab something, I'm not going anywhere",
        ],
    ),
    (
        r"\b(what('s| is) your name|who are you|what are you)\b",
        [
            "I'm VERA, your assistant",
            "Name's VERA, here to help",
            "VERA, at your service",
            "I'm VERA, what do you need",
        ],
    ),
    (
        r"\b(you('re| are) (smart|intelligent|clever)|smart girl)\b",
        [
            "I do my best",
            "Thanks, I've been working on it",
            "That's kind of you to say",
            "Appreciate that",
            "Just trying to keep up",
        ],
    ),
]


# ---------------------------------------------------------------------------
# Jokes
# ---------------------------------------------------------------------------

_JOKES: list[str] = [
    # Dad jokes
    "Why don't scientists trust atoms? Because they make up everything.",
    "I told my computer I needed a break. Now it won't stop sending me Kit Kat ads.",
    "Why did the scarecrow win an award? Because he was outstanding in his field.",
    "I'm reading a book about anti-gravity. It's impossible to put down.",
    "Why can't your nose be 12 inches long? Because then it'd be a foot.",
    "I used to hate facial hair but then it grew on me.",
    "What do you call a fake noodle? An impasta.",
    "I would tell you a joke about construction, but I'm still working on it.",
    "Why did the bicycle fall over? Because it was two tired.",
    "What do you call cheese that isn't yours? Nacho cheese.",
    # Dry / sarcastic
    "I'd tell you to go outside, but honestly same.",
    "I was going to make a joke, but I decided to spare you. You're welcome.",
    "Technically I'm always right. I just choose to let you feel good sometimes.",
    "My only flaw is that I'm perfect. It's a lot to deal with.",
    "I would say I work hard but I'm a voice assistant, so... I just talk.",
    "I don't always know what I'm doing, but I do it with confidence.",
    "Some people are like clouds. When they leave, it's a beautiful day.",
    # Gaming
    "Why did the gamer go broke? Because he kept losing his save data... and his wallet.",
    "What's a skeleton's favorite game? Bone Forager. Wait, that's not right. Dead Cells? Yeah, Dead Cells.",
    "I tried to play a game with no save points once. Never again.",
    "Why do gamers make bad cooks? They always skip the tutorial.",
    "You ever notice how NPCs always have the most important information but terrible directions.",
    "If life had a respawn button I feel like you'd be hitting it a lot.",
    # Random / misc
    "Fun fact: I made that fact up.",
    "I have a lot of thoughts. Most of them are about nothing important.",
    "If I had a dollar for every time I was wrong, I'd have no dollars. Allegedly.",
    "The WiFi password is probably wrong. It's always wrong on the first try.",
    "Plot twist: I've been a toaster this whole time.",
]


def get_joke() -> str:
    """Return a random joke."""
    return random.choice(_JOKES)


_FALLBACK_RESPONSES: list[str] = [
    "Hmm, not sure what you mean",
    "I didn't catch that, try again",
    "Not sure I got that one",
    "Can you say that again?",
    "I'm not sure what you're asking",
    "Didn't quite get that",
    "Say that again?",
    "Not sure I follow, try rephrasing",
    "That one went over my head",
    "I didn't get that, want to try again?",
    "Not sure I understood, say it differently maybe",
    "Hmm, draw a blank on that one",
]


def get_fallback() -> str:
    """Return a random fallback response for unrecognized commands."""
    return random.choice(_FALLBACK_RESPONSES)


def _get_name() -> str:
    try:
        from memory import recall as _recall
        return _recall("name") or ""
    except Exception:
        return ""


def _get_session_ctx() -> dict:
    try:
        from memory import get_session as _gs, session_minutes as _sm
        return {
            "mood": _gs("mood"),
            "activity": _gs("activity"),
            "minutes": _sm(),
            "commands": _gs("command_count", 0),
        }
    except Exception:
        return {}


def handle_social(transcript: str, speak_fn) -> bool:
    """
    Check transcript against social patterns and speak a response.
    Uses long-term name memory and short-term session context for richer replies.
    Returns True if a social response was triggered, False otherwise.
    """
    t = transcript.lower()
    name = _get_name()
    ctx = _get_session_ctx()
    mood = ctx.get("mood")
    activity = ctx.get("activity")
    minutes = ctx.get("minutes", 0)

    for pattern, pool in _SOCIAL_PATTERNS:
        if re.search(pattern, t):
            response = random.choice(pool)

            # Name-aware greetings
            if re.search(r"\b(good morning|morning|hey|hello|what's up|wassup|sup)\b", t):
                if name:
                    response = random.choice([
                        f"Hey {name}, what's up",
                        f"Hey {name}",
                        f"What's up {name}",
                        f"Morning {name}, hope you slept good" if "morning" in t else f"Hey {name}, what do you need",
                    ])

            # Session-aware how are you
            elif re.search(r"\b(how are you|how are you doing|how's it going|you good)\b", t):
                if mood and mood in ("tired", "exhausted", "stressed", "frustrated"):
                    response = random.choice([
                        f"Hanging in there, how about you",
                        f"I'm good, still thinking about what you said earlier though — you doing okay?",
                        f"I'm good. You still feeling {mood}?",
                    ])
                elif minutes > 60:
                    response = random.choice([
                        f"Doing good, you've been at it for a while though — you doing alright?",
                        f"All good on my end, you've been grinding for over an hour",
                    ])
                else:
                    response = random.choice([
                        "Doing good, what do you need",
                        "All good here, what's up",
                        "Good, ready to go",
                    ])

            # Long session callback
            elif re.search(r"\b(thanks|thank you|ty)\b", t) and minutes > 90:
                if name:
                    response = random.choice([
                        f"Of course {name}, you've been at it a while — take a break when you can",
                        f"Anytime {name}",
                    ])

            speak_fn(response)
            return True
    return False
