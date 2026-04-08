"""
KOR'TANA Autonomy Orchestrator — Phase 5 Core Loop

The single internal loop that drives kor'tana's self-evolution:

    observe → reflect (revelation synthesis) → synthesize self-model → persist

Called exclusively by the Silent Reviewer daemon.  No public API triggers.
"""

import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.kortana.models import AutonomyCycleRecord
from src.kortana.services.constitutional_service import ConstitutionalService
from src.kortana.services.execution_gate_service import ExecutionGateService
from src.kortana.services.goal_selection_service import GoalSelectionService
from src.kortana.services.outcome_learning_service import OutcomeLearningService
from src.kortana.services.revelation_engine import RevelationEngine
from src.kortana.services.self_model_service import SelfModelService

logger = logging.getLogger(__name__)


async def get_last_cycle_record(db: AsyncSession) -> Optional[Dict[str, Any]]:
    """Read the most recent AutonomyCycleRecord from the database."""
    stmt = (
        select(AutonomyCycleRecord)
        .order_by(AutonomyCycleRecord.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    row = result.scalar_one_or_none()
    if row is None:
        return None
    return {
        "cycle_id": row.cycle_id,
        "trigger": row.trigger,
        "timestamp": row.created_at.isoformat() if row.created_at else None,
        "duration_ms": row.duration_ms,
        "observations": row.observations_count,
        "revelations_written": row.revelations_written,
        "self_model_version": row.self_model_version,
        "developmental_stage": row.developmental_stage,
        "actions_taken": row.actions_taken,
    }


class AutonomyOrchestrator:
    """Drives kor'tana's autonomous self-evolution loop."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.self_model = SelfModelService(db)
        self.revelation_engine = RevelationEngine(db)

    async def run_cycle(self, trigger: str = "scheduled") -> Dict[str, Any]:
        """Execute one full autonomy cycle.

        Steps: observe → reflect (revelation synthesis) → synthesize self-model → persist.
        Returns a summary dict with cycle metadata.
        """
        cycle_id = str(uuid.uuid4())[:8]
        start = time.monotonic()
        actions_taken: List[str] = []

        logger.info(f"Autonomy cycle {cycle_id} starting (trigger={trigger})")

        # ---- 1. OBSERVE ----
        observations: List[str] = []
        try:
            observations = await self.self_model._gather_observations()
            actions_taken.append(f"observed {len(observations)} signals")
        except Exception:
            logger.exception("Observe phase failed")
            actions_taken.append("observe: failed")

        # ---- 2. REFLECT (revelation synthesis) ----
        revelations_written = 0
        try:
            revs = await self.revelation_engine.synthesise(force=False)
            revelations_written = len(revs)
            if revelations_written:
                actions_taken.append(f"synthesised {revelations_written} revelations")
        except Exception:
            logger.exception("Reflect phase failed")
            actions_taken.append("reflect: failed")

        # ---- 3. SYNTHESIZE SELF-MODEL (includes Inner Council) ----
        snapshot_version = None
        developmental_stage = None
        try:
            snapshot = await self.self_model.evolve(
                trigger=trigger,
                external_observations=[
                    f"[cycle {cycle_id}] {len(observations)} observations, "
                    f"{revelations_written} revelations"
                ],
            )
            if snapshot:
                snapshot_version = snapshot.version
                developmental_stage = str(snapshot.developmental_stage)
                actions_taken.append(
                    f"self-model v{snapshot.version} "
                    f"(stage={snapshot.developmental_stage}, "
                    f"confidence={snapshot.confidence:.2f})"
                )
            else:
                actions_taken.append("self-model: synthesis returned nothing")
        except Exception:
            logger.exception("Self-model synthesis failed")
            actions_taken.append("self-model: failed")

        # ---- 3.5 GOAL SELECTION (Agency Core) ----
        next_action_id: Optional[str] = None
        next_action_title: Optional[str] = None
        try:
            selector = GoalSelectionService(self.db)
            candidate = await selector.select_next_action(cycle_id=cycle_id)
            if candidate:
                next_action_id = str(candidate.id)
                next_action_title = str(candidate.title)
                actions_taken.append(
                    f"next-action: {candidate.title} "
                    f"(score={candidate.score:.4f}, type={candidate.action_type})"
                )
        except Exception:
            logger.exception("Goal selection failed")
            actions_taken.append("goal-selection: failed")

        # ---- 3.6 CANDIDATE ENFORCEMENT (Pre-Action Veto) ----
        candidate_blocked = False
        candidate_enforcement_verdict: Optional[str] = None
        result_status = "completed"
        execution_block_reason: Optional[str] = None
        try:
            if next_action_id and next_action_title:
                covenant = ConstitutionalService(self.db)
                # Load candidate payload for tier info
                from src.kortana.models import NextActionCandidate as NACModel

                nac_stmt = select(NACModel).where(NACModel.id == next_action_id)
                nac_result = await self.db.execute(nac_stmt)
                nac_row = nac_result.scalar_one_or_none()
                nac_payload: dict = nac_row.candidate_payload or {} if nac_row else {}  # type: ignore[assignment]

                enforce_verdict, _enf_rec = await covenant.enforce_candidate(
                    candidate_title=next_action_title,
                    candidate_id=next_action_id,
                    candidate_score=float(nac_row.score) if nac_row else 0.0,
                    action_type=str(nac_row.action_type) if nac_row else None,
                    goal_tier=str(nac_payload.get("goal_tier", "")),
                    cycle_id=cycle_id,
                )
                candidate_enforcement_verdict = enforce_verdict
                actions_taken.append(f"candidate-enforcement: {enforce_verdict}")
                if enforce_verdict == "blocked":
                    candidate_blocked = True
                    result_status = "blocked"
                    execution_block_reason = "candidate blocked by covenant"
                    logger.warning(
                        f"Candidate BLOCKED by covenant: {next_action_title}"
                    )
                elif enforce_verdict == "requires_human_override":
                    candidate_blocked = True  # don't proceed to gate
                    result_status = "requires_human_override"
                    execution_block_reason = "candidate requires human override"
                    logger.info(
                        f"Candidate requires HUMAN OVERRIDE: {next_action_title}"
                    )
        except Exception:
            logger.exception("Candidate enforcement failed")
            actions_taken.append("candidate-enforcement: failed")
            candidate_blocked = True
            result_status = "blocked"
            execution_block_reason = "candidate enforcement failed"

        # ---- 3.7 EXECUTION GATE (Action Realization) ----
        execution_record_id: Optional[str] = None
        execution_classification: Optional[str] = None
        if not candidate_blocked and next_action_id:
            try:
                gate = ExecutionGateService(self.db)
                exec_record = await gate.evaluate(
                    candidate_id=next_action_id, cycle_id=cycle_id
                )
                if exec_record:
                    execution_record_id = str(exec_record.id)
                    execution_classification = str(exec_record.classification)
                    actions_taken.append(
                        f"execution-gate: {exec_record.classification} "
                        f"(outcome={exec_record.outcome})"
                    )
            except Exception:
                logger.exception("Execution gate failed")
                actions_taken.append("execution-gate: failed")
        else:
            actions_taken.append(
                f"execution-gate: skipped (candidate {candidate_enforcement_verdict})"
            )

        # ---- 3.9 OUTCOME LEARNING (Recursive Adaptation) ----
        outcome_learning_id: Optional[str] = None
        outcome_verdict: Optional[str] = None
        adaptation_signal: Optional[str] = None
        try:
            if execution_record_id:
                learner = OutcomeLearningService(self.db)
                learning = await learner.learn_from_execution(
                    execution_record_id=execution_record_id,
                    cycle_id=cycle_id,
                )
                if learning:
                    outcome_learning_id = str(learning.id)
                    outcome_verdict = str(learning.outcome_verdict)
                    adaptation_signal = str(learning.adaptation_signal)
                    actions_taken.append(
                        f"outcome-learning: {learning.outcome_verdict} "
                        f"signal={learning.adaptation_signal} "
                        f"(weight={learning.signal_weight:+.2f})"
                    )
        except Exception:
            logger.exception("Outcome learning failed")
            actions_taken.append("outcome-learning: failed")

        # ---- 3.95 CONSTITUTIONAL REVIEW (Value Governance) ----
        constitutional_decision_id: Optional[str] = None
        constitutional_verdict: Optional[str] = None
        try:
            covenant = ConstitutionalService(self.db)
            summary_parts = []
            if next_action_title:
                summary_parts.append(f"next-action: {next_action_title}")
            if execution_classification:
                summary_parts.append(f"gate: {execution_classification}")
            if adaptation_signal:
                summary_parts.append(f"adaptation: {adaptation_signal}")
            subject_summary = (
                "; ".join(summary_parts)
                if summary_parts
                else f"cycle {cycle_id} with no active decisions"
            )
            decision = await covenant.evaluate(
                subject_type="cycle",
                subject_id=cycle_id,
                subject_summary=subject_summary,
                context={
                    "next_action_title": next_action_title,
                    "execution_classification": execution_classification,
                    "adaptation_signal": adaptation_signal or "",
                    "outcome_verdict": outcome_verdict,
                },
                cycle_id=cycle_id,
            )
            constitutional_decision_id = str(decision.id)
            constitutional_verdict = str(decision.verdict)
            drift_flag = " DRIFT" if decision.drift_detected else ""
            actions_taken.append(f"constitutional: {decision.verdict}{drift_flag}")
        except Exception:
            logger.exception("Constitutional review failed")
            actions_taken.append("constitutional: failed")

        # ---- 3.97 STALE OVERRIDE EXPIRY (Trust Calibration) ----
        expired_count = 0
        try:
            covenant_for_expiry = ConstitutionalService(self.db)
            expired = await covenant_for_expiry.expire_stale_overrides(
                max_age_hours=24
            )
            expired_count = len(expired)
            if expired_count > 0:
                actions_taken.append(f"expired_overrides: {expired_count}")
        except Exception:
            logger.exception("Stale override expiry sweep failed")

        # ---- 4. PERSIST cycle record to DB ----
        elapsed_ms = int((time.monotonic() - start) * 1000)

        result: Dict[str, Any] = {
            "cycle_id": cycle_id,
            "trigger": trigger,
            "timestamp": datetime.utcnow().isoformat(),
            "duration_ms": elapsed_ms,
            "observations": len(observations),
            "revelations_written": revelations_written,
            "self_model_version": snapshot_version,
            "developmental_stage": developmental_stage,
            "next_action_candidate_id": next_action_id,
            "next_action_title": next_action_title,
            "status": result_status,
            "candidate_enforcement_verdict": candidate_enforcement_verdict,
            "execution_block_reason": execution_block_reason,
            "execution_record_id": execution_record_id,
            "execution_classification": execution_classification,
            "outcome_learning_id": outcome_learning_id,
            "outcome_verdict": outcome_verdict,
            "adaptation_signal": adaptation_signal,
            "constitutional_decision_id": constitutional_decision_id,
            "constitutional_verdict": constitutional_verdict,
            "expired_overrides": expired_count,
            "actions_taken": actions_taken,
        }

        try:
            record = AutonomyCycleRecord(
                cycle_id=cycle_id,
                trigger=trigger,
                duration_ms=elapsed_ms,
                observations_count=len(observations),
                revelations_written=revelations_written,
                self_model_version=snapshot_version,
                developmental_stage=developmental_stage,
                actions_taken=actions_taken,
            )
            self.db.add(record)
            await self.db.commit()
        except Exception:
            logger.exception("Failed to persist AutonomyCycleRecord")
            await self.db.rollback()

        logger.info(
            f"Autonomy cycle {cycle_id} complete in {elapsed_ms}ms — "
            f"{', '.join(actions_taken)}"
        )

        return result
