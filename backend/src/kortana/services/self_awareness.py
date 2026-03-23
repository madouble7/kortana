"""
KOR'TANA Self-Awareness Engine

Real-time system introspection that gives KOR'TANA genuine self-knowledge:
  - Continuous system state assessment (NOMINAL / DEGRADED / CRITICAL)
  - Confidence scoring for autonomous decisions
  - Drift detection against learned baselines
  - Self-correction planning when anomalies surface
  - Capability inventory (what can I do right now?)

Runs as a singleton; integrates with the Autonomy Daemon event system.
"""

from __future__ import annotations

import os
import platform
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import psutil
from sqlalchemy import func, select
from src.kortana.database import get_db_manager
from src.kortana.logger import get_logger
from src.kortana.models import GitHubTask

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


class SystemState(Enum):
    NOMINAL = "nominal"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    RECOVERING = "recovering"


@dataclass
class PerformanceSnapshot:
    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    open_fds: int
    uptime_seconds: float
    pending_tasks: int
    completed_tasks: int
    failed_tasks: int
    success_rate: float
    avg_cycle_time: float | None


@dataclass
class DriftReport:
    metric: str
    label: str
    baseline: float
    current: float
    deviation_pct: float
    severity: str  # "low", "medium", "high"


@dataclass
class CorrectionPlan:
    action: str
    reason: str
    priority: str  # "low", "medium", "high", "critical"
    estimated_effect: str
    params: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class SelfAwarenessEngine:
    """KOR'TANA's introspection and self-knowledge system."""

    def __init__(self) -> None:
        self._boot_time = time.monotonic()
        self._state = SystemState.NOMINAL
        self._baseline: PerformanceSnapshot | None = None
        self._history: list[dict[str, Any]] = []
        self._max_history = 500
        self._db = get_db_manager()

        # Thresholds (configurable via env)
        self._cpu_warn = float(os.getenv("SA_CPU_WARN", "75"))
        self._cpu_crit = float(os.getenv("SA_CPU_CRIT", "90"))
        self._mem_warn = float(os.getenv("SA_MEM_WARN", "80"))
        self._mem_crit = float(os.getenv("SA_MEM_CRIT", "90"))
        self._err_warn = float(os.getenv("SA_ERR_WARN", "5"))
        self._err_crit = float(os.getenv("SA_ERR_CRIT", "15"))

    # ----- core introspection -----

    async def assess(self) -> dict[str, Any]:
        """Full system self-assessment.  Returns state + snapshot + drift."""
        snap = await self._collect_snapshot()

        # Set baseline on first assessment
        if self._baseline is None:
            self._baseline = snap

        state = self._derive_state(snap)
        drift = self._detect_drift(snap)
        corrections = self._plan_corrections(drift) if drift else []

        self._state = state
        entry = {
            "timestamp": snap.timestamp,
            "state": state.value,
            "cpu": snap.cpu_percent,
            "mem": snap.memory_percent,
            "tasks_pending": snap.pending_tasks,
            "success_rate": snap.success_rate,
        }
        self._history.append(entry)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history :]

        return {
            "state": state.value,
            "snapshot": snap.__dict__,
            "drift": [d.__dict__ for d in drift],
            "corrections": [c.__dict__ for c in corrections],
            "capabilities": self._capabilities(),
        }

    async def confidence(self, decision: dict[str, Any]) -> float:
        """Score confidence in an autonomous decision (0.0 – 1.0).

        Factors:
          - system_health: is the system in good shape?
          - data_quality: does the decision have enough context?
          - model_certainty: how certain was the AI provider?
          - historical: how well have similar decisions gone?
          - consensus: did multiple providers agree?
        """
        snap = await self._collect_snapshot()

        health = 1.0
        if self._state == SystemState.DEGRADED:
            health = 0.6
        elif self._state == SystemState.CRITICAL:
            health = 0.2

        data_q = min(1.0, len(str(decision.get("context", ""))) / 200)
        model_cert = float(decision.get("certainty", 0.7))
        hist = snap.success_rate / 100.0 if snap.success_rate else 0.5
        consensus = float(decision.get("consensus_score", 0.8))

        weights = {
            "health": 0.5,
            "data": 1.0,
            "model": 1.0,
            "history": 1.0,
            "consensus": 1.0,
        }
        num = (
            health * weights["health"]
            + data_q * weights["data"]
            + model_cert * weights["model"]
            + hist * weights["history"]
            + consensus * weights["consensus"]
        )
        return round(num / sum(weights.values()), 3)

    # ----- helpers -----

    async def _collect_snapshot(self) -> PerformanceSnapshot:
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory().percent
        disk = (
            psutil.disk_usage("/").percent
            if platform.system() != "Windows"
            else psutil.disk_usage("C:\\").percent
        )
        proc = psutil.Process()
        open_fds = proc.num_handles() if platform.system() == "Windows" else proc.num_fds()

        # DB stats
        pending = completed = failed = 0
        success_rate = 100.0
        try:
            async for session in self._db.get_session():
                row = await session.execute(
                    select(
                        func.count().filter(GitHubTask.status == "pending").label("pending"),
                        func.count()
                        .filter(GitHubTask.status.in_(["executed", "completed", "pr_created"]))
                        .label("ok"),
                        func.count().filter(GitHubTask.status == "failed").label("fail"),
                    )
                )
                r = row.one()
                pending, completed, failed = r.pending, r.ok, r.fail
                total = completed + failed
                success_rate = (completed / total * 100) if total > 0 else 100.0
        except Exception as e:
            logger.debug(f"DB stats unavailable: {e}")

        # avg cycle time from autonomy daemon
        avg_cycle: float | None = None
        try:
            from src.kortana.services.autonomy_daemon import get_autonomy_daemon

            d = get_autonomy_daemon()
            lc = d.metrics.get("last_cycle")
            if lc:
                avg_cycle = lc.get("duration_seconds")
        except Exception:
            pass

        return PerformanceSnapshot(
            timestamp=datetime.utcnow().isoformat(),
            cpu_percent=cpu,
            memory_percent=mem,
            disk_percent=disk,
            open_fds=open_fds,
            uptime_seconds=round(time.monotonic() - self._boot_time, 1),
            pending_tasks=pending,
            completed_tasks=completed,
            failed_tasks=failed,
            success_rate=round(success_rate, 2),
            avg_cycle_time=avg_cycle,
        )

    def _derive_state(self, s: PerformanceSnapshot) -> SystemState:
        crits = 0
        if s.cpu_percent > self._cpu_crit:
            crits += 1
        if s.memory_percent > self._mem_crit:
            crits += 1
        if s.success_rate < (100 - self._err_crit):
            crits += 1

        if crits >= 2:
            return SystemState.CRITICAL
        if s.cpu_percent > self._cpu_warn or s.memory_percent > self._mem_warn:
            return SystemState.DEGRADED
        if s.success_rate < (100 - self._err_warn):
            return SystemState.DEGRADED
        if self._state == SystemState.CRITICAL:
            return SystemState.RECOVERING
        return SystemState.NOMINAL

    def _detect_drift(self, current: PerformanceSnapshot) -> list[DriftReport]:
        if self._baseline is None:
            return []

        checks = [
            ("cpu_percent", "CPU", 30),
            ("memory_percent", "Memory", 25),
            ("success_rate", "Success Rate", 20),
        ]
        drifts: list[DriftReport] = []
        for attr, label, thresh in checks:
            cur = getattr(current, attr)
            base = getattr(self._baseline, attr)
            if base > 0:
                dev = abs(cur - base) / base * 100
            else:
                dev = 0
            if dev > thresh:
                sev = "high" if dev > thresh * 2 else "medium"
                drifts.append(DriftReport(attr, label, base, cur, round(dev, 1), sev))
        return drifts

    def _plan_corrections(self, drifts: list[DriftReport]) -> list[CorrectionPlan]:
        plans: list[CorrectionPlan] = []
        for d in drifts:
            if d.metric == "cpu_percent" and d.current > self._cpu_warn:
                plans.append(
                    CorrectionPlan(
                        action="reduce_concurrent_tasks",
                        reason=f"CPU at {d.current:.0f}% (baseline {d.baseline:.0f}%)",
                        priority="high",
                        estimated_effect="Lower CPU by throttling parallel work",
                        params={"max_tasks_per_cycle": 1},
                    )
                )
            elif d.metric == "memory_percent" and d.current > self._mem_warn:
                plans.append(
                    CorrectionPlan(
                        action="clear_caches",
                        reason=f"Memory at {d.current:.0f}% (baseline {d.baseline:.0f}%)",
                        priority="high",
                        estimated_effect="Free ~10-20% memory",
                    )
                )
            elif d.metric == "success_rate" and d.current < 80:
                plans.append(
                    CorrectionPlan(
                        action="enable_dry_run_mode",
                        reason=f"Success rate dropped to {d.current:.0f}%",
                        priority="critical",
                        estimated_effect="Prevent further failures while investigating",
                    )
                )
        return plans

    def _capabilities(self) -> dict[str, bool]:
        """What can KOR'TANA do right now?"""
        caps: dict[str, bool] = {}
        try:
            from src.kortana.services.ai_consensus import get_consensus_engine

            e = get_consensus_engine()
            caps["ai_consensus"] = True
            caps["ai_providers"] = e.get_status().get("total_providers", 0) > 0
        except Exception:
            caps["ai_consensus"] = False
            caps["ai_providers"] = False

        try:
            from src.kortana.services.autonomy_daemon import get_autonomy_daemon

            caps["autonomy_daemon"] = get_autonomy_daemon()._running
        except Exception:
            caps["autonomy_daemon"] = False

        try:
            from src.kortana.services.discord_service import get_discord_bot

            bot = get_discord_bot()
            caps["discord_bot"] = bot is not None and bot.is_ready()
        except Exception:
            caps["discord_bot"] = False

        caps["github_integration"] = bool(os.getenv("GITHUB_TOKEN"))
        caps["database"] = True  # We wouldn't be running without it
        return caps

    # ----- public status -----

    def get_status(self) -> dict[str, Any]:
        return {
            "state": self._state.value,
            "uptime_seconds": round(time.monotonic() - self._boot_time, 1),
            "assessments_recorded": len(self._history),
            "baseline_set": self._baseline is not None,
            "last_5": self._history[-5:] if self._history else [],
        }


# Singleton
_engine: SelfAwarenessEngine | None = None


def get_self_awareness() -> SelfAwarenessEngine:
    global _engine
    if _engine is None:
        _engine = SelfAwarenessEngine()
    return _engine
