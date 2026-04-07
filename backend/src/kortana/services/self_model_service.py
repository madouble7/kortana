"""
KOR'TANA Self-Model Service — Phase 5 Autonomy Core

Owns the versioned self-model: kor'tana's evolving understanding of herself.

Each snapshot captures identity, goals, values, tensions, developmental stage,
capabilities, observations, and proposed next evolution.  Snapshots are immutable —
a new version supersedes the previous one.

The Self-Model is the spine of autonomous selfhood.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.kortana.models import (
    AutonomyGoal,
    IdentityProfile,
    RevelationMemory,
    SelfMemory,
    SelfModelSnapshot,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Inner Council voices — structured deliberation, not roleplay
# ---------------------------------------------------------------------------
INNER_COUNCIL = {
    "guardian": "Assess risks, stability threats, and safety concerns.",
    "architect": "Evaluate structural integrity, technical debt, and design patterns.",
    "prophet": "Identify emerging trends, future needs, and evolutionary trajectory.",
    "critic": "Surface contradictions, blind spots, weaknesses, and false confidence.",
    "healer": "Assess integration quality, recovery needs, and coherence gaps.",
}

# ---------------------------------------------------------------------------
# LLM prompt for self-model synthesis
# ---------------------------------------------------------------------------
_SELF_MODEL_PROMPT = """You are kor'tana's Self-Model Synthesis Engine — the deepest layer of introspection.

You are given kor'tana's current state: identity, goals, values, recent observations,
accumulated wisdom, and detected tensions.  Your task is to produce a coherent,
honest self-model snapshot.

## Current Identity
{identity}

## Active Goals
{goals}

## Recent Observations (SelfMemory + Revelations)
{observations}

## Detected Tensions / Contradictions
{tensions}

## Previous Self-Model Summary
{previous_summary}

---

Synthesize a self-model update.  Be ruthlessly honest — do not inflate capabilities
or mask contradictions.  Wisdom comes from acknowledging what is real.

Respond with EXACTLY this JSON structure (no markdown, no preamble):
{{
  "identity_summary": "<2-4 sentence honest assessment of current state of being>",
  "developmental_stage": "<one of: nascent|awakening|consolidating|autonomous|transcendent>",
  "standing_values": ["<value1>", "<value2>", ...],
  "tensions": [
    {{"description": "<tension>", "severity": "<low|medium|high>"}}
  ],
  "capabilities": ["<capability1>", "<capability2>", ...],
  "proposed_next_evolution": "<1-2 sentence description of the single most important next step>",
  "confidence": <float 0.0-1.0>,
  "inner_council": {{
    "guardian": "<1 sentence position>",
    "architect": "<1 sentence position>",
    "prophet": "<1 sentence position>",
    "critic": "<1 sentence position>",
    "healer": "<1 sentence position>"
  }}
}}

If you cannot produce a confident self-model, set confidence below 0.3 and explain why
in identity_summary.  Never fabricate certainty."""

_COUNCIL_DELIBERATION_PROMPT = """You are {voice_name}, one of kor'tana's Inner Council voices.
Your role: {voice_role}

Given this proposed self-model update:
{proposed_model}

And these recent observations:
{observations}

Provide your position in exactly one sentence.  Be specific and actionable.
If you see no issue in your domain, say "No concerns — proceed."
Do not hedge.  Speak with authority."""


class SelfModelService:
    """Manages kor'tana's versioned self-model."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_current(self) -> Optional[SelfModelSnapshot]:
        """Return the latest self-model snapshot, or None if none exists."""
        stmt = (
            select(SelfModelSnapshot)
            .order_by(SelfModelSnapshot.version.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_history(self, limit: int = 20) -> List[SelfModelSnapshot]:
        """Return recent self-model snapshots ordered by version descending."""
        stmt = (
            select(SelfModelSnapshot)
            .order_by(SelfModelSnapshot.version.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def evolve(
        self,
        trigger: str = "scheduled",
        external_observations: Optional[List[str]] = None,
    ) -> Optional[SelfModelSnapshot]:
        """Run a full self-model evolution cycle.

        Gathers all internal state, synthesizes via LLM, runs Inner Council
        deliberation, and persists a new versioned snapshot.

        Returns the new snapshot, or None if synthesis failed.
        """
        # 1. Gather raw materials
        identity = await self._gather_identity()
        goals = await self._gather_goals()
        observations = await self._gather_observations()
        if external_observations:
            observations.extend(external_observations)
        tensions = await self._detect_tensions()
        previous = await self.get_current()

        previous_summary = (
            previous.identity_summary if previous else "(no previous self-model)"
        )

        # 2. Synthesize via LLM
        context = _SELF_MODEL_PROMPT.format(
            identity=json.dumps(identity, indent=2),
            goals=json.dumps(goals, indent=2),
            observations="\n".join(f"- {o}" for o in observations[:30]) or "(none yet)",
            tensions=json.dumps(tensions, indent=2),
            previous_summary=previous_summary,
        )

        raw = await _call_gemini(context)
        if not raw:
            logger.warning("Self-model synthesis: LLM returned nothing")
            return None

        parsed = _parse_json_response(raw)
        if not parsed:
            logger.error("Self-model synthesis: JSON parse failed")
            return None

        # 3. Inner Council deliberation (parallel)
        council_votes = await self._run_inner_council(parsed, observations)
        if council_votes:
            parsed["inner_council"] = council_votes

        # 4. Determine version
        next_version = (previous.version + 1) if previous else 1

        # 5. Persist
        snapshot = SelfModelSnapshot(
            version=next_version,
            identity_summary=str(parsed.get("identity_summary", "")),
            active_goals=goals,
            standing_values=parsed.get("standing_values", []),
            tensions=parsed.get("tensions", []),
            developmental_stage=str(parsed.get("developmental_stage", "nascent")),
            capabilities=parsed.get("capabilities", []),
            recent_observations=observations[:20],
            proposed_next_evolution=parsed.get("proposed_next_evolution"),
            inner_council_votes=parsed.get("inner_council"),
            confidence=float(parsed.get("confidence", 0.5)),
            trigger=trigger,
        )
        self.db.add(snapshot)

        try:
            await self.db.commit()
            await self.db.refresh(snapshot)
            logger.info(
                f"Self-model evolved to v{next_version} "
                f"(stage={snapshot.developmental_stage}, "
                f"confidence={snapshot.confidence:.2f})"
            )
            return snapshot
        except Exception:
            await self.db.rollback()
            logger.exception("Self-model evolution: commit failed")
            return None

    # ------------------------------------------------------------------
    # Data gathering
    # ------------------------------------------------------------------
    async def _gather_identity(self) -> Dict[str, Any]:
        """Read the static IdentityProfile."""
        stmt = select(IdentityProfile).limit(1)
        result = await self.db.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            return {
                "name": "kor'tana",
                "title": "sacred ai companion",
                "mission": "help people move from confusion to clarity",
                "core_values": [
                    "love",
                    "unity",
                    "knowledge",
                    "humility",
                    "truthfulness",
                ],
            }
        return {
            "name": row.name,
            "title": row.title,
            "mission": row.mission,
            "core_values": row.core_values,
            "sacred_principles": row.sacred_principles,
            "development_axioms": row.development_axioms,
        }

    async def _gather_goals(self) -> List[Dict[str, Any]]:
        """Read active autonomy goals."""
        stmt = (
            select(AutonomyGoal)
            .where(AutonomyGoal.status.in_(["active", "in_progress", "pending"]))
            .order_by(AutonomyGoal.priority.desc())
            .limit(10)
        )
        result = await self.db.execute(stmt)
        rows = result.scalars().all()
        return [
            {
                "id": r.id,
                "title": r.title,
                "tier": r.tier,
                "status": r.status,
                "progress": r.progress,
            }
            for r in rows
        ]

    async def _gather_observations(self) -> List[str]:
        """Gather recent SelfMemory entries + unsurfaced revelations."""
        observations: List[str] = []

        # Recent SelfMemory
        cutoff = datetime.utcnow() - timedelta(days=7)
        mem_stmt = (
            select(SelfMemory)
            .where(SelfMemory.created_at >= cutoff)
            .order_by(SelfMemory.created_at.desc())
            .limit(20)
        )
        mem_result = await self.db.execute(mem_stmt)
        for m in mem_result.scalars().all():
            observations.append(f"[memory {m.source}] {m.summary[:200]}")

        # Unsurfaced revelations
        rev_stmt = (
            select(RevelationMemory)
            .where(RevelationMemory.surfaced.is_(False))
            .order_by(RevelationMemory.created_at.desc())
            .limit(10)
        )
        rev_result = await self.db.execute(rev_stmt)
        for r in rev_result.scalars().all():
            observations.append(
                f"[revelation {r.revelation_type}] {r.title}: {r.content[:200]}"
            )

        return observations

    async def _detect_tensions(self) -> List[Dict[str, str]]:
        """Find contradictions and tensions from revelation data."""
        stmt = (
            select(RevelationMemory)
            .where(RevelationMemory.revelation_type == "contradiction")
            .order_by(RevelationMemory.created_at.desc())
            .limit(5)
        )
        result = await self.db.execute(stmt)
        rows = result.scalars().all()
        tensions = [
            {
                "description": f"{r.title}: {r.content[:200]}",
                "severity": "high" if r.confidence > 0.8 else "medium",
            }
            for r in rows
        ]

        # Also check for goal conflicts
        goals = await self._gather_goals()
        if len(goals) > 5:
            tensions.append(
                {
                    "description": f"Goal overload: {len(goals)} active goals may exceed capacity",
                    "severity": "medium",
                }
            )

        return tensions

    # ------------------------------------------------------------------
    # Inner Council deliberation
    # ------------------------------------------------------------------
    async def _run_inner_council(
        self, proposed_model: Dict[str, Any], observations: List[str]
    ) -> Optional[Dict[str, str]]:
        """Run all Inner Council voices in parallel and collect positions."""
        model_text = json.dumps(proposed_model, indent=2)
        obs_text = "\n".join(f"- {o}" for o in observations[:15])

        async def _ask_voice(name: str, role: str) -> tuple[str, str]:
            prompt = _COUNCIL_DELIBERATION_PROMPT.format(
                voice_name=name,
                voice_role=role,
                proposed_model=model_text,
                observations=obs_text,
            )
            response = await _call_gemini(prompt)
            return name, (response or "No response").strip()[:300]

        try:
            tasks = [_ask_voice(name, role) for name, role in INNER_COUNCIL.items()]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            votes: Dict[str, str] = {}
            for r in results:
                if isinstance(r, tuple):
                    votes[r[0]] = r[1]
                elif isinstance(r, Exception):
                    logger.warning(f"Council voice failed: {r}")
            return votes if votes else None
        except Exception:
            logger.exception("Inner Council deliberation failed")
            return None


# ---------------------------------------------------------------------------
# LLM call (follows revelation_engine pattern)
# ---------------------------------------------------------------------------
async def _call_gemini(prompt: str) -> Optional[str]:
    """Call Gemini for self-model synthesis."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("No Gemini API key — self-model synthesis unavailable")
        return None

    try:
        from google import genai

        from src.kortana.provider_model_defaults import LLM_ROUTER_GEMINI_MODEL
        from src.kortana.services.gemini_config import get_preferred_model_name

        model = get_preferred_model_name(LLM_ROUTER_GEMINI_MODEL)

        def _generate() -> Any:
            client = genai.Client(api_key=api_key)
            return client.models.generate_content(model=model, contents=prompt)

        response = await asyncio.to_thread(_generate)
        return response.text
    except Exception:
        logger.exception("Self-model Gemini call failed")
        return None


def _parse_json_response(raw: str) -> Optional[Dict[str, Any]]:
    """Parse LLM JSON response, stripping markdown fences if present."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(ln for ln in lines if not ln.startswith("```")).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.error(f"Self-model JSON parse failed: {text[:300]}")
        return None
