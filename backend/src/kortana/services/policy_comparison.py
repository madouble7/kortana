"""V9C — Policy Comparison: current vs proposed decision views.

Computes a side-by-side view of "what the daemon IS doing" versus
"what the daemon WOULD do" given current evidence.  Includes active
override status and drill health so operators see full context.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger("kortana.policy_comparison")


@dataclass
class PolicyComparison:
    """Side-by-side comparison of current and proposed policy decisions."""

    # Current state
    current_mode: str
    current_reasons: list[str] = field(default_factory=list)

    # Proposed state (what actuation would decide right now)
    proposed_action: str = "hold"  # escalate | de-escalate | hold
    proposed_mode: str = ""
    proposed_reasons: list[str] = field(default_factory=list)

    # Override context
    override_active: bool = False
    override_mode: str | None = None
    override_by: str | None = None
    override_expires: str | None = None
    override_blocking: bool = False

    # Quorum context
    quorum_pending: int = 0
    quorum_details: list[dict[str, Any]] = field(default_factory=list)

    # Rollback context
    rollback_would_trigger: bool = False
    rollback_to_mode: str | None = None

    # Drill health
    drill_slo_results: list[dict[str, Any]] = field(default_factory=list)
    drills_healthy: bool = True

    # Policy version
    policy_version: int | None = None
    policy_hash: str | None = None

    # Computed
    decision_differs: bool = False
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "current": {
                "mode": self.current_mode,
                "reasons": self.current_reasons,
            },
            "proposed": {
                "action": self.proposed_action,
                "mode": self.proposed_mode,
                "reasons": self.proposed_reasons,
            },
            "override": {
                "active": self.override_active,
                "mode": self.override_mode,
                "by": self.override_by,
                "expires": self.override_expires,
                "blocking": self.override_blocking,
            },
            "quorum": {
                "pending_count": self.quorum_pending,
                "details": self.quorum_details,
            },
            "rollback": {
                "would_trigger": self.rollback_would_trigger,
                "to_mode": self.rollback_to_mode,
            },
            "drill_health": {
                "healthy": self.drills_healthy,
                "slo_results": self.drill_slo_results,
            },
            "policy": {
                "version": self.policy_version,
                "hash": self.policy_hash,
            },
            "decision_differs": self.decision_differs,
            "timestamp": self.timestamp,
        }


def compute_policy_comparison(
    current_mode: str,
    recent_runs: list[dict[str, Any]],
    *,
    min_consecutive_promoted: int = 3,
    max_mode: str = "auto",
    override: Any | None = None,
    quorum_pending: list[Any] | None = None,
    latest_canary: dict[str, Any] | None = None,
    pre_actuation_mode: str | None = None,
    drill_slo_results: list[dict[str, Any]] | None = None,
    policy_version: int | None = None,
    policy_hash: str | None = None,
) -> PolicyComparison:
    """Build a PolicyComparison from current system state.

    Evaluates what the actuation engine would propose, checks override
    status, rollback conditions, and drill SLOs.
    """
    from src.kortana.services.auto_actuator import evaluate_actuation

    # --- Proposed decision ---
    decision = evaluate_actuation(
        current_mode,
        recent_runs,
        min_consecutive_promoted=min_consecutive_promoted,
        max_mode=max_mode,
    )

    comp = PolicyComparison(
        current_mode=current_mode,
        current_reasons=[f"Daemon is in {current_mode} mode"],
        proposed_action=decision.action,
        proposed_mode=decision.to_mode,
        proposed_reasons=decision.reasons,
        decision_differs=(decision.to_mode != current_mode),
        policy_version=policy_version,
        policy_hash=policy_hash,
    )

    # --- Override context ---
    if override is not None:
        is_active = getattr(override, "is_active", False)
        comp.override_active = is_active
        comp.override_mode = getattr(override, "mode", None)
        comp.override_by = getattr(override, "created_by", None)
        exp = getattr(override, "expires_at", None)
        comp.override_expires = exp.isoformat() if exp else None
        if is_active and comp.override_mode != decision.to_mode:
            comp.override_blocking = True

    # --- Quorum context ---
    if quorum_pending:
        comp.quorum_pending = len(quorum_pending)
        comp.quorum_details = [
            getattr(q, "to_dict", lambda: {})() for q in quorum_pending
        ]

    # --- Rollback context ---
    if latest_canary is not None:
        from src.kortana.services.rollback_engine import evaluate_rollback

        pre_mode = pre_actuation_mode or current_mode
        rb = evaluate_rollback(
            current_mode=current_mode,
            pre_actuation_mode=pre_mode,
            latest_canary=latest_canary,
            deploy_allowed=True,
        )
        comp.rollback_would_trigger = rb.should_rollback
        comp.rollback_to_mode = rb.to_mode

    # --- Drill health ---
    if drill_slo_results:
        comp.drill_slo_results = drill_slo_results
        comp.drills_healthy = all(
            r.get("met", True) for r in drill_slo_results
        )

    return comp
