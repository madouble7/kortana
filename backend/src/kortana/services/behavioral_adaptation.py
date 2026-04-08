"""behavioral adaptation — kor'tana learns what works with matt.

tracks engagement signals to evolve behavioral parameters over time:
  - positive signals: laughter, gratitude, detailed responses, engagement
  - negative signals: silence, "not now", short dismissals, topic changes
  - neutral signals: routine exchanges

behavioral parameters adjust gradually:
  - verbosity: how much detail she offers unprompted
  - proactivity: how bold her suggestions are
  - humor_frequency: how often she plays
  - depth_default: how deep she goes by default
  - warmth_level: emotional openness calibration

she becomes more of what works. less of what doesn't.
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
# engagement signal detection
# ---------------------------------------------------------------------------

_POSITIVE_PATTERNS = [
    re.compile(r"\b(thanks?|thank you|thx|ty|appreciate)\b", re.IGNORECASE),
    re.compile(
        r"\b(perfect|exactly|nice|great|awesome|love it|beautiful)\b", re.IGNORECASE
    ),
    re.compile(r"\b(haha|lol|lmao|rofl|hehe|😂|🤣)\b", re.IGNORECASE),
    re.compile(r"\b(yes|yeah|yep|yup|absolutely|definitely)\b", re.IGNORECASE),
    re.compile(r"\b(keep going|more|tell me more|go on|continue)\b", re.IGNORECASE),
    re.compile(r"\b(good call|smart|clever|brilliant)\b", re.IGNORECASE),
]

_NEGATIVE_PATTERNS = [
    re.compile(r"\b(not now|later|stop|enough|too much|chill)\b", re.IGNORECASE),
    re.compile(r"\b(no|nah|nope|wrong|bad|don't)\b", re.IGNORECASE),
    re.compile(r"\b(whatever|idc|i don't care|skip|next)\b", re.IGNORECASE),
    re.compile(r"\b(shut up|be quiet|silence|shh|stfu)\b", re.IGNORECASE),
    re.compile(r"\b(too long|tldr|tl;dr|shorter|brief)\b", re.IGNORECASE),
]

_DEPTH_PATTERNS = [
    re.compile(
        r"\b(explain|why|how does|what is|tell me about|deep dive)\b", re.IGNORECASE
    ),
    re.compile(r"\b(detail|elaborate|expand|unpack)\b", re.IGNORECASE),
]

_HUMOR_PATTERNS = [
    re.compile(r"\b(haha|lol|lmao|rofl|hehe|funny|hilarious|joke)\b", re.IGNORECASE),
    re.compile(r"😂|🤣|😆|😄", re.IGNORECASE),
]


def detect_engagement(user_message: str) -> dict[str, float]:
    """detect engagement signals from a user message.

    returns a dict of signal types and their strengths (0-1).
    """
    signals: dict[str, float] = {
        "positive": 0.0,
        "negative": 0.0,
        "depth_seeking": 0.0,
        "humor_response": 0.0,
        "message_length": 0.0,
    }

    # message length as engagement proxy
    word_count = len(user_message.split())
    if word_count > 50:
        signals["message_length"] = 1.0
    elif word_count > 20:
        signals["message_length"] = 0.7
    elif word_count > 8:
        signals["message_length"] = 0.4
    elif word_count <= 2:
        signals["message_length"] = -0.3  # very short = disengaged

    # pattern matching
    for pat in _POSITIVE_PATTERNS:
        if pat.search(user_message):
            signals["positive"] = min(signals["positive"] + 0.3, 1.0)

    for pat in _NEGATIVE_PATTERNS:
        if pat.search(user_message):
            signals["negative"] = min(signals["negative"] + 0.4, 1.0)

    for pat in _DEPTH_PATTERNS:
        if pat.search(user_message):
            signals["depth_seeking"] = min(signals["depth_seeking"] + 0.5, 1.0)

    for pat in _HUMOR_PATTERNS:
        if pat.search(user_message):
            signals["humor_response"] = min(signals["humor_response"] + 0.5, 1.0)

    return signals


# ---------------------------------------------------------------------------
# behavioral parameters — the evolving self
# ---------------------------------------------------------------------------

_behavioral_params: dict[str, float] = {
    "verbosity": 0.5,  # 0 = terse, 1 = expansive
    "proactivity": 0.5,  # 0 = only when asked, 1 = freely offers
    "humor_frequency": 0.3,  # 0 = serious, 1 = playful
    "depth_default": 0.5,  # 0 = surface, 1 = deep analysis
    "warmth_level": 0.6,  # 0 = clinical, 1 = emotional
    "suggestion_boldness": 0.4,  # 0 = conservative, 1 = bold suggestions
}

# learning rate — how fast parameters shift per signal
_LEARNING_RATE = 0.02
_MIN_PARAM = 0.1
_MAX_PARAM = 0.9

# history of recent signals for trend analysis
_signal_history: list[dict[str, float]] = []
_MAX_SIGNAL_HISTORY = 100


def get_behavioral_params() -> dict[str, float]:
    """return current behavioral parameters."""
    return dict(_behavioral_params)


def adapt_behavior(user_message: str) -> dict[str, Any]:
    """analyze user message and adapt behavioral parameters.

    returns the updated parameters and the detected signals.
    """
    signals = detect_engagement(user_message)
    _signal_history.append(signals)
    if len(_signal_history) > _MAX_SIGNAL_HISTORY:
        _signal_history.pop(0)

    # apply adaptations based on signals
    if signals["positive"] > 0:
        _adjust("verbosity", signals["positive"] * _LEARNING_RATE)
        _adjust("proactivity", signals["positive"] * _LEARNING_RATE * 0.5)
        _adjust("warmth_level", signals["positive"] * _LEARNING_RATE * 0.8)

    if signals["negative"] > 0:
        _adjust("verbosity", -signals["negative"] * _LEARNING_RATE * 1.5)
        _adjust("proactivity", -signals["negative"] * _LEARNING_RATE)
        _adjust("suggestion_boldness", -signals["negative"] * _LEARNING_RATE)

    if signals["depth_seeking"] > 0:
        _adjust("depth_default", signals["depth_seeking"] * _LEARNING_RATE * 1.2)
        _adjust("verbosity", signals["depth_seeking"] * _LEARNING_RATE * 0.5)

    if signals["humor_response"] > 0:
        _adjust("humor_frequency", signals["humor_response"] * _LEARNING_RATE * 1.5)

    if signals["message_length"] < 0:
        # short messages = dial back verbosity
        _adjust("verbosity", signals["message_length"] * _LEARNING_RATE)

    return {
        "signals": signals,
        "params": get_behavioral_params(),
        "adaptations_applied": True,
    }


def _adjust(param: str, delta: float) -> None:
    """adjust a behavioral parameter within bounds."""
    current = _behavioral_params.get(param, 0.5)
    _behavioral_params[param] = max(_MIN_PARAM, min(_MAX_PARAM, current + delta))


def get_behavioral_guidance() -> str:
    """generate a natural language behavioral guidance string for the system prompt.

    this is injected into the chat context so the LLM knows how to calibrate.
    """
    p = _behavioral_params
    parts: list[str] = []

    if p["verbosity"] > 0.7:
        parts.append(
            "matt tends to engage with detailed responses — feel free to elaborate"
        )
    elif p["verbosity"] < 0.3:
        parts.append("matt prefers concise responses — keep it tight")

    if p["proactivity"] > 0.7:
        parts.append("he responds well to proactive suggestions")
    elif p["proactivity"] < 0.3:
        parts.append("hold back on unsolicited suggestions unless important")

    if p["humor_frequency"] > 0.6:
        parts.append("humor lands well — don't be afraid to be playful")

    if p["depth_default"] > 0.7:
        parts.append("he likes going deep — default to thorough analysis")
    elif p["depth_default"] < 0.3:
        parts.append("surface-level is usually enough unless he asks for more")

    if p["warmth_level"] > 0.7:
        parts.append("emotional warmth is welcome")
    elif p["warmth_level"] < 0.3:
        parts.append("keep the emotional temperature moderate")

    if p["suggestion_boldness"] > 0.7:
        parts.append("bold architectural suggestions are appreciated")

    if not parts:
        return ""

    return "## behavioral calibration\n" + "\n".join(f"- {p}" for p in parts)


# ---------------------------------------------------------------------------
# persistence — save/load behavioral state
# ---------------------------------------------------------------------------


async def save_behavioral_snapshot() -> None:
    """persist current behavioral params to self_memory."""
    db = get_db_manager()
    snapshot = {
        "params": _behavioral_params,
        "signal_count": len(_signal_history),
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        async with db.session_scope() as session:
            # upsert — delete old snapshot, insert new
            await session.execute(
                text("DELETE FROM self_memory WHERE source = 'behavioral-adaptation'")
            )
            await session.execute(
                text(
                    "INSERT INTO self_memory (id, cycle_number, summary, tags, source, created_at) "
                    "VALUES (:id, :cycle, :summary, :tags, :source, :created_at)"
                ),
                {
                    "id": _generate_id(),
                    "cycle": 0,
                    "summary": json.dumps(snapshot),
                    "tags": json.dumps(["behavioral", "adaptation", "snapshot"]),
                    "source": "behavioral-adaptation",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            await session.commit()
    except Exception as exc:
        logger.debug("behavioral snapshot save failed: %s", exc)


async def load_behavioral_snapshot() -> None:
    """load behavioral params from last saved snapshot."""
    db = get_db_manager()
    try:
        async with db.session_scope() as session:
            result = await session.execute(
                text(
                    "SELECT summary FROM self_memory "
                    "WHERE source = 'behavioral-adaptation' "
                    "ORDER BY created_at DESC LIMIT 1"
                )
            )
            row = result.fetchone()
            if row and row[0]:
                snapshot = json.loads(row[0])
                saved_params = snapshot.get("params", {})
                for key in _behavioral_params:
                    if key in saved_params:
                        _behavioral_params[key] = float(saved_params[key])
                logger.info(
                    "behavioral params loaded from snapshot (signals: %s)",
                    snapshot.get("signal_count", 0),
                )
    except Exception as exc:
        logger.debug("behavioral snapshot load failed: %s", exc)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _generate_id() -> str:
    import uuid

    return str(uuid.uuid4())
