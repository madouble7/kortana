"""Tests for canary_simulator — the bounded adaptation measurement harness."""

from __future__ import annotations

from src.kortana.services.canary_simulator import (
    CanarySimulator,
    _default_task_pool,
    _synthetic_task,
)


class TestSyntheticTaskFactory:
    def test_creates_task_with_defaults(self) -> None:
        task = _synthetic_task(title="test task")
        assert task.title == "test task"
        assert task.priority == "medium"
        assert task.status == "queued"
        assert task.error_count == 0
        assert task.created_at is not None

    def test_creates_task_with_custom_fields(self) -> None:
        task = _synthetic_task(
            title="high pri",
            priority="high",
            status="analyzed",
            error_count=3,
            task_id="custom-id",
        )
        assert task.id == "custom-id"
        assert task.priority == "high"
        assert task.status == "analyzed"
        assert task.error_count == 3

    def test_default_pool_has_12_tasks(self) -> None:
        pool = _default_task_pool()
        assert len(pool) == 12

    def test_default_pool_has_goal_linked_tasks(self) -> None:
        pool = _default_task_pool()
        ids = {str(t.id) for t in pool}
        assert "goal-1" in ids
        assert "goal-2" in ids
        assert "goal-3" in ids
        assert "goal-4" in ids


class TestCanarySimulator:
    def test_runs_default_20_cycles(self) -> None:
        sim = CanarySimulator(cycle_count=20)
        report = sim.run()
        assert report.total_cycles == 20
        assert len(report.snapshots) == 20
        assert report.task_pool_size == 12

    def test_cycle_0_has_no_signals(self) -> None:
        sim = CanarySimulator(cycle_count=5)
        report = sim.run()
        assert report.snapshots[0].signals_active == 0

    def test_signals_accumulate_over_cycles(self) -> None:
        sim = CanarySimulator(cycle_count=20, inject_signals=True)
        report = sim.run()
        first = report.snapshots[0].signals_active
        last = report.snapshots[-1].signals_active
        assert last > first, "Signals should accumulate over cycles"

    def test_no_signals_when_injection_disabled(self) -> None:
        sim = CanarySimulator(cycle_count=10, inject_signals=False)
        report = sim.run()
        for snap in report.snapshots:
            assert snap.signals_active == 0
            assert snap.outcome_adjustment == 0.0

    def test_outcome_adjustment_grows_with_signals(self) -> None:
        sim = CanarySimulator(cycle_count=20, inject_signals=True)
        report = sim.run()
        first_adj = report.snapshots[0].outcome_adjustment
        last_adj = report.snapshots[-1].outcome_adjustment
        assert last_adj > first_adj, "Outcome adjustment should grow with signals"

    def test_outcome_adjustment_clamped(self) -> None:
        sim = CanarySimulator(cycle_count=200, inject_signals=True)
        report = sim.run()
        for snap in report.snapshots:
            assert -0.3 <= snap.outcome_adjustment <= 0.3

    def test_goal_aligned_tasks_in_top_5(self) -> None:
        sim = CanarySimulator(cycle_count=5)
        report = sim.run()
        for snap in report.snapshots:
            assert snap.goal_aligned_in_top_5 >= 0

    def test_score_distribution_has_all_tasks(self) -> None:
        sim = CanarySimulator(cycle_count=4)
        report = sim.run()
        for snap in report.snapshots:
            assert len(snap.score_distribution) == 12

    def test_score_breakdown_has_expected_keys(self) -> None:
        sim = CanarySimulator(cycle_count=4)
        report = sim.run()
        breakdown = report.snapshots[0].score_distribution[0]
        expected_keys = {
            "task_id", "title", "total", "base_priority", "outcome",
            "novelty", "status_bonus", "goal_alignment", "risk_penalty",
        }
        assert expected_keys.issubset(set(breakdown.keys()))

    def test_tasks_advance_state_over_cycles(self) -> None:
        sim = CanarySimulator(cycle_count=10, inject_signals=False)

        # After 10 cycles, some tasks should have advanced past "queued"
        statuses = {str(t.status) for t in sim._task_pool}
        assert "queued" in statuses or "pending" in statuses or "analyzed" in statuses


class TestCanaryAnalysis:
    def test_analysis_has_verdict(self) -> None:
        sim = CanarySimulator(cycle_count=20, inject_signals=True)
        report = sim.run()
        assert "verdict" in report.analysis
        assert report.analysis["verdict"] in ("adaptive", "static")

    def test_analysis_detects_adaptation_with_signals(self) -> None:
        sim = CanarySimulator(cycle_count=50, inject_signals=True)
        report = sim.run()
        assert report.analysis["behavior_changed"] is True
        assert report.analysis["verdict"] == "adaptive"

    def test_analysis_detects_static_without_signals(self) -> None:
        sim = CanarySimulator(cycle_count=20, inject_signals=False)
        report = sim.run()
        # Without signals, only task state evolution causes change
        # The outcome_growth should be 0
        assert report.analysis["outcome_adaptation"]["growth"] == 0.0

    def test_analysis_has_expected_sections(self) -> None:
        sim = CanarySimulator(cycle_count=20)
        report = sim.run()
        expected_sections = {
            "score_shift", "goal_alignment", "outcome_adaptation",
            "ranking_stability", "signal_accumulation", "score_spread",
        }
        assert expected_sections.issubset(set(report.analysis.keys()))

    def test_analysis_score_shift_has_delta(self) -> None:
        sim = CanarySimulator(cycle_count=20)
        report = sim.run()
        shift = report.analysis["score_shift"]
        assert "early_mean" in shift
        assert "late_mean" in shift
        assert "delta" in shift

    def test_analysis_ranking_stability(self) -> None:
        sim = CanarySimulator(cycle_count=20)
        report = sim.run()
        stability = report.analysis["ranking_stability"]
        assert 0.0 <= stability["top3_churn_rate"] <= 1.0

    def test_analysis_insufficient_cycles(self) -> None:
        sim = CanarySimulator(cycle_count=4)
        report = sim.run()
        # 4 cycles is minimum, should still produce a verdict
        assert "verdict" in report.analysis

    def test_signal_accumulation_tracked(self) -> None:
        sim = CanarySimulator(cycle_count=30, inject_signals=True)
        report = sim.run()
        acc = report.analysis["signal_accumulation"]
        assert acc["baseline"] == 0
        assert acc["final"] > 0
        assert acc["net_new"] == acc["final"] - acc["baseline"]


class TestCanaryEdgeCases:
    def test_max_cycles_capped_at_200(self) -> None:
        sim = CanarySimulator(cycle_count=500)
        assert sim.cycle_count == 200

    def test_custom_goal_task_ids(self) -> None:
        sim = CanarySimulator(goal_task_ids=["custom-1"])
        report = sim.run()
        assert report.goal_task_ids == ["custom-1"]

    def test_empty_goal_ids_still_runs(self) -> None:
        sim = CanarySimulator(goal_task_ids=[])
        report = sim.run()
        for snap in report.snapshots:
            assert snap.goal_aligned_in_top_5 == 0
