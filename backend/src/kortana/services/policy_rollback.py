"""V21C — policy rollback: reversible policy changes with rollback points."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class RollbackPoint:
    """Snapshot of policy state before and after a promoted change."""

    point_id: str
    proposal_id: str
    prior_state: dict[str, Any]
    applied_state: dict[str, Any]
    created_at: str = ""
    rolled_back: bool = False
    rolled_back_at: str = ""
    rollback_reason: str = ""
    rollback_hash: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.rollback_hash:
            blob = f"{self.point_id}:{self.proposal_id}:{sorted(self.prior_state.keys())}"
            self.rollback_hash = hashlib.sha256(blob.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "point_id": self.point_id,
            "proposal_id": self.proposal_id,
            "prior_state": self.prior_state,
            "applied_state": self.applied_state,
            "created_at": self.created_at,
            "rolled_back": self.rolled_back,
            "rolled_back_at": self.rolled_back_at,
            "rollback_reason": self.rollback_reason,
            "rollback_hash": self.rollback_hash,
        }


class PolicyRollback:
    """Manages rollback points for promoted policy changes."""

    def __init__(self) -> None:
        self._points: dict[str, RollbackPoint] = {}
        self._history: list[dict[str, Any]] = []

    def create_point(
        self,
        proposal_id: str,
        prior_state: dict[str, Any],
        applied_state: dict[str, Any],
    ) -> RollbackPoint:
        """Create a rollback point when a proposal is promoted."""
        point = RollbackPoint(
            point_id=f"rb-{uuid.uuid4().hex[:12]}",
            proposal_id=proposal_id,
            prior_state=dict(prior_state),
            applied_state=dict(applied_state),
        )
        self._points[point.point_id] = point
        self._record("created", point)
        return point

    def rollback(self, point_id: str, reason: str = "") -> RollbackPoint | None:
        """Execute a rollback, restoring prior state."""
        point = self._points.get(point_id)
        if point is None:
            return None
        if point.rolled_back:
            return None
        point.rolled_back = True
        point.rolled_back_at = datetime.now(timezone.utc).isoformat()
        point.rollback_reason = reason
        self._record("rolled_back", point, reason=reason)
        return point

    def can_rollback(self, point_id: str) -> bool:
        """Check if a rollback point can be rolled back."""
        point = self._points.get(point_id)
        if point is None:
            return False
        return not point.rolled_back

    def get_point(self, point_id: str) -> RollbackPoint | None:
        return self._points.get(point_id)

    def get_point_for_proposal(self, proposal_id: str) -> RollbackPoint | None:
        """Find rollback point for a specific proposal."""
        for p in self._points.values():
            if p.proposal_id == proposal_id:
                return p
        return None

    def get_active_points(self) -> list[RollbackPoint]:
        """Get rollback points that have not been rolled back."""
        return [p for p in self._points.values() if not p.rolled_back]

    def get_history(self) -> list[dict[str, Any]]:
        return list(self._history)

    @property
    def point_count(self) -> int:
        return len(self._points)

    @property
    def active_count(self) -> int:
        return len(self.get_active_points())

    def _record(self, action: str, point: RollbackPoint, **extra: Any) -> None:
        entry = {
            "action": action,
            "point_id": point.point_id,
            "proposal_id": point.proposal_id,
            "rolled_back": point.rolled_back,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **extra,
        }
        self._history.append(entry)


_rollback: PolicyRollback | None = None


def get_policy_rollback() -> PolicyRollback:
    """Module singleton."""
    global _rollback
    if _rollback is None:
        _rollback = PolicyRollback()
    return _rollback
