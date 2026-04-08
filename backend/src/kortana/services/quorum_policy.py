"""V22B — quorum policy: identity/quorum requirements scaled by sensitivity."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from src.kortana.services.constitution import Sensitivity


class QuorumType(Enum):
    """Type of quorum required for policy changes."""

    UNANIMOUS = "unanimous"
    SUPERMAJORITY = "supermajority"
    SIMPLE_MAJORITY = "simple_majority"
    SINGLE_APPROVER = "single_approver"
    AUTO = "auto"


@dataclass
class QuorumRequirement:
    """Quorum requirements for a given sensitivity level."""

    sensitivity: Sensitivity
    quorum_type: QuorumType
    min_approvers: int
    require_identity_verification: bool
    cooldown_hours: int
    requirement_hash: str = ""

    def __post_init__(self) -> None:
        if not self.requirement_hash:
            blob = f"{self.sensitivity.value}:{self.quorum_type.value}:{self.min_approvers}"
            self.requirement_hash = hashlib.sha256(blob.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "sensitivity": self.sensitivity.value,
            "quorum_type": self.quorum_type.value,
            "min_approvers": self.min_approvers,
            "require_identity_verification": self.require_identity_verification,
            "cooldown_hours": self.cooldown_hours,
            "requirement_hash": self.requirement_hash,
        }


@dataclass
class QuorumVote:
    """A single vote in a quorum decision."""

    vote_id: str
    proposal_id: str
    voter: str
    approved: bool
    identity_verified: bool
    voted_at: str = ""
    vote_hash: str = ""

    def __post_init__(self) -> None:
        if not self.voted_at:
            self.voted_at = datetime.now(timezone.utc).isoformat()
        if not self.vote_hash:
            blob = f"{self.vote_id}:{self.proposal_id}:{self.voter}:{self.approved}"
            self.vote_hash = hashlib.sha256(blob.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "vote_id": self.vote_id,
            "proposal_id": self.proposal_id,
            "voter": self.voter,
            "approved": self.approved,
            "identity_verified": self.identity_verified,
            "voted_at": self.voted_at,
            "vote_hash": self.vote_hash,
        }


@dataclass
class QuorumResult:
    """Result of a quorum check."""

    proposal_id: str
    quorum_met: bool
    quorum_type: QuorumType
    required_approvers: int
    actual_approvers: int
    total_votes: int
    identity_check_passed: bool
    reason: str
    result_hash: str = ""

    def __post_init__(self) -> None:
        if not self.result_hash:
            blob = f"{self.proposal_id}:{self.quorum_met}:{self.actual_approvers}"
            self.result_hash = hashlib.sha256(blob.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "quorum_met": self.quorum_met,
            "quorum_type": self.quorum_type.value,
            "required_approvers": self.required_approvers,
            "actual_approvers": self.actual_approvers,
            "total_votes": self.total_votes,
            "identity_check_passed": self.identity_check_passed,
            "reason": self.reason,
            "result_hash": self.result_hash,
        }


# Default quorum requirements by sensitivity
_DEFAULT_REQUIREMENTS: dict[Sensitivity, QuorumRequirement] = {
    Sensitivity.CRITICAL: QuorumRequirement(
        sensitivity=Sensitivity.CRITICAL,
        quorum_type=QuorumType.UNANIMOUS,
        min_approvers=3,
        require_identity_verification=True,
        cooldown_hours=48,
    ),
    Sensitivity.HIGH: QuorumRequirement(
        sensitivity=Sensitivity.HIGH,
        quorum_type=QuorumType.SUPERMAJORITY,
        min_approvers=2,
        require_identity_verification=True,
        cooldown_hours=24,
    ),
    Sensitivity.STANDARD: QuorumRequirement(
        sensitivity=Sensitivity.STANDARD,
        quorum_type=QuorumType.SIMPLE_MAJORITY,
        min_approvers=1,
        require_identity_verification=False,
        cooldown_hours=4,
    ),
    Sensitivity.LOW: QuorumRequirement(
        sensitivity=Sensitivity.LOW,
        quorum_type=QuorumType.AUTO,
        min_approvers=0,
        require_identity_verification=False,
        cooldown_hours=0,
    ),
}


class QuorumPolicy:
    """Manages quorum requirements and voting for policy changes."""

    def __init__(self) -> None:
        self._requirements: dict[Sensitivity, QuorumRequirement] = dict(_DEFAULT_REQUIREMENTS)
        self._votes: dict[str, list[QuorumVote]] = {}
        self._results: list[QuorumResult] = []

    def get_requirement(self, sensitivity: Sensitivity) -> QuorumRequirement:
        return self._requirements[sensitivity]

    def set_requirement(self, requirement: QuorumRequirement) -> None:
        self._requirements[requirement.sensitivity] = requirement

    def cast_vote(
        self,
        proposal_id: str,
        voter: str,
        approved: bool,
        identity_verified: bool = False,
    ) -> QuorumVote:
        """Cast a vote on a proposal."""
        vote = QuorumVote(
            vote_id=f"vote-{uuid.uuid4().hex[:12]}",
            proposal_id=proposal_id,
            voter=voter,
            approved=approved,
            identity_verified=identity_verified,
        )
        if proposal_id not in self._votes:
            self._votes[proposal_id] = []
        # Replace existing vote from same voter
        self._votes[proposal_id] = [
            v for v in self._votes[proposal_id] if v.voter != voter
        ]
        self._votes[proposal_id].append(vote)
        return vote

    def check_quorum(self, proposal_id: str, sensitivity: Sensitivity) -> QuorumResult:
        """Check whether quorum is met for a proposal at a given sensitivity."""
        req = self._requirements[sensitivity]
        votes = self._votes.get(proposal_id, [])
        approvals = [v for v in votes if v.approved]
        rejections = [v for v in votes if not v.approved]

        # Auto quorum type always passes
        if req.quorum_type == QuorumType.AUTO:
            result = QuorumResult(
                proposal_id=proposal_id,
                quorum_met=True,
                quorum_type=req.quorum_type,
                required_approvers=0,
                actual_approvers=len(approvals),
                total_votes=len(votes),
                identity_check_passed=True,
                reason="auto-approved: low sensitivity",
            )
            self._results.append(result)
            return result

        # Identity verification check
        identity_ok = True
        if req.require_identity_verification:
            identity_ok = all(v.identity_verified for v in approvals) and len(approvals) > 0

        # Quorum check
        quorum_met = False
        reason = ""

        if req.quorum_type == QuorumType.UNANIMOUS:
            quorum_met = (
                len(approvals) >= req.min_approvers
                and len(rejections) == 0
                and identity_ok
            )
            if not quorum_met:
                parts = []
                if len(approvals) < req.min_approvers:
                    parts.append(f"need {req.min_approvers} approvers, have {len(approvals)}")
                if len(rejections) > 0:
                    parts.append(f"{len(rejections)} rejection(s) block unanimous")
                if not identity_ok:
                    parts.append("identity verification failed")
                reason = "unanimous not met: " + "; ".join(parts)
            else:
                reason = f"unanimous quorum met: {len(approvals)} approvers, 0 rejections"

        elif req.quorum_type == QuorumType.SUPERMAJORITY:
            total = len(approvals) + len(rejections)
            threshold = total * 2 / 3 if total > 0 else req.min_approvers
            quorum_met = (
                len(approvals) >= req.min_approvers
                and len(approvals) >= threshold
                and identity_ok
            )
            if not quorum_met:
                parts = []
                if len(approvals) < req.min_approvers:
                    parts.append(f"need {req.min_approvers} approvers, have {len(approvals)}")
                if total > 0 and len(approvals) < threshold:
                    parts.append(f"need 2/3 supermajority ({threshold:.0f}), have {len(approvals)}")
                if not identity_ok:
                    parts.append("identity verification failed")
                reason = "supermajority not met: " + "; ".join(parts)
            else:
                reason = f"supermajority met: {len(approvals)}/{total} approvers"

        elif req.quorum_type == QuorumType.SIMPLE_MAJORITY:
            total = len(approvals) + len(rejections)
            quorum_met = (
                len(approvals) >= req.min_approvers
                and (total == 0 or len(approvals) > total / 2)
            )
            if not quorum_met:
                reason = f"simple majority not met: {len(approvals)} approvals, {len(rejections)} rejections"
            else:
                reason = f"simple majority met: {len(approvals)}/{total}"

        elif req.quorum_type == QuorumType.SINGLE_APPROVER:
            quorum_met = len(approvals) >= 1 and identity_ok
            if not quorum_met:
                reason = "single approver required"
            else:
                reason = f"single approver: {approvals[0].voter}"

        result = QuorumResult(
            proposal_id=proposal_id,
            quorum_met=quorum_met,
            quorum_type=req.quorum_type,
            required_approvers=req.min_approvers,
            actual_approvers=len(approvals),
            total_votes=len(votes),
            identity_check_passed=identity_ok,
            reason=reason,
        )
        self._results.append(result)
        return result

    def get_votes(self, proposal_id: str) -> list[QuorumVote]:
        return list(self._votes.get(proposal_id, []))

    def get_results(self) -> list[QuorumResult]:
        return list(self._results)

    @property
    def total_votes(self) -> int:
        return sum(len(v) for v in self._votes.values())

    @property
    def result_count(self) -> int:
        return len(self._results)


_quorum: QuorumPolicy | None = None


def get_quorum_policy() -> QuorumPolicy:
    """Module singleton."""
    global _quorum
    if _quorum is None:
        _quorum = QuorumPolicy()
    return _quorum
