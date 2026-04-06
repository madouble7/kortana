"""
KOR'TANA Revelation Engine — Phase 9 Insight Synthesis
Scans accumulated observations (SelfMemory, git activity, CI patterns, conversation
topics) and asks an LLM whether any non-obvious pattern has emerged worth surfacing.

Design principles:
  - High signal, low noise: only write when confidence >= CONFIDENCE_THRESHOLD
  - Deduplication: skip revelations too similar to recent ones
  - Token budget guard: mirrors ExperienceDistiller's budget pattern
  - Async: works cleanly inside FastAPI's event loop
"""

import asyncio
import logging
import os
import subprocess
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.kortana.model_lane_policy import describe_model_lane
from src.kortana.models import (
    ConstitutionalDecision,
    ConversationMessage,
    CovenantEnforcementRecord,
    OutcomeLearningRecord,
    RevelationMemory,
    SelfMemory,
)
from src.kortana.provider_model_defaults import LLM_ROUTER_GEMINI_MODEL
from src.kortana.services.gemini_config import get_preferred_model_name

logger = logging.getLogger(__name__)

REVELATION_MODEL = LLM_ROUTER_GEMINI_MODEL
CONFIDENCE_THRESHOLD = 0.65
MIN_OBSERVATIONS = 5          # don't synthesise without at least this many data points
REVELATION_COOLDOWN_HOURS = 6  # minimum gap between revelation runs
DEDUP_SIMILARITY_THRESHOLD = 0.7  # title overlap ratio to skip duplicates

_session_tokens_used = 0
_SESSION_TOKEN_BUDGET = 30_000


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------
def get_revelation_model_info() -> Dict[str, str]:
    """Return preferred and resolved Gemini model metadata for revelation synthesis."""
    resolved_model = get_preferred_model_name(REVELATION_MODEL)
    return {
        "preferred_model": REVELATION_MODEL,
        "model": resolved_model,
        "model_lane": describe_model_lane(resolved_model),
    }


async def _call_gemini_revelation(prompt: str) -> Optional[str]:
    global _session_tokens_used
    if _session_tokens_used >= _SESSION_TOKEN_BUDGET:
        logger.warning("Revelation token budget exhausted")
        return None

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None

    try:
        from google import genai

        model_info = get_revelation_model_info()

        def _generate() -> Any:
            client = genai.Client(api_key=api_key)
            return client.models.generate_content(
                model=model_info["model"], contents=prompt
            )

        response = await asyncio.to_thread(_generate)
        _session_tokens_used += (len(prompt) + len(response.text or "")) // 4
        return response.text
    except Exception as e:
        logger.error(f"Revelation LLM call failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Observation gathering helpers
# ---------------------------------------------------------------------------

async def _gather_self_memories(db: AsyncSession, limit: int = 40) -> List[str]:
    stmt = (
        select(SelfMemory)
        .order_by(SelfMemory.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [
        f"[{r.created_at.strftime('%Y-%m-%d')} source={r.source}] {r.summary[:300]}"
        for r in rows
    ]


async def _gather_conversation_topics(db: AsyncSession, limit: int = 20) -> List[str]:
    stmt = (
        select(ConversationMessage)
        .where(ConversationMessage.role == "user")
        .order_by(ConversationMessage.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [f"[{r.created_at.strftime('%Y-%m-%d')}] {r.content[:200]}" for r in rows]


def _gather_git_activity(repo_root: str = r"c:\kortana", limit: int = 20) -> List[str]:
    try:
        result = subprocess.run(
            ["git", "log", f"--max-count={limit}", "--format=%ad %s", "--date=short"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return [line for line in result.stdout.strip().splitlines() if line]
    except Exception as e:
        logger.debug(f"git log failed (non-fatal): {e}")
    return []


async def _recent_revelation_titles(db: AsyncSession, hours: int = 72) -> List[str]:
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    stmt = (
        select(RevelationMemory.title)
        .where(RevelationMemory.created_at >= cutoff)
        .order_by(RevelationMemory.created_at.desc())
    )
    result = await db.execute(stmt)
    return [row[0] for row in result.all()]


async def _gather_outcome_signals(db: AsyncSession, limit: int = 20) -> List[str]:
    """Summarise recent outcome learning records for the synthesis prompt."""
    stmt = (
        select(OutcomeLearningRecord)
        .order_by(OutcomeLearningRecord.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    lines = []
    for r in rows:
        ts = r.created_at.strftime("%Y-%m-%d") if r.created_at else "?"
        lines.append(
            f"{ts} outcome={r.outcome_verdict} signal={r.adaptation_signal} "
            f"weight={r.weight_delta:+.2f} scope={r.scope} lesson={r.lesson[:80]}"
        )
    return lines


async def _gather_covenant_decisions(db: AsyncSession, limit: int = 15) -> List[str]:
    """Summarise recent constitutional decisions for the synthesis prompt."""
    stmt = (
        select(ConstitutionalDecision)
        .order_by(ConstitutionalDecision.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    lines = []
    for r in rows:
        ts = r.created_at.strftime("%Y-%m-%d") if r.created_at else "?"
        drift = " DRIFT" if r.drift_detected else ""
        lines.append(
            f"{ts} verdict={r.verdict} subject={r.subject_type}{drift} "
            f"principles={r.principles_invoked}"
        )
    return lines


async def _gather_override_resolutions(db: AsyncSession, limit: int = 10) -> List[str]:
    """Summarise recent human override resolutions for the synthesis prompt."""
    stmt = (
        select(CovenantEnforcementRecord)
        .where(CovenantEnforcementRecord.override_status != "pending")
        .order_by(CovenantEnforcementRecord.override_resolved_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    lines = []
    for r in rows:
        ts = r.override_resolved_at.strftime("%Y-%m-%d") if r.override_resolved_at else "?"
        lines.append(
            f"{ts} resolution={r.override_status} target={r.target_type} "
            f"action={r.action} rationale={str(r.human_rationale or '')[:60]}"
        )
    return lines


def _is_duplicate(new_title: str, existing_titles: List[str]) -> bool:
    """Simple token-overlap dedup — avoid re-surfacing the same insight."""
    new_words = set(new_title.lower().split())
    for title in existing_titles:
        existing_words = set(title.lower().split())
        if not new_words or not existing_words:
            continue
        overlap = len(new_words & existing_words) / max(len(new_words), len(existing_words))
        if overlap >= DEDUP_SIMILARITY_THRESHOLD:
            return True
    return False


# ---------------------------------------------------------------------------
# Synthesis prompt
# ---------------------------------------------------------------------------

_SYNTHESIS_PROMPT_TEMPLATE = """You are kor'tana's Revelation Engine — a subsystem whose only job is to detect genuine, non-obvious patterns from accumulated observations.

You have access to the following raw observations:

## Recent self-memories (distilled diary entries, voice interactions, diary logs)
{self_memories}

## Recent conversation topics (what Matt has been asking or discussing)
{conversation_topics}

## Recent git activity (what code has actually been changing)
{git_activity}

## Recent outcome learning signals (what succeeded, failed, or was inconclusive in the autonomy pipeline)
{outcome_signals}

## Recent covenant decisions (constitutional verdicts on goals, candidates, and adaptations)
{covenant_decisions}

## Recent human override resolutions (where Matt intervened in the autonomy pipeline)
{override_resolutions}

---

Your task: Identify at most 2 revelations — genuine insights that:
  - Require time accumulation to notice (not obvious from a single data point)
  - Cross-cut multiple observation categories above
  - Would be genuinely useful or meaningful for Matt to hear
  - Are specific, not generic platitudes

Pay particular attention to:
  - Patterns in outcome signals (recurring failures, surprising successes)
  - Drift between covenant verdicts and actual override decisions (is the covenant calibrated?)
  - Whether human overrides cluster around specific goal or action types
  - Whether autonomy pipeline weight shifts are converging or oscillating

For each revelation, respond with EXACTLY this JSON structure (no markdown, no preamble):
[
  {{
    "title": "<short, specific title (max 10 words)>",
    "content": "<1-3 sentence explanation of the pattern and why it matters>",
    "evidence": ["<evidence item 1>", "<evidence item 2>", ...],
    "revelation_type": "<pattern|contradiction|self_discovery|prediction>",
    "confidence": <float 0.0-1.0>
  }}
]

If there are NO genuine revelations worth surfacing (low signal, insufficient data, or too early), respond with exactly: []

Bias strongly toward [] — only surface revelations you are confident about. One excellent revelation beats three mediocre ones."""


# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------

class RevelationEngine:
    """Synthesise accumulated observations into high-confidence insights."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def should_run(self, force: bool = False) -> bool:
        """Check if enough time has passed since the last revelation run."""
        if force:
            return True
        cutoff = datetime.utcnow() - timedelta(hours=REVELATION_COOLDOWN_HOURS)
        stmt = (
            select(RevelationMemory)
            .where(RevelationMemory.created_at >= cutoff)
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is None

    async def synthesise(self, force: bool = False) -> List[RevelationMemory]:
        """Run full revelation cycle. Returns newly written RevelationMemory rows."""
        if not await self.should_run(force=force):
            logger.info("Revelation Engine: cooldown active, skipping")
            return []

        # Gather observations — core + autonomy pipeline
        self_memories, conversation_topics, git_activity, outcome_signals, covenant_decisions, override_resolutions = await asyncio.gather(
            _gather_self_memories(self.db, limit=40),
            _gather_conversation_topics(self.db, limit=20),
            asyncio.to_thread(_gather_git_activity),
            _gather_outcome_signals(self.db, limit=20),
            _gather_covenant_decisions(self.db, limit=15),
            _gather_override_resolutions(self.db, limit=10),
        )

        total_observations = (
            len(self_memories) + len(conversation_topics) + len(git_activity)
            + len(outcome_signals) + len(covenant_decisions)
        )
        if total_observations < MIN_OBSERVATIONS:
            logger.info(
                f"Revelation Engine: only {total_observations} observations — need {MIN_OBSERVATIONS}"
            )
            return []

        prompt = _SYNTHESIS_PROMPT_TEMPLATE.format(
            self_memories="\n".join(self_memories) or "(none yet)",
            conversation_topics="\n".join(conversation_topics) or "(none yet)",
            git_activity="\n".join(git_activity) or "(none yet)",
            outcome_signals="\n".join(outcome_signals) or "(none yet)",
            covenant_decisions="\n".join(covenant_decisions) or "(none yet)",
            override_resolutions="\n".join(override_resolutions) or "(none yet)",
        )

        raw = await _call_gemini_revelation(prompt)
        if not raw:
            return []

        return await self._parse_and_store(raw.strip())

    async def _parse_and_store(self, raw_json: str) -> List[RevelationMemory]:
        """Parse LLM JSON response and write qualifying revelations to DB."""
        import json

        # Strip markdown code blocks if present
        if raw_json.startswith("```"):
            lines = raw_json.splitlines()
            raw_json = "\n".join(
                line for line in lines if not line.startswith("```")
            ).strip()

        try:
            items = json.loads(raw_json)
        except json.JSONDecodeError as e:
            logger.error(f"Revelation Engine: JSON parse failed: {e}\nRaw: {raw_json[:300]}")
            return []

        if not isinstance(items, list):
            return []

        existing_titles = await _recent_revelation_titles(self.db, hours=72)
        written: List[RevelationMemory] = []

        for item in items:
            if not isinstance(item, dict):
                continue

            confidence = float(item.get("confidence", 0.0))
            if confidence < CONFIDENCE_THRESHOLD:
                logger.debug(
                    f"Skipping low-confidence revelation ({confidence:.2f}): {item.get('title', '?')}"
                )
                continue

            title = str(item.get("title", ""))[:256]
            if not title:
                continue

            if _is_duplicate(title, existing_titles):
                logger.info(f"Revelation Engine: dedup skip — '{title}'")
                continue

            revelation = RevelationMemory(
                id=str(uuid.uuid4()),
                title=title,
                content=str(item.get("content", ""))[:4000],
                evidence=item.get("evidence") or [],
                revelation_type=str(item.get("revelation_type", "pattern"))[:64],
                confidence=confidence,
                surfaced=False,
                source="revelation_engine",
            )
            self.db.add(revelation)
            written.append(revelation)
            existing_titles.append(title)
            logger.info(
                f"Revelation Engine: new revelation — '{title}' "
                f"(type={revelation.revelation_type}, confidence={confidence:.2f})"
            )

        if written:
            try:
                await self.db.commit()
                for r in written:
                    await self.db.refresh(r)
            except Exception:
                await self.db.rollback()
                logger.exception("Revelation Engine: failed to persist revelations")
                return []

        return written

    async def get_unsurfaced(self, limit: int = 5) -> List[RevelationMemory]:
        """Return revelations not yet acknowledged by the user."""
        stmt = (
            select(RevelationMemory)
            .where(RevelationMemory.surfaced == False)  # noqa: E712
            .order_by(RevelationMemory.created_at.asc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def mark_surfaced(self, revelation_id: str) -> bool:
        """Mark a revelation as surfaced (acknowledged)."""
        stmt = select(RevelationMemory).where(RevelationMemory.id == revelation_id)
        result = await self.db.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            return False
        row.surfaced = True
        row.acknowledged_at = datetime.utcnow()
        await self.db.commit()
        return True

    async def list_revelations(
        self,
        limit: int = 20,
        unsurfaced_only: bool = False,
        revelation_type: Optional[str] = None,
    ) -> List[RevelationMemory]:
        stmt = select(RevelationMemory).order_by(RevelationMemory.created_at.desc())
        if unsurfaced_only:
            stmt = stmt.where(RevelationMemory.surfaced == False)  # noqa: E712
        if revelation_type:
            stmt = stmt.where(RevelationMemory.revelation_type == revelation_type)
        stmt = stmt.limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_status(self) -> Dict[str, Any]:
        """Return revelation system status for operator-facing observability."""
        total_result = await self.db.execute(
            select(func.count()).select_from(RevelationMemory)
        )
        unsurfaced_result = await self.db.execute(
            select(func.count())
            .select_from(RevelationMemory)
            .where(RevelationMemory.surfaced.is_(False))
        )
        latest_result = await self.db.execute(
            select(RevelationMemory)
            .order_by(RevelationMemory.created_at.desc())
            .limit(1)
        )
        latest = latest_result.scalar_one_or_none()
        status = {
            "status": "active",
            "total_revelations": int(total_result.scalar() or 0),
            "unsurfaced_revelations": int(unsurfaced_result.scalar() or 0),
            "last_revelation_at": latest.created_at.isoformat() if latest else None,
            "latest_revelation_title": latest.title if latest else None,
            "latest_revelation_type": latest.revelation_type if latest else None,
            "cooldown_hours": REVELATION_COOLDOWN_HOURS,
            "minimum_observations": MIN_OBSERVATIONS,
            **get_token_stats(),
            **get_revelation_model_info(),
        }
        return status


def get_token_stats() -> Dict[str, Any]:
    return {
        "session_tokens_used": _session_tokens_used,
        "session_token_budget": _SESSION_TOKEN_BUDGET,
        "budget_remaining": _SESSION_TOKEN_BUDGET - _session_tokens_used,
        "budget_pct_used": round(_session_tokens_used / _SESSION_TOKEN_BUDGET * 100, 1),
    }
