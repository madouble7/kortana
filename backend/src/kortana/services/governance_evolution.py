"""V20D — Governance Evolution: self-evolving governance rules."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from src.kortana.services.trust_calibrator import TrustCalibrator, TrustLevel, TrustCalibration
from src.kortana.services.autonomy_adjuster import AutonomyAdjuster, AutonomyThreshold
from src.kortana.services.policy_feedback_loop import PolicyFeedbackLoop, AmendmentStatus


# ── Enums ─────────────────────────────────────────────────────────────────


class EvolutionStage(Enum):
    """Stage of governance evolution."""

    STATIC = "static"
    CALIBRATING = "calibrating"
    ADAPTIVE = "adaptive"
    SELF_GOVERNING = "self_governing"


# ── Data structures ───────────────────────────────────────────────────────


@dataclass
class GovernanceSnapshot:
    """A snapshot of the governance state at a point in time."""

    snapshot_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    trust_level: TrustLevel = TrustLevel.UNTRUSTED
    trust_score: float = 0.0
    evolution_stage: EvolutionStage = EvolutionStage.STATIC
    autonomy_categories: int = 0
    pending_amendments: int = 0
    applied_amendments: int = 0
    total_amendments: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    snapshot_hash: str = ""

    def __post_init__(self) -> None:
        if not self.snapshot_hash:
            raw = f"{self.snapshot_id}:{self.trust_level.value}:{self.evolution_stage.value}:{self.created_at}"
            self.snapshot_hash = hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "trust_level": self.trust_level.value,
            "trust_score": round(self.trust_score, 3),
            "evolution_stage": self.evolution_stage.value,
            "autonomy_categories": self.autonomy_categories,
            "pending_amendments": self.pending_amendments,
            "applied_amendments": self.applied_amendments,
            "total_amendments": self.total_amendments,
            "created_at": self.created_at,
            "snapshot_hash": self.snapshot_hash,
        }


# ── Governance Evolution ─────────────────────────────────────────────────


class GovernanceEvolution:
    """Orchestrates trust → autonomy → policy → governance evolution."""

    def __init__(
        self,
        trust_calibrator: TrustCalibrator | None = None,
        autonomy_adjuster: AutonomyAdjuster | None = None,
        policy_feedback: PolicyFeedbackLoop | None = None,
    ) -> None:
        self._calibrator = trust_calibrator or TrustCalibrator()
        self._adjuster = autonomy_adjuster or AutonomyAdjuster(calibrator=self._calibrator)
        self._feedback = policy_feedback or PolicyFeedbackLoop()
        self._snapshots: list[GovernanceSnapshot] = []

    @property
    def calibrator(self) -> TrustCalibrator:
        return self._calibrator

    @property
    def adjuster(self) -> AutonomyAdjuster:
        return self._adjuster

    @property
    def feedback(self) -> PolicyFeedbackLoop:
        return self._feedback

    def evolve(self) -> GovernanceSnapshot:
        """Run one evolution cycle: calibrate → adjust → amend → snapshot."""
        # Step 1: Calibrate trust
        cal = self._calibrator.calibrate_trust()

        # Step 2: Adjust autonomy thresholds
        thresholds = self._adjuster.adjust_thresholds()

        # Step 3: Generate policy amendments
        self._feedback.generate_amendments()

        # Step 4: Determine evolution stage
        stage = self._compute_stage(cal, thresholds, self._feedback)

        # Step 5: Create snapshot
        applied = len(self._feedback.get_amendments(status=AmendmentStatus.APPLIED))
        snapshot = GovernanceSnapshot(
            trust_level=cal.trust_level,
            trust_score=cal.trust_score,
            evolution_stage=stage,
            autonomy_categories=len(thresholds),
            pending_amendments=self._feedback.pending_count,
            applied_amendments=applied,
            total_amendments=self._feedback.amendment_count,
        )
        self._snapshots.append(snapshot)
        return snapshot

    def get_current_snapshot(self) -> GovernanceSnapshot | None:
        return self._snapshots[-1] if self._snapshots else None

    def get_evolution_history(self) -> list[GovernanceSnapshot]:
        return list(self._snapshots)

    def get_evolution_stage(self) -> EvolutionStage:
        """Get current evolution stage."""
        if self._snapshots:
            return self._snapshots[-1].evolution_stage
        return EvolutionStage.STATIC

    def get_governance_summary(self) -> dict[str, Any]:
        """Get a summary of current governance state."""
        snapshot = self.get_current_snapshot()
        cal = self._calibrator.get_current_trust()
        return {
            "evolution_stage": (snapshot.evolution_stage.value if snapshot else EvolutionStage.STATIC.value),
            "trust_level": cal.trust_level.value,
            "trust_score": round(cal.trust_score, 3),
            "autonomy_categories": self._adjuster.threshold_count,
            "pending_amendments": self._feedback.pending_count,
            "total_amendments": self._feedback.amendment_count,
            "evolution_cycles": len(self._snapshots),
        }

    @property
    def snapshot_count(self) -> int:
        return len(self._snapshots)

    @staticmethod
    def _compute_stage(
        cal: TrustCalibration,
        thresholds: dict[str, AutonomyThreshold],
        feedback: PolicyFeedbackLoop,
    ) -> EvolutionStage:
        applied = len(feedback.get_amendments(status=AmendmentStatus.APPLIED))

        if cal.trust_level == TrustLevel.AUTONOMOUS and applied >= 3:
            return EvolutionStage.SELF_GOVERNING
        if cal.trust_level in (TrustLevel.HIGH_TRUST, TrustLevel.AUTONOMOUS) and applied >= 1:
            return EvolutionStage.ADAPTIVE
        if cal.trust_score > 0.0:
            return EvolutionStage.CALIBRATING
        return EvolutionStage.STATIC


# ── Module singleton ──────────────────────────────────────────────────────

_governance_evolution: GovernanceEvolution | None = None


def get_governance_evolution() -> GovernanceEvolution:
    global _governance_evolution
    if _governance_evolution is None:
        _governance_evolution = GovernanceEvolution()
    return _governance_evolution
