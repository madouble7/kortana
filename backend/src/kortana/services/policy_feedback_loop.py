"""V20C — Policy Feedback Loop: policy refinement from learning outcomes."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from src.kortana.services.trust_calibrator import TrustCalibrator, TrustLevel
from src.kortana.services.outcome_tracker import OutcomeTracker
from src.kortana.services.improvement_tracker import ImprovementTracker, LearningMaturity


# ── Enums ─────────────────────────────────────────────────────────────────


class AmendmentStatus(Enum):
    """Status of a policy amendment."""

    PENDING = "pending"
    APPLIED = "applied"
    REJECTED = "rejected"


class PolicyArea(Enum):
    """Areas of policy that can be amended."""

    ROLLOUT = "rollout"
    AUTONOMY = "autonomy"
    ESCALATION = "escalation"
    RETRY = "retry"
    PRIORITY = "priority"
    GOVERNANCE = "governance"


# ── Data structures ───────────────────────────────────────────────────────


@dataclass
class PolicyAmendment:
    """A proposed amendment to an existing policy rule."""

    amendment_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    policy_area: PolicyArea = PolicyArea.GOVERNANCE
    current_rule: str = ""
    proposed_rule: str = ""
    justification: str = ""
    confidence: float = 0.0
    evidence_count: int = 0
    status: AmendmentStatus = AmendmentStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved_at: str = ""
    amendment_hash: str = ""

    def __post_init__(self) -> None:
        if not self.amendment_hash:
            raw = f"{self.amendment_id}:{self.policy_area.value}:{self.proposed_rule}:{self.created_at}"
            self.amendment_hash = hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "amendment_id": self.amendment_id,
            "policy_area": self.policy_area.value,
            "current_rule": self.current_rule,
            "proposed_rule": self.proposed_rule,
            "justification": self.justification,
            "confidence": round(self.confidence, 3),
            "evidence_count": self.evidence_count,
            "status": self.status.value,
            "created_at": self.created_at,
            "resolved_at": self.resolved_at,
            "amendment_hash": self.amendment_hash,
        }


# ── Policy Feedback Loop ─────────────────────────────────────────────────


class PolicyFeedbackLoop:
    """Feeds recovery performance into policy rules."""

    MIN_EVIDENCE = 5

    def __init__(
        self,
        outcome_tracker: OutcomeTracker | None = None,
        improvement_tracker: ImprovementTracker | None = None,
        trust_calibrator: TrustCalibrator | None = None,
    ) -> None:
        self._outcome_tracker = outcome_tracker or OutcomeTracker()
        self._improvement_tracker = improvement_tracker or ImprovementTracker()
        self._trust_calibrator = trust_calibrator or TrustCalibrator()
        self._amendments: list[PolicyAmendment] = []

    def generate_amendments(self) -> list[PolicyAmendment]:
        """Generate policy amendments based on current performance data."""
        new_amendments: list[PolicyAmendment] = []
        outcomes = self._outcome_tracker.get_outcomes()

        if len(outcomes) < self.MIN_EVIDENCE:
            return new_amendments

        eff_rate = self._outcome_tracker.get_effectiveness_rate()
        esc_rate = self._outcome_tracker.get_escalation_rate()
        stab_rate = self._outcome_tracker.get_stability_rate()
        avg_retries = self._outcome_tracker.get_avg_retries()
        cal = self._trust_calibrator.get_current_trust()

        # Amendment: Escalation policy
        if esc_rate > 0.5 and eff_rate > 0.7:
            new_amendments.append(PolicyAmendment(
                policy_area=PolicyArea.ESCALATION,
                current_rule=f"Escalation rate: {esc_rate:.0%}",
                proposed_rule="Reduce escalation frequency — autonomous recovery is effective",
                justification=f"Effectiveness at {eff_rate:.0%} despite {esc_rate:.0%} escalation; most escalations unnecessary",
                confidence=min(1.0, eff_rate * 0.9),
                evidence_count=len(outcomes),
            ))

        # Amendment: Retry policy
        if avg_retries > 3 and eff_rate > 0.6:
            new_amendments.append(PolicyAmendment(
                policy_area=PolicyArea.RETRY,
                current_rule=f"Avg retries: {avg_retries:.1f}",
                proposed_rule=f"Set max retries to {max(2, int(avg_retries) - 1)} — reduce unnecessary retries",
                justification=f"Recovery effective at {eff_rate:.0%} with avg {avg_retries:.1f} retries; excess retries detected",
                confidence=min(1.0, eff_rate * 0.8),
                evidence_count=len(outcomes),
            ))
        elif avg_retries < 2 and eff_rate < 0.5:
            new_amendments.append(PolicyAmendment(
                policy_area=PolicyArea.RETRY,
                current_rule=f"Avg retries: {avg_retries:.1f}",
                proposed_rule=f"Increase max retries to {int(avg_retries) + 2} — more attempts may improve recovery",
                justification=f"Low effectiveness ({eff_rate:.0%}) with few retries ({avg_retries:.1f}); more attempts may help",
                confidence=0.5,
                evidence_count=len(outcomes),
            ))

        # Amendment: Autonomy threshold
        if cal.trust_level in (TrustLevel.HIGH_TRUST, TrustLevel.AUTONOMOUS) and eff_rate > 0.8:
            new_amendments.append(PolicyAmendment(
                policy_area=PolicyArea.AUTONOMY,
                current_rule=f"Trust: {cal.trust_level.value}, effectiveness: {eff_rate:.0%}",
                proposed_rule="Widen autonomy window — system has demonstrated reliable self-recovery",
                justification=f"Trust at {cal.trust_level.value} with {eff_rate:.0%} effectiveness warrants expanded autonomy",
                confidence=cal.trust_score,
                evidence_count=len(outcomes),
            ))

        # Amendment: Priority policy
        if stab_rate < 0.6 and eff_rate > 0.5:
            new_amendments.append(PolicyAmendment(
                policy_area=PolicyArea.PRIORITY,
                current_rule=f"Stability rate: {stab_rate:.0%}",
                proposed_rule="Increase priority for unstable drift types — faster re-reconciliation needed",
                justification=f"Resolutions unstable ({stab_rate:.0%}) despite {eff_rate:.0%} effectiveness; higher priority may reduce re-drift",
                confidence=min(1.0, (1.0 - stab_rate) * 0.8),
                evidence_count=len(outcomes),
            ))

        # Amendment: Rollout policy
        maturity = self._improvement_tracker.get_learning_maturity()
        if maturity in (LearningMaturity.MATURE, LearningMaturity.EXPERT):
            latest = self._improvement_tracker.get_latest_report()
            if latest and latest.overall_improvement_pct > 10:
                new_amendments.append(PolicyAmendment(
                    policy_area=PolicyArea.ROLLOUT,
                    current_rule=f"Maturity: {maturity.value}, improvement: {latest.overall_improvement_pct:.0f}%",
                    proposed_rule="Enable learning-first rollout — adaptive plans should be default for known drift types",
                    justification=f"Learning is {maturity.value} with {latest.overall_improvement_pct:.0f}% improvement; learned plans outperform defaults",
                    confidence=min(1.0, latest.overall_improvement_pct / 50.0),
                    evidence_count=latest.total_outcomes_analyzed,
                ))

        self._amendments.extend(new_amendments)
        return new_amendments

    def get_pending_amendments(self) -> list[PolicyAmendment]:
        return [a for a in self._amendments if a.status == AmendmentStatus.PENDING]

    def get_amendments(self, status: AmendmentStatus | None = None) -> list[PolicyAmendment]:
        if status is not None:
            return [a for a in self._amendments if a.status == status]
        return list(self._amendments)

    def apply_amendment(self, amendment_id: str) -> bool:
        """Mark an amendment as applied."""
        for a in self._amendments:
            if a.amendment_id == amendment_id and a.status == AmendmentStatus.PENDING:
                a.status = AmendmentStatus.APPLIED
                a.resolved_at = datetime.now(timezone.utc).isoformat()
                return True
        return False

    def reject_amendment(self, amendment_id: str) -> bool:
        """Mark an amendment as rejected."""
        for a in self._amendments:
            if a.amendment_id == amendment_id and a.status == AmendmentStatus.PENDING:
                a.status = AmendmentStatus.REJECTED
                a.resolved_at = datetime.now(timezone.utc).isoformat()
                return True
        return False

    @property
    def amendment_count(self) -> int:
        return len(self._amendments)

    @property
    def pending_count(self) -> int:
        return sum(1 for a in self._amendments if a.status == AmendmentStatus.PENDING)


# ── Module singleton ──────────────────────────────────────────────────────

_policy_feedback_loop: PolicyFeedbackLoop | None = None


def get_policy_feedback_loop() -> PolicyFeedbackLoop:
    global _policy_feedback_loop
    if _policy_feedback_loop is None:
        _policy_feedback_loop = PolicyFeedbackLoop()
    return _policy_feedback_loop
