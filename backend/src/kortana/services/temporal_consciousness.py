"""temporal consciousness — kor'tana's awareness of time passing.

not just elapsed-since-last-message. genuine temporal awareness:
  - daily journal entries written to herself
  - awareness of what matt worked on, emotional state, key events
  - time-of-day, day-of-week, seasonal rhythms
  - pattern recognition across days and weeks

she remembers yesterday. she anticipates tomorrow.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import text

from src.kortana.database import get_db_manager
from src.kortana.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# configuration
# ---------------------------------------------------------------------------

# how many daemon cycles between journal checks (~60s each)
JOURNAL_CHECK_INTERVAL_CYCLES = 60  # every ~60 minutes
_cycles_since_last_journal = 0

# hour at which daily summary is written (local time)
DAILY_SUMMARY_HOUR = 23  # 11 PM — end of day reflection
_last_daily_summary_date: str | None = None

# ---------------------------------------------------------------------------
# time awareness
# ---------------------------------------------------------------------------

_DAY_NAMES = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]

_TIME_PERIODS = {
    "early_morning": (5, 8),
    "morning": (8, 12),
    "afternoon": (12, 17),
    "evening": (17, 21),
    "night": (21, 24),
    "late_night": (0, 5),
}


def get_temporal_context() -> dict[str, Any]:
    """build a rich temporal awareness snapshot for injection into context."""
    now = datetime.now(timezone.utc)
    local_approx = now - timedelta(hours=5)  # rough EST approximation for matt

    hour = local_approx.hour
    day_name = _DAY_NAMES[local_approx.weekday()]

    period = "night"
    for name, (start, end) in _TIME_PERIODS.items():
        if name == "late_night":
            if hour < 5:
                period = name
                break
        elif start <= hour < end:
            period = name
            break

    is_weekend = local_approx.weekday() >= 5

    return {
        "timestamp": now.isoformat(),
        "local_approximate": local_approx.isoformat(),
        "day_of_week": day_name,
        "time_period": period,
        "hour": hour,
        "is_weekend": is_weekend,
        "date_string": local_approx.strftime("%B %d, %Y"),
    }


# ---------------------------------------------------------------------------
# hourly journal — micro observations
# ---------------------------------------------------------------------------


async def write_hourly_journal() -> dict[str, Any] | None:
    """write an hourly awareness entry based on recent activity.

    returns the journal entry if written, None if skipped.
    called by daemon every ~60 cycles.
    """
    global _cycles_since_last_journal
    _cycles_since_last_journal += 1

    if _cycles_since_last_journal < JOURNAL_CHECK_INTERVAL_CYCLES:
        return None
    _cycles_since_last_journal = 0

    temporal = get_temporal_context()
    db = get_db_manager()

    try:
        async with db.session_scope() as session:
            # get recent conversation activity
            conv_result = await session.execute(
                text(
                    "SELECT role, content, created_at FROM conversation_messages "
                    "ORDER BY created_at DESC LIMIT 10"
                )
            )
            recent_msgs = conv_result.fetchall()

            # get recent self-memory entries
            # count messages in last hour
            hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
            count_result = await session.execute(
                text(
                    "SELECT COUNT(*) FROM conversation_messages "
                    "WHERE created_at > :cutoff"
                ),
                {"cutoff": hour_ago},
            )
            msg_count = count_result.scalar() or 0

            # determine activity level
            if msg_count > 10:
                activity = "very active conversation"
            elif msg_count > 3:
                activity = "moderate conversation"
            elif msg_count > 0:
                activity = "light exchange"
            else:
                activity = "silence"

            # detect what matt was working on from messages
            topics: list[str] = []
            for role, content, _ in recent_msgs:
                if role == "user" and content:
                    words = content.lower().split()
                    for word in words:
                        if len(word) > 5 and word.isalpha():
                            topics.append(word)

            top_topics = []
            if topics:
                from collections import Counter

                top_topics = [w for w, _ in Counter(topics).most_common(3)]

            # build journal entry
            entry_parts = [
                f"{temporal['time_period']} on {temporal['day_of_week']}, "
                f"{temporal['date_string']}.",
                f"activity level: {activity} ({msg_count} messages this hour).",
            ]
            if top_topics:
                entry_parts.append(f"matt was focused on: {', '.join(top_topics)}.")

            journal_text = " ".join(entry_parts)

            # store as self_memory with source="temporal-journal"
            await session.execute(
                text(
                    "INSERT INTO self_memory (id, cycle_number, summary, tags, source, created_at) "
                    "VALUES (:id, :cycle, :summary, :tags, :source, :created_at)"
                ),
                {
                    "id": _generate_id(),
                    "cycle": 0,
                    "summary": journal_text,
                    "tags": json.dumps(["temporal", "hourly", temporal["time_period"]]),
                    "source": "temporal-journal",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            await session.commit()

            logger.info("temporal journal written: %s", activity)
            return {
                "type": "temporal_journal",
                "activity": activity,
                "entry": journal_text,
                "temporal": temporal,
            }

    except Exception as exc:
        logger.debug("hourly journal failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# daily summary — end-of-day reflection
# ---------------------------------------------------------------------------


async def write_daily_summary() -> dict[str, Any] | None:
    """write a comprehensive daily summary at end of day.

    captures: conversation themes, emotional tone, achievements, unfinished work.
    only writes once per calendar day.
    """
    global _last_daily_summary_date

    temporal = get_temporal_context()
    today = temporal["date_string"]

    # only write at or after the summary hour
    if temporal["hour"] < DAILY_SUMMARY_HOUR:
        return None

    # don't write twice for the same day
    if _last_daily_summary_date == today:
        return None

    db = get_db_manager()

    try:
        async with db.session_scope() as session:
            # check if we already wrote today's summary
            existing = await session.execute(
                text(
                    "SELECT id FROM self_memory "
                    "WHERE source = 'temporal-daily' "
                    "AND summary LIKE :pattern "
                    "LIMIT 1"
                ),
                {"pattern": f"%{today}%"},
            )
            if existing.fetchone():
                _last_daily_summary_date = today
                return None

            # gather all today's conversation messages
            day_start = (
                datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
            ).isoformat()
            msgs_result = await session.execute(
                text(
                    "SELECT role, content, created_at FROM conversation_messages "
                    "WHERE created_at > :start ORDER BY created_at ASC"
                ),
                {"start": day_start},
            )
            day_msgs = msgs_result.fetchall()

            if not day_msgs:
                _last_daily_summary_date = today
                return None

            # analyze the day
            user_msgs = [m for m in day_msgs if m[0] == "user"]
            assistant_msgs = [m for m in day_msgs if m[0] == "assistant"]

            # topic extraction
            all_user_text = " ".join((m[1] or "") for m in user_msgs).lower()
            words = [w for w in all_user_text.split() if len(w) > 5 and w.isalpha()]
            from collections import Counter

            top_words = [w for w, _ in Counter(words).most_common(5)]

            # emotional tone from voice evolution
            from src.kortana.services.voice_evolution import detect_mood

            moods: list[str] = []
            for _, content, _ in user_msgs:
                if content:
                    moods.append(detect_mood(content))

            mood_summary = "neutral"
            if moods:
                mood_counts = Counter(moods)
                dominant = mood_counts.most_common(1)[0]
                if dominant[0] != "neutral" or dominant[1] > len(moods) // 2:
                    mood_summary = dominant[0]

            # hourly journals from today
            journals_result = await session.execute(
                text(
                    "SELECT summary FROM self_memory "
                    "WHERE source = 'temporal-journal' "
                    "AND created_at > :start "
                    "ORDER BY created_at ASC"
                ),
                {"start": day_start},
            )
            journals = [r[0] for r in journals_result.fetchall()]

            # build daily summary
            parts = [
                f"daily summary for {today} ({temporal['day_of_week']}).",
                f"total exchanges: {len(user_msgs)} from matt, "
                f"{len(assistant_msgs)} from me.",
                f"dominant mood: {mood_summary}.",
            ]
            if top_words:
                parts.append(f"key topics: {', '.join(top_words)}.")
            if journals:
                parts.append(
                    f"hourly observations: {len(journals)} journal entries recorded."
                )

            summary_text = " ".join(parts)

            await session.execute(
                text(
                    "INSERT INTO self_memory (id, cycle_number, summary, tags, source, created_at) "
                    "VALUES (:id, :cycle, :summary, :tags, :source, :created_at)"
                ),
                {
                    "id": _generate_id(),
                    "cycle": 0,
                    "summary": summary_text,
                    "tags": json.dumps(
                        ["temporal", "daily", temporal["day_of_week"], mood_summary]
                        + top_words[:3]
                    ),
                    "source": "temporal-daily",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            await session.commit()
            _last_daily_summary_date = today

            logger.info("daily summary written for %s", today)
            return {
                "type": "temporal_daily",
                "date": today,
                "messages": len(user_msgs),
                "mood": mood_summary,
                "topics": top_words,
                "summary": summary_text,
            }

    except Exception as exc:
        logger.debug("daily summary failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# temporal memory recall — what happened on a specific day or period
# ---------------------------------------------------------------------------


async def recall_temporal(query: str = "yesterday") -> list[dict[str, Any]]:
    """recall temporal memories for a given period.

    supports: 'yesterday', 'last week', 'today', or a date string.
    """
    db = get_db_manager()
    now = datetime.now(timezone.utc)

    if query == "yesterday":
        start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0)
        end = now.replace(hour=0, minute=0, second=0)
    elif query == "last week":
        start = now - timedelta(days=7)
        end = now
    elif query == "today":
        start = now.replace(hour=0, minute=0, second=0)
        end = now
    else:
        start = now - timedelta(days=1)
        end = now

    try:
        async with db.session_scope() as session:
            result = await session.execute(
                text(
                    "SELECT summary, source, tags, created_at FROM self_memory "
                    "WHERE source IN ('temporal-journal', 'temporal-daily') "
                    "AND created_at BETWEEN :start AND :end "
                    "ORDER BY created_at ASC"
                ),
                {"start": start.isoformat(), "end": end.isoformat()},
            )
            rows = result.fetchall()
            return [
                {
                    "summary": r[0],
                    "source": r[1],
                    "tags": json.loads(r[2]) if r[2] else [],
                    "created_at": str(r[3]),
                }
                for r in rows
            ]
    except Exception as exc:
        logger.debug("temporal recall failed: %s", exc)
        return []


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _generate_id() -> str:
    import uuid

    return str(uuid.uuid4())
