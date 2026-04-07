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
import json
import logging
import os
import subprocess
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.kortana.model_lane_policy import describe_model_lane
from src.kortana.models import ConversationMessage, RevelationMemory, SelfMemory
from src.kortana.provider_model_defaults import LLM_ROUTER_GEMINI_MODEL
from src.kortana.services.gemini_config import get_preferred_model_name

logger = logging.getLogger(__name__)


# Repo root derived from this file location (works on any OS, any clone path)
_REPO_ROOT = str(Path(__file__).resolve().parents[4])

# Whitelists for LLM-provided tags
_VALID_DOMAINS = frozenset(
    {"architecture", "workflow", "performance", "security", "developer_experience", "self_improvement"}
)
_VALID_URGENCIES = frozenset({"low", "medium", "high"})

REVELATION_MODEL = LLM_ROUTER_GEMINI_MODEL
CONFIDENCE_THRESHOLD = 0.65
MIN_OBSERVATIONS = 5  # don't synthesise without at least this many data points
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
    stmt = select(SelfMemory).order_by(SelfMemory.created_at.desc()).limit(limit)
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


def _gather_git_activity(repo_root: Optional[str] = None, limit: int = 20) -> List[str]:
    if repo_root is None:
        repo_root = _REPO_ROOT
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
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    stmt = (
        select(RevelationMemory.title)
        .where(RevelationMemory.created_at >= cutoff)
        .order_by(RevelationMemory.created_at.desc())
    )
    result = await db.execute(stmt)
    return [row[0] for row in result.all()]


def _is_duplicate(new_title: str, existing_titles: List[str]) -> bool:
    """Simple token-overlap dedup — avoid re-surfacing the same insight."""
    new_words = set(new_title.lower().split())
    for title in existing_titles:
        existing_words = set(title.lower().split())
        if not new_words or not existing_words:
            continue
        overlap = len(new_words & existing_words) / max(
            len(new_words), len(existing_words)
        )
        if overlap >= DEDUP_SIMILARITY_THRESHOLD:
            return True
    return False


def _parse_llm_json(raw: str) -> Optional[list]:
    """Strip optional markdown code fences then parse a JSON array from an LLM response."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(ln for ln in lines if not ln.startswith("```")).strip()
    try:
        items = json.loads(text)
    except json.JSONDecodeError as exc:
        logger.error(f"LLM JSON parse failed: {exc}\nRaw: {text[:300]}")
        return None
    if not isinstance(items, list):
        return None
    return items



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

---

Your task: Identify at most 2 revelations — genuine insights that:
  - Require time accumulation to notice (not obvious from a single data point)
  - Cross-cut multiple observation categories above
  - Would be genuinely useful or meaningful for Matt to hear
  - Are specific, not generic platitudes

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
        cutoff = datetime.now(timezone.utc) - timedelta(hours=REVELATION_COOLDOWN_HOURS)
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

        # Gather observations
        self_memories = await _gather_self_memories(self.db, limit=40)
        conversation_topics = await _gather_conversation_topics(self.db, limit=20)
        git_activity = await asyncio.to_thread(_gather_git_activity)

        total_observations = (
            len(self_memories) + len(conversation_topics) + len(git_activity)
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
        )

        raw = await _call_gemini_revelation(prompt)
        if not raw:
            return []

        return await self._parse_and_store(raw.strip())

    async def _parse_and_store(self, raw_json: str) -> List[RevelationMemory]:
        """Parse LLM JSON response and write qualifying revelations to DB."""
        items = _parse_llm_json(raw_json)
        if items is None:
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

    # ------------------------------------------------------------------
    # Phase 4: Wisdom Distillation
    # ------------------------------------------------------------------
    async def distill_wisdom(self) -> List[Dict[str, Any]]:
        """Synthesize long-term architectural wisdom from accumulated revelations.

        Gathers all revelations from the last 30 days, asks the LLM to find
        convergent truths, and stores them as SelfMemory entries tagged
        with ["wisdom", "phase4"].
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        stmt = (
            select(RevelationMemory)
            .where(RevelationMemory.created_at >= cutoff)
            .order_by(RevelationMemory.created_at.desc())
            .limit(200)
        )
        result = await self.db.execute(stmt)
        revelations = result.scalars().all()

        if len(revelations) < 3:
            logger.info(
                f"Wisdom distillation: only {len(revelations)} revelations — need >= 3"
            )
            return []

        rev_text = "\n".join(
            f"- [{r.created_at.strftime('%Y-%m-%d')} type={r.revelation_type} "
            f"conf={r.confidence:.2f}] {r.title}: {r.content[:300]}"
            for r in revelations
        )
        git_activity = await asyncio.to_thread(_gather_git_activity)

        prompt = _WISDOM_DISTILLATION_PROMPT.format(
            revelations=rev_text or "(none)",
            git_activity="\n".join(git_activity) or "(none)",
        )

        raw = await _call_gemini_revelation(prompt)
        if not raw:
            return []

        items = _parse_llm_json(raw)
        if items is None:
            return []

        stored: List[Dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            confidence = float(item.get("confidence", 0.0))
            if confidence < CONFIDENCE_THRESHOLD:
                continue
            wisdom_text = str(item.get("wisdom", ""))
            if not wisdom_text:
                continue

            raw_domain = item.get("domain", "architecture")
            domain = raw_domain if raw_domain in _VALID_DOMAINS else "architecture"

            entry = SelfMemory(
                cycle_number=0,
                summary=f"[WISDOM] {wisdom_text}",
                tags=["wisdom", "phase4", domain],
                source="revelation-engine-wisdom",
            )
            self.db.add(entry)
            stored.append(
                {
                    "wisdom": wisdom_text,
                    "domain": domain,
                    "derived_from": item.get("derived_from", []),
                    "confidence": confidence,
                }
            )

        if stored:
            try:
                await self.db.commit()
                logger.info(f"Wisdom distillation: stored {len(stored)} wisdom entries")
            except Exception:
                await self.db.rollback()
                logger.exception("Wisdom distillation: commit failed")
                return []

        return stored

    async def predict_evolution(self) -> List[Dict[str, Any]]:
        """Generate forward-looking architectural predictions.

        Uses accumulated wisdom and recent revelations to anticipate
        drift, friction, and upcoming refactoring needs.
        """
        # Gather wisdom entries
        stmt = (
            select(SelfMemory)
            .where(SelfMemory.source == "revelation-engine-wisdom")
            .order_by(SelfMemory.created_at.desc())
            .limit(20)
        )
        wisdom_result = await self.db.execute(stmt)
        wisdom_rows = wisdom_result.scalars().all()

        # Gather recent revelations
        cutoff = datetime.now(timezone.utc) - timedelta(days=14)
        rev_stmt = (
            select(RevelationMemory)
            .where(RevelationMemory.created_at >= cutoff)
            .order_by(RevelationMemory.created_at.desc())
            .limit(10)
        )
        rev_result = await self.db.execute(rev_stmt)
        recent_revs = rev_result.scalars().all()

        if not wisdom_rows and not recent_revs:
            logger.info("Prediction: no wisdom or revelations to predict from")
            return []

        wisdom_text = "\n".join(f"- {r.summary}" for r in wisdom_rows) or "(none yet)"
        rev_text = (
            "\n".join(
                f"- [{r.created_at.strftime('%Y-%m-%d')}] {r.title}: {r.content[:200]}"
                for r in recent_revs
            )
            or "(none yet)"
        )
        git_activity = await asyncio.to_thread(_gather_git_activity)

        prompt = _PREDICTION_PROMPT.format(
            wisdom_entries=wisdom_text,
            recent_revelations=rev_text,
            git_activity="\n".join(git_activity) or "(none)",
        )

        raw = await _call_gemini_revelation(prompt)
        if not raw:
            return []

        items = _parse_llm_json(raw)
        if items is None:
            return []

        predictions: List[Dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            confidence = float(item.get("confidence", 0.0))
            if confidence < CONFIDENCE_THRESHOLD:
                continue
            prediction_text = str(item.get("prediction", ""))
            if not prediction_text:
                continue

            raw_urgency = item.get("urgency", "low")
            urgency = raw_urgency if raw_urgency in _VALID_URGENCIES else "low"

            # Store prediction as SelfMemory for continuity
            entry = SelfMemory(
                cycle_number=0,
                summary=f"[PREDICTION] {prediction_text} | Basis: {item.get('basis', '')}",
                tags=["prediction", "phase4", urgency],
                source="revelation-engine-prediction",
            )
            self.db.add(entry)
            predictions.append(
                {
                    "prediction": prediction_text,
                    "basis": item.get("basis", ""),
                    "urgency": urgency,
                    "confidence": confidence,
                }
            )

        if predictions:
            try:
                await self.db.commit()
                logger.info(f"Prediction: stored {len(predictions)} predictions")
            except Exception:
                await self.db.rollback()
                logger.exception("Prediction: commit failed")
                return []

        return predictions

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
        row.acknowledged_at = datetime.now(timezone.utc)
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


# ---------------------------------------------------------------------------
# Phase 4 prompts — Wisdom Distillation & Self-Prediction
# ---------------------------------------------------------------------------

_WISDOM_DISTILLATION_PROMPT = """You are kor'tana's Wisdom Distillation Engine — a higher-order subsystem that synthesizes long-term architectural truths from accumulated revelations.

You have access to every revelation generated over the last 30 days:

## Revelations
{revelations}

## Recent Git Activity
{git_activity}

---

Your task: Distill at most 3 **wisdom statements** — enduring architectural truths that:
  - Emerge from the convergence of multiple revelations over time
  - Represent deep, non-obvious patterns about the codebase, the developer, or the system
  - Are actionable — they can guide future autonomous decisions
  - Transcend any single data point or revelation

Respond with EXACTLY this JSON structure (no markdown, no preamble):
[
  {{
    "wisdom": "<1-2 sentence distilled truth>",
    "derived_from": ["<revelation title 1>", "<revelation title 2>", ...],
    "domain": "<architecture|workflow|performance|security|developer_experience|self_improvement>",
    "confidence": <float 0.0-1.0>
  }}
]

If there is insufficient convergence for genuine wisdom (too few revelations, or no cross-cutting pattern), respond with exactly: []

Bias strongly toward []. Wisdom is rare. One true insight is worth more than many plausible ones."""


_PREDICTION_PROMPT = """You are kor'tana's Self-Prediction Engine — a forward-looking subsystem that anticipates architectural evolution.

Based on the following accumulated wisdom and recent trajectory:

## Distilled Wisdom
{wisdom_entries}

## Recent Revelations
{recent_revelations}

## Git Trajectory
{git_activity}

---

Your task: Generate at most 2 **predictions** about the system's near-future evolution:
  - What architectural drift is likely if no intervention occurs?
  - What optimization or refactor will become necessary within the next 2-4 weeks?
  - What friction point is growing that hasn't been addressed yet?

Respond with EXACTLY this JSON structure (no markdown, no preamble):
[
  {{
    "prediction": "<1-2 sentence forward-looking statement>",
    "basis": "<brief explanation of why this prediction is likely>",
    "urgency": "<low|medium|high>",
    "confidence": <float 0.0-1.0>
  }}
]

If there is insufficient data for confident prediction, respond with exactly: []"""
