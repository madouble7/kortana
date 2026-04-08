"""V9B — Drill Scheduler: recurring chaos drills with pass/fail SLOs.

Wraps the chaos engine with scheduling, tracks pass rates over
configurable lookback windows, and evaluates service-level objectives.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger("kortana.drill_scheduler")


# ---------------------------------------------------------------------------
# Drill schedule
# ---------------------------------------------------------------------------


@dataclass
class DrillSchedule:
    """Defines when and which scenario to run automatically."""

    scenario: str
    interval_minutes: int = 60
    enabled: bool = True
    last_run_at: datetime | None = None
    run_count: int = 0
    pass_count: int = 0
    fail_count: int = 0

    @property
    def pass_rate(self) -> float:
        if self.run_count == 0:
            return 1.0
        return self.pass_count / self.run_count

    @property
    def is_due(self) -> bool:
        if not self.enabled:
            return False
        if self.last_run_at is None:
            return True
        elapsed = (datetime.utcnow() - self.last_run_at).total_seconds()
        return elapsed >= self.interval_minutes * 60

    def record_result(self, passed: bool) -> None:
        self.last_run_at = datetime.utcnow()
        self.run_count += 1
        if passed:
            self.pass_count += 1
        else:
            self.fail_count += 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario,
            "interval_minutes": self.interval_minutes,
            "enabled": self.enabled,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "run_count": self.run_count,
            "pass_count": self.pass_count,
            "fail_count": self.fail_count,
            "pass_rate": round(self.pass_rate, 4),
            "is_due": self.is_due,
        }


# ---------------------------------------------------------------------------
# SLO definition and evaluation
# ---------------------------------------------------------------------------


@dataclass
class DrillSLO:
    """Service-level objective for a chaos drill scenario."""

    scenario: str
    min_pass_rate: float = 0.95
    lookback_window_minutes: int = 1440  # 24 hours
    min_runs: int = 3  # minimum runs before SLO is evaluated

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario,
            "min_pass_rate": self.min_pass_rate,
            "lookback_window_minutes": self.lookback_window_minutes,
            "min_runs": self.min_runs,
        }


@dataclass
class SLOResult:
    """Evaluation result for a drill SLO."""

    scenario: str
    met: bool
    actual_pass_rate: float
    required_pass_rate: float
    total_runs: int
    passed_runs: int
    window_start: str
    insufficient_data: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario,
            "met": self.met,
            "actual_pass_rate": round(self.actual_pass_rate, 4),
            "required_pass_rate": self.required_pass_rate,
            "total_runs": self.total_runs,
            "passed_runs": self.passed_runs,
            "window_start": self.window_start,
            "insufficient_data": self.insufficient_data,
        }


def evaluate_slo(
    slo: DrillSLO,
    drill_history: list[dict[str, Any]],
    now: datetime | None = None,
) -> SLOResult:
    """Evaluate whether a drill SLO is met based on recent history.

    drill_history entries must have "scenario", "passed", and "created_at"
    (ISO format string or datetime).
    """
    now = now or datetime.utcnow()
    cutoff = now - timedelta(minutes=slo.lookback_window_minutes)

    matching: list[dict[str, Any]] = []
    for entry in drill_history:
        if entry.get("scenario") != slo.scenario:
            continue
        created = entry.get("created_at")
        if created is None:
            continue
        if isinstance(created, str):
            try:
                created = datetime.fromisoformat(created)
            except ValueError:
                continue
        if created >= cutoff:
            matching.append(entry)

    total = len(matching)
    passed = sum(1 for e in matching if e.get("passed"))

    if total < slo.min_runs:
        return SLOResult(
            scenario=slo.scenario,
            met=True,  # not enough data to fail
            actual_pass_rate=passed / total if total > 0 else 1.0,
            required_pass_rate=slo.min_pass_rate,
            total_runs=total,
            passed_runs=passed,
            window_start=cutoff.isoformat(),
            insufficient_data=True,
        )

    actual_rate = passed / total
    return SLOResult(
        scenario=slo.scenario,
        met=actual_rate >= slo.min_pass_rate,
        actual_pass_rate=actual_rate,
        required_pass_rate=slo.min_pass_rate,
        total_runs=total,
        passed_runs=passed,
        window_start=cutoff.isoformat(),
    )


# ---------------------------------------------------------------------------
# Drill scheduler
# ---------------------------------------------------------------------------


class DrillScheduler:
    """Manages scheduled chaos drills and SLO tracking."""

    def __init__(self) -> None:
        self._schedules: dict[str, DrillSchedule] = {}
        self._slos: dict[str, DrillSLO] = {}
        self._history: list[dict[str, Any]] = []

    def add_schedule(
        self,
        scenario: str,
        interval_minutes: int = 60,
        enabled: bool = True,
    ) -> DrillSchedule:
        """Register a recurring drill schedule."""
        schedule = DrillSchedule(
            scenario=scenario,
            interval_minutes=interval_minutes,
            enabled=enabled,
        )
        self._schedules[scenario] = schedule
        logger.info("Drill schedule added: %s every %dm", scenario, interval_minutes)
        return schedule

    def remove_schedule(self, scenario: str) -> bool:
        """Remove a drill schedule. Returns True if found."""
        if scenario in self._schedules:
            del self._schedules[scenario]
            return True
        return False

    def set_slo(
        self,
        scenario: str,
        min_pass_rate: float = 0.95,
        lookback_window_minutes: int = 1440,
        min_runs: int = 3,
    ) -> DrillSLO:
        """Define or update the SLO for a scenario."""
        slo = DrillSLO(
            scenario=scenario,
            min_pass_rate=min_pass_rate,
            lookback_window_minutes=lookback_window_minutes,
            min_runs=min_runs,
        )
        self._slos[scenario] = slo
        return slo

    def get_due_drills(self) -> list[DrillSchedule]:
        """Return all schedules whose interval has elapsed."""
        return [s for s in self._schedules.values() if s.is_due]

    def run_due_drills(self, current_mode: str = "self-aware") -> list[dict[str, Any]]:
        """Run all due drills via the chaos engine and record results.

        Returns list of DrillResult dicts.
        """
        from src.kortana.services.chaos_engine import run_scenario

        due = self.get_due_drills()
        results = []
        for schedule in due:
            result = run_scenario(schedule.scenario, current_mode)
            schedule.record_result(result.passed)
            entry = result.to_dict()
            entry["created_at"] = datetime.utcnow().isoformat()
            self._history.append(entry)
            results.append(entry)
            logger.info(
                "Scheduled drill %s: %s (pass_rate=%.2f%%)",
                schedule.scenario,
                "PASS" if result.passed else "FAIL",
                schedule.pass_rate * 100,
            )
        return results

    def evaluate_all_slos(self) -> list[SLOResult]:
        """Evaluate all registered SLOs against drill history."""
        results = []
        for slo in self._slos.values():
            results.append(evaluate_slo(slo, self._history))
        return results

    def evaluate_slo(self, scenario: str) -> SLOResult | None:
        """Evaluate SLO for a specific scenario."""
        slo = self._slos.get(scenario)
        if slo is None:
            return None
        return evaluate_slo(slo, self._history)

    def record_external_result(
        self,
        scenario: str,
        passed: bool,
        created_at: str | None = None,
    ) -> None:
        """Record a drill result from an external source (e.g. DB)."""
        self._history.append({
            "scenario": scenario,
            "passed": passed,
            "created_at": created_at or datetime.utcnow().isoformat(),
        })

    @property
    def schedules(self) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self._schedules.values()]

    @property
    def slos(self) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self._slos.values()]

    @property
    def history(self) -> list[dict[str, Any]]:
        return list(reversed(self._history))


# Module-level singleton
_scheduler = DrillScheduler()


def get_drill_scheduler() -> DrillScheduler:
    """Return the module-level drill scheduler singleton."""
    return _scheduler
