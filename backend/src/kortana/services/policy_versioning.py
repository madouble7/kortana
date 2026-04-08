"""V8B — Policy Versioning: immutable policy snapshots with diff and replay.

Every policy configuration change is captured as a numbered version.
Decisions reference their policy version.  Operators can diff versions
and replay historical decisions under a new policy to understand
"what would have happened."
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger("kortana.policy_versioning")


# ---------------------------------------------------------------------------
# Policy snapshot
# ---------------------------------------------------------------------------


@dataclass
class PolicySnapshot:
    """Immutable snapshot of the active rollout policy configuration."""

    version: int
    cooldown_seconds: int
    max_changes_per_window: int
    window_seconds: int
    min_consecutive_promoted: int
    max_mode: str
    auto_rollback_enabled: bool
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    created_by: str = "daemon"
    commit_sha: str | None = None
    content_hash: str = ""

    def __post_init__(self) -> None:
        if not self.content_hash:
            self.content_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """SHA-256 over the policy content (not metadata)."""
        payload = {
            "cooldown_seconds": self.cooldown_seconds,
            "max_changes_per_window": self.max_changes_per_window,
            "window_seconds": self.window_seconds,
            "min_consecutive_promoted": self.min_consecutive_promoted,
            "max_mode": self.max_mode,
            "auto_rollback_enabled": self.auto_rollback_enabled,
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a dict suitable for storage or API response."""
        return {
            "version": self.version,
            "cooldown_seconds": self.cooldown_seconds,
            "max_changes_per_window": self.max_changes_per_window,
            "window_seconds": self.window_seconds,
            "min_consecutive_promoted": self.min_consecutive_promoted,
            "max_mode": self.max_mode,
            "auto_rollback_enabled": self.auto_rollback_enabled,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "commit_sha": self.commit_sha,
            "content_hash": self.content_hash,
        }


# ---------------------------------------------------------------------------
# Diff
# ---------------------------------------------------------------------------


@dataclass
class PolicyDiff:
    """Describes differences between two policy versions."""

    from_version: int
    to_version: int
    changes: list[dict[str, Any]]  # [{field, old, new}, ...]

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0


_DIFF_FIELDS = [
    "cooldown_seconds",
    "max_changes_per_window",
    "window_seconds",
    "min_consecutive_promoted",
    "max_mode",
    "auto_rollback_enabled",
]


def diff_policies(a: PolicySnapshot, b: PolicySnapshot) -> PolicyDiff:
    """Compute the diff between two policy snapshots.

    Only compares policy-content fields, not metadata like
    created_at or created_by.
    """
    changes: list[dict[str, Any]] = []
    for f in _DIFF_FIELDS:
        va = getattr(a, f)
        vb = getattr(b, f)
        if va != vb:
            changes.append({"field": f, "old": va, "new": vb})
    return PolicyDiff(from_version=a.version, to_version=b.version, changes=changes)


# ---------------------------------------------------------------------------
# Replay
# ---------------------------------------------------------------------------


@dataclass
class ReplayResult:
    """Result of replaying historical decisions under a policy."""

    policy_version: int
    total_decisions: int
    outcomes: list[dict[str, Any]]
    changed_count: int  # how many would have been different


def replay_decisions(
    policy: PolicySnapshot,
    historical_runs: list[dict[str, Any]],
) -> ReplayResult:
    """Replay canary evidence against a policy to see what would have happened.

    For each window of runs, evaluates escalation/de-escalation
    using the given policy's parameters and compares with the
    actual decision (if stored in the run dict as 'actual_action').
    """
    from src.kortana.services.auto_actuator import evaluate_actuation, _MODE_ORDER

    outcomes: list[dict[str, Any]] = []
    changed = 0
    current_mode = _MODE_ORDER[0]  # start at lowest

    # Walk through runs oldest-first
    ordered = list(reversed(historical_runs))

    for i, run in enumerate(ordered):
        window = list(reversed(ordered[max(0, i - policy.min_consecutive_promoted + 1):i + 1]))

        decision = evaluate_actuation(
            current_mode,
            window,
            min_consecutive_promoted=policy.min_consecutive_promoted,
            max_mode=policy.max_mode,
        )

        actual = run.get("actual_action", None)
        would_differ = actual is not None and actual != decision.action

        outcome = {
            "run_index": i,
            "current_mode": current_mode,
            "action": decision.action,
            "to_mode": decision.to_mode,
            "reasons": decision.reasons,
            "actual_action": actual,
            "would_differ": would_differ,
        }
        outcomes.append(outcome)

        if would_differ:
            changed += 1

        # Apply the decision for next iteration
        if decision.action in ("escalate", "de-escalate"):
            current_mode = decision.to_mode

    return ReplayResult(
        policy_version=policy.version,
        total_decisions=len(outcomes),
        outcomes=outcomes,
        changed_count=changed,
    )


# ---------------------------------------------------------------------------
# In-memory policy registry (for the daemon process)
# ---------------------------------------------------------------------------


class PolicyRegistry:
    """Ordered registry of policy versions within a daemon process.

    Backed by the database for persistence; this provides fast
    in-process access and version-bump semantics.
    """

    def __init__(self) -> None:
        self._versions: list[PolicySnapshot] = []
        self._current: PolicySnapshot | None = None

    @property
    def current(self) -> PolicySnapshot | None:
        return self._current

    @property
    def version_count(self) -> int:
        return len(self._versions)

    def register(self, snapshot: PolicySnapshot) -> None:
        """Add a new version and make it current."""
        self._versions.append(snapshot)
        self._current = snapshot
        logger.info(
            "Policy v%d registered (hash=%s, by=%s)",
            snapshot.version, snapshot.content_hash[:12], snapshot.created_by,
        )

    def get_version(self, version: int) -> PolicySnapshot | None:
        """Retrieve a specific version."""
        for s in self._versions:
            if s.version == version:
                return s
        return None

    def latest_version_number(self) -> int:
        """Return the highest version number, or 0 if none."""
        if not self._versions:
            return 0
        return self._versions[-1].version

    def diff(self, from_v: int, to_v: int) -> PolicyDiff | None:
        """Compute the diff between two registered versions."""
        a = self.get_version(from_v)
        b = self.get_version(to_v)
        if a is None or b is None:
            return None
        return diff_policies(a, b)

    def history(self) -> list[dict[str, Any]]:
        """Return all versions as dicts, newest first."""
        return [s.to_dict() for s in reversed(self._versions)]


# Module-level singleton
_registry = PolicyRegistry()


def get_policy_registry() -> PolicyRegistry:
    """Return the module-level policy registry singleton."""
    return _registry
