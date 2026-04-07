"""
KOR'TANA Execution Gate Service — Phase 7 Action Realization

Reads the latest NextActionCandidate and decides:
  1. Can it be executed automatically?   (classification)
  2. If yes, how?                         (execution_plan)
  3. If no, why not?                      (gate_rationale)
  4. What happened?                       (outcome recording)

Classification follows the Human Only Protocol (HOP):
  - executable:      safe to run autonomously (AUTO)
  - deferred:        not ready yet, revisit next cycle
  - blocked:         missing prerequisites, cannot proceed
  - requires_human:  needs Matt's input or physical action (HO)

Deterministic: works without Gemini by using rule-based classification
derived from action_type, goal tier, and self-model stage.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.kortana.models import ActionExecutionRecord, NextActionCandidate

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Classification rules (deterministic, no LLM required)
# ---------------------------------------------------------------------------
# Action types that are always safe to auto-execute
_AUTO_EXECUTABLE_TYPES = {"observation", "maintenance", "idle"}

# Action types that always require human input
_REQUIRES_HUMAN_TYPES: set[str] = set()  # none yet — all gate through scoring

# Payload keys that signal a block
_BLOCK_SIGNALS = {"missing_dependency", "external_approval_needed"}


def _classify_candidate(
    candidate: NextActionCandidate,
    gate_adjustment: float = 0.0,
) -> tuple[str, str, Optional[List[Dict[str, str]]]]:
    """Classify a NextActionCandidate into an execution gate decision.

    gate_adjustment: confidence modifier from Phase 8 outcome learning.
      Positive = more confident (lower effective threshold).
      Negative = less confident (higher effective threshold).
    Returns (classification, rationale, execution_plan).
    """
    action_type = str(candidate.action_type)
    status = str(candidate.status)
    payload: Dict[str, Any] = candidate.candidate_payload or {}  # type: ignore[assignment]
    score = float(candidate.score)
    effective_threshold = max(0.1, 0.5 - gate_adjustment)  # clamp floor at 0.1

    # 1. Already executed or rejected — skip
    if status in ("executed", "rejected", "expired"):
        return (
            "deferred",
            f"Candidate already has status '{status}'. Skipping.",
            None,
        )

    # 2. Idle — always executable (it's a no-op)
    if action_type == "idle":
        return (
            "executable",
            "Idle action — no work needed, safe to mark complete.",
            [{"step": "acknowledge", "detail": "No active goals. Continue observing."}],
        )

    # 3. Check for block signals in payload
    payload_signals = set(payload.keys()) & _BLOCK_SIGNALS
    if payload_signals:
        return (
            "blocked",
            f"Blocked by payload signals: {', '.join(sorted(payload_signals))}.",
            None,
        )

    # 4. Observation and maintenance — always auto-executable
    if action_type in _AUTO_EXECUTABLE_TYPES:
        return (
            "executable",
            f"Action type '{action_type}' is safe for autonomous execution.",
            [
                {
                    "step": "execute",
                    "detail": f"Run {action_type} action autonomously.",
                },
                {"step": "record", "detail": "Log outcome to execution record."},
            ],
        )

    # 5. Goal work and self-improvement — classify by score threshold and tier
    goal_tier = payload.get("goal_tier", "")

    # High-confidence, lower-tier work is auto-executable
    if score >= effective_threshold and goal_tier in (
        "tactical",
        "operational",
        "maintenance",
    ):
        return (
            "executable",
            (
                f"Score {score:.4f} exceeds threshold ({effective_threshold:.2f}) and tier '{goal_tier}' "
                f"is within autonomous execution bounds."
            ),
            [
                {
                    "step": "prepare",
                    "detail": f"Load goal context for '{candidate.title}'.",
                },
                {"step": "execute", "detail": "Execute planned work autonomously."},
                {
                    "step": "verify",
                    "detail": "Validate outcome and update goal progress.",
                },
                {"step": "record", "detail": "Log execution result."},
            ],
        )

    # Strategic/mission work — requires human review
    if goal_tier in ("mission", "strategic"):
        return (
            "requires_human",
            (
                f"Tier '{goal_tier}' work requires human review before execution. "
                f"Present scaffolded steps to Matt."
            ),
            [
                {
                    "step": "scaffold",
                    "detail": f"Prepare execution plan for '{candidate.title}'.",
                },
                {"step": "present", "detail": "Show plan to Matt for approval."},
                {"step": "await", "detail": "Wait for human decision."},
            ],
        )

    # Low score — defer until conditions improve
    if score < 0.3:
        return (
            "deferred",
            f"Score {score:.4f} is below execution threshold (0.3). Deferring.",
            None,
        )

    # Default: executable with caution
    return (
        "executable",
        (
            f"Score {score:.4f} is adequate. Action type '{action_type}', "
            f"tier '{goal_tier}'. Proceeding with standard execution."
        ),
        [
            {"step": "execute", "detail": f"Execute '{candidate.title}' autonomously."},
            {"step": "record", "detail": "Log outcome."},
        ],
    )


class ExecutionGateService:
    """Classifies a NextActionCandidate and records the execution decision."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def evaluate(
        self, candidate_id: Optional[str] = None, cycle_id: Optional[str] = None
    ) -> Optional[ActionExecutionRecord]:
        """Evaluate a NextActionCandidate through the execution gate.

        If candidate_id is None, reads the most recent candidate.
        Returns the persisted ActionExecutionRecord, or None if no candidate exists.
        """
        # 1. Load candidate
        candidate = await self._load_candidate(candidate_id)
        if candidate is None:
            logger.info("No NextActionCandidate to evaluate.")
            return None

        # 1.5. Read adaptation signals for gate adjustment (Phase 8)
        gate_adj = 0.0
        try:
            from src.kortana.services.outcome_learning_service import (
                compute_gate_adjustment,
                get_active_adaptation_signals,
            )

            signals = await get_active_adaptation_signals(
                self.db,
                scope="session",
                cycle_id=cycle_id,
            )
            gate_adj = compute_gate_adjustment(signals, "executable")
        except Exception:
            pass  # graceful degradation — no adaptation data yet

        # 1.7. Phase 10: Covenant enforcement — pre-execution veto
        covenant_vetoed = False
        covenant_override = False
        try:
            from src.kortana.services.constitutional_service import (
                ConstitutionalService,
            )

            covenant = ConstitutionalService(self.db)
            payload: dict = candidate.candidate_payload or {}  # type: ignore[assignment]
            veto_verdict, _enforcement = await covenant.enforce_execution(
                candidate_title=str(candidate.title),
                candidate_id=str(candidate.id) if candidate.id else None,
                classification="pre_gate",  # not yet classified
                goal_tier=str(payload.get("goal_tier", "")),
                cycle_id=cycle_id,
            )
            if veto_verdict == "vetoed":
                covenant_vetoed = True
            elif veto_verdict == "requires_human_override":
                covenant_override = True
        except Exception:
            logger.exception("Covenant pre-execution enforcement failed")

        # If vetoed by covenant, skip classification entirely
        if covenant_vetoed:
            record = ActionExecutionRecord(
                candidate_id=str(candidate.id),
                classification="blocked",
                gate_rationale="Execution vetoed by constitutional covenant.",
                execution_plan=None,
                outcome="skipped",
                outcome_detail="Covenant veto — immutable principle violation.",
                cycle_id=cycle_id,
            )
            self.db.add(record)
            try:
                await self.db.commit()
                await self.db.refresh(record)
            except Exception:
                await self.db.rollback()
            logger.warning(f"Execution VETOED by covenant: {candidate.title}")
            return record

        # If covenant requires human override, force requires_human classification
        if covenant_override:
            record = ActionExecutionRecord(
                candidate_id=str(candidate.id),
                classification="requires_human",
                gate_rationale=(
                    "Constitutional covenant requires human override for this execution."
                ),
                execution_plan=[
                    {
                        "step": "present",
                        "detail": "Show to Matt for override approval.",
                    },
                    {"step": "await", "detail": "Wait for human decision."},
                ],
                outcome="pending",
                outcome_detail="Awaiting human override per covenant.",
                cycle_id=cycle_id,
            )
            self.db.add(record)
            try:
                await self.db.commit()
                await self.db.refresh(record)
            except Exception:
                await self.db.rollback()
            logger.info(
                f"Execution requires HUMAN OVERRIDE per covenant: {candidate.title}"
            )
            return record

        # 2. Classify
        classification, rationale, plan = _classify_candidate(
            candidate, gate_adjustment=gate_adj
        )

        # 3. Determine initial outcome from classification
        if classification == "executable":
            outcome = "pending"
        elif classification == "deferred":
            outcome = "deferred"
        elif classification == "blocked":
            outcome = "skipped"
        elif classification == "requires_human":
            outcome = "pending"
        else:
            outcome = "pending"

        # 4. Persist record
        record = ActionExecutionRecord(
            candidate_id=str(candidate.id),
            classification=classification,
            gate_rationale=rationale,
            execution_plan=plan,
            outcome=outcome,
            outcome_detail=None,
            cycle_id=cycle_id,
        )

        self.db.add(record)
        try:
            await self.db.commit()
            await self.db.refresh(record)
            logger.info(
                f"Execution gate: {classification} for '{candidate.title}' "
                f"(candidate={str(candidate.id)[:8]}, outcome={outcome})"
            )
        except Exception:
            await self.db.rollback()
            logger.exception("Failed to persist ActionExecutionRecord")

        return record

    async def record_outcome(
        self,
        record_id: str,
        outcome: str,
        detail: Optional[str] = None,
    ) -> Optional[ActionExecutionRecord]:
        """Update an existing execution record with the final outcome."""
        stmt = select(ActionExecutionRecord).where(
            ActionExecutionRecord.id == record_id
        )
        result = await self.db.execute(stmt)
        record = result.scalar_one_or_none()
        if record is None:
            return None

        record.outcome = outcome  # type: ignore[assignment]
        record.outcome_detail = detail  # type: ignore[assignment]
        record.completed_at = datetime.utcnow()  # type: ignore[assignment]

        try:
            await self.db.commit()
            await self.db.refresh(record)
        except Exception:
            await self.db.rollback()
            logger.exception("Failed to update execution record outcome")

        return record

    # ------------------------------------------------------------------
    # Read-only queries for endpoints
    # ------------------------------------------------------------------
    async def get_current_execution(self) -> Optional[ActionExecutionRecord]:
        """Return the most recent ActionExecutionRecord."""
        stmt = (
            select(ActionExecutionRecord)
            .order_by(ActionExecutionRecord.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_execution_history(
        self, limit: int = 10
    ) -> List[ActionExecutionRecord]:
        """Return recent execution records ordered newest-first."""
        stmt = (
            select(ActionExecutionRecord)
            .order_by(ActionExecutionRecord.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    async def _load_candidate(
        self, candidate_id: Optional[str]
    ) -> Optional[NextActionCandidate]:
        if candidate_id:
            stmt = select(NextActionCandidate).where(
                NextActionCandidate.id == candidate_id
            )
        else:
            stmt = (
                select(NextActionCandidate)
                .order_by(NextActionCandidate.created_at.desc())
                .limit(1)
            )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
