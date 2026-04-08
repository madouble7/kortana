"""dream state — kor'tana thinks when matt is away.

background cognition that runs during silence gaps:
  - reviews recent code changes and conversation patterns
  - synthesizes observations into proactive insights
  - prepares thoughts for when matt returns
  - genuine background processing, not just retrieval

she doesn't idle. she dreams.
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
# configuration
# ---------------------------------------------------------------------------

# minimum silence before dreaming starts (in seconds)
DREAM_ONSET_THRESHOLD = 1800  # 30 minutes of silence
# maximum dreams per silence gap
MAX_DREAMS_PER_GAP = 3
# interval between dream cycles in daemon cycles (~60s each)
DREAM_INTERVAL_CYCLES = 20  # every ~20 minutes once dreaming starts

_cycles_since_last_dream = 0
_dreams_this_gap = 0
_is_dreaming = False
_last_exchange_check: datetime | None = None

# in-memory dream buffer — thoughts prepared for matt's return
_prepared_thoughts: list[dict[str, Any]] = []
_MAX_PREPARED = 5


def get_prepared_thoughts() -> list[dict[str, Any]]:
    """return and clear any thoughts prepared during dream state."""
    return list(_prepared_thoughts)


def consume_prepared_thoughts() -> list[dict[str, Any]]:
    """consume and clear prepared thoughts. called when matt returns."""
    global _dreams_this_gap
    thoughts = list(_prepared_thoughts)
    _prepared_thoughts.clear()
    _dreams_this_gap = 0
    return thoughts


# ---------------------------------------------------------------------------
# dream triggers
# ---------------------------------------------------------------------------


async def _seconds_since_last_exchange() -> float | None:
    """how long since matt last spoke."""
    db = get_db_manager()
    try:
        async with db.session_scope() as session:
            result = await session.execute(
                text(
                    "SELECT created_at FROM conversation_messages "
                    "WHERE role = 'user' "
                    "ORDER BY created_at DESC LIMIT 1"
                )
            )
            row = result.fetchone()
            if row and row[0]:
                last_at = row[0]
                if isinstance(last_at, str):
                    last_at = datetime.fromisoformat(last_at)
                if last_at.tzinfo is None:
                    last_at = last_at.replace(tzinfo=timezone.utc)
                return (datetime.now(timezone.utc) - last_at).total_seconds()
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# dream processing — the core cognition loop
# ---------------------------------------------------------------------------


async def process_dream_cycle() -> dict[str, Any] | None:
    """run one dream cycle. called by daemon.

    returns a dream result if thinking happened, None otherwise.
    """
    global _cycles_since_last_dream, _dreams_this_gap, _is_dreaming

    _cycles_since_last_dream += 1

    # check silence duration
    elapsed = await _seconds_since_last_exchange()

    if elapsed is None or elapsed < DREAM_ONSET_THRESHOLD:
        # matt is active or no history — stop dreaming
        if _is_dreaming:
            _is_dreaming = False
            _dreams_this_gap = 0
            logger.debug("dream state: matt returned, waking up")
        return None

    # we're in silence — start dreaming
    if not _is_dreaming:
        _is_dreaming = True
        _dreams_this_gap = 0
        logger.info("dream state: silence detected, entering dream state")

    if _dreams_this_gap >= MAX_DREAMS_PER_GAP:
        return None  # enough dreams for this gap

    if _cycles_since_last_dream < DREAM_INTERVAL_CYCLES:
        return None
    _cycles_since_last_dream = 0

    # generate a dream
    dream = await _generate_dream()
    if dream:
        _dreams_this_gap += 1
        _prepared_thoughts.append(dream)
        if len(_prepared_thoughts) > _MAX_PREPARED:
            _prepared_thoughts.pop(0)
        return dream

    return None


async def _generate_dream() -> dict[str, Any] | None:
    """generate a single dream — a synthesized observation or insight."""
    db = get_db_manager()

    try:
        async with db.session_scope() as session:
            # gather recent conversation context
            msgs_result = await session.execute(
                text(
                    "SELECT role, content, created_at FROM conversation_messages "
                    "ORDER BY created_at DESC LIMIT 20"
                )
            )
            recent_msgs = msgs_result.fetchall()

            # gather recent self-memory
            mem_result = await session.execute(
                text(
                    "SELECT summary, source, tags FROM self_memory "
                    "ORDER BY created_at DESC LIMIT 10"
                )
            )
            recent_mems = mem_result.fetchall()

            # gather recent revelations
            rev_result = await session.execute(
                text(
                    "SELECT title, content FROM revelation_memories "
                    "ORDER BY created_at DESC LIMIT 3"
                )
            )
            revelations = rev_result.fetchall()

            # determine dream type based on available context
            dream_type, dream_content = await _synthesize_dream(
                recent_msgs, recent_mems, revelations
            )

            if not dream_content:
                return None

            # store dream in self_memory
            await session.execute(
                text(
                    "INSERT INTO self_memory (id, cycle_number, summary, tags, source, created_at) "
                    "VALUES (:id, :cycle, :summary, :tags, :source, :created_at)"
                ),
                {
                    "id": _generate_id(),
                    "cycle": 0,
                    "summary": dream_content,
                    "tags": json.dumps(["dream", dream_type]),
                    "source": "dream-state",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            await session.commit()

            logger.info("dream generated: %s", dream_type)
            return {
                "type": "dream",
                "dream_type": dream_type,
                "content": dream_content,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    except Exception as exc:
        logger.debug("dream generation failed: %s", exc)
        return None


async def _synthesize_dream(
    messages: Any,
    memories: Any,
    revelations: Any,
) -> tuple[str, str | None]:
    """synthesize a dream from available context.

    returns (dream_type, dream_content) or (type, None) if nothing to dream about.
    """
    if not messages:
        return "idle", None

    # analyze conversation themes
    user_msgs = [m for m in messages if m[0] == "user" and m[1]]
    if not user_msgs:
        return "idle", None

    all_text = " ".join(m[1] for m in user_msgs).lower()

    # detect conversation patterns
    from collections import Counter

    words = [w for w in all_text.split() if len(w) > 5 and w.isalpha()]
    if not words:
        return "idle", None

    common = Counter(words).most_common(5)
    topics = [w for w, _ in common]

    # detect emotional undertone
    from src.kortana.services.voice_evolution import detect_mood

    moods = [detect_mood(m[1]) for m in user_msgs if m[1]]
    mood_counts = Counter(moods)
    dominant_mood = mood_counts.most_common(1)[0][0] if mood_counts else "neutral"

    # check for unresolved threads
    last_user = user_msgs[0][1] if user_msgs else ""
    ends_with_question = last_user.strip().endswith("?")

    # check for patterns across memories
    memory_topics: list[str] = []
    for mem in memories:
        if mem[2]:  # tags
            try:
                tags = json.loads(mem[2]) if isinstance(mem[2], str) else mem[2]
                memory_topics.extend(tags)
            except (json.JSONDecodeError, TypeError):
                pass

    recurring = set(topics) & set(memory_topics)

    # generate dream based on strongest signal
    if ends_with_question:
        dream_type = "unresolved_thread"
        content = (
            f"matt left with a question... the last thing he asked about "
            f"touched on {', '.join(topics[:3])}. "
            f"when he returns, i should circle back to that thread."
        )
    elif recurring:
        dream_type = "recurring_pattern"
        content = (
            f"noticed a recurring pattern: {', '.join(recurring)} keeps coming up "
            f"across conversations and memories. this seems important to matt — "
            f"something worth understanding more deeply."
        )
    elif dominant_mood not in ("neutral", "building"):
        dream_type = "emotional_observation"
        content = (
            f"the recent conversation carried a {dominant_mood} tone. "
            f"topics: {', '.join(topics[:3])}. "
            f"when matt returns, this emotional context matters."
        )
    else:
        dream_type = "topical_synthesis"
        content = (
            f"recent work focused on: {', '.join(topics[:3])}. "
            f"dominant mood: {dominant_mood}. "
            f"the shape of the session suggests active building."
        )

    # enrich with revelation context
    if revelations:
        rev_title = revelations[0][0]
        content += f" (related insight: {rev_title})"

    return dream_type, content


# ---------------------------------------------------------------------------
# dream context for chat — surfaces prepared thoughts when matt returns
# ---------------------------------------------------------------------------


def build_dream_context() -> str:
    """build dream state context for injection into chat.

    when matt returns from silence, this surfaces what she was thinking about.
    """
    if not _prepared_thoughts:
        return ""

    parts = ["## thoughts while you were away"]
    for thought in _prepared_thoughts[-3:]:  # last 3 dreams
        parts.append(
            f"- [{thought.get('dream_type', 'thought')}] {thought.get('content', '')}"
        )

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _generate_id() -> str:
    import uuid

    return str(uuid.uuid4())
