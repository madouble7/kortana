"""V10C — Deploy Gate: branch/deploy protections consuming governance state.

Evaluates whether a deployment should be allowed based on:
- operator identity + permissions
- active human or quorum overrides
- drill SLO health
- rollback cooldown state
- policy version requirements
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger("kortana.deploy_gate")


# ---------------------------------------------------------------------------
# Gate check result
# ---------------------------------------------------------------------------


@dataclass
class GateCheck:
    """A single prerequisite check for the deploy gate."""

    name: str
    passed: bool
    reason: str
    severity: str = "blocking"  # blocking | warning | info

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "reason": self.reason,
            "severity": self.severity,
        }


@dataclass
class DeployGateResult:
    """Aggregate result of all deploy gate checks."""

    allowed: bool
    checks: list[GateCheck] = field(default_factory=list)
    operator_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    gate_hash: str = ""

    def __post_init__(self) -> None:
        if not self.gate_hash:
            self.gate_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        payload = json.dumps(
            {
                "allowed": self.allowed,
                "checks": [c.to_dict() for c in self.checks],
                "operator_id": self.operator_id,
                "timestamp": self.timestamp,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    @property
    def blocking_failures(self) -> list[GateCheck]:
        return [c for c in self.checks if not c.passed and c.severity == "blocking"]

    @property
    def warnings(self) -> list[GateCheck]:
        return [c for c in self.checks if not c.passed and c.severity == "warning"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "checks": [c.to_dict() for c in self.checks],
            "blocking_failures": [c.to_dict() for c in self.blocking_failures],
            "warnings": [c.to_dict() for c in self.warnings],
            "operator_id": self.operator_id,
            "timestamp": self.timestamp,
            "gate_hash": self.gate_hash,
        }


# ---------------------------------------------------------------------------
# Gate evaluator
# ---------------------------------------------------------------------------


def evaluate_deploy_gate(
    operator_id: str,
    *,
    target_mode: str | None = None,
    current_mode: str = "manual",
    # Override state
    active_override_mode: str | None = None,
    # Quorum state
    quorum_pending_count: int = 0,
    # Drill SLO state
    drill_slo_results: list[dict[str, Any]] | None = None,
    # Rollback state
    in_cooldown: bool = False,
    rate_limit_blocked: bool = False,
    # Policy state
    policy_version: int | None = None,
    min_policy_version: int | None = None,
) -> DeployGateResult:
    """Evaluate all deploy gate checks and return the aggregate result.

    Each check is independent; the gate passes only if all blocking
    checks pass.
    """
    checks: list[GateCheck] = []

    # 1. Operator identity + permission check
    from src.kortana.services.operator_identity import Permission, get_operator_registry

    registry = get_operator_registry()
    operator = registry.get(operator_id)

    if operator is None:
        checks.append(GateCheck(
            name="operator_identity",
            passed=False,
            reason=f"Operator {operator_id!r} not found in registry",
        ))
    elif not operator.active:
        checks.append(GateCheck(
            name="operator_identity",
            passed=False,
            reason=f"Operator {operator_id!r} is deactivated",
        ))
    else:
        perm_check = registry.check(operator_id, Permission.DEPLOY_GATE)
        checks.append(GateCheck(
            name="operator_identity",
            passed=perm_check.allowed,
            reason=perm_check.reason,
        ))

    # 2. Override conflict check
    if active_override_mode is not None:
        if target_mode and target_mode != active_override_mode:
            checks.append(GateCheck(
                name="override_conflict",
                passed=False,
                reason=(
                    f"Active override locks mode to {active_override_mode!r}, "
                    f"cannot deploy to {target_mode!r}"
                ),
            ))
        else:
            checks.append(GateCheck(
                name="override_conflict",
                passed=True,
                reason="No override conflict",
            ))
    else:
        checks.append(GateCheck(
            name="override_conflict",
            passed=True,
            reason="No active override",
        ))

    # 3. Pending quorum check (warning — deploy during pending quorum is risky)
    if quorum_pending_count > 0:
        checks.append(GateCheck(
            name="quorum_pending",
            passed=False,
            reason=f"{quorum_pending_count} quorum override(s) pending — deploy may conflict",
            severity="warning",
        ))
    else:
        checks.append(GateCheck(
            name="quorum_pending",
            passed=True,
            reason="No pending quorum overrides",
            severity="warning",
        ))

    # 4. Drill SLO health
    if drill_slo_results:
        violated = [r for r in drill_slo_results if not r.get("met", True)]
        if violated:
            scenarios = ", ".join(r.get("scenario", "?") for r in violated)
            checks.append(GateCheck(
                name="drill_slo_health",
                passed=False,
                reason=f"Drill SLOs violated: {scenarios}",
            ))
        else:
            checks.append(GateCheck(
                name="drill_slo_health",
                passed=True,
                reason="All drill SLOs met",
            ))
    else:
        checks.append(GateCheck(
            name="drill_slo_health",
            passed=True,
            reason="No drill SLOs configured",
            severity="info",
        ))

    # 5. Rollback cooldown
    if in_cooldown:
        checks.append(GateCheck(
            name="rollback_cooldown",
            passed=False,
            reason="Rollback cooldown is active — recent rollback prevents deploy",
        ))
    else:
        checks.append(GateCheck(
            name="rollback_cooldown",
            passed=True,
            reason="No rollback cooldown",
        ))

    # 6. Rate limit
    if rate_limit_blocked:
        checks.append(GateCheck(
            name="rate_limit",
            passed=False,
            reason="Actuation rate limit reached — too many recent changes",
        ))
    else:
        checks.append(GateCheck(
            name="rate_limit",
            passed=True,
            reason="Rate limit not exceeded",
        ))

    # 7. Policy version check
    if min_policy_version is not None and policy_version is not None:
        if policy_version < min_policy_version:
            checks.append(GateCheck(
                name="policy_version",
                passed=False,
                reason=(
                    f"Policy version {policy_version} is below minimum "
                    f"required {min_policy_version}"
                ),
            ))
        else:
            checks.append(GateCheck(
                name="policy_version",
                passed=True,
                reason=f"Policy version {policy_version} meets minimum {min_policy_version}",
            ))
    else:
        checks.append(GateCheck(
            name="policy_version",
            passed=True,
            reason="No policy version requirement",
            severity="info",
        ))

    # Aggregate: allowed if all blocking checks pass
    blocking = [c for c in checks if c.severity == "blocking"]
    allowed = all(c.passed for c in blocking)

    result = DeployGateResult(
        allowed=allowed,
        checks=checks,
        operator_id=operator_id,
    )

    logger.info(
        "Deploy gate: %s for %s — %d checks, %d blocking failures",
        "ALLOWED" if allowed else "DENIED",
        operator_id,
        len(checks),
        len(result.blocking_failures),
    )

    return result
