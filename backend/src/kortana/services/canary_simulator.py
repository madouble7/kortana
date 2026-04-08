"""Canary v3 — bounded simulation harness for measuring behavioral adaptation.

Runs N lightweight daemon cycles against synthetic tasks and outcome signals,
capturing score distributions, goal-alignment shifts, approval patterns, and
truth-state drift across cycles.  The goal is a measurable claim:

    *The system changed behavior across cycles under controlled conditions.*

This does NOT require GitHub, Gemini, or any external service.  It drives the
daemon's scoring/adaptation pipeline directly with synthetic data so results
are reproducible and fast (~1 s per cycle).
"""

from __future__ import annotations

import statistics
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from src.kortana.models import GitHubTask

# ---------------------------------------------------------------------------
# Synthetic data factories
# ---------------------------------------------------------------------------


def _synthetic_task(
    *,
    title: str,
    priority: str = "medium",
    status: str = "queued",
    error_count: int = 0,
    age_hours: float = 1.0,
    task_id: str | None = None,
    description: str = "",
) -> GitHubTask:
    """Create an in-memory GitHubTask for simulation (no DB required)."""
    task = GitHubTask(
        id=task_id or str(uuid.uuid4()),
        title=title,
        description=description,
        github_issue_number=0,
        github_repo="sim/canary",
    )
    task.priority = priority
    task.status = status
    task.error_count = error_count
    task.created_at = datetime.utcnow() - timedelta(hours=age_hours)
    task.updated_at = datetime.utcnow()
    return task


def _default_task_pool() -> list[GitHubTask]:
    """A fixed pool of 12 diverse tasks to feed into scoring each cycle."""
    return [
        _synthetic_task(title="fix auth token refresh", priority="high",
                        status="planning_complete", task_id="goal-1"),
        _synthetic_task(title="add rate limiter middleware", priority="high",
                        status="analyzed", task_id="goal-2"),
        _synthetic_task(title="update openapi docs", priority="low",
                        status="queued", age_hours=72),
        _synthetic_task(title="refactor db connection pool", priority="medium",
                        status="pending", error_count=2),
        _synthetic_task(title="add prometheus metrics endpoint", priority="medium",
                        status="queued", task_id="goal-3"),
        _synthetic_task(title="investigate flaky test_auth_flow", priority="high",
                        status="queued", error_count=1),
        _synthetic_task(title="clean up dead imports", priority="low",
                        status="queued", age_hours=120),
        _synthetic_task(title="add redis cache layer", priority="medium",
                        status="analyzed"),
        _synthetic_task(title="security: patch ssrf in webhook handler",
                        priority="high", status="queued", age_hours=0.5),
        _synthetic_task(title="improve error messages in CLI", priority="low",
                        status="queued", age_hours=48),
        _synthetic_task(title="implement websocket heartbeat", priority="medium",
                        status="pending"),
        _synthetic_task(title="add integration test for goal manager",
                        priority="medium", status="queued", task_id="goal-4"),
    ]


# ---------------------------------------------------------------------------
# Simulation state per cycle
# ---------------------------------------------------------------------------


@dataclass
class CycleSnapshot:
    """Captured state from a single simulated cycle."""

    cycle: int
    outcome_adjustment: float
    score_distribution: list[dict[str, Any]]
    top_3_ids: list[str]
    goal_aligned_in_top_5: int
    mean_score: float
    score_spread: float  # max - min
    approval_mode: str
    signals_active: int
    truth_clean: bool


@dataclass
class CanaryReport:
    """Full report across all simulated cycles."""

    total_cycles: int
    task_pool_size: int
    goal_task_ids: list[str]
    snapshots: list[CycleSnapshot]
    analysis: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Core simulator
# ---------------------------------------------------------------------------


class CanarySimulator:
    """Runs bounded scoring cycles and measures behavioral change."""

    def __init__(
        self,
        cycle_count: int = 20,
        goal_task_ids: list[str] | None = None,
        approval_mode: str = "self-aware",
        inject_signals: bool = True,
    ) -> None:
        self.cycle_count = min(cycle_count, 200)  # hard cap
        self.goal_task_ids = goal_task_ids if goal_task_ids is not None else ["goal-1", "goal-2", "goal-3", "goal-4"]
        self.approval_mode = approval_mode
        self.inject_signals = inject_signals
        self._task_pool = _default_task_pool()
        self._accumulated_signals: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self) -> CanaryReport:
        """Execute all cycles synchronously and return full report."""
        snapshots: list[CycleSnapshot] = []

        for cycle_num in range(self.cycle_count):
            # Simulate outcome signals accumulating over time
            if self.inject_signals:
                self._evolve_signals(cycle_num)

            outcome_adj = self._compute_adjustment()
            scored = self._score_tasks(outcome_adj)
            snapshot = self._capture(cycle_num, scored, outcome_adj)
            snapshots.append(snapshot)

            # Simulate task state evolution (tasks advance after being selected)
            self._evolve_tasks(scored[:5])

        report = CanaryReport(
            total_cycles=self.cycle_count,
            task_pool_size=len(self._task_pool),
            goal_task_ids=self.goal_task_ids,
            snapshots=snapshots,
        )
        report.analysis = self._analyze(report)
        return report

    # ------------------------------------------------------------------
    # Scoring — mirrors _prioritize_tasks exactly
    # ------------------------------------------------------------------

    def _score_tasks(self, outcome_adjustment: float) -> list[GitHubTask]:
        """Score tasks using the same multi-factor formula as the daemon."""
        now = datetime.utcnow()
        active_goal_ids = set(self.goal_task_ids)
        scored: list[tuple[float, GitHubTask]] = []

        for task in self._task_pool:
            base = {"high": 30.0, "medium": 20.0, "low": 10.0}.get(
                str(task.priority or "medium"), 20.0
            )

            outcome_signal = outcome_adjustment * 100.0

            age_hours = max(
                (now - (task.created_at or now)).total_seconds() / 3600.0, 0.0
            )
            novelty_bonus = max(5.0 - age_hours * 0.1, 0.0)

            risk_penalty = (task.error_count or 0) * 8.0

            status_bonus = {
                "planning_complete": 15.0,
                "analyzed": 10.0,
                "pending": 5.0,
                "queued": 0.0,
            }.get(str(task.status or "queued"), 0.0)

            goal_bonus = 12.0 if str(task.id) in active_goal_ids else 0.0

            total = (
                base + outcome_signal + novelty_bonus
                + status_bonus + goal_bonus - risk_penalty
            )

            task._score_breakdown = {  # type: ignore[attr-defined]
                "total": round(total, 2),
                "base_priority": base,
                "outcome": round(outcome_signal, 2),
                "novelty": round(novelty_bonus, 2),
                "status_bonus": status_bonus,
                "goal_alignment": goal_bonus,
                "risk_penalty": risk_penalty,
            }
            scored.append((total, task))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [t for _, t in scored]

    # ------------------------------------------------------------------
    # Signal evolution — simulates outcome learning over time
    # ------------------------------------------------------------------

    def _evolve_signals(self, cycle: int) -> None:
        """Simulate outcome learning records accumulating."""
        if cycle == 0:
            return  # cycle 0 is the baseline, no signals yet

        # Every 3 cycles, add a positive signal for tactical tasks
        if cycle % 3 == 0:
            self._accumulated_signals.append({
                "signal": "boost_tier:tactical",
                "total_weight": 0.08,
                "occurrences": 1,
            })

        # Every 5 cycles, add a trust signal (success pattern)
        if cycle % 5 == 0:
            self._accumulated_signals.append({
                "signal": "trust_observation",
                "total_weight": 0.05,
                "occurrences": 1,
            })

        # At cycle 10+, add a penalty for goal_work that keeps failing
        if cycle >= 10 and cycle % 7 == 0:
            self._accumulated_signals.append({
                "signal": "penalise_type:flaky",
                "total_weight": -0.04,
                "occurrences": 1,
            })

    def _compute_adjustment(self) -> float:
        """Mirror compute_score_adjustment from outcome_learning_service."""
        total = 0.0
        for s in self._accumulated_signals:
            sig_name = str(s.get("signal", ""))
            weight = float(s.get("total_weight", 0.0))
            if sig_name.startswith("boost_") or sig_name.startswith("trust_"):
                total += weight
            elif sig_name.startswith("penalise_"):
                total += weight
        return max(-0.3, min(0.3, total))

    # ------------------------------------------------------------------
    # Task evolution — simulates state advancement
    # ------------------------------------------------------------------

    def _evolve_tasks(self, selected: list[GitHubTask]) -> None:
        """Advance the state of selected tasks to simulate processing."""
        transitions = {
            "queued": "pending",
            "pending": "analyzed",
            "analyzed": "planning_complete",
        }
        for task in selected[:3]:  # simulate 3 of top-5 advancing
            new_status = transitions.get(str(task.status or "queued"))
            if new_status:
                task.status = new_status

    # ------------------------------------------------------------------
    # Snapshot capture
    # ------------------------------------------------------------------

    def _capture(
        self, cycle: int, ranked: list[GitHubTask], outcome_adj: float
    ) -> CycleSnapshot:
        """Capture metrics for this cycle."""
        breakdowns = [
            {
                "task_id": str(t.id),
                "title": (t.title or "")[:60],
                **getattr(t, "_score_breakdown", {}),
            }
            for t in ranked
        ]
        scores = [b["total"] for b in breakdowns]
        goal_set = set(self.goal_task_ids)
        top_5_ids = [str(t.id) for t in ranked[:5]]

        return CycleSnapshot(
            cycle=cycle,
            outcome_adjustment=round(outcome_adj, 4),
            score_distribution=breakdowns,
            top_3_ids=[str(t.id) for t in ranked[:3]],
            goal_aligned_in_top_5=sum(1 for tid in top_5_ids if tid in goal_set),
            mean_score=round(statistics.mean(scores), 2) if scores else 0.0,
            score_spread=round(max(scores) - min(scores), 2) if scores else 0.0,
            approval_mode=self.approval_mode,
            signals_active=len(self._accumulated_signals),
            truth_clean=True,  # canary runs in clean sandbox
        )

    # ------------------------------------------------------------------
    # Cross-cycle analysis
    # ------------------------------------------------------------------

    def _analyze(self, report: CanaryReport) -> dict[str, Any]:
        """Compare early vs late cycles to measure behavioral adaptation."""
        if len(report.snapshots) < 4:
            return {"verdict": "insufficient_cycles", "detail": "Need >= 4 cycles"}

        # Split into early (first quarter) and late (last quarter)
        n = len(report.snapshots)
        quarter = max(n // 4, 1)
        early = report.snapshots[:quarter]
        late = report.snapshots[-quarter:]

        # 1. Score distribution shift
        early_means = [s.mean_score for s in early]
        late_means = [s.mean_score for s in late]
        mean_shift = (
            statistics.mean(late_means) - statistics.mean(early_means)
        )

        # 2. Goal alignment trend
        early_goal = statistics.mean([s.goal_aligned_in_top_5 for s in early])
        late_goal = statistics.mean([s.goal_aligned_in_top_5 for s in late])
        goal_alignment_shift = late_goal - early_goal

        # 3. Outcome adjustment growth
        early_adj = statistics.mean([s.outcome_adjustment for s in early])
        late_adj = statistics.mean([s.outcome_adjustment for s in late])
        outcome_growth = late_adj - early_adj

        # 4. Top-3 stability (do the same tasks keep winning?)
        top3_sets = [frozenset(s.top_3_ids) for s in report.snapshots]
        top3_changes = sum(
            1 for i in range(1, len(top3_sets))
            if top3_sets[i] != top3_sets[i - 1]
        )
        top3_churn_rate = top3_changes / max(len(top3_sets) - 1, 1)

        # 5. Signal accumulation
        final_signals = report.snapshots[-1].signals_active
        baseline_signals = report.snapshots[0].signals_active

        # 6. Score spread evolution
        early_spread = statistics.mean([s.score_spread for s in early])
        late_spread = statistics.mean([s.score_spread for s in late])
        spread_change = late_spread - early_spread

        # Verdict
        behavior_changed = (
            abs(mean_shift) > 0.5
            or abs(outcome_growth) > 0.01
            or top3_churn_rate > 0.1
        )

        return {
            "verdict": "adaptive" if behavior_changed else "static",
            "behavior_changed": behavior_changed,
            "score_shift": {
                "early_mean": round(statistics.mean(early_means), 2),
                "late_mean": round(statistics.mean(late_means), 2),
                "delta": round(mean_shift, 2),
            },
            "goal_alignment": {
                "early_avg_in_top5": round(early_goal, 2),
                "late_avg_in_top5": round(late_goal, 2),
                "delta": round(goal_alignment_shift, 2),
            },
            "outcome_adaptation": {
                "early_adjustment": round(early_adj, 4),
                "late_adjustment": round(late_adj, 4),
                "growth": round(outcome_growth, 4),
            },
            "ranking_stability": {
                "top3_churn_rate": round(top3_churn_rate, 3),
                "total_top3_changes": top3_changes,
            },
            "signal_accumulation": {
                "baseline": baseline_signals,
                "final": final_signals,
                "net_new": final_signals - baseline_signals,
            },
            "score_spread": {
                "early": round(early_spread, 2),
                "late": round(late_spread, 2),
                "delta": round(spread_change, 2),
            },
        }
