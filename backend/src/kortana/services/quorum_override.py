"""V9A — Quorum Override: multi-person approval for governance-grade overrides.

Instead of a single human override, quorum overrides require N-of-M
approvals from authorised operators before the override takes effect.
Each approval is individually signed.  Once the threshold is met the
pending override converts to a standard active override.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger("kortana.quorum_override")


# ---------------------------------------------------------------------------
# Approval record
# ---------------------------------------------------------------------------


def compute_approval_hash(
    override_id: str,
    approver: str,
    approved: bool,
    reason: str,
    timestamp: str,
) -> str:
    """SHA-256 hash over the approval fields for tamper evidence."""
    payload = json.dumps(
        {
            "override_id": override_id,
            "approver": approver,
            "approved": approved,
            "reason": reason,
            "timestamp": timestamp,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode()).hexdigest()


@dataclass
class ApprovalRecord:
    """A single approval or rejection of a pending quorum override."""

    override_id: str
    approver: str
    approved: bool
    reason: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    audit_hash: str = ""

    def __post_init__(self) -> None:
        if not self.audit_hash:
            self.audit_hash = compute_approval_hash(
                self.override_id,
                self.approver,
                self.approved,
                self.reason,
                self.timestamp,
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "override_id": self.override_id,
            "approver": self.approver,
            "approved": self.approved,
            "reason": self.reason,
            "timestamp": self.timestamp,
            "audit_hash": self.audit_hash,
        }


# ---------------------------------------------------------------------------
# Quorum policy
# ---------------------------------------------------------------------------


@dataclass
class QuorumPolicy:
    """Defines the approval requirements for a quorum override."""

    required_approvals: int = 2
    allowed_approvers: list[str] = field(default_factory=lambda: ["matt"])
    timeout_minutes: int = 60

    def to_dict(self) -> dict[str, Any]:
        return {
            "required_approvals": self.required_approvals,
            "allowed_approvers": self.allowed_approvers,
            "timeout_minutes": self.timeout_minutes,
        }


# ---------------------------------------------------------------------------
# Pending quorum override
# ---------------------------------------------------------------------------


@dataclass
class PendingQuorumOverride:
    """A quorum override collecting approvals before activation."""

    override_id: str
    mode: str
    reason: str
    policy: QuorumPolicy
    requested_by: str
    requested_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None
    approvals: list[ApprovalRecord] = field(default_factory=list)
    activated: bool = False
    activated_at: datetime | None = None
    rejected: bool = False
    rejected_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.expires_at is None:
            self.expires_at = self.requested_at + timedelta(
                minutes=self.policy.timeout_minutes,
            )

    @property
    def approval_count(self) -> int:
        return sum(1 for a in self.approvals if a.approved)

    @property
    def rejection_count(self) -> int:
        return sum(1 for a in self.approvals if not a.approved)

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at  # type: ignore[operator]

    @property
    def has_quorum(self) -> bool:
        return self.approval_count >= self.policy.required_approvals

    @property
    def is_resolved(self) -> bool:
        return self.activated or self.rejected or self.is_expired

    @property
    def status(self) -> str:
        if self.activated:
            return "activated"
        if self.rejected:
            return "rejected"
        if self.is_expired:
            return "expired"
        return "pending"

    def add_approval(self, approver: str, approved: bool, reason: str = "") -> ApprovalRecord:
        """Add an approval/rejection vote.

        Raises ValueError if the approver is not allowed or has already voted.
        """
        if approver not in self.policy.allowed_approvers:
            raise ValueError(f"Approver {approver!r} is not in allowed list")

        existing = [a for a in self.approvals if a.approver == approver]
        if existing:
            raise ValueError(f"Approver {approver!r} has already voted")

        if self.is_resolved:
            raise ValueError(f"Override {self.override_id} is already {self.status}")

        record = ApprovalRecord(
            override_id=self.override_id,
            approver=approver,
            approved=approved,
            reason=reason,
        )
        self.approvals.append(record)

        logger.info(
            "Quorum vote: %s %s override %s (reason: %s) — %d/%d approvals",
            approver,
            "approved" if approved else "rejected",
            self.override_id,
            reason,
            self.approval_count,
            self.policy.required_approvals,
        )

        return record

    def evaluate(self) -> str:
        """Check if the quorum threshold has been reached.

        Returns the new status: "activated", "rejected", "expired", or "pending".
        """
        if self.activated or self.rejected:
            return self.status

        if self.is_expired:
            return "expired"

        if self.has_quorum:
            self.activated = True
            self.activated_at = datetime.utcnow()
            logger.info("Quorum reached for override %s — activated", self.override_id)
            return "activated"

        # If remaining possible approvals can't reach quorum, auto-reject
        voted = len(self.approvals)
        remaining = len(self.policy.allowed_approvers) - voted
        if self.approval_count + remaining < self.policy.required_approvals:
            self.rejected = True
            self.rejected_at = datetime.utcnow()
            logger.info("Quorum impossible for override %s — rejected", self.override_id)
            return "rejected"

        return "pending"

    def to_dict(self) -> dict[str, Any]:
        return {
            "override_id": self.override_id,
            "mode": self.mode,
            "reason": self.reason,
            "requested_by": self.requested_by,
            "requested_at": self.requested_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "status": self.status,
            "policy": self.policy.to_dict(),
            "approvals": [a.to_dict() for a in self.approvals],
            "approval_count": self.approval_count,
            "rejection_count": self.rejection_count,
            "activated": self.activated,
            "activated_at": self.activated_at.isoformat() if self.activated_at else None,
        }


# ---------------------------------------------------------------------------
# Quorum manager
# ---------------------------------------------------------------------------


class QuorumManager:
    """Manages pending quorum overrides within a daemon process."""

    def __init__(self, default_policy: QuorumPolicy | None = None) -> None:
        self._pending: dict[str, PendingQuorumOverride] = {}
        self._history: list[PendingQuorumOverride] = []
        self._next_id: int = 1
        self.default_policy = default_policy or QuorumPolicy()

    def request(
        self,
        mode: str,
        reason: str,
        requested_by: str = "matt",
        policy: QuorumPolicy | None = None,
    ) -> PendingQuorumOverride:
        """Create a new pending quorum override request."""
        oid = f"qo-{self._next_id}"
        self._next_id += 1
        p = policy or self.default_policy

        pending = PendingQuorumOverride(
            override_id=oid,
            mode=mode,
            reason=reason,
            policy=p,
            requested_by=requested_by,
        )
        self._pending[oid] = pending
        logger.info(
            "Quorum override %s requested: mode=%s by=%s requires=%d/%d",
            oid, mode, requested_by, p.required_approvals, len(p.allowed_approvers),
        )
        return pending

    def vote(
        self,
        override_id: str,
        approver: str,
        approved: bool,
        reason: str = "",
    ) -> tuple[ApprovalRecord, str]:
        """Cast a vote on a pending quorum override.

        Returns (approval_record, new_status).
        Raises KeyError if override_id is not found.
        """
        pending = self._pending.get(override_id)
        if pending is None:
            raise KeyError(f"Quorum override {override_id!r} not found")

        record = pending.add_approval(approver, approved, reason)
        status = pending.evaluate()

        if status in ("activated", "rejected", "expired"):
            self._history.append(pending)
            del self._pending[override_id]

        return record, status

    def get(self, override_id: str) -> PendingQuorumOverride | None:
        """Look up a pending override by ID."""
        return self._pending.get(override_id)

    @property
    def pending(self) -> list[PendingQuorumOverride]:
        """Return all currently pending quorum overrides."""
        return list(self._pending.values())

    @property
    def history(self) -> list[dict[str, Any]]:
        """Return resolved overrides as dicts, newest first."""
        return [p.to_dict() for p in reversed(self._history)]

    @property
    def count(self) -> int:
        return len(self._pending)


# Module-level singleton
_manager = QuorumManager()


def get_quorum_manager() -> QuorumManager:
    """Return the module-level quorum manager singleton."""
    return _manager
