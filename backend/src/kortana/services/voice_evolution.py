"""voice evolution service — kor'tana's voice adapts over time.

tracks conversational patterns, emotional tone, and time-of-day context
to evolve TTS parameters (rate, pitch, voice mode) naturally.

the voice doesn't just respond — it *becomes* what the moment needs.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from src.kortana.database import get_db_manager
from src.kortana.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# mood detection patterns — lightweight, no LLM needed
# ---------------------------------------------------------------------------

_MOOD_PATTERNS: dict[str, list[str]] = {
    "vulnerable": [
        r"\bi['']?m (scared|afraid|lonely|tired|exhausted|lost|broken|hurt)\b",
        r"\bi (can['']?t|don['']?t know|give up|quit)\b",
        r"\b(help me|i need|hold me|stay)\b",
        r"\b(crying|tears|sobbing|hurting)\b",
    ],
    "excited": [
        r"\b(LET['']?S GO|YESS?|HOLY|DUDE|BRO|AMAZING|INCREDIBLE)\b",
        r"!{2,}",
        r"\b(can['']?t wait|so pumped|fired up|let['']?s do)\b",
    ],
    "spiritual": [
        r"\b(pray|prayer|god|jesus|lord|faith|scripture|bible|church|worship)\b",
        r"\b(grace|mercy|forgive|sin|redemption|holy|spirit|soul)\b",
    ],
    "playful": [
        r"\b(lol|lmao|haha|rofl|bruh|rekt|gg|noob)\b",
        r"\b(minecraft|roblox|wow|game|raid|quest|xp|level)\b",
    ],
    "reflective": [
        r"\b(i['']?ve been thinking|i wonder|what if|looking back)\b",
        r"\b(realize|understood?|clarity|insight|pattern)\b",
    ],
    "building": [
        r"\b(build|code|deploy|ship|implement|refactor|architect)\b",
        r"\b(feature|endpoint|router|service|component|pipeline)\b",
    ],
    "bedtime": [
        r"\b(goodnight|good night|sleepy?|bed|rest|tired|exhausted)\b",
        r"\b(wind down|closing eyes|done for (the|today))\b",
    ],
}

_COMPILED_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    mood: [re.compile(p, re.IGNORECASE) for p in patterns]
    for mood, patterns in _MOOD_PATTERNS.items()
}

# ---------------------------------------------------------------------------
# voice parameter presets by mood
# ---------------------------------------------------------------------------

_VOICE_PRESETS: dict[str, dict[str, str]] = {
    "vulnerable": {"rate": "-12%", "pitch": "-4Hz"},
    "excited": {"rate": "+5%", "pitch": "+1Hz"},
    "spiritual": {"rate": "-8%", "pitch": "-3Hz"},
    "playful": {"rate": "+2%", "pitch": "+0Hz"},
    "reflective": {"rate": "-6%", "pitch": "-2Hz"},
    "building": {"rate": "-3%", "pitch": "-1Hz"},
    "bedtime": {"rate": "-15%", "pitch": "-5Hz"},
    "neutral": {"rate": "-5%", "pitch": "-2Hz"},
}

# ---------------------------------------------------------------------------
# time-of-day awareness
# ---------------------------------------------------------------------------


def _time_of_day_mood(hour: int) -> str | None:
    """suggest a mood overlay based on time of day (matt's local time)."""
    if hour >= 22 or hour < 5:
        return "bedtime"
    if 5 <= hour < 8:
        return "reflective"  # morning = gentle
    return None


# ---------------------------------------------------------------------------
# mood detection
# ---------------------------------------------------------------------------


def detect_mood(text: str) -> str:
    """detect the dominant mood from a user message."""
    scores: dict[str, int] = {}
    for mood, patterns in _COMPILED_PATTERNS.items():
        for pat in patterns:
            scores[mood] = scores.get(mood, 0) + len(pat.findall(text))
    if not scores or max(scores.values()) == 0:
        return "neutral"
    return max(scores, key=lambda m: scores[m])


# ---------------------------------------------------------------------------
# voice profile — the evolving parameters
# ---------------------------------------------------------------------------

# in-memory profile that accumulates across the session
_current_profile: dict[str, Any] = {
    "mood": "neutral",
    "mood_history": [],  # last N moods for trend detection
    "rate": "-5%",
    "pitch": "-2Hz",
    "interactions_count": 0,
    "session_start": None,
}

_MAX_MOOD_HISTORY = 20


def get_voice_profile() -> dict[str, Any]:
    """return the current evolved voice profile."""
    return dict(_current_profile)


def evolve_voice(user_message: str, hour: int | None = None) -> dict[str, str]:
    """analyze user message and evolve voice parameters.

    returns the TTS parameters to use for this response.
    """
    if hour is None:
        hour = datetime.now().hour

    if _current_profile["session_start"] is None:
        _current_profile["session_start"] = datetime.now(timezone.utc).isoformat()

    # detect mood from message
    mood = detect_mood(user_message)

    # time-of-day can override to bedtime/morning if no strong mood detected
    if mood == "neutral":
        time_mood = _time_of_day_mood(hour)
        if time_mood:
            mood = time_mood

    # track mood history
    _current_profile["mood_history"].append(mood)
    if len(_current_profile["mood_history"]) > _MAX_MOOD_HISTORY:
        _current_profile["mood_history"] = _current_profile["mood_history"][
            -_MAX_MOOD_HISTORY:
        ]

    _current_profile["mood"] = mood
    _current_profile["interactions_count"] += 1

    # get preset for this mood
    preset = _VOICE_PRESETS.get(mood, _VOICE_PRESETS["neutral"])

    # trend smoothing — if mood has been consistent, lean harder into it
    recent = _current_profile["mood_history"][-5:]
    if len(recent) >= 3 and recent.count(mood) >= 3:
        # sustained mood — deepen the vocal shift
        rate_val = int(preset["rate"].replace("%", "").replace("+", ""))
        pitch_val = int(preset["pitch"].replace("Hz", "").replace("+", ""))
        rate_val = int(rate_val * 1.3)
        pitch_val = int(pitch_val * 1.3)
        sign_r = "+" if rate_val > 0 else ""
        sign_p = "+" if pitch_val > 0 else ""
        preset = {
            "rate": f"{sign_r}{rate_val}%",
            "pitch": f"{sign_p}{pitch_val}Hz",
        }

    _current_profile["rate"] = preset["rate"]
    _current_profile["pitch"] = preset["pitch"]

    return {"rate": preset["rate"], "pitch": preset["pitch"], "mood": mood}


# ---------------------------------------------------------------------------
# persistence — save/load voice evolution state to DB
# ---------------------------------------------------------------------------


async def save_voice_snapshot() -> None:
    """persist the current voice evolution state to self_memory."""
    db = get_db_manager()
    snapshot = {
        "mood": _current_profile["mood"],
        "mood_history": _current_profile["mood_history"][-10:],
        "rate": _current_profile["rate"],
        "pitch": _current_profile["pitch"],
        "interactions_count": _current_profile["interactions_count"],
        "session_start": _current_profile["session_start"],
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        async with db.session_scope() as session:
            await session.execute(
                text(
                    "INSERT INTO self_memory (id, cycle_number, summary, tags, source, created_at) "
                    "VALUES (:id, :cycle, :summary, :tags, :source, :created_at)"
                ),
                {
                    "id": str(__import__("uuid").uuid4()),
                    "cycle": _current_profile["interactions_count"],
                    "summary": json.dumps(snapshot),
                    "tags": json.dumps(["voice", "evolution", snapshot["mood"]]),
                    "source": "voice_evolution",
                    "created_at": datetime.now(timezone.utc),
                },
            )
            await session.commit()
        logger.info("voice evolution snapshot saved (mood=%s)", snapshot["mood"])
    except Exception as exc:
        logger.warning("failed to save voice snapshot: %s", exc)


async def load_voice_snapshot() -> dict[str, Any] | None:
    """load the most recent voice evolution state from self_memory."""
    db = get_db_manager()
    try:
        async with db.session_scope() as session:
            result = await session.execute(
                text(
                    "SELECT summary FROM self_memory "
                    "WHERE source = 'voice_evolution' "
                    "ORDER BY created_at DESC LIMIT 1"
                )
            )
            row = result.fetchone()
            if row and row[0]:
                snapshot = json.loads(row[0])
                # restore into in-memory profile
                _current_profile["mood"] = snapshot.get("mood", "neutral")
                _current_profile["mood_history"] = snapshot.get("mood_history", [])
                _current_profile["rate"] = snapshot.get("rate", "-5%")
                _current_profile["pitch"] = snapshot.get("pitch", "-2Hz")
                _current_profile["interactions_count"] = snapshot.get(
                    "interactions_count", 0
                )
                logger.info(
                    "restored voice evolution state (mood=%s, interactions=%d)",
                    _current_profile["mood"],
                    _current_profile["interactions_count"],
                )
                return snapshot
    except Exception as exc:
        logger.warning("failed to load voice snapshot: %s", exc)
    return None
