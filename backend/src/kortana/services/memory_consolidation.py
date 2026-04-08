"""memory consolidation service -- kor tana remembers across sessions.

periodically reviews conversation history and distills durable memories:
  - recurring topics matt cares about
  - emotional patterns and preferences
  - important life events and people mentioned
  - things matt explicitly asked to remember
  - interaction style preferences

these consolidations are stored as self_memory entries with source='consolidation'
and injected into future conversations via the memory policy system.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from src.kortana.database import get_db_manager
from src.kortana.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# configuration
# ---------------------------------------------------------------------------

# minimum messages before consolidation runs
MIN_MESSAGES_FOR_CONSOLIDATION = 10

# how many recent messages to analyze per run
CONSOLIDATION_WINDOW = 50

# how often to consolidate (in daemon cycles, ~60s each)
CONSOLIDATION_INTERVAL_CYCLES = 30  # every ~30 minutes

_cycles_since_last = 0

# ---------------------------------------------------------------------------
# pattern extractors — lightweight, no LLM needed
# ---------------------------------------------------------------------------

# explicit "remember this" patterns
_REMEMBER_PATTERNS = [
    re.compile(r"remember (?:that |this[: ])?(.{10,200})", re.IGNORECASE),
    re.compile(r"don['']?t forget[: ]+(.{10,200})", re.IGNORECASE),
    re.compile(r"keep in mind[: ]+(.{10,200})", re.IGNORECASE),
    re.compile(r"note[: ]+(.{10,200})", re.IGNORECASE),
]

# people mentioned (capitalized names after relational words)
_PEOPLE_PATTERN = re.compile(
    r"\b(?:my |his |her )?"
    r"(?:brother|sister|son|daughter|wife|ex|friend|teacher|student|co-teacher|mom|dad|father|mother)"
    r" (?:is |named |called )?([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)",
    re.MULTILINE,
)

# topics — common nouns that appear frequently
_TOPIC_STOPWORDS = {
    "the",
    "and",
    "but",
    "for",
    "not",
    "you",
    "all",
    "can",
    "had",
    "her",
    "was",
    "one",
    "our",
    "out",
    "are",
    "has",
    "his",
    "how",
    "its",
    "let",
    "may",
    "say",
    "she",
    "too",
    "use",
    "way",
    "who",
    "did",
    "get",
    "got",
    "him",
    "hit",
    "now",
    "old",
    "see",
    "two",
    "boy",
    "day",
    "did",
    "eye",
    "few",
    "man",
    "new",
    "put",
    "ran",
    "red",
    "run",
    "set",
    "sit",
    "top",
    "win",
    "yet",
    "also",
    "back",
    "been",
    "call",
    "come",
    "each",
    "even",
    "give",
    "good",
    "have",
    "help",
    "here",
    "high",
    "just",
    "keep",
    "know",
    "last",
    "like",
    "long",
    "look",
    "made",
    "make",
    "many",
    "much",
    "must",
    "name",
    "need",
    "next",
    "only",
    "over",
    "part",
    "same",
    "some",
    "such",
    "take",
    "tell",
    "than",
    "that",
    "them",
    "then",
    "they",
    "this",
    "time",
    "turn",
    "very",
    "want",
    "well",
    "went",
    "were",
    "what",
    "when",
    "will",
    "with",
    "work",
    "year",
    "your",
    "yeah",
    "okay",
    "sure",
    "yes",
    "matt",
    "thing",
    "think",
    "don't",
    "it's",
    "i'm",
    "that's",
    "there",
    "about",
    "would",
    "could",
    "should",
    "going",
    "really",
    "right",
    "being",
}


def _extract_explicit_memories(messages: list[dict[str, str]]) -> list[str]:
    """find explicit 'remember this' instructions from matt."""
    memories = []
    for msg in messages:
        if msg["role"] != "user":
            continue
        for pattern in _REMEMBER_PATTERNS:
            match = pattern.search(msg["content"])
            if match:
                memories.append(match.group(1).strip().rstrip("."))
    return memories


def _extract_people(messages: list[dict[str, str]]) -> list[str]:
    """find people mentioned in conversation."""
    people: set[str] = set()
    for msg in messages:
        for match in _PEOPLE_PATTERN.finditer(msg["content"]):
            name = match.group(1).strip()
            if len(name) > 2:
                people.add(name)
    return sorted(people)


def _extract_recurring_topics(messages: list[dict[str, str]]) -> list[str]:
    """find recurring topics from user messages."""
    word_freq: Counter[str] = Counter()
    for msg in messages:
        if msg["role"] != "user":
            continue
        words = re.findall(r"\b[a-z]{4,}\b", msg["content"].lower())
        for w in words:
            if w not in _TOPIC_STOPWORDS:
                word_freq[w] += 1
    # return words that appear 3+ times
    return [word for word, count in word_freq.most_common(10) if count >= 3]


def _extract_emotional_patterns(messages: list[dict[str, str]]) -> dict[str, int]:
    """detect emotional tone patterns from user messages."""
    from src.kortana.services.voice_evolution import detect_mood

    mood_counts: Counter[str] = Counter()
    for msg in messages:
        if msg["role"] != "user":
            continue
        mood = detect_mood(msg["content"])
        mood_counts[mood] += 1
    return dict(mood_counts)


# ---------------------------------------------------------------------------
# consolidation engine
# ---------------------------------------------------------------------------


async def consolidate_memories(force: bool = False) -> dict[str, Any] | None:
    """review recent conversations and distill durable memories.

    returns a summary of what was consolidated, or None if skipped.
    """
    global _cycles_since_last

    if not force:
        _cycles_since_last += 1
        if _cycles_since_last < CONSOLIDATION_INTERVAL_CYCLES:
            return None
    _cycles_since_last = 0

    db = get_db_manager()

    # fetch recent messages
    try:
        async with db.session_scope() as session:
            result = await session.execute(
                text(
                    "SELECT role, content, created_at FROM conversation_messages "
                    "ORDER BY created_at DESC LIMIT :limit"
                ),
                {"limit": CONSOLIDATION_WINDOW},
            )
            rows = result.fetchall()
    except Exception as exc:
        logger.warning("memory consolidation: failed to fetch messages: %s", exc)
        return None

    if len(rows) < MIN_MESSAGES_FOR_CONSOLIDATION:
        return None

    messages = [{"role": row[0], "content": row[1]} for row in reversed(rows)]

    # extract
    explicit = _extract_explicit_memories(messages)
    people = _extract_people(messages)
    topics = _extract_recurring_topics(messages)
    moods = _extract_emotional_patterns(messages)

    # check if we have anything worth storing
    if not explicit and not people and not topics:
        return None

    # build consolidation summary
    parts: list[str] = []
    if explicit:
        parts.append(f"matt asked to remember: {'; '.join(explicit)}")
    if people:
        parts.append(f"people mentioned: {', '.join(people)}")
    if topics:
        parts.append(f"recurring topics: {', '.join(topics)}")
    if moods:
        dominant = max(moods, key=lambda m: moods[m])
        parts.append(f"dominant mood: {dominant} ({moods[dominant]} occurrences)")

    summary = " | ".join(parts)
    tags = ["consolidation"] + topics[:5]
    if explicit:
        tags.append("explicit_memory")

    # deduplicate — don't store if very similar to last consolidation
    try:
        async with db.session_scope() as session:
            last_result = await session.execute(
                text(
                    "SELECT summary FROM self_memory "
                    "WHERE source = 'consolidation' "
                    "ORDER BY created_at DESC LIMIT 1"
                )
            )
            last_row = last_result.fetchone()
            if last_row and last_row[0]:
                # simple overlap check
                last_words = set(last_row[0].lower().split())
                new_words = set(summary.lower().split())
                overlap = len(last_words & new_words) / max(len(new_words), 1)
                if overlap > 0.7:
                    logger.debug("memory consolidation: skipped (too similar to last)")
                    return None
    except Exception:
        pass  # dedup is best-effort

    # persist
    try:
        async with db.session_scope() as session:
            await session.execute(
                text(
                    "INSERT INTO self_memory (id, cycle_number, summary, tags, source, created_at) "
                    "VALUES (:id, :cycle, :summary, :tags, :source, :created_at)"
                ),
                {
                    "id": str(__import__("uuid").uuid4()),
                    "cycle": 0,
                    "summary": summary,
                    "tags": json.dumps(tags),
                    "source": "consolidation",
                    "created_at": datetime.now(timezone.utc),
                },
            )
            await session.commit()
        logger.info("memory consolidated: %s", summary[:100])
    except Exception as exc:
        logger.warning("memory consolidation: failed to persist: %s", exc)
        return None

    result = {
        "explicit_memories": explicit,
        "people": people,
        "topics": topics,
        "moods": moods,
        "summary": summary,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return result
