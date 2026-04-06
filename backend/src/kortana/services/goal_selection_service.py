"""
KOR'TANA Goal Selection Service — Phase 6 Agency Core

Reads the latest self-model and active goals, scores them, selects the
single best next action, and persists a NextActionCandidate row.

Deterministic fallback: works without Gemini by using pure rule-based
scoring.  When Gemini is available, it refines rationale text only —
the ranking itself is always computable locally.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.kortana.models import AutonomyGoal, NextActionCandidate, SelfModelSnapshot

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Scoring weights (deterministic, no LLM required)
# ---------------------------------------------------------------------------
_TIER_WEIGHT: Dict[str, float] = {
    "mission": 1.0,
    "strategic": 0.8,
    "operational": 0.6,
    "tactical": 0.4,
    "maintenance": 0.2,
}

_STATUS_BOOST: Dict[str, float] = {
    "in_progress": 0.3,  # momentum — prefer continuing work
    "active": 0.1,
    "pending": 0.0,
}


def _compute_goal_score(
    goal: AutonomyGoal,
    self_model_stage: Optional[str],
    adaptation_adjustment: float = 0.0,
) -> float:
    """Pure deterministic score for a single goal.

    Formula: tier_weight * priority_norm + status_boost + stage_alignment + adaptation
    All inputs from existing AutonomyGoal columns — no new schema needed.
    adaptation_adjustment is fed from Phase 8 outcome learning signals.
    """
    tier_w = _TIER_WEIGHT.get(str(goal.tier or ""), 0.3)
    priority_norm = (goal.priority or 50) / 100.0
    status_b = _STATUS_BOOST.get(str(goal.status or ""), 0.0)

    # Stage alignment: early stages favour observation/self-improvement,
    # later stages favour operational/mission work.
    stage_align = 0.0
    if self_model_stage in ("nascent", "awakening"):
        if goal.tier in ("maintenance", "tactical"):
            stage_align = 0.15
    elif self_model_stage in ("consolidating", "autonomous", "transcendent"):
        if goal.tier in ("mission", "strategic"):
            stage_align = 0.15

    # Progress discount: nearly-done goals get a small boost to finish them
    progress_boost = 0.0
    progress = float(goal.progress or 0.0)
    if 0.7 <= progress < 1.0:
        progress_boost = 0.1

    return float(
        tier_w * priority_norm
        + status_b
        + stage_align
        + progress_boost
        + adaptation_adjustment
    )


def _build_idle_candidate(cycle_id: Optional[str]) -> NextActionCandidate:
    """When no active goals exist, propose an observation/idle action."""
    return NextActionCandidate(
        title="Observe and wait for new goals",
        action_type="idle",
        rationale="No active goals found. The best action is continued observation.",
        why_now="Nothing is pending or in-progress.",
        why_not_alternatives="There are no alternatives to consider.",
        score=0.0,
        goal_id=None,
        candidate_payload=None,
        status="proposed",
        cycle_id=cycle_id,
    )


def _rank_goals(
    goals: List[AutonomyGoal],
    self_model_stage: Optional[str],
    adaptation_adjustment: float = 0.0,
) -> List[Dict[str, Any]]:
    """Score and rank goals. Returns list sorted by score descending."""
    scored: List[Dict[str, Any]] = []
    for g in goals:
        s = _compute_goal_score(g, self_model_stage, adaptation_adjustment)
        scored.append({"goal": g, "score": round(s, 4)})
    scored.sort(key=lambda x: float(x["score"]), reverse=True)
    return scored


class GoalSelectionService:
    """Selects the next action from the self-model and active goals."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def select_next_action(
        self, cycle_id: Optional[str] = None
    ) -> NextActionCandidate:
        """Read state, rank goals, select the best, and persist.

        Always returns a NextActionCandidate (persisted).
        Works deterministically without Gemini.
        """
        # 1. Read latest self-model
        self_model = await self._get_latest_self_model()
        stage = str(self_model.developmental_stage) if self_model else None
        proposed_evolution = (
            str(self_model.proposed_next_evolution)
            if self_model and self_model.proposed_next_evolution
            else None
        )

        # 2. Read active goals
        goals = await self._get_active_goals()

        # 2.5. Read adaptation signals from outcome learning (Phase 8)
        adaptation_adj = 0.0
        try:
            from src.kortana.services.outcome_learning_service import (
                compute_score_adjustment,
                get_active_adaptation_signals,
            )

            signals = await get_active_adaptation_signals(self.db, scope="session")
            adaptation_adj = compute_score_adjustment(signals)
        except Exception:
            pass  # graceful degradation — no adaptation data yet

        # 3. If no goals, return idle candidate
        if not goals:
            candidate = _build_idle_candidate(cycle_id)
            self.db.add(candidate)
            try:
                await self.db.commit()
                await self.db.refresh(candidate)
            except Exception:
                await self.db.rollback()
                logger.exception("Failed to persist idle candidate")
            return candidate

        # 4. Rank goals
        ranked = _rank_goals(goals, stage, adaptation_adj)

        # 4.5. Phase 10: Covenant enforcement — pre-screen goals
        enforced_ranked: List[Dict[str, Any]] = []
        try:
            from src.kortana.services.constitutional_service import (
                ConstitutionalService,
            )

            covenant = ConstitutionalService(self.db)
            for entry in ranked:
                g: AutonomyGoal = entry["goal"]
                verdict, adj, _decision = await covenant.enforce_goal(
                    goal_title=str(g.title),
                    goal_id=str(g.id) if g.id else None,
                    goal_tier=str(g.tier or ""),
                    cycle_id=cycle_id,
                )
                if verdict == "reject":
                    logger.info(f"Goal rejected by covenant: {g.title}")
                    continue  # exclude from ranking
                entry["score"] = round(float(entry["score"]) + adj, 4)
                enforced_ranked.append(entry)
            # Re-sort after adjustments
            enforced_ranked.sort(key=lambda x: float(x["score"]), reverse=True)
        except Exception:
            logger.exception("Covenant goal enforcement failed, using unfiltered ranks")
            enforced_ranked = ranked

        # If all goals were rejected, return idle
        if not enforced_ranked:
            candidate = _build_idle_candidate(cycle_id)
            self.db.add(candidate)
            try:
                await self.db.commit()
                await self.db.refresh(candidate)
            except Exception:
                await self.db.rollback()
            return candidate

        top = enforced_ranked[0]
        top_goal: AutonomyGoal = top["goal"]
        top_score: float = top["score"]

        # 5. Build rationale
        alternatives_text = self._format_alternatives(enforced_ranked[1:5])
        why_now = self._compute_why_now(top_goal, stage, proposed_evolution)

        # 6. Determine action_type from goal tier
        action_type = self._infer_action_type(top_goal)

        candidate = NextActionCandidate(
            title=f"Work on: {top_goal.title}",
            action_type=action_type,
            rationale=(
                f"Goal '{top_goal.title}' (tier={top_goal.tier}, "
                f"priority={top_goal.priority}, progress={(top_goal.progress or 0):.0%}) "
                f"scored highest at {top_score:.4f}."
            ),
            why_now=why_now,
            why_not_alternatives=alternatives_text,
            score=top_score,
            goal_id=top_goal.id,
            candidate_payload={
                "goal_tier": top_goal.tier,
                "goal_status": top_goal.status,
                "goal_progress": top_goal.progress,
                "self_model_stage": stage,
                "ranked_count": len(ranked),
            },
            status="proposed",
            cycle_id=cycle_id,
        )

        self.db.add(candidate)
        try:
            await self.db.commit()
            await self.db.refresh(candidate)
            logger.info(
                f"Next action selected: '{top_goal.title}' "
                f"(score={top_score:.4f}, type={action_type})"
            )
        except Exception:
            await self.db.rollback()
            logger.exception("Failed to persist NextActionCandidate")

        return candidate

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------
    async def _get_latest_self_model(self) -> Optional[SelfModelSnapshot]:
        stmt = (
            select(SelfModelSnapshot)
            .order_by(SelfModelSnapshot.version.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_active_goals(self) -> List[AutonomyGoal]:
        stmt = (
            select(AutonomyGoal)
            .where(AutonomyGoal.status.in_(["active", "in_progress", "pending"]))
            .order_by(AutonomyGoal.priority.desc())
            .limit(20)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Read-only query for endpoints
    # ------------------------------------------------------------------
    async def get_current_next_action(self) -> Optional[NextActionCandidate]:
        """Return the most recent NextActionCandidate."""
        stmt = (
            select(NextActionCandidate)
            .order_by(NextActionCandidate.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_next_action_history(
        self, limit: int = 10
    ) -> List[NextActionCandidate]:
        """Return recent NextActionCandidates ordered newest-first."""
        stmt = (
            select(NextActionCandidate)
            .order_by(NextActionCandidate.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Internal logic helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _infer_action_type(goal: AutonomyGoal) -> str:
        tier = goal.tier or ""
        if tier in ("mission", "strategic"):
            return "goal_work"
        if tier == "maintenance":
            return "maintenance"
        if tier == "tactical":
            return "self_improvement"
        return "observation"

    @staticmethod
    def _compute_why_now(
        goal: AutonomyGoal,
        stage: Optional[str],
        proposed_evolution: Optional[str],
    ) -> str:
        parts = []
        if goal.status == "in_progress":
            parts.append(
                f"Already in progress ({(goal.progress or 0):.0%} complete) — "
                f"continuing reduces context-switch cost."
            )
        if stage:
            parts.append(f"Current developmental stage is '{stage}'.")
        if proposed_evolution:
            parts.append(f"Self-model proposes: {proposed_evolution[:200]}")
        if not parts:
            parts.append(
                f"Highest-scoring goal (tier={goal.tier}, priority={goal.priority})."
            )
        return " ".join(parts)

    @staticmethod
    def _format_alternatives(others: List[Dict[str, Any]]) -> str:
        if not others:
            return "No other active goals to consider."
        lines = []
        for entry in others:
            g: AutonomyGoal = entry["goal"]
            s: float = entry["score"]
            lines.append(f"- '{g.title}' scored {s:.4f} (tier={g.tier})")
        return "Other candidates considered but scored lower:\n" + "\n".join(lines)
