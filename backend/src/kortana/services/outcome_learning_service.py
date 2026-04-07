"""
KOR'TANA Outcome Learning Service — Phase 8 Recursive Adaptation

After each execution gate decision, this service:
  1. Interprets the outcome verdict  (succeeded / partial / failed / inconclusive / skipped)
  2. Checks whether the result matched expectations
  3. Derives a concrete lesson
  4. Produces a lightweight **adaptation signal** that downstream services
     (goal selection, execution gate) can consume to adjust behaviour

Deterministic: no Gemini dependency.  Rules are driven by the relationship
between the execution gate classification, the outcome, and the action type.

Adaptation signals are namespaced strings like:
  - boost_tier:tactical         → increase weight for tactical goals
  - penalise_type:goal_work     → decrease confidence in goal_work actions
  - trust_classification:executable → reinforce executable gate decisions
  - lower_threshold:score       → suggest lowering the score threshold

Signal weight is -1.0 to +1.0.
Signal scope determines how long the signal applies:
  - cycle:      this cycle only (default, conservative)
  - session:    current orchestrator session
  - persistent: stored for future sessions (high-confidence lessons only)
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.kortana.models import (
    ActionExecutionRecord,
    CovenantEnforcementRecord,
    OutcomeLearningRecord,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Outcome interpretation rules (deterministic)
# ---------------------------------------------------------------------------


def _interpret_outcome(
    exec_record: ActionExecutionRecord,
) -> tuple[str, str, str, str, float, str]:
    """Derive learning from an execution record.

    Returns (verdict, expectation_match, lesson, signal, weight, scope).
    """
    classification = str(exec_record.classification)
    outcome = str(exec_record.outcome)
    detail = str(exec_record.outcome_detail or "")

    # --- Map execution outcome to verdict ---
    verdict_map = {
        "succeeded": "succeeded",
        "failed": "failed",
        "deferred": "skipped",
        "skipped": "skipped",
        "pending": "inconclusive",
    }
    verdict = verdict_map.get(outcome, "inconclusive")

    # --- Was this expected given the classification? ---
    expectation, lesson, signal, weight, scope = _derive_lesson(
        classification, verdict, outcome, detail
    )

    return verdict, expectation, lesson, signal, weight, scope


def _derive_lesson(
    classification: str,
    verdict: str,
    outcome: str,
    detail: str,
) -> tuple[str, str, str, float, str]:
    """Compute expectation match, lesson, adaptation signal, weight, and scope."""

    # Executable + succeeded → expected, reinforce
    if classification == "executable" and verdict == "succeeded":
        return (
            "expected",
            "Executable action succeeded as predicted. Gate classification was correct.",
            "trust_classification:executable",
            0.1,
            "session",
        )

    # Executable + failed → surprising, penalise this pattern
    if classification == "executable" and verdict == "failed":
        return (
            "surprising",
            f"Executable action failed unexpectedly. {detail}".strip(),
            "penalise_classification:executable",
            -0.2,
            "session",
        )

    # Executable + partial (inconclusive or other) → mildly surprising
    if classification == "executable" and verdict in ("inconclusive", "partial"):
        return (
            "surprising",
            "Executable action had an inconclusive or partial outcome.",
            "review_classification:executable",
            -0.05,
            "cycle",
        )

    # Deferred + skipped → expected, no real lesson
    if classification == "deferred" and verdict == "skipped":
        return (
            "expected",
            "Deferred action was skipped as expected.",
            "neutral:deferred",
            0.0,
            "cycle",
        )

    # Blocked + skipped → expected
    if classification == "blocked" and verdict == "skipped":
        return (
            "expected",
            "Blocked action was correctly held. No progression possible.",
            "neutral:blocked",
            0.0,
            "cycle",
        )

    # Requires human + any verdict → depends on outcome
    if classification == "requires_human":
        if verdict == "succeeded":
            return (
                "expected",
                "Human-required action was completed. Gate was correct to defer.",
                "trust_classification:requires_human",
                0.1,
                "session",
            )
        return (
            "expected",
            "Human-required action awaiting human input.",
            "neutral:requires_human",
            0.0,
            "cycle",
        )

    # Executable + skipped → contradictory (classified as runnable but skipped)
    if classification == "executable" and verdict == "skipped":
        return (
            "contradictory",
            "Action was classified executable but ended up skipped. "
            "Classification may have been too optimistic.",
            "penalise_classification:executable",
            -0.15,
            "session",
        )

    # Default fallback
    return (
        "expected",
        f"Outcome '{outcome}' for classification '{classification}'. No strong signal.",
        f"neutral:{classification}",
        0.0,
        "cycle",
    )


# ---------------------------------------------------------------------------
# Adaptation signal aggregation (for downstream consumers)
# ---------------------------------------------------------------------------


async def get_active_adaptation_signals(
    db: AsyncSession,
    scope: Optional[str] = None,
    limit: int = 20,
    cycle_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Read recent adaptation signals for downstream services.

    Returns aggregated signal weights grouped by signal name.
    Downstream consumers (goal selector, execution gate) call this to adjust.
    """
    query = select(
        OutcomeLearningRecord.adaptation_signal,
        func.sum(OutcomeLearningRecord.signal_weight).label("total_weight"),
        func.count(OutcomeLearningRecord.id).label("occurrences"),
    ).group_by(OutcomeLearningRecord.adaptation_signal)

    if scope:
        query = query.where(OutcomeLearningRecord.signal_scope == scope)
        if scope == "session" and cycle_id is not None:
            query = query.where(OutcomeLearningRecord.cycle_id == cycle_id)

    query = query.order_by(
        func.abs(func.sum(OutcomeLearningRecord.signal_weight)).desc()
    ).limit(limit)

    result = await db.execute(query)
    rows = result.all()
    return [
        {
            "signal": row[0],
            "total_weight": round(float(row[1]), 4),
            "occurrences": int(row[2]),
        }
        for row in rows
    ]


def compute_score_adjustment(signals: List[Dict[str, Any]]) -> float:
    """Compute a single numeric adjustment from adaptation signals.

    Used by GoalSelectionService._compute_goal_score to adjust scoring.
    Clamped to [-0.3, +0.3] to prevent runaway feedback.
    """
    total = 0.0
    for s in signals:
        sig_name = str(s.get("signal", ""))
        weight = float(s.get("total_weight", 0.0))
        # Only count signals that affect scoring
        if sig_name.startswith("boost_") or sig_name.startswith("trust_"):
            total += weight
        elif sig_name.startswith("penalise_"):
            total += weight  # already negative
    return max(-0.3, min(0.3, total))


def compute_gate_adjustment(
    signals: List[Dict[str, Any]], classification: str
) -> float:
    """Compute a confidence adjustment for the execution gate.

    Positive = more confident in classification, negative = less confident.
    Used by ExecutionGateService to adjust threshold or add caution.
    Clamped to [-0.2, +0.2].
    """
    total = 0.0
    for s in signals:
        sig_name = str(s.get("signal", ""))
        weight = float(s.get("total_weight", 0.0))
        if f"classification:{classification}" in sig_name:
            total += weight
    return max(-0.2, min(0.2, total))


class OutcomeLearningService:
    """Interprets execution outcomes and records lessons + adaptation signals."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def learn_from_execution(
        self,
        execution_record_id: str,
        cycle_id: Optional[str] = None,
    ) -> Optional[OutcomeLearningRecord]:
        """Interpret an execution record and persist a learning record.

        Returns the persisted OutcomeLearningRecord, or None if the
        execution record doesn't exist.
        """
        # 1. Load execution record
        stmt = select(ActionExecutionRecord).where(
            ActionExecutionRecord.id == execution_record_id
        )
        result = await self.db.execute(stmt)
        exec_record = result.scalar_one_or_none()
        if exec_record is None:
            logger.info(f"No execution record found for id={execution_record_id}")
            return None

        # 2. Interpret
        verdict, expectation, lesson, signal, weight, scope = _interpret_outcome(
            exec_record
        )

        # 3. Persist
        record = OutcomeLearningRecord(
            execution_record_id=execution_record_id,
            outcome_verdict=verdict,
            expectation_match=expectation,
            lesson=lesson,
            adaptation_signal=signal,
            signal_weight=weight,
            signal_scope=scope,
            applied=False,
            cycle_id=cycle_id,
        )
        self.db.add(record)
        try:
            await self.db.commit()
            await self.db.refresh(record)
            logger.info(
                f"Outcome learned: {verdict} → {signal} (weight={weight:+.2f}, "
                f"scope={scope})"
            )
        except Exception:
            await self.db.rollback()
            logger.exception("Failed to persist OutcomeLearningRecord")

        return record

    # ------------------------------------------------------------------
    # Read-only queries for endpoints
    # ------------------------------------------------------------------
    async def get_current_outcome(self) -> Optional[OutcomeLearningRecord]:
        """Return the most recent OutcomeLearningRecord."""
        stmt = (
            select(OutcomeLearningRecord)
            .order_by(OutcomeLearningRecord.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_outcome_history(self, limit: int = 10) -> List[OutcomeLearningRecord]:
        """Return recent outcome learning records, newest first."""
        stmt = (
            select(OutcomeLearningRecord)
            .order_by(OutcomeLearningRecord.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_adaptations(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Return aggregated adaptation signals for observation."""
        return await get_active_adaptation_signals(self.db, limit=limit)

    # ------------------------------------------------------------------
    # Phase 11: Override Resolution Feedback
    # ------------------------------------------------------------------

    async def learn_from_override_resolution(
        self,
        enforcement_record: CovenantEnforcementRecord,
        cycle_id: Optional[str] = None,
    ) -> Optional[OutcomeLearningRecord]:
        """Produce an adaptation signal from an approved/denied override.

        Approved overrides teach kor'tana that the covenant was too strict
        on this target type — mildly relax future scoring.
        Denied overrides reinforce that the covenant was correct to flag —
        strengthen future caution.
        Expired/revoked overrides produce neutral signals.

        Returns the persisted OutcomeLearningRecord, or None on failure.
        """
        resolution = str(enforcement_record.resolution_outcome or "")
        target_type = str(enforcement_record.target_type or "unknown")
        rationale = str(enforcement_record.human_rationale or "")

        if resolution == "approved":
            signal = f"override_approved:{target_type}"
            weight = 0.15  # mildly loosen future enforcement on this type
            verdict = "succeeded"
            expectation = "surprising"
            lesson = (
                f"Human approved override for {target_type}. "
                f"Covenant may have been overly strict. Rationale: {rationale}"
            )
            scope = "session"
        elif resolution == "denied":
            signal = f"override_denied:{target_type}"
            weight = -0.15  # reinforce covenant strictness
            verdict = "failed"
            expectation = "expected"
            lesson = (
                f"Human denied override for {target_type}. "
                f"Covenant enforcement was appropriate. Rationale: {rationale}"
            )
            scope = "session"
        elif resolution == "expired":
            signal = f"override_expired:{target_type}"
            weight = -0.05  # slight negative — no one acted
            verdict = "inconclusive"
            expectation = "expected"
            lesson = (
                f"Override for {target_type} expired without resolution. "
                "Treating as implicit denial."
            )
            scope = "cycle"
        elif resolution == "revoked":
            signal = f"override_revoked:{target_type}"
            weight = -0.1  # previously approved, now pulled back
            verdict = "failed"
            expectation = "surprising"
            lesson = (
                f"Previously approved override for {target_type} was revoked. "
                f"Rationale: {rationale}"
            )
            scope = "session"
        else:
            logger.info(
                f"No learning signal for resolution '{resolution}' "
                f"on record {enforcement_record.id}"
            )
            return None

        record = OutcomeLearningRecord(
            execution_record_id=None,
            source_type="override_resolution",
            outcome_verdict=verdict,
            expectation_match=expectation,
            lesson=lesson,
            adaptation_signal=signal,
            signal_weight=weight,
            signal_scope=scope,
            applied=False,
            cycle_id=cycle_id or enforcement_record.cycle_id,
        )
        self.db.add(record)
        try:
            await self.db.commit()
            await self.db.refresh(record)
            logger.info(
                f"Override learning: {resolution} → {signal} "
                f"(weight={weight:+.2f}, scope={scope})"
            )
        except Exception:
            await self.db.rollback()
            logger.exception("Failed to persist override learning record")
            return None

        return record
