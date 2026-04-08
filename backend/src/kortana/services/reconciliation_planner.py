"""V18B — Reconciliation Planner: targeted recovery plan generation."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from src.kortana.services.drift_detector import DriftSignal, DriftType, DriftSeverity


# ── Enums ─────────────────────────────────────────────────────────────────


class ReconciliationActionType(Enum):
    """Types of reconciliation actions."""

    REDEPLOY = "redeploy"
    RECONNECT = "reconnect"
    REVERIFY = "reverify"
    PATCH_CONFIG = "patch_config"
    RESEAL_EVIDENCE = "reseal_evidence"
    RESTART_ROLLOUT = "restart_rollout"
    FORCE_HEALTH_CHECK = "force_health_check"
    ESCALATE_HUMAN = "escalate_human"


class PlanPriority(Enum):
    """Priority levels for reconciliation plans."""

    IMMEDIATE = "immediate"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    DEFERRED = "deferred"


class PlanStatus(Enum):
    """Status of a reconciliation plan."""

    CREATED = "created"
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ── Severity to priority mapping ─────────────────────────────────────────

_SEVERITY_PRIORITY: dict[DriftSeverity, PlanPriority] = {
    DriftSeverity.CRITICAL: PlanPriority.IMMEDIATE,
    DriftSeverity.HIGH: PlanPriority.HIGH,
    DriftSeverity.MEDIUM: PlanPriority.NORMAL,
    DriftSeverity.LOW: PlanPriority.LOW,
}

# ── Drift type to action mapping ─────────────────────────────────────────

_DRIFT_ACTIONS: dict[DriftType, list[ReconciliationActionType]] = {
    DriftType.VERSION_MISMATCH: [ReconciliationActionType.REDEPLOY, ReconciliationActionType.REVERIFY],
    DriftType.CONFIG_DRIFT: [ReconciliationActionType.PATCH_CONFIG, ReconciliationActionType.FORCE_HEALTH_CHECK],
    DriftType.CONNECTION_LOST: [ReconciliationActionType.RECONNECT, ReconciliationActionType.FORCE_HEALTH_CHECK],
    DriftType.HEALTH_DEGRADED: [ReconciliationActionType.FORCE_HEALTH_CHECK, ReconciliationActionType.REDEPLOY],
    DriftType.EVIDENCE_GAP: [ReconciliationActionType.RESEAL_EVIDENCE, ReconciliationActionType.REVERIFY],
    DriftType.ROLLOUT_STALLED: [ReconciliationActionType.RESTART_ROLLOUT, ReconciliationActionType.FORCE_HEALTH_CHECK],
}


# ── Data structures ───────────────────────────────────────────────────────


@dataclass
class ReconciliationAction:
    """A single action within a reconciliation plan."""

    action_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    action_type: ReconciliationActionType = ReconciliationActionType.FORCE_HEALTH_CHECK
    target_provider: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    priority: PlanPriority = PlanPriority.NORMAL
    estimated_impact: str = "low"
    source_drift_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "target_provider": self.target_provider,
            "parameters": self.parameters,
            "priority": self.priority.value,
            "estimated_impact": self.estimated_impact,
            "source_drift_id": self.source_drift_id,
        }


@dataclass
class ReconciliationPlan:
    """A structured plan for reconciling detected drift."""

    plan_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    status: PlanStatus = PlanStatus.CREATED
    priority: PlanPriority = PlanPriority.NORMAL
    drift_signal_ids: list[str] = field(default_factory=list)
    actions: list[ReconciliationAction] = field(default_factory=list)
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: str = ""
    plan_hash: str = ""

    def __post_init__(self) -> None:
        if not self.plan_hash:
            raw = f"{self.plan_id}:{self.priority.value}:{','.join(self.drift_signal_ids)}:{self.created_at}"
            self.plan_hash = hashlib.sha256(raw.encode()).hexdigest()

    @property
    def action_count(self) -> int:
        return len(self.actions)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "status": self.status.value,
            "priority": self.priority.value,
            "drift_signal_ids": self.drift_signal_ids,
            "actions": [a.to_dict() for a in self.actions],
            "description": self.description,
            "action_count": self.action_count,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "plan_hash": self.plan_hash,
        }


# ── Reconciliation Planner ────────────────────────────────────────────────


class ReconciliationPlanner:
    """Generates targeted reconciliation plans from drift signals."""

    def __init__(self) -> None:
        self._plans: list[ReconciliationPlan] = []

    def plan_from_drift(self, signal: DriftSignal) -> ReconciliationPlan:
        """Generate a reconciliation plan from a single drift signal."""
        priority = _SEVERITY_PRIORITY.get(signal.severity, PlanPriority.NORMAL)
        action_types = _DRIFT_ACTIONS.get(signal.drift_type, [ReconciliationActionType.ESCALATE_HUMAN])

        actions: list[ReconciliationAction] = []
        for at in action_types:
            action = ReconciliationAction(
                action_type=at,
                target_provider=signal.provider_name,
                priority=priority,
                estimated_impact=self._estimate_impact(at),
                source_drift_id=signal.signal_id,
                parameters=self._build_parameters(at, signal),
            )
            actions.append(action)

        plan = ReconciliationPlan(
            priority=priority,
            drift_signal_ids=[signal.signal_id],
            actions=actions,
            description=f"Reconcile {signal.drift_type.value} on {signal.provider_name or 'system'}",
        )
        self._plans.append(plan)
        return plan

    def plan_from_batch(self, signals: list[DriftSignal]) -> ReconciliationPlan:
        """Generate a single reconciliation plan from multiple drift signals."""
        if not signals:
            plan = ReconciliationPlan(description="Empty batch — no drifts")
            self._plans.append(plan)
            return plan

        # Use highest severity as plan priority
        max_severity = max(signals, key=lambda s: list(DriftSeverity).index(s.severity))
        priority = _SEVERITY_PRIORITY.get(max_severity.severity, PlanPriority.NORMAL)

        actions: list[ReconciliationAction] = []
        drift_ids: list[str] = []
        for sig in signals:
            drift_ids.append(sig.signal_id)
            action_types = _DRIFT_ACTIONS.get(sig.drift_type, [ReconciliationActionType.ESCALATE_HUMAN])
            for at in action_types:
                action = ReconciliationAction(
                    action_type=at,
                    target_provider=sig.provider_name,
                    priority=_SEVERITY_PRIORITY.get(sig.severity, PlanPriority.NORMAL),
                    estimated_impact=self._estimate_impact(at),
                    source_drift_id=sig.signal_id,
                    parameters=self._build_parameters(at, sig),
                )
                actions.append(action)

        plan = ReconciliationPlan(
            priority=priority,
            drift_signal_ids=drift_ids,
            actions=actions,
            description=f"Batch reconciliation for {len(signals)} drift(s)",
        )
        self._plans.append(plan)
        return plan

    def approve_plan(self, plan_id: str) -> bool:
        plan = self.get_plan(plan_id)
        if plan and plan.status == PlanStatus.CREATED:
            plan.status = PlanStatus.APPROVED
            return True
        return False

    def cancel_plan(self, plan_id: str) -> bool:
        plan = self.get_plan(plan_id)
        if plan and plan.status in (PlanStatus.CREATED, PlanStatus.APPROVED):
            plan.status = PlanStatus.CANCELLED
            return True
        return False

    # ── queries ───────────────────────────────────────────────────────

    def get_plan(self, plan_id: str) -> ReconciliationPlan | None:
        for p in self._plans:
            if p.plan_id == plan_id:
                return p
        return None

    def get_plans(
        self,
        status: PlanStatus | None = None,
        priority: PlanPriority | None = None,
    ) -> list[ReconciliationPlan]:
        results = self._plans
        if status is not None:
            results = [p for p in results if p.status == status]
        if priority is not None:
            results = [p for p in results if p.priority == priority]
        return results

    @property
    def plan_count(self) -> int:
        return len(self._plans)

    # ── helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _estimate_impact(action_type: ReconciliationActionType) -> str:
        impacts: dict[ReconciliationActionType, str] = {
            ReconciliationActionType.REDEPLOY: "high",
            ReconciliationActionType.RECONNECT: "medium",
            ReconciliationActionType.REVERIFY: "low",
            ReconciliationActionType.PATCH_CONFIG: "medium",
            ReconciliationActionType.RESEAL_EVIDENCE: "low",
            ReconciliationActionType.RESTART_ROLLOUT: "high",
            ReconciliationActionType.FORCE_HEALTH_CHECK: "low",
            ReconciliationActionType.ESCALATE_HUMAN: "high",
        }
        return impacts.get(action_type, "unknown")

    @staticmethod
    def _build_parameters(action_type: ReconciliationActionType, signal: DriftSignal) -> dict[str, Any]:
        params: dict[str, Any] = {"drift_type": signal.drift_type.value, "provider": signal.provider_name}
        if action_type == ReconciliationActionType.REDEPLOY:
            params["target_version"] = signal.expected_value
        elif action_type == ReconciliationActionType.PATCH_CONFIG:
            params["config_expected"] = signal.expected_value
            params["config_actual"] = signal.actual_value
        return params


# ── Module singleton ──────────────────────────────────────────────────────

_reconciliation_planner: ReconciliationPlanner | None = None


def get_reconciliation_planner() -> ReconciliationPlanner:
    global _reconciliation_planner
    if _reconciliation_planner is None:
        _reconciliation_planner = ReconciliationPlanner()
    return _reconciliation_planner
