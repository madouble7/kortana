"""V7 — Automatic Actuation: closed-loop autonomy control.

Makes approved rollout decisions automatically change daemon mode.
Every decision is signed with an audit hash for tamper evidence.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger("kortana.auto_actuator")


# ---------------------------------------------------------------------------
# Mode ordering
# ---------------------------------------------------------------------------

_MODE_ORDER: list[str] = ["manual", "self-aware", "auto"]


def _mode_rank(mode: str) -> int:
    """Return the ordinal rank of an approval mode."""
    try:
        return _MODE_ORDER.index(mode)
    except ValueError:
        return 0


def _next_mode(mode: str) -> str:
    """Return the next higher approval mode, capped at max."""
    rank = _mode_rank(mode)
    return _MODE_ORDER[min(rank + 1, len(_MODE_ORDER) - 1)]


def _prev_mode(mode: str) -> str:
    """Return the next lower approval mode, capped at min."""
    rank = _mode_rank(mode)
    return _MODE_ORDER[max(rank - 1, 0)]


# ---------------------------------------------------------------------------
# Actuation decision
# ---------------------------------------------------------------------------


@dataclass
class ActuationDecision:
    """A signed policy decision produced by the auto-actuation engine."""

    action: str  # "escalate", "de-escalate", "hold"
    from_mode: str
    to_mode: str
    reasons: list[str] = field(default_factory=list)
    actor: str = "daemon"  # "daemon", "human", "ci"
    decision_type: str = "escalation"  # "escalation", "deployment", "alert"
    commit_sha: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    audit_hash: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.audit_hash:
            self.audit_hash = compute_audit_hash(self)


def compute_audit_hash(decision: ActuationDecision) -> str:
    """Compute a SHA-256 audit hash over decision fields.

    Provides tamper evidence for policy decision records.
    The hash covers all decision fields except the hash itself.
    """
    payload = {
        "action": decision.action,
        "from_mode": decision.from_mode,
        "to_mode": decision.to_mode,
        "reasons": decision.reasons,
        "actor": decision.actor,
        "decision_type": decision.decision_type,
        "commit_sha": decision.commit_sha,
        "timestamp": decision.timestamp,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Auto-escalation evaluation
# ---------------------------------------------------------------------------


def evaluate_auto_escalation(
    current_mode: str,
    recent_runs: list[dict[str, Any]],
    *,
    min_consecutive_promoted: int = 3,
    max_mode: str = "auto",
) -> ActuationDecision:
    """Evaluate whether the daemon should auto-escalate its approval mode.

    Rules:
    1. Already at max mode → hold.
    2. Fewer than min_consecutive_promoted recent promoted runs → hold.
    3. All N most-recent runs must be promoted + adaptive → escalate.
    """
    target = _next_mode(current_mode)

    if _mode_rank(current_mode) >= _mode_rank(max_mode):
        return ActuationDecision(
            action="hold",
            from_mode=current_mode,
            to_mode=current_mode,
            reasons=[f"Already at max mode ({max_mode})"],
        )

    if len(recent_runs) < min_consecutive_promoted:
        return ActuationDecision(
            action="hold",
            from_mode=current_mode,
            to_mode=current_mode,
            reasons=[
                f"Need {min_consecutive_promoted} consecutive promoted runs, "
                f"only have {len(recent_runs)} total"
            ],
        )

    # Check the most recent N runs are all promoted
    check_window = recent_runs[:min_consecutive_promoted]
    all_promoted = all(
        r.get("promotion_status") == "promoted" for r in check_window
    )
    all_adaptive = all(
        r.get("verdict") == "adaptive" for r in check_window
    )

    if not all_promoted:
        return ActuationDecision(
            action="hold",
            from_mode=current_mode,
            to_mode=current_mode,
            reasons=["Not all recent runs are promoted"],
        )

    if not all_adaptive:
        return ActuationDecision(
            action="hold",
            from_mode=current_mode,
            to_mode=current_mode,
            reasons=["Not all recent runs have adaptive verdict"],
        )

    commit = check_window[0].get("commit_sha") if check_window else None

    return ActuationDecision(
        action="escalate",
        from_mode=current_mode,
        to_mode=target,
        reasons=[
            f"{min_consecutive_promoted} consecutive promoted+adaptive runs detected",
            f"Auto-escalating from {current_mode} to {target}",
        ],
        commit_sha=commit,
    )


# ---------------------------------------------------------------------------
# Auto-de-escalation evaluation
# ---------------------------------------------------------------------------


def evaluate_auto_de_escalation(
    current_mode: str,
    latest_run: dict[str, Any] | None,
) -> ActuationDecision:
    """Evaluate whether the daemon should auto-de-escalate.

    Rules:
    1. No latest run → de-escalate (safety).
    2. Latest run is rejected → de-escalate.
    3. Latest verdict is static → de-escalate.
    4. Otherwise → hold.
    """
    target = _prev_mode(current_mode)

    if current_mode == _MODE_ORDER[0]:
        return ActuationDecision(
            action="hold",
            from_mode=current_mode,
            to_mode=current_mode,
            reasons=["Already at lowest mode"],
        )

    if latest_run is None:
        return ActuationDecision(
            action="de-escalate",
            from_mode=current_mode,
            to_mode=target,
            reasons=["No canary run available — de-escalating for safety"],
        )

    if latest_run.get("promotion_status") == "rejected":
        return ActuationDecision(
            action="de-escalate",
            from_mode=current_mode,
            to_mode=target,
            reasons=[
                "Latest canary run was rejected",
                f"De-escalating from {current_mode} to {target}",
            ],
            commit_sha=latest_run.get("commit_sha"),
        )

    if latest_run.get("verdict") == "static":
        return ActuationDecision(
            action="de-escalate",
            from_mode=current_mode,
            to_mode=target,
            reasons=[
                "Latest canary verdict is static",
                f"De-escalating from {current_mode} to {target}",
            ],
            commit_sha=latest_run.get("commit_sha"),
        )

    return ActuationDecision(
        action="hold",
        from_mode=current_mode,
        to_mode=current_mode,
        reasons=["Latest run is healthy — no de-escalation needed"],
    )


# ---------------------------------------------------------------------------
# Combined evaluation
# ---------------------------------------------------------------------------


def evaluate_actuation(
    current_mode: str,
    recent_runs: list[dict[str, Any]],
    *,
    min_consecutive_promoted: int = 3,
    max_mode: str = "auto",
) -> ActuationDecision:
    """Run the full actuation pipeline: check de-escalation first, then escalation.

    De-escalation takes priority since it is a safety action.
    """
    latest = recent_runs[0] if recent_runs else None

    # Safety first: check de-escalation
    de_esc = evaluate_auto_de_escalation(current_mode, latest)
    if de_esc.action == "de-escalate":
        return de_esc

    # Then check escalation
    return evaluate_auto_escalation(
        current_mode, recent_runs,
        min_consecutive_promoted=min_consecutive_promoted,
        max_mode=max_mode,
    )


def apply_actuation(
    daemon: Any,
    decision: ActuationDecision,
) -> bool:
    """Apply an actuation decision to the daemon.

    Returns True if the mode was changed, False if held.
    """
    if decision.action == "hold":
        logger.info(
            "Actuation HOLD: %s stays at %s — %s",
            decision.actor, decision.from_mode, "; ".join(decision.reasons),
        )
        return False

    old_mode = daemon.default_approval_mode
    daemon.default_approval_mode = decision.to_mode

    logger.warning(
        "Actuation %s: %s -> %s (actor=%s, hash=%s) — %s",
        decision.action.upper(),
        old_mode,
        decision.to_mode,
        decision.actor,
        decision.audit_hash[:12],
        "; ".join(decision.reasons),
    )
    return True


def decision_to_log_dict(decision: ActuationDecision) -> dict[str, Any]:
    """Convert an ActuationDecision to a dict suitable for PolicyDecisionLog."""
    return {
        "decision_type": decision.decision_type,
        "actor": decision.actor,
        "action": decision.action,
        "from_state": decision.from_mode,
        "to_state": decision.to_mode,
        "reasons": decision.reasons,
        "audit_hash": decision.audit_hash,
        "commit_sha": decision.commit_sha,
        "extra_metadata": decision.metadata,
    }
