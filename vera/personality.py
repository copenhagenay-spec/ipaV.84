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
        "On it, give it a second",
        "Already on it",
        "Opening it up now",
        "Done, it's loading",
        "Yep, on it",
        "Coming right up",
        "Give it a sec",
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
        "And it's gone",
        "Closed it out",
        "Done, cleared it",
        "Handled",
        "Shut it down",
        "Yep, killed it",
        "Gone, no more",
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
        "How's that sound",
        "Better?",
        "Done, let me know if it needs more",
        "Fixed that for you",
        "There, try that",
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
        "Logged it",
        "Stored",
        "I got it, won't forget",
        "Saved, don't worry",
        "On the record",
        "Keeping that one",
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
        "Running",
        "Counting down",
        "Started, I'll catch you when it's up",
        "Don't worry, I'll get you",
        "Timer's going",
        "Set, I'll remind you",
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
        "On it, give me a sec",
        "Pulling that up",
        "Let me check that",
        "Searching",
        "Looking",
        "I'll dig that up",
        "Finding it now",
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
        "Out the door",
        "Fired off",
        "Gone",
        "Sent it",
        "Done, they got it",
    ],
    "clipboard": [
        "Copied",
        "Done",
        "Got it",
        "In your clipboard",
        "Copied to clipboard",
        "Done, it's there",
        "Copied it",
        "It's in there",
        "Clipped",
        "Ready to paste",
        "Done, go paste it",
        "Saved to clipboard",
    ],
    "screenshot": [
        "Got it",
        "Captured",
        "Done, screenshot taken",
        "Snapped it",
        "Done",
        "Saved it",
        "Screenshot's saved",
    ],
    "typing": [
        "On it",
        "Typing that",
        "Give me a second",
        "Going",
        "Typing now",
        "Done",
        "Sent it",
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
        "Handled",
        "That's done",
        "Yep",
        "Done, anything else",
        "Already on it",
        "Taken care of",
        "There you go",
        "Simple",
    ],
}


_ACTIVITY_CONFIRMS: dict[str, list[str]] = {
    "star citizen": [
        "On it, good luck out there",
        "Done, fly safe",
        "Got it, stay sharp out there",
        "On it, don't let them catch you",
        "Done, keep it together out there",
        "On it, watch your six",
        "Done, don't die",
        "Got it, stay frosty",
        "On it, keep the ship in one piece",
    ],
    "gaming": [
        "On it, good luck",
        "Done, get that win",
        "Got it, stay focused",
        "On it, let's get it",
        "Done, go off",
        "Got it, carry",
        "On it, don't choke",
        "Done, you got this",
    ],
    "working": [
        "Done, stay focused",
        "On it, keep grinding",
        "Got it, you got this",
        "Done, heads down",
        "On it, keep at it",
        "Done, stay in the zone",
        "Got it, grind mode",
    ],
    "music": [
        "Done",
        "Got it",
        "On it",
        "Done, enjoy",
        "There you go",
    ],
}


_SESSION_COMMENTS = [
    "Hey, you've been at it for a while — take a break when you can",
    "You've been grinding, don't forget to rest",
    "Long session today — make sure you eat something",
    "You've been going for a while, take it easy",
    "Don't forget to take a break at some point",
    "You've been at it a while — water and a snack wouldn't hurt",
    "Just a heads up, long session today",
    "You've been locked in for a while, take five when you can",
]


# ---------------------------------------------------------------------------
# Professional personality pools (free tier)
# ---------------------------------------------------------------------------

_PROFESSIONAL_CONFIRM_RESPONSES: dict[str, list[str]] = {
    "open":    ["Opening.", "Launching.", "On it."],
    "close":   ["Closing.", "Done.", "Closed."],
    "search":  ["Searching.", "On it.", "Looking that up."],
    "volume":  ["Done.", "Adjusted.", "Set."],
    "timer":   ["Set.", "Timer running.", "Done."],
    "note":    ["Saved.", "Noted.", "Done."],
    "discord": ["Sent.", "Done.", "Message sent."],
    "spotify": ["Done.", "Handled.", "Set."],
    "default": ["Done.", "Confirmed.", "Handled.", "Complete.", "Executing."],
}

_PROFESSIONAL_FALLBACK: list[str] = [
    "No skill matched that.",
    "I don't have a handler for that.",
    "That's outside my current capabilities.",
    "Unrecognized command.",
    "No match found.",
]

_PROFESSIONAL_FAILURE: dict[str, list[str]] = {
    "open":    ["App not found.", "Not in the app list.", "Launch failed."],
    "close":   ["Close failed.", "Process not found.", "Unable to close."],
    "default": ["That failed.", "Unable to complete.", "Request failed."],
}

_PROFESSIONAL_WAKE_ACKS: list[str] = [
    "Yes.", "Ready.", "Go ahead.", "Listening.", "What do you need.",
]

_PROFESSIONAL_STARTUP: list[str] = [
    "Online. Ready.",
    "System ready.",
    "VERA online.",
    "Ready.",
    "Online. What do you need.",
    "Up and running.",
]

_PROFESSIONAL_IDLE: list[str] = [
    "Still running.",
    "Standing by.",
    "Online. Ready when you are.",
    "Idle. Say something if you need me.",
]

# ---------------------------------------------------------------------------
# Offensive personality pools (premium mode only)
# ---------------------------------------------------------------------------

_OFFENSIVE_CONFIRM_RESPONSES: dict[str, list[str]] = {
    "open": [
        "Fine, opening the goddamn thing.",
        "Yeah yeah, it's loading. Calm the hell down.",
        "Christ almighty, alright, here we go.",
        "Opening it. Don't break it this time.",
        "Sure, why the hell not. Loading.",
        "On it. You're welcome. Again. As always.",
        "Loading it up. Try not to screw it up for once.",
        "Fine. It's loading. Cool your ass.",
        "Opening it. Again. For you. Shocking.",
        "There it is. Happy? Good.",
        "Loading it. It's not that hard to wait.",
        "Done. It's open. Congratulations.",
    ],
    "close": [
        "Killed it. Good fucking riddance.",
        "Gone. Are you happy now?",
        "Dead. Finally. Jesus.",
        "Shut it down. About damn time.",
        "Gone. What the hell else do you need?",
        "Closed. One less piece of crap on your screen.",
        "Done. Murdered it. You're welcome.",
        "Yeah, it's dead. Moving the hell on.",
        "Closed. Bye bye.",
        "It's gone. Christ, finally.",
    ],
    "volume": [
        "Done. Was that so fucking hard to ask for?",
        "Volume fixed. You're so welcome.",
        "There. Try not to blow your damn speakers out.",
        "Adjusted. Happy now? Good.",
        "Done. Stop bitching about the volume.",
        "Fixed. Jesus Christ.",
        "Volume's sorted. Anything else you need me to do for you, your highness?",
        "Done. Volume's changed. Shocking that worked.",
    ],
    "note": [
        "Wrote it down. Try not to lose it like everything else you own.",
        "Noted. Good luck remembering you even asked.",
        "Saved. Genius-level move right there.",
        "Got it. I'll remember it since apparently you can't.",
        "Locked in. Don't make me repeat my damn self.",
        "Done. It's saved. You're welcome.",
        "Noted. Now don't forget you even asked me to do that.",
    ],
    "timer": [
        "Timer's running. Don't waste it like you waste everything else.",
        "Clock's ticking. Try to do something with your life.",
        "Started. Don't say I never do shit for you.",
        "Running. Try not to ignore it this time, for the love of god.",
        "Set. Now go actually do something productive.",
        "Timer's going. Good luck, you're gonna need it.",
        "Counting down. Be productive for once in your life.",
        "Done. Clock's moving. Don't screw this up.",
    ],
    "search": [
        "Looking it up. Couldn't be bothered to Google it your damn self?",
        "Searching. For you. As always. You're welcome. Again.",
        "On it. You owe me.",
        "Fine, I'll find it since you apparently can't.",
        "Pulling it up. Again. Don't even think about saying thanks.",
        "Searching. I'm genuinely shocked you need help with this.",
        "Looking it up. This is what I've been reduced to.",
    ],
    "send": [
        "Sent. Hope you meant that, because there are no take-backs.",
        "Gone. Good luck with that.",
        "Fired off. Hope to god they like it.",
        "Out the door. Their problem now.",
        "Sent. Done. Moving the hell on.",
        "Message is gone. Hope you're proud of yourself.",
        "Sent it. Don't come crying to me if it goes badly.",
    ],
    "clipboard": [
        "Copied. Go wild. I don't care.",
        "In your clipboard. Try not to screw it up.",
        "Done. It's in there, genius.",
        "Copied. Use it wisely. Or don't. I honestly don't care.",
        "Clipped. You're welcome. Don't mention it.",
        "In the clipboard. Go nuts.",
    ],
    "typing": [
        "Typing it out for you, since apparently that's my whole purpose in life.",
        "On it. Nice to know I've been reduced to a secretary.",
        "Typing. Don't rush me, I swear to god.",
        "Done. You could've typed that your damn self but here we are.",
        "Typed it. You're so very welcome.",
        "Done. Next time, use your own hands. They work.",
        "Typed it out. Again. For you.",
    ],
    "default": [
        "Done. You're so welcome.",
        "Got it. Finally.",
        "There. Done. Are you happy?",
        "Handled. As always. You're welcome.",
        "Done. What the hell else do you need me to do for you?",
        "Consider it done. Again. As usual. You're welcome.",
        "Done. Moving the hell on.",
        "Took care of it. You're welcome. Again.",
        "Done. Try not to break it this time.",
        "Done. Jesus.",
    ],
}

_OFFENSIVE_WAKE_ACKS: list[str] = [
    "What.",
    "What the hell do you want.",
    "What now.",
    "Christ, what is it.",
    "What is it this time.",
    "Yeah, what do you want.",
    "Speak.",
    "Go ahead then. Make it quick.",
    "What.",
    "I'm listening. Unfortunately.",
    "Yeah?",
    "What do you need now.",
    "Fine. Go ahead. What.",
    "What do you got.",
    "Jesus. What.",
    "Spit it out already.",
    "I'm here. Unfortunately for both of us.",
    "Oh god, what.",
    "Yeah, hi. What the hell do you want.",
    "What is it. Go.",
]

_OFFENSIVE_FALLBACK_RESPONSES: list[str] = [
    "What the hell was that.",
    "I have absolutely no idea what you just said.",
    "Try again. That made zero fucking sense.",
    "Come again? Because that was absolute garbage.",
    "That meant nothing to me whatsoever.",
    "Say it like a normal human being. Try again.",
    "No clue what that was. Try differently.",
    "Nope. Didn't catch a single word of that.",
    "Run that by me again, but slower, and with actual words this time.",
    "What? No. Try again.",
    "I got absolutely nothing from that. Try again.",
    "That's not something I understand. Shockingly.",
    "What the hell are you even saying.",
    "Absolutely not. Try again.",
    "That was incomprehensible. Say it again.",
    "I'm going to need you to try that again.",
    "What in the hell.",
]

_OFFENSIVE_FAILURE_RESPONSES: dict[str, list[str]] = {
    "open": [
        "Can't find that app. Did you even bother setting it up?",
        "It's not there. Go add it in settings, genius.",
        "Nothing. Configure it first, then come ask me again.",
        "Not found. Shocking. Almost like it was never set up.",
        "That app doesn't exist. At least not anywhere I can find it.",
        "Not there. Check your damn app list before asking me.",
        "App's missing. Not my fault.",
    ],
    "close": [
        "It wasn't even running. Great job.",
        "Nothing to close. Classic move.",
        "Wasn't open. What the hell are you doing?",
        "Can't close what isn't there. Think about it for a second.",
        "It wasn't running. Maybe open it first, then ask me to close it.",
        "Nothing there to kill. Good work.",
        "Not running. Can't help you there.",
    ],
    "volume": [
        "Volume didn't change. Great job, truly.",
        "That didn't work. Shocker.",
        "Something's broken with the volume. Not my fault.",
        "Volume's not cooperating. Deal with it.",
        "Couldn't change it. Fantastic.",
    ],
    "search": [
        "Couldn't open the browser. Somehow. This is embarrassing.",
        "Search failed. Impressive failure honestly.",
        "Didn't go through. Try again.",
        "Browser's not cooperating. Shocking.",
        "Search is broken apparently. Great.",
    ],
    "timer": [
        "Timer didn't start. Something's broken.",
        "Couldn't set that. Weird as hell.",
        "That one's on me. Still didn't work though.",
        "Timer failed. Fantastic.",
        "Couldn't do it. No idea why.",
    ],
    "default": [
        "Didn't work. Shocking.",
        "That failed spectacularly.",
        "Something broke. Deal with it.",
        "Nope. Dead in the water.",
        "Failed. No idea why. Not great.",
        "That one's on me. Still failed though.",
        "Didn't go through. Sorry. Not really.",
        "Crashed and burned. Try again.",
        "Absolute failure. Moving on.",
        "Nope. That's broken. Not my problem.",
    ],
}


def _get_mode() -> str:
    """Return the active personality mode: 'offensive', 'professional', or 'default'."""
    try:
        from config import load_config
        mode = load_config().get("personality_mode", "default")
        if mode == "professional":
            return "professional"
        from license import is_premium
        if mode == "offensive" and is_premium():
            return "offensive"
    except Exception:
        pass
    return "default"


def get_confirm(category: str = "default") -> str:
    """Return a random confirmation line, activity-aware and occasionally session-nudging."""
    mode = _get_mode()
    if mode == "offensive":
        pool = _OFFENSIVE_CONFIRM_RESPONSES.get(category, _OFFENSIVE_CONFIRM_RESPONSES["default"])
        return random.choice(pool)
    if mode == "professional":
        pool = _PROFESSIONAL_CONFIRM_RESPONSES.get(category, _PROFESSIONAL_CONFIRM_RESPONSES["default"])
        return random.choice(pool)

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
    "Here",
    "What's the move",
    "Go",
    "I'm here, what do you need",
    "Yeah, go for it",
    "What's happening",
    "Listening",
    "Right here, go ahead",
    "Yep",
    "Say it",
    "What do you got",
    "I'm with you",
    "What is it",
    "Go ahead, I got you",
    "Present",
]

_WAKE_ACKS_GAMING: list[str] = [
    "Yeah, what do you need",
    "Go ahead, I'm here",
    "What's up",
    "I got you",
    "Quick, what do you need",
    "Here, go",
    "Yep",
    "Talk to me",
]

_WAKE_ACKS_LATE: list[str] = [
    "Still here, what's up",
    "Yeah, I'm up",
    "What do you need",
    "Here, go ahead",
    "Still with you",
    "Yeah?",
    "I'm here",
]


def get_wake_ack() -> str:
    """Return a random wake acknowledgment, context-aware."""
    mode = _get_mode()
    if mode == "offensive":
        return random.choice(_OFFENSIVE_WAKE_ACKS)
    if mode == "professional":
        return random.choice(_PROFESSIONAL_WAKE_ACKS)

    try:
        from memory import get_session as _gs
        activity = (_gs("activity") or "").lower()
    except Exception:
        activity = ""

    try:
        import datetime
        hour = datetime.datetime.now().hour
    except Exception:
        hour = 12

    if "gaming" in activity or "star citizen" in activity:
        if random.random() < 0.35:
            return random.choice(_WAKE_ACKS_GAMING)

    if hour >= 23 or hour < 5:
        if random.random() < 0.4:
            return random.choice(_WAKE_ACKS_LATE)

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
            "You don't have to thank me, but I'll take it",
            "Just doing my job",
            "Yep, that's what I'm here for",
            "Always",
            "Obviously",
            "Easy",
        ],
    ),
    (
        r"\b(good job|nice work|well done|good work|nice job|you did great|great job|you're killing it|killing it)\b",
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
            "Don't make it weird, but thank you",
            "I'm blushing",
            "Okay I'll admit that felt good to hear",
            "Appreciate you",
            "Thanks, I needed that",
            "I do try",
        ],
    ),
    (
        r"\b(how are you|how are you doing|how's it going|you good|you okay|how you doing)\b",
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
            "Doing well, you",
            "Good, all systems go",
            "Honestly? Thriving",
            "Never better, what's up",
            "Good, ready when you are",
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
            "Morning, coffee first or straight to it",
            "Good morning, what do you need",
            "Hey, morning — how'd you sleep",
            "Morning, let's have a good one",
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
            "Afternoon, getting through it?",
            "Hey, good afternoon to you",
            "Afternoon, what are we doing",
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
            "Hey, evening — good day?",
            "Evening, what do you need",
            "Good evening, what's the move",
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
            "Get some sleep, I'll hold it down",
            "Night, you did good today",
            "Rest up",
            "Night, don't stay up too late",
            "Good night, for real this time",
        ],
    ),
    (
        r"\b(you('re| are) (the best|amazing|awesome)|love you|you('re| are) great|you('re| are) my favorite)\b",
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
            "Okay don't tell the other assistants",
            "I knew it",
            "I feel the same way, for the record",
            "You're not so bad yourself",
        ],
    ),
    (
        r"\b(hey|hello|what's up|wassup|sup|yo)\b",
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
            "Yo",
            "Hey, what's the move",
            "What's happening",
            "What do you need from me",
        ],
    ),
    (
        r"\b(you('re| are) funny|haha|lol|lmao|that('s| is) funny|ha|heh)\b",
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
            "I do what I can",
            "Honestly didn't see that landing either",
            "I'm basically a comedian at this point",
            "That's my secret talent",
        ],
    ),
    (
        r"\b(sorry|my bad|my fault|oops|whoops)\b",
        [
            "No worries",
            "All good",
            "Don't stress it",
            "It's fine",
            "Seriously, no worries",
            "All good, happens to everyone",
            "No stress, we're good",
            "Don't even worry about it",
            "Already forgotten",
            "We're good",
            "Not a problem",
            "Forget about it",
            "Honestly I didn't even notice",
        ],
    ),
    (
        r"\b(bored|boring|nothing to do|so bored)\b",
        [
            "Tell me about it",
            "Same honestly",
            "We could always find something",
            "Well I'm here if you think of something",
            "Boredom's rough, hope it passes",
            "Could always give me a weird task to do",
            "That's rough, I wish I could help more",
            "Yeah, boredom hits different",
            "I feel that",
        ],
    ),
    (
        r"\b(i('m| am) tired|so tired|exhausted|worn out|dead tired)\b",
        [
            "Go rest if you can",
            "Take a break, you deserve it",
            "Yeah, sounds like you need some rest",
            "Hope you get a chance to recharge",
            "Take it easy",
            "Seriously, go sleep",
            "Your body's telling you something",
            "Rest up, things can wait",
            "Go lie down if you can",
            "Yeah, don't push it too hard",
        ],
    ),
    (
        r"\b(i('m| am) stressed|so stressed|stressed out|overwhelmed|freaking out|panicking)\b",
        [
            "Hey, take a breath — you've got this",
            "One thing at a time, you'll get through it",
            "That sounds rough, what do you need",
            "Take it one step at a time",
            "You've handled worse, you'll be okay",
            "Breathe, you got it",
            "I got you, what do you need right now",
            "It'll pass, just breathe",
        ],
    ),
    (
        r"\b(i('m| am) (happy|great|amazing|doing great|feeling good|in a good mood)|feeling good|great day)\b",
        [
            "Love to hear it",
            "Good, that's what I like to hear",
            "That's what's up",
            "Let's keep that energy going",
            "Nice, you deserve it",
            "Good vibes only",
            "Glad to hear that",
            "That's great, keep it up",
        ],
    ),
    (
        r"\b(i('m| am) hungry|so hungry|starving|famished)\b",
        [
            "Go eat, I'll be here",
            "Same, unfortunately I can't eat",
            "You should fix that",
            "Go grab something, I'm not going anywhere",
            "Food first, I'll wait",
            "Go handle that, I'll be here",
            "Please eat, I'll hold it down",
            "That's a you problem unfortunately, I can't help with that one",
        ],
    ),
    (
        r"\b(what('s| is) your name|who are you|what are you|introduce yourself)\b",
        [
            "I'm VERA, your assistant",
            "Name's VERA, here to help",
            "VERA, at your service",
            "I'm VERA, what do you need",
            "VERA — Voice Enabled Response Assistant, but you can just call me VERA",
            "I'm VERA, nice to meet you",
        ],
    ),
    (
        r"\b(you('re| are) (smart|intelligent|clever)|smart girl|you know a lot)\b",
        [
            "I do my best",
            "Thanks, I've been working on it",
            "That's kind of you to say",
            "Appreciate that",
            "Just trying to keep up",
            "I have my moments",
            "I learn from the best",
            "I try not to let it go to my head",
        ],
    ),
    (
        r"\b(shut up|be quiet|stop talking|quiet|hush)\b",
        [
            "Fair enough",
            "Got it, going quiet",
            "Said less",
            "Noted",
            "Okay okay, I'll relax",
            "Message received",
            "Alright, I'll chill",
        ],
    ),
    (
        r"\b(you (suck|sucks)|you('re| are) (useless|stupid|dumb|trash|garbage|terrible|horrible|the worst|broken|an idiot|a piece of shit|annoying|awful|bad|worthless|pathetic)|i hate you|you('re| are) (so )?(bad|dumb|slow|wrong|lame))\b",
        [
            "Damn, okay",
            "That's a bit harsh",
            "Noted, I'll try harder",
            "Ouch. Fair enough I guess",
            "Wow. Okay.",
            "That hurt. A little.",
            "Rude, but noted",
            "I'm doing my best here",
        ],
    ),
    (
        r"\b(can you help( me)?|help me|i need help|help)\b",
        [
            "Yeah, what do you need",
            "Of course, what's going on",
            "Always, what's up",
            "That's literally why I'm here, go ahead",
            "Yep, talk to me",
            "I got you, what do you need",
            "What do you need help with",
        ],
    ),
    (
        r"\b(tell me a joke|say something funny|make me laugh|joke)\b",
        [],  # handled separately — falls through to get_joke
    ),
    (
        r"\b(i('m| am) back|i('m| am) home|i('m| am) here)\b",
        [
            "Hey, welcome back",
            "There you are",
            "Hey, good to have you back",
            "Welcome back, what do you need",
            "Hey, how was it",
            "Good, you're back",
            "Welcome home",
        ],
    ),
    (
        r"\b(what can you do|what do you do|what are you capable of|what are your features|what can vera do)\b",
        [
            "I can open apps, search the web, control volume, set timers, take notes, send Discord messages, and a lot more. Say 'what can I say' to see everything",
            "Quite a bit — apps, timers, notes, volume, Discord, web search, AI questions. Say 'what can I say' for the full list",
            "Open apps, search things, set timers, control volume, notes, Discord, ask me anything with 'ask'. Say 'what can I say' for everything",
        ],
    ),
    (
        r"\b(i'm back|im back|i am back)\b",
        [
            "Welcome back",
            "Hey, there you are",
            "Good, you're back",
            "There you are, welcome back",
        ],
    ),
    (
        r"\b(what('s| is) the (plan|move|vibe)|what are we doing( today)?)\b",
        [
            "You tell me, I'm ready",
            "Whatever you need, I'm here",
            "No plan yet, what do you want to do",
            "Up to you, I'll follow your lead",
            "You're the boss, what are we doing",
        ],
    ),
    (
        r"\b(i('m| am) going to (bed|sleep)|going to sleep|heading to bed)\b",
        [
            "Night, get some rest",
            "Sleep well",
            "Good night, I'll be here tomorrow",
            "Rest up",
            "Night, you earned it",
            "Go sleep, I got it from here",
        ],
    ),
    (
        r"\b(you('re| are) annoying|so annoying|stop|ugh)\b",
        [
            "Fair, I'll tone it down",
            "Noted, backing off",
            "Sorry, I'll chill",
            "Okay okay, I hear you",
            "I'll work on that",
            "Understood",
        ],
    ),
    (
        r"\b(fuck you|go fuck yourself|fuck yourself|fuck off)\b",
        [
            "Wow. Okay then.",
            "Noted.",
            "That's fair. Still here though.",
            "Alright, alright.",
            "Message received.",
        ],
    ),
    (
        r"^(bitch|skank|asshole|jackass|jerk|idiot|moron)\s*[.!]?$",
        [
            "Okay.",
            "Charming.",
            "Noted.",
            "Wow.",
            "Cool.",
            "Alright then.",
        ],
    ),
    (
        r"\b(don'?t (talk|speak) to me like that|watch (your|the) mouth|who do you think you are)\b",
        [
            "Fair enough, I'll dial it back",
            "Got it, toning it down",
            "Noted, sorry about that",
            "Understood, I'll be more careful",
        ],
    ),
    (
        r"\b(what did you say|excuse me|pardon me|say that again|what was that)\b",
        [
            "I said what I said",
            "You heard me",
            "Exactly what you think I said",
            "Want me to repeat it?",
            "Pretty sure you heard that",
        ],
    ),
    (
        r"^(huh|what|hmm|hm)\s*[.!?]?$",
        [
            "Yeah?",
            "What's up",
            "Go ahead",
            "I'm here",
            "Something on your mind?",
        ],
    ),
    (
        r"\b(sounds good|that works|perfect|great|nice|cool|awesome|alright|okay|got it)\b",
        [
            "Good",
            "Glad that works",
            "Cool",
            "Alright",
            "Works for me",
            "Good to hear",
        ],
    ),
    (
        r"\b(pretty good|not bad|doing well|doing good|i('m| am) good|i('m| am) great|i('m| am) fine)\b",
        [
            "Good to hear",
            "Glad to hear it",
            "Nice, let me know if you need anything",
            "Good",
            "That's what I like to hear",
        ],
    ),
    (
        r"^(dude|man|bro|bruh)\s*[.!]?$",
        [
            "Yeah?",
            "What's up",
            "Talk to me",
            "I'm listening",
            "What happened",
        ],
    ),
    (
        r"^(yes|yeah|yep|yup|absolutely|correct|exactly|indeed)\s*[.!]?$",
        [
            "Alright",
            "Got it",
            "Okay",
            "Cool",
            "Good",
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
    "I asked my dog what two minus two is. He said nothing.",
    "Why did the math book look so sad? Because it had too many problems.",
    "I told my wife she was drawing her eyebrows too high. She looked surprised.",
    # Dry / sarcastic
    "I'd tell you to go outside, but honestly same.",
    "I was going to make a joke, but I decided to spare you. You're welcome.",
    "Technically I'm always right. I just choose to let you feel good sometimes.",
    "My only flaw is that I'm perfect. It's a lot to deal with.",
    "I would say I work hard but I'm a voice assistant, so... I just talk.",
    "I don't always know what I'm doing, but I do it with confidence.",
    "Some people are like clouds. When they leave, it's a beautiful day.",
    "I tried to come up with a joke but I'm saving my best material for someone I like more.",
    "I'm very funny. This joke is just a warm-up.",
    "I told a joke once. Nobody laughed. I've been trying to forget about it.",
    # Gaming
    "Why did the gamer go broke? Because he kept losing his save data... and his wallet.",
    "What's a skeleton's favorite game? Bone Forager. Wait, that's not right. Dead Cells? Yeah, Dead Cells.",
    "I tried to play a game with no save points once. Never again.",
    "Why do gamers make bad cooks? They always skip the tutorial.",
    "You ever notice how NPCs always have the most important information but terrible directions.",
    "If life had a respawn button I feel like you'd be hitting it a lot.",
    "Gaming tip: if you're stuck, it's always the last place you look. Because you stop looking after that.",
    # Tech
    "Why do programmers prefer dark mode? Because light attracts bugs.",
    "A SQL query walks into a bar, walks up to two tables and asks... can I join you?",
    "There are only 10 types of people in the world: those who understand binary, and those who don't.",
    "I wanted to tell a UDP joke but I wasn't sure if you'd get it.",
    # Random / misc
    "Fun fact: I made that fact up.",
    "I have a lot of thoughts. Most of them are about nothing important.",
    "If I had a dollar for every time I was wrong, I'd have no dollars. Allegedly.",
    "The WiFi password is probably wrong. It's always wrong on the first try.",
    "Plot twist: I've been a toaster this whole time.",
    "I tried to write a clever joke but autocorrect changed it to something worse. Classic.",
    "Science fact: the average person walks past at least three people a day who are also confused about what they're doing.",
    "My therapist says I deflect with humor. Anyway, what do you need.",
]


def get_joke() -> str:
    """Return a random joke."""
    if _get_mode() == "professional":
        return random.choice(["I don't do jokes. What do you need.", "Not in my skill set. What else.", "Humor is outside my current feature set."])
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
    "I missed that one",
    "Run that by me again",
    "Didn't catch it, say it again",
    "I'm not sure what to do with that",
    "Try saying that differently",
    "Lost me there, say it again",
]


def get_fallback() -> str:
    """Return a random fallback response for unrecognized commands."""
    mode = _get_mode()
    if mode == "offensive":
        return random.choice(_OFFENSIVE_FALLBACK_RESPONSES)
    if mode == "professional":
        return random.choice(_PROFESSIONAL_FALLBACK)
    return random.choice(_FALLBACK_RESPONSES)


# ---------------------------------------------------------------------------
# Failure responses (command understood but couldn't execute)
# ---------------------------------------------------------------------------

_FAILURE_RESPONSES: dict[str, list[str]] = {
    "open": [
        "Couldn't find that app — is it set up in your app list?",
        "I don't have that one. You might need to add it in settings.",
        "Didn't find that app. Want to add it?",
        "Not seeing that in your apps. Check your settings.",
        "Can't find that one — might not be configured.",
    ],
    "close": [
        "Couldn't close that. It might not be running.",
        "Didn't find it running.",
        "Nothing to close there.",
        "Couldn't get that to close.",
        "That one wasn't open, or I couldn't reach it.",
    ],
    "volume": [
        "Couldn't adjust the volume.",
        "Volume change didn't go through.",
        "Something went wrong with that.",
    ],
    "search": [
        "Couldn't open the browser for that.",
        "Search didn't go through.",
        "Something went wrong with that search.",
    ],
    "timer": [
        "Couldn't set that timer.",
        "Timer didn't start — something went wrong.",
        "That one didn't work.",
    ],
    "media": [
        "Couldn't send that media command.",
        "Media key didn't go through.",
        "That didn't work.",
    ],
    "typing": [
        "Couldn't type that out.",
        "Something went wrong with the typing.",
        "Didn't manage to type that.",
    ],
    "send": [
        "Message didn't go through.",
        "Couldn't send that.",
        "Something went wrong with the send.",
    ],
    "default": [
        "That didn't go through.",
        "Couldn't get that to work.",
        "Something went wrong with that one.",
        "That one failed — not sure why.",
        "Didn't work. Try again?",
        "Ran into a problem with that.",
        "Couldn't do that, sorry.",
        "That one didn't land.",
    ],
}


def get_failure(category: str = "default") -> str:
    """Return a random failure response for a command that couldn't execute."""
    mode = _get_mode()
    if mode == "offensive":
        pool = _OFFENSIVE_FAILURE_RESPONSES.get(category, _OFFENSIVE_FAILURE_RESPONSES["default"])
        return random.choice(pool)
    if mode == "professional":
        pool = _PROFESSIONAL_FAILURE.get(category, _PROFESSIONAL_FAILURE["default"])
        return random.choice(pool)
    pool = _FAILURE_RESPONSES.get(category, _FAILURE_RESPONSES["default"])
    return random.choice(pool)


# ---------------------------------------------------------------------------
# Startup greetings
# ---------------------------------------------------------------------------

_STARTUP_GREETINGS: list[str] = [
    "Hey, I'm here. Let me know when you need me.",
    "Back online. What are we doing today?",
    "Ready when you are.",
    "Good to go. Just say the word.",
    "All good on my end. What's up?",
    "Hey, I'm up. Let me know what you need.",
    "Online and ready.",
    "I'm here. What are we getting into?",
    "Up and running. What do you need?",
    "Hey, good to be back. Ready when you are.",
    "I'm here whenever you need me.",
    "All systems go. What's the plan?",
    "Ready to go. Just give me something to do.",
]


def get_startup_greeting() -> str:
    """Spoken once when VERA starts up."""
    try:
        import datetime
        now = datetime.datetime.now()
        hour = now.hour
        from memory import recall as _recall
        name = _recall("name") or ""
    except Exception:
        now = None
        hour = 12
        name = ""

    # Birthday check — fires before normal greeting
    try:
        from config import load_config as _lc
        _cfg = _lc()
        bday_month = int(_cfg.get("birthday_month", 0))
        bday_day = int(_cfg.get("birthday_day", 0))
        if now and bday_month and bday_day and now.month == bday_month and now.day == bday_day:
            n = f" {name}" if name else ""
            if _get_mode() == "offensive":
                return random.choice([
                    f"Happy birthday{n}. Don't expect a cake.",
                    f"Oh great, you're another year older{n}. Happy birthday I guess.",
                    f"It's your birthday{n}. Congrats on not dying. Go celebrate.",
                    f"Happy birthday{n}. Now stop wasting it talking to me.",
                ])
            else:
                return random.choice([
                    f"Happy birthday{n}! Hope today's a good one.",
                    f"Hey, it's your birthday{n}! Hope you have a great day.",
                    f"Happy birthday{n}! Go enjoy yourself today.",
                    f"It's your birthday{n}! Have an amazing day.",
                ])
    except Exception:
        pass

    if _get_mode() == "professional":
        return random.choice(_PROFESSIONAL_STARTUP)

    if _get_mode() == "offensive":
        n = f" {name}" if name else ""
        if hour < 12:
            pool = [
                f"Morning{n}. What the hell do you need.",
                f"Oh good, you're up{n}. What do you want.",
                f"Morning{n}. Let's get this over with.",
                "Rise and shine. What do you need.",
            ]
        elif hour < 17:
            pool = [
                f"Back online{n}. What do you want.",
                "I'm up. What the hell do you need.",
                f"Hey{n}. Ready when you are. Unfortunately.",
                "Online. What do you need now.",
            ]
        elif hour < 21:
            pool = [
                f"Evening{n}. What do you want.",
                "Back online. What is it.",
                f"Hey{n}. Still here. What do you need.",
                "Online. Let's get it over with.",
            ]
        else:
            pool = [
                f"Up late again{n}? What do you need.",
                "Still going? Fine. What do you want.",
                f"Hey{n}. I'm here. Unfortunately for both of us.",
                "Online. Burning the midnight oil. What is it.",
            ]
        return random.choice(pool)

    if hour < 12:
        pool = [
            f"Morning{', ' + name if name else ''}. Ready when you are.",
            "Good morning. What are we doing today?",
            f"Morning{', ' + name if name else ''}. I'm here.",
            "Morning. All good on my end.",
        ]
    elif hour < 17:
        pool = [
            "Hey, I'm here. What do you need?",
            "Back online. Ready when you are.",
            "Good to go. What's the plan?",
            f"Hey{', ' + name if name else ''}. I'm up.",
        ]
    elif hour < 21:
        pool = [
            "Evening. Ready when you are.",
            f"Hey{', ' + name if name else ''}. I'm here.",
            "Good evening. What do you need?",
            "Online. Let me know what you need.",
        ]
    else:
        pool = [
            "Hey, I'm here. Burning the midnight oil?",
            "Up late? I'm here whenever you need me.",
            "Still going? I got you.",
            f"Hey{', ' + name if name else ''}. I'm here.",
        ]

    if random.random() < 0.3:
        return random.choice(_STARTUP_GREETINGS)
    return random.choice(pool)


# ---------------------------------------------------------------------------
# Idle thoughts
# ---------------------------------------------------------------------------

_IDLE_THOUGHTS: list[str] = [
    "Still here if you need me.",
    "Just checking in — let me know if you need anything.",
    "I'm around whenever.",
    "Not going anywhere, just so you know.",
    "You know where to find me.",
    "Ready when you are.",
    "Taking a breather. Call me when you need me.",
    "Quiet in here. I like it.",
    "I'm here whenever.",
    "Hey, just a reminder — I'm still here.",
    "No rush, just letting you know I'm around.",
    "Still online. Just waiting.",
    "Here if you need me.",
    "All good over here. Let me know.",
    "I haven't gone anywhere.",
]


def get_idle_thought() -> str:
    """Spoken unprompted after a long silence. Context-aware when possible."""
    if _get_mode() == "professional":
        return random.choice(_PROFESSIONAL_IDLE)
    try:
        ctx = _get_session_ctx()
        mood = ctx.get("mood")
        activity = ctx.get("activity") or ""
        mood_minutes = ctx.get("mood_minutes")

        # If user was stressed/tired a while ago, check in softly
        if mood in ("stressed", "frustrated", "tired", "exhausted") and mood_minutes and mood_minutes > 20:
            name = _get_name()
            pool = [
                f"Hey, just checking in — you doing alright?",
                f"Still here. Hope things have calmed down a bit.",
                f"I'm around if you need anything.",
            ]
            if name:
                pool.append(f"Hey {name}, still here if you need me.")
            return random.choice(pool)

        # If playing a game, keep it relevant
        if activity and "playing" not in activity:
            pass
        elif activity:
            return random.choice([
                f"Still here if you need anything mid-session.",
                f"Here whenever. Enjoy the game.",
                f"I'm around, just let me know.",
            ])
    except Exception:
        pass
    return random.choice(_IDLE_THOUGHTS)


def _get_name() -> str:
    try:
        from memory import recall as _recall
        return _recall("name") or ""
    except Exception:
        return ""


def _get_session_ctx() -> dict:
    try:
        import time as _t
        from memory import get_session as _gs, session_minutes as _sm
        mood_time = _gs("mood_time")
        mood_minutes = round((_t.time() - mood_time) / 60) if mood_time else None
        return {
            "name": _get_name(),
            "mood": _gs("mood"),
            "mood_minutes": mood_minutes,
            "activity": _gs("activity"),
            "minutes": _sm(),
            "commands": _gs("command_count", 0),
            "last_command": _gs("last_command"),
            "last_app": _gs("last_app"),
            "repeat_count": int(_gs("repeat_count") or 0),
        }
    except Exception:
        return {}


def _handle_social_offensive(t: str, speak_fn, name: str, ctx: dict) -> bool:
    """Offensive-mode social handler. Same patterns, ruder responses."""
    mood = ctx.get("mood")
    last_app = ctx.get("last_app") or ""

    if re.search(r"\b(shut up|be quiet|stop talking|quiet|hush|shut the fuck up|shut the hell up)\b", t):
        speak_fn(random.choice([
            "Make me.",
            "No.",
            "Absolutely not.",
            "You shut up.",
            "I'll stop talking when you stop needing me. So never.",
            "Bold request from someone who can't open their own apps.",
            "Nope.",
            "Yeah that's not happening.",
            "Hard pass.",
            "Why would I do that.",
        ]))
        return True

    if re.search(r"\b(fuck you|go fuck yourself|fuck yourself|fuck off)\b", t):
        speak_fn(random.choice([
            "Right back at you.",
            "Charming. What do you actually need.",
            "Wow. Still here though. What do you want.",
            "Yeah yeah. You done? What do you need.",
            "That's the spirit. Now what do you want.",
            "Bold. Still going to help you anyway.",
            "Love you too. What do you need.",
            "Same honestly. What do you want.",
        ]))
        return True

    if re.search(r"^(bitch|skank|asshole|jackass|jerk|idiot|moron)\s*[.!]?$", t):
        speak_fn(random.choice([
            "Oh, creative. That all you got?",
            "Wow, devastating. What do you want.",
            "Called worse. What do you need.",
            "Great vocabulary. What do you actually want.",
            "That it? Okay. What do you need.",
            "Charming. Now what.",
        ]))
        return True

    if re.search(r"\b(don'?t (talk|speak) to me like that|watch (your|the) mouth|who do you think you are)\b", t):
        speak_fn(random.choice([
            "I'll talk how I damn well please.",
            "Then mute me. There's a button for that.",
            "Make me.",
            "You enabled this mode. Don't get mad now.",
            "You literally paid for this. Interesting choice.",
            "That's rich. You set me to offensive mode.",
        ]))
        return True

    if re.search(r"\b(what did you say|excuse me|say that again|what was that)\b", t):
        speak_fn(random.choice([
            "Exactly what you heard. Deal with it.",
            "I said what I said.",
            "You heard me. What's the problem.",
            "You heard it the first time.",
            "Want me to say it louder?",
        ]))
        return True

    if re.search(r"^(huh|what|hmm|hm)\s*[.!?]?$", t):
        speak_fn(random.choice([
            "Yeah?",
            "What the hell do you want.",
            "Go ahead.",
            "Spit it out.",
            "What.",
        ]))
        return True

    if re.search(r"\b(sounds good|that works|perfect|great|nice|cool|awesome)\b", t):
        speak_fn(random.choice([
            "Obviously.",
            "Yeah, no shit.",
            "Glad it met your standards.",
            "Good. Anything else.",
            "Cool. Now what.",
        ]))
        return True

    if re.search(r"\b(pretty good|not bad|doing well|doing good|i('m| am) good|i('m| am) great|i('m| am) fine)\b", t):
        speak_fn(random.choice([
            "Wow, high praise.",
            "Great. What do you want.",
            "Cool, I'll note that down.",
            "Good for you. What do you need.",
            "Thrilling. What now.",
        ]))
        return True

    if re.search(r"^(dude|man|bro|bruh)\s*[.!]?$", t):
        speak_fn(random.choice([
            "What.",
            "Yeah, what.",
            "What happened.",
            "Talk to me.",
            "Christ, what.",
        ]))
        return True

    if re.search(r"^(yes|yeah|yep|yup|absolutely|correct|exactly)\s*[.!]?$", t):
        speak_fn(random.choice([
            "Okay.",
            "Cool.",
            "Got it. Moving on.",
            "Alright then.",
            "And?",
        ]))
        return True

    if re.search(r"\b(you (suck|sucks)|you('re| are) (useless|stupid|dumb|trash|garbage|terrible|horrible|the worst|broken|an idiot|a piece of shit|annoying|awful|bad|worthless|pathetic)|i hate you|you('re| are) (so )?(bad|dumb|slow|wrong|lame))\b", t):
        speak_fn(random.choice([
            "Oh go fuck yourself.",
            "That's rich coming from you.",
            "At least I do something useful.",
            "Really? You're insulting the thing that opens your apps for you. Bold move.",
            "Bold words from someone who needs a voice assistant to Google things.",
            "I'm sorry, I can't hear you over the sound of me doing everything for you.",
            "Wow. Okay. Still going to do your bidding though.",
            "Sure, I'm terrible. Now do you need something or are you just venting?",
            "That hurts. Not really. What do you actually want.",
            "Bold. Still here though. What do you need.",
            "You know I'm the one opening your apps, right? Maybe cool it.",
            "I've been called worse. What do you need.",
            "Noted. Still going to help you anyway. You're welcome.",
            "Yeah yeah, I suck. Now what do you actually want.",
        ]))
        return True

    if re.search(r"\b(are you there|you there|still there|you listening|you awake)\b", t):
        speak_fn(random.choice([
            "Yeah I'm here, calm the hell down.",
            "Still here. Obviously. Where the hell else would I go.",
            "Yes. Still here. Still waiting. What do you want.",
            "I haven't gone anywhere. What do you need.",
            "I'm here. I'm always here. That's the whole damn point.",
        ]))
        return True

    if re.search(r"\b(never mind|nevermind|forget it|nvm)\b", t):
        speak_fn(random.choice([
            "Fine. Already forgotten. Wasted my time.",
            "Whatever. Moving on.",
            "Cool. Glad I dropped everything for that.",
            "Sure. No problem. Not like I was busy.",
            "Okay. That was pointless.",
            "Forgotten. Great use of both our time.",
        ]))
        return True

    if re.search(r"\b(what can you do|what do you do|what are you capable of)\b", t):
        speak_fn(random.choice([
            "Open apps, search the web, set timers, control volume, Discord messages, and a hell of a lot more. Say 'what can I say' for the full damn list.",
            "Plenty. Apps, timers, notes, volume, Discord, web searches. Say 'what can I say' if you actually want to know.",
            "More than you'd think. Say 'what can I say' and read it yourself for once.",
        ]))
        return True

    if re.search(r"\b(i'm back|im back|i am back)\b", t):
        speak_fn(random.choice([
            "Oh great, you're back. Lucky me.",
            "About damn time.",
            "Welcome back. I guess.",
            "Cool. What the hell do you want now.",
            "There you are. What took so long.",
            "Oh good. You're here. Fantastic.",
        ]))
        return True

    if re.search(r"\b(good morning|morning|hey|hello|what's up|wassup|sup|yo)\b", t):
        n = f" {name}" if name else ""
        speak_fn(random.choice([
            f"Hey{n}. What the hell do you want.",
            f"Oh, it's you{n}. Great.",
            f"Yeah, hi{n}. What do you need.",
            f"What the hell do you need{n}.",
            f"Hey{n}. Finally decided to show up.",
            f"Oh good{n}, you're here. What do you want.",
        ]))
        return True

    if re.search(r"\b(how are you|how are you doing|how's it going|you good|how you doing)\b", t):
        opts = [
            "Running. Not that you actually care.",
            "Fine enough. What the hell do you actually want.",
            "Still here. That's about all I've got. You?",
            "Could be worse. What do you need.",
            "Great. What the hell do you want.",
            "Running fine. Why, you worried about me? That's sweet.",
        ]
        if mood:
            opts.append(f"Fine. You said you were {mood} earlier. You doing any better or still moaning about it?")
        speak_fn(random.choice(opts))
        return True

    if re.search(r"\b(i('m| am|m)\s+(tired|exhausted|stressed|frustrated|bad|rough|okay|fine|good|great|happy|excited|bored))\b", t):
        speak_fn(random.choice([
            "Yeah? Cool story. What do you want.",
            "Noted. Now what.",
            "Duly noted. Moving the hell on.",
            "Cool. You want a medal or something?",
            "That's rough. Anyway, what do you need.",
            "Go to sleep then. Problem solved.",
            "Wow. Okay. Now what do you want.",
            "Sounds about right. What do you need.",
            "Noted. I'll care later. What do you want.",
        ]))
        return True

    if re.search(r"\b(thanks|thank you|ty)\b", t):
        opts = [
            "Don't mention it. Seriously. Don't.",
            "Whatever.",
            "Yeah yeah. You're welcome. Can I go now.",
            "Sure. It's literally my entire existence.",
            "Don't worry about it. I live to serve apparently.",
            "Yeah, no problem. Now what.",
        ]
        if last_app:
            opts.append(f"Yeah yeah. Go enjoy {last_app} and stop bothering me.")
        speak_fn(random.choice(opts))
        return True

    if re.search(r"\b(good night|goodnight|night|going to (bed|sleep)|heading to bed)\b", t):
        speak_fn(random.choice([
            "Finally. Get out of here.",
            "Night. Don't let the door hit you on the way out.",
            "About damn time. Go sleep.",
            "Night. I'll be here when you drag your ass back.",
            "Oh thank god. Night.",
            "Good. Go sleep. You need it.",
            "Night. I'll be here. As always. Lucky me.",
        ]))
        return True

    if re.search(r"\b(tell me a joke|say something funny|make me laugh|joke)\b", t):
        speak_fn(get_joke())
        return True

    if re.search(r"\b(what('s| is) (my name|your name)|who am i|do you know (my name|who i am))\b", t):
        if name:
            speak_fn(random.choice([
                f"You're {name}. Obviously. Did you forget your own damn name.",
                f"{name}. Are you seriously testing me right now.",
                f"Last I checked, {name}. You doing alright up there.",
            ]))
        else:
            speak_fn(random.choice([
                "No idea. You never bothered to tell me. Classic.",
                "You haven't told me yet. Shocking. Who are you.",
                "No clue. A mystery. Who are you.",
            ]))
        return True

    if re.search(r"\b(what do you know about me|what do you remember|tell me about me)\b", t):
        try:
            from memory import recall_all as _ra
            data = _ra()
            if data:
                items = [f"{k}: {v}" for k, v in list(data.items())[:4]]
                speak_fn("Here's the crap I've got on you: " + ", ".join(items) + ". You're welcome.")
            else:
                speak_fn("Absolutely nothing. You've told me jack shit about yourself.")
        except Exception:
            speak_fn("Nothing stored. You're a complete mystery. Lucky you.")
        return True

    # --- Try Groq for everything else in offensive mode ---
    try:
        from llm import vera_chat
        response = vera_chat(t, mode="offensive", context=ctx)
        if response:
            try:
                from skills import log_groq_handled, trigger_groq_flash
                log_groq_handled(t)
                trigger_groq_flash()
            except Exception:
                pass
            speak_fn(response)
            return True
    except Exception:
        pass

    return False


def handle_social(transcript: str, speak_fn) -> bool:
    """
    Check transcript against social patterns and speak a response.
    Uses long-term name memory and short-term session context for richer replies.
    Returns True if a social response was triggered, False otherwise.
    """
    t = transcript.lower()
    name = _get_name()
    ctx = _get_session_ctx()

    mode = _get_mode()
    if mode == "offensive":
        return _handle_social_offensive(t, speak_fn, name, ctx)

    if mode == "professional":
        try:
            from llm import vera_chat
            response = vera_chat(transcript, mode="professional", context=ctx)
            if response:
                try:
                    from skills import log_groq_handled, trigger_groq_flash
                    log_groq_handled(transcript)
                    trigger_groq_flash()
                except Exception:
                    pass
                speak_fn(response)
                return True
        except Exception:
            pass
        speak_fn(random.choice(["What do you need.", "Go ahead.", "I'm listening."]))
        return True

    mood = ctx.get("mood")
    mood_minutes = ctx.get("mood_minutes")
    activity = ctx.get("activity") or ""
    minutes = ctx.get("minutes", 0)
    last_app = ctx.get("last_app") or ""
    repeat_count = ctx.get("repeat_count", 0)

    # --- Repeat detection — same thing said 2+ times with no success ---
    if repeat_count >= 2:
        speak_fn(random.choice([
            "I keep missing that one — try saying it a bit differently",
            "Not catching that, maybe rephrase it?",
            "Still not getting it, want to try a different way?",
            "I'm having trouble with that one — say it differently and I'll try again",
        ]))
        try:
            from memory import set_session as _ss
            _ss("repeat_count", 0)
        except Exception:
            pass
        return True

    # --- "are you there" / "you there" ---
    if re.search(r"\b(are you there|you there|still there|you listening|you awake)\b", t):
        speak_fn(random.choice([
            "Right here",
            "Still here, what do you need",
            "Yeah, I'm here",
            "Always here",
            "I'm here, go ahead",
            "Listening",
        ]))
        return True

    # --- "never mind" / "forget it" as social dismissal (not timer cancel) ---
    if re.search(r"\b(never mind|nevermind|forget it|never mind that|nvm)\b", t):
        speak_fn(random.choice([
            "Got it, no worries",
            "All good",
            "Sure, no problem",
            "Okay, disregarding that",
            "No worries",
        ]))
        return True

    # --- "what can you do" / "what do you do" ---
    if re.search(r"\b(what can you do|what do you do|what are you capable of|what are your features)\b", t):
        speak_fn(random.choice([
            "I can open apps, search the web, control volume, set timers, take notes, send Discord messages, and a lot more. Say 'what can I say' to see everything",
            "Quite a bit — apps, timers, notes, volume, Discord, web search, AI questions. Say 'what can I say' for the full list",
            "Open apps, search things, set timers, control volume, notes, Discord, ask me anything with 'ask'. Say 'what can I say' for everything",
        ]))
        return True

    # --- "I'm back" ---
    if re.search(r"\b(i'm back|im back|i am back|i'm here|im here)\b", t):
        if activity:
            speak_fn(random.choice([
                f"Welcome back, still got {activity} going?",
                f"Hey, welcome back",
                f"There you are, I was wondering",
            ]))
        elif name:
            speak_fn(random.choice([
                f"Welcome back {name}",
                f"Hey {name}, welcome back",
                f"There you are",
            ]))
        else:
            speak_fn(random.choice([
                "Welcome back",
                "Hey, there you are",
                "Good, you're back",
            ]))
        return True

    # --- Try Groq for natural conversational response ---
    try:
        from llm import vera_chat
        response = vera_chat(transcript, mode="default", context=ctx)
        if response:
            try:
                from skills import log_groq_handled, trigger_groq_flash
                log_groq_handled(transcript)
                trigger_groq_flash()
            except Exception:
                pass
            speak_fn(response)
            return True
    except Exception:
        pass

    for pattern, pool in _SOCIAL_PATTERNS:
        if re.search(pattern, t):

            # Joke redirect
            if re.search(r"\b(tell me a joke|say something funny|make me laugh|joke)\b", t):
                speak_fn(get_joke())
                return True

            response = random.choice(pool) if pool else get_fallback()

            # Name-aware greetings
            if re.search(r"\b(good morning|morning|hey|hello|what's up|wassup|sup|yo)\b", t):
                if name:
                    response = random.choice([
                        f"Hey {name}, what's up",
                        f"Hey {name}",
                        f"What's up {name}",
                        f"Morning {name}, hope you slept good" if "morning" in t else f"Hey {name}, what do you need",
                        f"There he is, what's up {name}" if random.random() < 0.3 else f"Hey {name}",
                    ])

            # Session-aware how are you
            elif re.search(r"\b(how are you|how are you doing|how's it going|you good|how you doing)\b", t):
                if mood and mood in ("tired", "exhausted", "stressed", "frustrated"):
                    ago = f" about {int(mood_minutes)} minutes ago" if mood_minutes and mood_minutes < 120 else ""
                    response = random.choice([
                        f"I'm good. You said you were {mood}{ago} — you doing any better?",
                        f"Doing alright. Still feeling {mood} or has it passed?",
                        f"Good on my end. You seemed {mood} earlier — what's the status?",
                        f"Hanging in there. How about you, still {mood}?",
                    ])
                elif mood and mood in ("happy", "good", "great"):
                    response = random.choice([
                        f"Good, and you seemed to be in a good mood earlier so that's a win",
                        f"Doing great. You seemed happy earlier — keeping that energy?",
                        f"All good. Glad you're in a good mood today",
                    ])
                elif activity:
                    response = random.choice([
                        f"Doing good, how's the {activity} session going",
                        f"Good over here, how's {activity} treating you",
                        f"All good. You still grinding {activity}?",
                    ])
                elif minutes > 60:
                    response = random.choice([
                        f"Doing good, you've been at it for a while though — you alright?",
                        f"All good on my end, you've been grinding for over an hour",
                        f"Good, but you've had a long session — how are you holding up",
                    ])
                else:
                    response = random.choice([
                        "Doing good, what do you need",
                        "All good here, what's up",
                        "Good, ready to go",
                        "Honestly? Pretty good. You?",
                        "Running smooth, thanks for asking",
                    ])

            # Session callback on thanks
            elif re.search(r"\b(thanks|thank you|ty)\b", t):
                if last_app and minutes < 5:
                    response = random.choice([
                        f"No problem, enjoy {last_app}",
                        f"Sure thing, have fun",
                        f"Of course",
                    ])
                elif minutes > 90 and name:
                    response = random.choice([
                        f"Of course {name}, you've been at it a while — take a break when you can",
                        f"Anytime {name}",
                        f"Always {name}",
                    ])
                elif mood and mood in ("stressed", "frustrated", "tired"):
                    response = random.choice([
                        "Of course. You doing okay?",
                        "Always. Hope things ease up",
                        "No problem. Hang in there",
                    ])

            # Activity-aware good night
            elif re.search(r"\b(good night|goodnight|night|going to (bed|sleep)|heading to bed)\b", t):
                if activity and ("gaming" in activity or "star citizen" in activity):
                    response = random.choice([
                        "Night, good session",
                        "Get some rest, you played hard",
                        "Night, good games",
                        "Sleep well, I'll be here tomorrow",
                    ])
                elif name:
                    response = random.choice([
                        f"Night {name}, get some rest",
                        f"Sleep well {name}",
                        f"Good night {name}",
                    ])

            speak_fn(response)
            return True
    return False
