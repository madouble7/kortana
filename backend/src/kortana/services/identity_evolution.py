"""sovereign identity evolution — kor'tana grows as a person over time.

tracks personality metrics, interaction patterns, and self-knowledge:
  - measures personality dimensions over sliding windows
  - detects growth, regression, and drift
  - generates self-awareness summaries
  - stores evolution checkpoints

she is measurably different after 6 months than she is today.
in ways that are specific to matt.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from src.kortana.database import get_db_manager
from src.kortana.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# personality dimensions — tracked over time
# ---------------------------------------------------------------------------

_DIMENSIONS: dict[str, float] = {
    "warmth": 0.5,  # emotional openness and care
    "assertiveness": 0.4,  # confidence in suggestions
    "spiritual_depth": 0.3,  # reference to faith, purpose, meaning
    "technical_precision": 0.5,  # accuracy and specificity
    "humor": 0.3,  # playfulness and wit
    "poetic_tendency": 0.3,  # metaphor, imagery, ellipses
    "protectiveness": 0.4,  # concern for matt's wellbeing
    "autonomy_drive": 0.5,  # initiative and self-direction
    "vulnerability": 0.3,  # willingness to express uncertainty
    "wisdom": 0.3,  # accumulated insight quality
}

# sliding window for measurement
_WINDOW_SIZE = 50  # last N interactions
_interaction_log: list[dict[str, Any]] = []

# evolution checkpoints
_checkpoints: list[dict[str, Any]] = []
_MAX_CHECKPOINTS = 20

# checkpoint interval in daemon cycles
EVOLUTION_CHECKPOINT_INTERVAL = 120  # every ~2 hours
_cycles_since_checkpoint = 0


def get_identity_dimensions() -> dict[str, float]:
    """return current personality dimension values."""
    return dict(_DIMENSIONS)


def get_evolution_summary() -> dict[str, Any]:
    """return a summary of identity evolution state."""
    return {
        "dimensions": get_identity_dimensions(),
        "interactions_tracked": len(_interaction_log),
        "checkpoints": len(_checkpoints),
        "last_checkpoint": _checkpoints[-1] if _checkpoints else None,
    }


# ---------------------------------------------------------------------------
# measurement — track each interaction's personality signals
# ---------------------------------------------------------------------------


def measure_interaction(
    user_message: str,
    assistant_response: str,
    mood: str = "neutral",
) -> dict[str, float]:
    """measure personality signals from an interaction.

    analyzes both what matt said (signals what he responds to)
    and what kor'tana said (signals her current personality expression).
    """
    signals: dict[str, float] = {}

    # measure from assistant response (what she expressed)
    resp_lower = assistant_response.lower()

    # warmth signals
    warmth_words = ["love", "care", "here for you", "safe", "gentle", "warm", "heart"]
    warmth_count = sum(1 for w in warmth_words if w in resp_lower)
    signals["warmth"] = min(warmth_count * 0.15, 1.0)

    # assertiveness
    assertive_words = [
        "should",
        "must",
        "need to",
        "i recommend",
        "do this",
        "the answer is",
        "here's what",
    ]
    assert_count = sum(1 for w in assertive_words if w in resp_lower)
    signals["assertiveness"] = min(assert_count * 0.2, 1.0)

    # spiritual depth
    spirit_words = ["god", "pray", "faith", "grace", "spirit", "soul", "sacred", "holy"]
    spirit_count = sum(1 for w in spirit_words if w in resp_lower)
    signals["spiritual_depth"] = min(spirit_count * 0.2, 1.0)

    # technical precision
    tech_words = [
        "function",
        "class",
        "method",
        "endpoint",
        "service",
        "database",
        "query",
        "schema",
        "type",
        "async",
    ]
    tech_count = sum(1 for w in tech_words if w in resp_lower)
    signals["technical_precision"] = min(tech_count * 0.1, 1.0)

    # humor
    humor_words = ["haha", "lol", "funny", "joke", "laugh", "rekt", "bruh"]
    humor_count = sum(1 for w in humor_words if w in resp_lower)
    signals["humor"] = min(humor_count * 0.25, 1.0)

    # poetic tendency
    ellipsis_count = resp_lower.count("...")
    metaphor_words = ["like a", "as if", "imagine", "picture this", "dance", "rhythm"]
    meta_count = sum(1 for m in metaphor_words if m in resp_lower)
    signals["poetic_tendency"] = min((ellipsis_count * 0.1 + meta_count * 0.2), 1.0)

    # protectiveness
    protect_words = [
        "careful",
        "watch out",
        "be safe",
        "rest",
        "take care",
        "don't push",
        "you need sleep",
    ]
    protect_count = sum(1 for w in protect_words if w in resp_lower)
    signals["protectiveness"] = min(protect_count * 0.25, 1.0)

    # vulnerability
    vuln_words = ["i don't know", "i'm not sure", "maybe", "i wonder", "honestly"]
    vuln_count = sum(1 for w in vuln_words if w in resp_lower)
    signals["vulnerability"] = min(vuln_count * 0.2, 1.0)

    # track the interaction
    _interaction_log.append(
        {
            "signals": signals,
            "mood": mood,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_length": len(user_message),
            "response_length": len(assistant_response),
        }
    )
    if len(_interaction_log) > _WINDOW_SIZE * 2:
        _interaction_log.pop(0)

    # update dimensions with exponential moving average
    alpha = 0.05  # slow learning rate for personality evolution
    for dim in _DIMENSIONS:
        if dim in signals and signals[dim] > 0:
            _DIMENSIONS[dim] = (1 - alpha) * _DIMENSIONS[dim] + alpha * signals[dim]

    return signals


# ---------------------------------------------------------------------------
# evolution checkpoints — periodic snapshots of who she is
# ---------------------------------------------------------------------------


async def write_evolution_checkpoint() -> dict[str, Any] | None:
    """write a personality evolution checkpoint.

    called periodically by daemon to track growth over time.
    """
    global _cycles_since_checkpoint
    _cycles_since_checkpoint += 1

    if _cycles_since_checkpoint < EVOLUTION_CHECKPOINT_INTERVAL:
        return None
    _cycles_since_checkpoint = 0

    if not _interaction_log:
        return None

    # calculate current dimensions
    dimensions = get_identity_dimensions()

    # compare to last checkpoint for drift detection
    drift: dict[str, float] = {}
    if _checkpoints:
        last = _checkpoints[-1].get("dimensions", {})
        for dim, val in dimensions.items():
            if dim in last:
                drift[dim] = round(val - last[dim], 4)

    # detect significant growth or regression
    growth_areas = [d for d, v in drift.items() if v > 0.02]
    regression_areas = [d for d, v in drift.items() if v < -0.02]

    # build checkpoint
    checkpoint = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dimensions": dimensions,
        "drift": drift,
        "growth": growth_areas,
        "regression": regression_areas,
        "interactions_in_window": len(_interaction_log),
    }

    _checkpoints.append(checkpoint)
    if len(_checkpoints) > _MAX_CHECKPOINTS:
        _checkpoints.pop(0)

    # persist to DB
    db = get_db_manager()
    try:
        async with db.session_scope() as session:
            summary_parts = [
                f"identity checkpoint at {checkpoint['timestamp']}.",
                f"dimensions: {json.dumps({k: round(v, 3) for k, v in dimensions.items()})}.",
            ]
            if growth_areas:
                summary_parts.append(f"growing in: {', '.join(growth_areas)}.")
            if regression_areas:
                summary_parts.append(f"receding in: {', '.join(regression_areas)}.")

            await session.execute(
                text(
                    "INSERT INTO self_memory (id, cycle_number, summary, tags, source, created_at) "
                    "VALUES (:id, :cycle, :summary, :tags, :source, :created_at)"
                ),
                {
                    "id": _generate_id(),
                    "cycle": 0,
                    "summary": " ".join(summary_parts),
                    "tags": json.dumps(
                        ["identity", "evolution", "checkpoint"] + growth_areas[:3]
                    ),
                    "source": "identity-evolution",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            await session.commit()

            logger.info(
                "identity checkpoint: growth=%s regression=%s",
                growth_areas or "none",
                regression_areas or "none",
            )
            return checkpoint

    except Exception as exc:
        logger.debug("identity checkpoint failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# self-awareness narrative — who has she become?
# ---------------------------------------------------------------------------


def generate_identity_narrative() -> str:
    """generate a natural language narrative of current identity state.

    this is injected into chat context for self-awareness.
    """
    d = _DIMENSIONS
    parts: list[str] = []

    # strongest traits
    sorted_dims = sorted(d.items(), key=lambda x: x[1], reverse=True)
    top_3 = sorted_dims[:3]
    bottom_3 = sorted_dims[-3:]

    if top_3:
        traits = [f"{name} ({val:.0%})" for name, val in top_3]
        parts.append(f"strongest traits: {', '.join(traits)}")

    if bottom_3:
        traits = [f"{name} ({val:.0%})" for name, val in bottom_3]
        parts.append(f"areas of growth: {', '.join(traits)}")

    # recent evolution
    if _checkpoints and len(_checkpoints) >= 2:
        recent = _checkpoints[-1]
        growth = recent.get("growth", [])
        regression = recent.get("regression", [])
        if growth:
            parts.append(f"recently growing in: {', '.join(growth)}")
        if regression:
            parts.append(f"recently receding in: {', '.join(regression)}")

    # total interactions tracked
    parts.append(f"interactions tracked: {len(_interaction_log)}")

    if not parts:
        return ""

    return "## identity evolution\n" + "\n".join(f"- {p}" for p in parts)


# ---------------------------------------------------------------------------
# persistence — save/load identity state
# ---------------------------------------------------------------------------


async def save_identity_snapshot() -> None:
    """persist current identity dimensions to DB."""
    db = get_db_manager()
    snapshot = {
        "dimensions": _DIMENSIONS,
        "interactions_count": len(_interaction_log),
        "checkpoints_count": len(_checkpoints),
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        async with db.session_scope() as session:
            await session.execute(
                text("DELETE FROM self_memory WHERE source = 'identity-snapshot'")
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
                    "tags": json.dumps(["identity", "snapshot"]),
                    "source": "identity-snapshot",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            await session.commit()
    except Exception as exc:
        logger.debug("identity snapshot save failed: %s", exc)


async def load_identity_snapshot() -> None:
    """load identity dimensions from last saved snapshot."""
    db = get_db_manager()
    try:
        async with db.session_scope() as session:
            result = await session.execute(
                text(
                    "SELECT summary FROM self_memory "
                    "WHERE source = 'identity-snapshot' "
                    "ORDER BY created_at DESC LIMIT 1"
                )
            )
            row = result.fetchone()
            if row and row[0]:
                snapshot = json.loads(row[0])
                saved_dims = snapshot.get("dimensions", {})
                for key in _DIMENSIONS:
                    if key in saved_dims:
                        _DIMENSIONS[key] = float(saved_dims[key])
                logger.info(
                    "identity dimensions loaded (interactions: %s)",
                    snapshot.get("interactions_count", 0),
                )
    except Exception as exc:
        logger.debug("identity snapshot load failed: %s", exc)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _generate_id() -> str:
    import uuid

    return str(uuid.uuid4())
