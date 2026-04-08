"""V21B — approval gate: controls when learned changes are accepted."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from src.kortana.services.proposal_registry import PolicyProposal
from src.kortana.services.trust_calibrator import TrustLevel


class DecisionType(Enum):
    """How the approval decision was made."""

    AUTO = "auto"
    HUMAN = "human"


@dataclass
class ApprovalPolicy:
    """Rules governing automatic vs human approval."""

    policy_id: str = "default"
    min_confidence: float = 0.75
    min_trust_level: TrustLevel = TrustLevel.HIGH_TRUST
    require_human_below_confidence: float = 0.50
    max_auto_approve_per_cycle: int = 5
    created_at: str = ""
    policy_hash: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.policy_hash:
            blob = f"{self.policy_id}:{self.min_confidence}:{self.min_trust_level.value}:{self.max_auto_approve_per_cycle}"
            self.policy_hash = hashlib.sha256(blob.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "min_confidence": self.min_confidence,
            "min_trust_level": self.min_trust_level.value,
            "require_human_below_confidence": self.require_human_below_confidence,
            "max_auto_approve_per_cycle": self.max_auto_approve_per_cycle,
            "created_at": self.created_at,
            "policy_hash": self.policy_hash,
        }


@dataclass
class ApprovalDecision:
    """Record of an approval or rejection decision."""

    decision_id: str
    proposal_id: str
    approved: bool
    decision_type: DecisionType
    decided_by: str
    reason: str
    conditions: str = ""
    decided_at: str = ""
    decision_hash: str = ""

    def __post_init__(self) -> None:
        if not self.decided_at:
            self.decided_at = datetime.now(timezone.utc).isoformat()
        if not self.decision_hash:
            blob = f"{self.decision_id}:{self.proposal_id}:{self.approved}:{self.decided_by}"
            self.decision_hash = hashlib.sha256(blob.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "proposal_id": self.proposal_id,
            "approved": self.approved,
            "decision_type": self.decision_type.value,
            "decided_by": self.decided_by,
            "reason": self.reason,
            "conditions": self.conditions,
            "decided_at": self.decided_at,
            "decision_hash": self.decision_hash,
        }


class ApprovalGate:
    """Gate between 'learning suggests' and 'governance accepts'."""

    def __init__(self) -> None:
        self._policy = ApprovalPolicy()
        self._decisions: list[ApprovalDecision] = []
        self._auto_approve_count: int = 0

    # ── policy management ──

    def set_policy(self, policy: ApprovalPolicy) -> None:
        self._policy = policy
        self._auto_approve_count = 0

    def get_policy(self) -> ApprovalPolicy:
        return self._policy

    # ── evaluation ──

    def evaluate(self, proposal: PolicyProposal, trust_level: TrustLevel) -> ApprovalDecision:
        """Evaluate a proposal against the approval policy.

        Returns an ApprovalDecision indicating whether the proposal
        passes the gate automatically or needs human review.
        """
        can_auto = self._can_auto_approve(proposal, trust_level)

        if can_auto:
            decision = ApprovalDecision(
                decision_id=f"dec-{uuid.uuid4().hex[:12]}",
                proposal_id=proposal.proposal_id,
                approved=True,
                decision_type=DecisionType.AUTO,
                decided_by="system",
                reason=self._auto_reason(proposal, trust_level),
            )
            self._auto_approve_count += 1
        else:
            decision = ApprovalDecision(
                decision_id=f"dec-{uuid.uuid4().hex[:12]}",
                proposal_id=proposal.proposal_id,
                approved=False,
                decision_type=DecisionType.HUMAN,
                decided_by="pending_human",
                reason=self._human_reason(proposal, trust_level),
            )

        self._decisions.append(decision)
        return decision

    def approve_manual(
        self,
        proposal_id: str,
        decided_by: str = "human",
        reason: str = "manually approved",
        conditions: str = "",
    ) -> ApprovalDecision:
        """Record a human approval decision."""
        decision = ApprovalDecision(
            decision_id=f"dec-{uuid.uuid4().hex[:12]}",
            proposal_id=proposal_id,
            approved=True,
            decision_type=DecisionType.HUMAN,
            decided_by=decided_by,
            reason=reason,
            conditions=conditions,
        )
        self._decisions.append(decision)
        return decision

    def reject_manual(
        self,
        proposal_id: str,
        decided_by: str = "human",
        reason: str = "manually rejected",
    ) -> ApprovalDecision:
        """Record a human rejection decision."""
        decision = ApprovalDecision(
            decision_id=f"dec-{uuid.uuid4().hex[:12]}",
            proposal_id=proposal_id,
            approved=False,
            decision_type=DecisionType.HUMAN,
            decided_by=decided_by,
            reason=reason,
        )
        self._decisions.append(decision)
        return decision

    # ── queries ──

    def get_decisions(self, proposal_id: str | None = None) -> list[ApprovalDecision]:
        if proposal_id is None:
            return list(self._decisions)
        return [d for d in self._decisions if d.proposal_id == proposal_id]

    def get_auto_approve_count(self) -> int:
        return self._auto_approve_count

    def reset_cycle(self) -> None:
        """Reset auto-approve counter for a new evolution cycle."""
        self._auto_approve_count = 0

    @property
    def decision_count(self) -> int:
        return len(self._decisions)

    # ── internal ──

    _TRUST_RANK: dict[TrustLevel, int] = {
        TrustLevel.UNTRUSTED: 0,
        TrustLevel.PROVISIONAL: 1,
        TrustLevel.TRUSTED: 2,
        TrustLevel.HIGH_TRUST: 3,
        TrustLevel.AUTONOMOUS: 4,
    }

    def _can_auto_approve(self, proposal: PolicyProposal, trust_level: TrustLevel) -> bool:
        if self._auto_approve_count >= self._policy.max_auto_approve_per_cycle:
            return False
        if proposal.confidence < self._policy.min_confidence:
            return False
        required_rank = self._TRUST_RANK.get(self._policy.min_trust_level, 3)
        actual_rank = self._TRUST_RANK.get(trust_level, 0)
        if actual_rank < required_rank:
            return False
        return True

    def _auto_reason(self, proposal: PolicyProposal, trust_level: TrustLevel) -> str:
        return (
            f"auto-approved: confidence {proposal.confidence:.2f} >= {self._policy.min_confidence}, "
            f"trust {trust_level.value} meets minimum {self._policy.min_trust_level.value}"
        )

    def _human_reason(self, proposal: PolicyProposal, trust_level: TrustLevel) -> str:
        parts: list[str] = []
        if proposal.confidence < self._policy.min_confidence:
            parts.append(f"confidence {proposal.confidence:.2f} < {self._policy.min_confidence}")
        required_rank = self._TRUST_RANK.get(self._policy.min_trust_level, 3)
        actual_rank = self._TRUST_RANK.get(trust_level, 0)
        if actual_rank < required_rank:
            parts.append(f"trust {trust_level.value} below {self._policy.min_trust_level.value}")
        if self._auto_approve_count >= self._policy.max_auto_approve_per_cycle:
            parts.append("auto-approve limit reached")
        return "requires human review: " + "; ".join(parts) if parts else "requires human review"


_gate: ApprovalGate | None = None


def get_approval_gate() -> ApprovalGate:
    """Module singleton."""
    global _gate
    if _gate is None:
        _gate = ApprovalGate()
    return _gate
