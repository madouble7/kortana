"""V21A — proposal registry: formal lifecycle for learned policy changes."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from kortana.services.policy_feedback_loop import PolicyAmendment, PolicyArea


class ProposalStatus(Enum):
    """Lifecycle stages for a policy change proposal."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    PROMOTED = "promoted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


_VALID_TRANSITIONS: dict[ProposalStatus, set[ProposalStatus]] = {
    ProposalStatus.DRAFT: {ProposalStatus.SUBMITTED, ProposalStatus.WITHDRAWN},
    ProposalStatus.SUBMITTED: {ProposalStatus.UNDER_REVIEW, ProposalStatus.WITHDRAWN},
    ProposalStatus.UNDER_REVIEW: {
        ProposalStatus.APPROVED,
        ProposalStatus.REJECTED,
        ProposalStatus.WITHDRAWN,
    },
    ProposalStatus.APPROVED: {ProposalStatus.PROMOTED, ProposalStatus.WITHDRAWN},
    ProposalStatus.PROMOTED: set(),
    ProposalStatus.REJECTED: set(),
    ProposalStatus.WITHDRAWN: set(),
}


@dataclass
class PolicyProposal:
    """A formal proposal wrapping a learned policy amendment."""

    proposal_id: str
    source_amendment_id: str
    policy_area: PolicyArea
    current_rule: str
    proposed_rule: str
    justification: str
    confidence: float
    evidence_count: int
    status: ProposalStatus = ProposalStatus.DRAFT
    submitted_at: str = ""
    reviewed_at: str = ""
    promoted_at: str = ""
    reviewer: str = ""
    review_notes: str = ""
    created_at: str = ""
    proposal_hash: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.proposal_hash:
            self.proposal_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        blob = f"{self.proposal_id}:{self.source_amendment_id}:{self.policy_area.value}:{self.proposed_rule}"
        return hashlib.sha256(blob.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "source_amendment_id": self.source_amendment_id,
            "policy_area": self.policy_area.value,
            "current_rule": self.current_rule,
            "proposed_rule": self.proposed_rule,
            "justification": self.justification,
            "confidence": self.confidence,
            "evidence_count": self.evidence_count,
            "status": self.status.value,
            "submitted_at": self.submitted_at,
            "reviewed_at": self.reviewed_at,
            "promoted_at": self.promoted_at,
            "reviewer": self.reviewer,
            "review_notes": self.review_notes,
            "created_at": self.created_at,
            "proposal_hash": self.proposal_hash,
        }


class ProposalRegistry:
    """Manages the lifecycle of learned policy change proposals."""

    def __init__(self) -> None:
        self._proposals: dict[str, PolicyProposal] = {}
        self._history: list[dict[str, Any]] = []

    # ── creation ──

    def create_proposal(self, amendment: PolicyAmendment) -> PolicyProposal:
        """Create a DRAFT proposal from a V20 PolicyAmendment."""
        proposal = PolicyProposal(
            proposal_id=f"prop-{uuid.uuid4().hex[:12]}",
            source_amendment_id=amendment.amendment_id,
            policy_area=amendment.policy_area,
            current_rule=amendment.current_rule,
            proposed_rule=amendment.proposed_rule,
            justification=amendment.justification,
            confidence=amendment.confidence,
            evidence_count=amendment.evidence_count,
        )
        self._proposals[proposal.proposal_id] = proposal
        self._record("created", proposal)
        return proposal

    def create_proposal_direct(
        self,
        policy_area: PolicyArea,
        current_rule: str,
        proposed_rule: str,
        justification: str,
        confidence: float = 0.5,
        evidence_count: int = 0,
    ) -> PolicyProposal:
        """Create a DRAFT proposal without an existing amendment."""
        proposal = PolicyProposal(
            proposal_id=f"prop-{uuid.uuid4().hex[:12]}",
            source_amendment_id="manual",
            policy_area=policy_area,
            current_rule=current_rule,
            proposed_rule=proposed_rule,
            justification=justification,
            confidence=confidence,
            evidence_count=evidence_count,
        )
        self._proposals[proposal.proposal_id] = proposal
        self._record("created", proposal)
        return proposal

    # ── transitions ──

    def submit_proposal(self, proposal_id: str) -> bool:
        """Move proposal from DRAFT → SUBMITTED."""
        return self._transition(proposal_id, ProposalStatus.SUBMITTED)

    def begin_review(self, proposal_id: str) -> bool:
        """Move proposal from SUBMITTED → UNDER_REVIEW."""
        return self._transition(proposal_id, ProposalStatus.UNDER_REVIEW)

    def mark_approved(self, proposal_id: str, reviewer: str = "system", notes: str = "") -> bool:
        """Move proposal from UNDER_REVIEW → APPROVED."""
        p = self._proposals.get(proposal_id)
        if p is None:
            return False
        if ProposalStatus.APPROVED not in _VALID_TRANSITIONS.get(p.status, set()):
            return False
        p.reviewer = reviewer
        p.review_notes = notes
        p.reviewed_at = datetime.now(timezone.utc).isoformat()
        return self._transition(proposal_id, ProposalStatus.APPROVED)

    def mark_rejected(self, proposal_id: str, reviewer: str = "system", notes: str = "") -> bool:
        """Move proposal from UNDER_REVIEW → REJECTED."""
        p = self._proposals.get(proposal_id)
        if p is None:
            return False
        if ProposalStatus.REJECTED not in _VALID_TRANSITIONS.get(p.status, set()):
            return False
        p.reviewer = reviewer
        p.review_notes = notes
        p.reviewed_at = datetime.now(timezone.utc).isoformat()
        return self._transition(proposal_id, ProposalStatus.REJECTED)

    def promote(self, proposal_id: str) -> bool:
        """Move proposal from APPROVED → PROMOTED (applies the change)."""
        ok = self._transition(proposal_id, ProposalStatus.PROMOTED)
        if ok:
            p = self._proposals[proposal_id]
            p.promoted_at = datetime.now(timezone.utc).isoformat()
        return ok

    def withdraw(self, proposal_id: str) -> bool:
        """Withdraw a proposal (valid from DRAFT, SUBMITTED, UNDER_REVIEW, APPROVED)."""
        return self._transition(proposal_id, ProposalStatus.WITHDRAWN)

    # ── queries ──

    def get_proposal(self, proposal_id: str) -> PolicyProposal | None:
        return self._proposals.get(proposal_id)

    def list_proposals(self, status: ProposalStatus | None = None) -> list[PolicyProposal]:
        if status is None:
            return list(self._proposals.values())
        return [p for p in self._proposals.values() if p.status == status]

    def get_proposals_by_area(self, area: PolicyArea) -> list[PolicyProposal]:
        return [p for p in self._proposals.values() if p.policy_area == area]

    def get_history(self) -> list[dict[str, Any]]:
        return list(self._history)

    @property
    def proposal_count(self) -> int:
        return len(self._proposals)

    # ── internal ──

    def _transition(self, proposal_id: str, target: ProposalStatus) -> bool:
        p = self._proposals.get(proposal_id)
        if p is None:
            return False
        valid = _VALID_TRANSITIONS.get(p.status, set())
        if target not in valid:
            return False
        old_status = p.status
        p.status = target
        self._record("transition", p, old_status=old_status.value, new_status=target.value)
        return True

    def _record(self, action: str, proposal: PolicyProposal, **extra: Any) -> None:
        entry = {
            "action": action,
            "proposal_id": proposal.proposal_id,
            "status": proposal.status.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **extra,
        }
        self._history.append(entry)


_registry: ProposalRegistry | None = None


def get_proposal_registry() -> ProposalRegistry:
    """Module singleton."""
    global _registry
    if _registry is None:
        _registry = ProposalRegistry()
    return _registry
