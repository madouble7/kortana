"""V18D — Convergence Manager: system-wide convergence state tracking."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from src.kortana.services.drift_detector import DriftDetector
from src.kortana.services.reconciliation_planner import ReconciliationPlanner, PlanStatus
from src.kortana.services.reconciliation_executor import ReconciliationExecutor


# ── Enums ─────────────────────────────────────────────────────────────────


class ConvergenceStatus(Enum):
    """System-wide convergence state."""

    CONVERGED = "converged"
    DRIFTING = "drifting"
    RECONCILING = "reconciling"
    DIVERGED = "diverged"
    UNKNOWN = "unknown"


class SystemHealth(Enum):
    """Overall system health assessment."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


# ── Data structures ───────────────────────────────────────────────────────


@dataclass
class ConvergenceScore:
    """Numeric convergence score breakdown."""

    overall_score: float = 100.0
    provider_health_pct: float = 100.0
    rollout_health_pct: float = 100.0
    evidence_integrity_pct: float = 100.0
    drift_free_pct: float = 100.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_score": round(self.overall_score, 1),
            "provider_health_pct": round(self.provider_health_pct, 1),
            "rollout_health_pct": round(self.rollout_health_pct, 1),
            "evidence_integrity_pct": round(self.evidence_integrity_pct, 1),
            "drift_free_pct": round(self.drift_free_pct, 1),
        }


@dataclass
class SystemicIssue:
    """A systemic issue detected across the control plane."""

    issue_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    category: str = ""
    description: str = ""
    affected_providers: list[str] = field(default_factory=list)
    severity: str = "medium"

    def to_dict(self) -> dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "category": self.category,
            "description": self.description,
            "affected_providers": self.affected_providers,
            "severity": self.severity,
        }


@dataclass
class ConvergenceSnapshot:
    """Point-in-time convergence state."""

    snapshot_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    status: ConvergenceStatus = ConvergenceStatus.UNKNOWN
    health: SystemHealth = SystemHealth.HEALTHY
    score: ConvergenceScore = field(default_factory=ConvergenceScore)
    active_drift_count: int = 0
    active_reconciliation_count: int = 0
    systemic_issues: list[SystemicIssue] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    snapshot_hash: str = ""

    def __post_init__(self) -> None:
        if not self.snapshot_hash:
            raw = f"{self.snapshot_id}:{self.status.value}:{self.score.overall_score}:{self.timestamp}"
            self.snapshot_hash = hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "status": self.status.value,
            "health": self.health.value,
            "score": self.score.to_dict(),
            "active_drift_count": self.active_drift_count,
            "active_reconciliation_count": self.active_reconciliation_count,
            "systemic_issues": [i.to_dict() for i in self.systemic_issues],
            "timestamp": self.timestamp,
            "snapshot_hash": self.snapshot_hash,
        }


# ── Convergence Manager ──────────────────────────────────────────────────


class ConvergenceManager:
    """Tracks system-wide convergence state across all subsystems."""

    def __init__(
        self,
        drift_detector: DriftDetector | None = None,
        planner: ReconciliationPlanner | None = None,
        executor: ReconciliationExecutor | None = None,
    ) -> None:
        self._drift_detector = drift_detector or DriftDetector()
        self._planner = planner or ReconciliationPlanner()
        self._executor = executor or ReconciliationExecutor()
        self._snapshots: list[ConvergenceSnapshot] = []

    @property
    def drift_detector(self) -> DriftDetector:
        return self._drift_detector

    @property
    def planner(self) -> ReconciliationPlanner:
        return self._planner

    @property
    def executor(self) -> ReconciliationExecutor:
        return self._executor

    # ── snapshot ──────────────────────────────────────────────────────

    def take_snapshot(self) -> ConvergenceSnapshot:
        """Capture current convergence state."""
        active_drifts = self._drift_detector.get_active_drifts()
        active_drift_count = len(active_drifts)

        executing_plans = self._planner.get_plans(status=PlanStatus.EXECUTING)
        active_recon_count = len(executing_plans)

        # Compute score
        score = self._compute_score(active_drift_count, active_recon_count)
        status = self._derive_status(active_drift_count, active_recon_count, score.overall_score)
        health = self._derive_health(score.overall_score)
        issues = self._detect_systemic_issues(active_drifts)

        snapshot = ConvergenceSnapshot(
            status=status,
            health=health,
            score=score,
            active_drift_count=active_drift_count,
            active_reconciliation_count=active_recon_count,
            systemic_issues=issues,
        )
        self._snapshots.append(snapshot)
        return snapshot

    # ── status ────────────────────────────────────────────────────────

    def get_status(self) -> ConvergenceStatus:
        if not self._snapshots:
            return ConvergenceStatus.UNKNOWN
        return self._snapshots[-1].status

    def is_healthy(self) -> bool:
        if not self._snapshots:
            return True
        last = self._snapshots[-1]
        return last.health in (SystemHealth.HEALTHY, SystemHealth.DEGRADED) and last.score.overall_score >= 70.0

    def get_history(self, limit: int = 50) -> list[ConvergenceSnapshot]:
        return self._snapshots[-limit:]

    def get_latest_snapshot(self) -> ConvergenceSnapshot | None:
        return self._snapshots[-1] if self._snapshots else None

    # ── systemic issues ───────────────────────────────────────────────

    def get_systemic_issues(self) -> list[SystemicIssue]:
        if not self._snapshots:
            return []
        return self._snapshots[-1].systemic_issues

    # ── global reconciliation ─────────────────────────────────────────

    def trigger_global_reconciliation(self) -> dict[str, Any]:
        """Trigger reconciliation for all active drifts."""
        active = self._drift_detector.get_active_drifts()
        if not active:
            return {"status": "no_drifts", "plans_created": 0}

        plan = self._planner.plan_from_batch(active)

        # Mark all drifts as reconciling
        for drift in active:
            self._drift_detector.mark_reconciling(drift.signal_id)

        execution = self._executor.execute_plan(plan)

        # Resolve drifts where steps succeeded
        for step in execution.step_results:
            if step.outcome.value == "success":
                for drift in active:
                    if drift.signal_id == step.action_id or drift.provider_name == step.target_provider:
                        self._drift_detector.resolve_drift(drift.signal_id)

        return {
            "status": "reconciled",
            "plans_created": 1,
            "plan_id": plan.plan_id,
            "execution_id": execution.execution_id,
            "execution_status": execution.status.value,
            "steps_succeeded": execution.success_count,
            "steps_failed": execution.failure_count,
        }

    @property
    def snapshot_count(self) -> int:
        return len(self._snapshots)

    # ── helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _compute_score(active_drift_count: int, active_recon_count: int) -> ConvergenceScore:
        # Each active drift reduces score by 15 pts
        drift_penalty = min(active_drift_count * 15, 100)
        drift_free = 100.0 - drift_penalty

        # Active reconciliations slightly reduce score (instability signal)
        recon_penalty = min(active_recon_count * 5, 30)

        overall = max(0.0, 100.0 - drift_penalty - recon_penalty)

        return ConvergenceScore(
            overall_score=overall,
            provider_health_pct=max(0.0, 100.0 - drift_penalty * 0.8),
            rollout_health_pct=max(0.0, 100.0 - drift_penalty * 0.6),
            evidence_integrity_pct=max(0.0, 100.0 - drift_penalty * 0.4),
            drift_free_pct=drift_free,
        )

    @staticmethod
    def _derive_status(
        active_drift_count: int,
        active_recon_count: int,
        overall_score: float,
    ) -> ConvergenceStatus:
        if active_drift_count == 0 and active_recon_count == 0:
            return ConvergenceStatus.CONVERGED
        if active_recon_count > 0:
            return ConvergenceStatus.RECONCILING
        if overall_score < 30:
            return ConvergenceStatus.DIVERGED
        return ConvergenceStatus.DRIFTING

    @staticmethod
    def _derive_health(overall_score: float) -> SystemHealth:
        if overall_score >= 90:
            return SystemHealth.HEALTHY
        if overall_score >= 70:
            return SystemHealth.DEGRADED
        if overall_score >= 40:
            return SystemHealth.UNHEALTHY
        return SystemHealth.CRITICAL

    @staticmethod
    def _detect_systemic_issues(active_drifts: list) -> list[SystemicIssue]:
        issues: list[SystemicIssue] = []
        if len(active_drifts) >= 3:
            providers = list({d.provider_name for d in active_drifts if d.provider_name})
            issues.append(SystemicIssue(
                category="widespread_drift",
                description=f"{len(active_drifts)} active drifts detected across system",
                affected_providers=providers,
                severity="high",
            ))

        # Check for critical drifts
        critical = [d for d in active_drifts if d.severity.value == "critical"]
        if critical:
            providers = list({d.provider_name for d in critical if d.provider_name})
            issues.append(SystemicIssue(
                category="critical_drift",
                description=f"{len(critical)} critical drift(s) requiring immediate attention",
                affected_providers=providers,
                severity="critical",
            ))

        return issues


# ── Module singleton ──────────────────────────────────────────────────────

_convergence_manager: ConvergenceManager | None = None


def get_convergence_manager() -> ConvergenceManager:
    global _convergence_manager
    if _convergence_manager is None:
        _convergence_manager = ConvergenceManager()
    return _convergence_manager
