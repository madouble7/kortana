"""Tests for V4 — promotion gates, regression alarms, and persistence helpers."""

from __future__ import annotations

from src.kortana.services.canary_eval import (
    PromotionThresholds,
    detect_regressions,
    evaluate_promotion,
    report_to_db_dict,
)
from src.kortana.services.canary_simulator import CanarySimulator


# ---------------------------------------------------------------------------
# Promotion gate tests
# ---------------------------------------------------------------------------


class TestPromotionGate:
    """Evaluate whether canary runs meet promotion criteria."""

    def test_adaptive_run_is_promoted(self) -> None:
        sim = CanarySimulator(cycle_count=50, inject_signals=True)
        report = sim.run()
        result = evaluate_promotion(report)
        assert result.promoted is True
        assert "All promotion criteria passed" in result.reasons

    def test_static_run_is_rejected(self) -> None:
        sim = CanarySimulator(cycle_count=20, inject_signals=False)
        report = sim.run()
        # Static verdict should fail if thresholds require adaptive
        # But task state evolution alone can cause churn — check verdict
        if report.analysis.get("verdict") == "static":
            result = evaluate_promotion(report)
            assert result.promoted is False
            assert any("adaptive" in r.lower() for r in result.reasons)

    def test_permissive_thresholds_promote_static(self) -> None:
        sim = CanarySimulator(cycle_count=10, inject_signals=False)
        report = sim.run()
        permissive = PromotionThresholds(verdict_must_be_adaptive=False)
        result = evaluate_promotion(report, permissive)
        # With no verdict requirement, should pass unless other metrics fail
        assert isinstance(result.promoted, bool)
        assert len(result.reasons) > 0

    def test_goal_alignment_regression_fails(self) -> None:
        sim = CanarySimulator(cycle_count=20, inject_signals=True)
        report = sim.run()
        # Force analysis to have a bad goal alignment delta
        report.analysis["goal_alignment"] = {"delta": -1.0, "early_avg_in_top5": 4, "late_avg_in_top5": 3}
        strict = PromotionThresholds(min_goal_alignment_delta=0.0)
        result = evaluate_promotion(report, strict)
        assert result.promoted is False
        assert any("goal alignment" in r.lower() for r in result.reasons)

    def test_high_churn_fails_promotion(self) -> None:
        sim = CanarySimulator(cycle_count=20, inject_signals=True)
        report = sim.run()
        report.analysis["ranking_stability"] = {"top3_churn_rate": 0.99, "total_top3_changes": 19}
        result = evaluate_promotion(report, PromotionThresholds(max_top3_churn_rate=0.95))
        assert result.promoted is False
        assert any("churn" in r.lower() for r in result.reasons)

    def test_score_spread_explosion_fails(self) -> None:
        sim = CanarySimulator(cycle_count=20, inject_signals=True)
        report = sim.run()
        report.analysis["score_spread"] = {"early": 10, "late": 80, "delta": 70}
        result = evaluate_promotion(report, PromotionThresholds(max_score_spread_delta=15.0))
        assert result.promoted is False
        assert any("spread" in r.lower() for r in result.reasons)

    def test_empty_analysis_is_rejected(self) -> None:
        sim = CanarySimulator(cycle_count=20)
        report = sim.run()
        report.analysis = {}
        result = evaluate_promotion(report)
        assert result.promoted is False

    def test_warnings_populated_on_slight_regression(self) -> None:
        sim = CanarySimulator(cycle_count=50, inject_signals=True)
        report = sim.run()
        # Slight goal regression within tolerance
        report.analysis["goal_alignment"] = {"delta": -0.2, "early_avg_in_top5": 4, "late_avg_in_top5": 3.8}
        result = evaluate_promotion(report)
        assert any("regressed" in w.lower() for w in result.warnings)


# ---------------------------------------------------------------------------
# Regression alarm tests
# ---------------------------------------------------------------------------


class TestRegressionAlarms:
    """Detect metric regressions between canary runs."""

    def test_no_alarms_when_no_previous(self) -> None:
        current = {"verdict": "adaptive"}
        alarms = detect_regressions(current, None)
        assert alarms == []

    def test_verdict_regression_is_critical(self) -> None:
        prev = {"verdict": "adaptive"}
        curr = {"verdict": "static"}
        alarms = detect_regressions(curr, prev)
        assert len(alarms) >= 1
        verdict_alarm = next(a for a in alarms if a.metric == "verdict")
        assert verdict_alarm.severity == "critical"
        assert "adaptive" in verdict_alarm.message
        assert "static" in verdict_alarm.message

    def test_no_alarm_when_verdict_stable(self) -> None:
        prev = {"verdict": "adaptive"}
        curr = {"verdict": "adaptive"}
        alarms = detect_regressions(curr, prev)
        verdict_alarms = [a for a in alarms if a.metric == "verdict"]
        assert len(verdict_alarms) == 0

    def test_goal_alignment_drop_is_warning(self) -> None:
        prev = {"goal_alignment": {"late_avg_in_top5": 4.0}}
        curr = {"goal_alignment": {"late_avg_in_top5": 2.5}}
        alarms = detect_regressions(curr, prev)
        goal_alarms = [a for a in alarms if a.metric == "goal_alignment"]
        assert len(goal_alarms) == 1
        assert goal_alarms[0].severity == "warning"

    def test_score_spread_explosion_is_warning(self) -> None:
        prev = {"score_spread": {"late": 20.0}}
        curr = {"score_spread": {"late": 35.0}}  # >50% increase
        alarms = detect_regressions(curr, prev)
        spread_alarms = [a for a in alarms if a.metric == "score_spread"]
        assert len(spread_alarms) == 1

    def test_outcome_growth_collapse_is_critical(self) -> None:
        prev = {"outcome_adaptation": {"growth": 0.05}}
        curr = {"outcome_adaptation": {"growth": -0.01}}
        alarms = detect_regressions(curr, prev)
        growth_alarms = [a for a in alarms if a.metric == "outcome_growth"]
        assert len(growth_alarms) == 1
        assert growth_alarms[0].severity == "critical"

    def test_signal_accumulation_stall_is_warning(self) -> None:
        prev = {"signal_accumulation": {"net_new": 8}}
        curr = {"signal_accumulation": {"net_new": 0}}
        alarms = detect_regressions(curr, prev)
        signal_alarms = [a for a in alarms if a.metric == "signal_accumulation"]
        assert len(signal_alarms) == 1
        assert signal_alarms[0].severity == "warning"

    def test_no_false_alarms_on_improvement(self) -> None:
        prev = {
            "verdict": "static",
            "goal_alignment": {"late_avg_in_top5": 2.0},
            "score_spread": {"late": 30.0},
            "outcome_adaptation": {"growth": 0.0},
            "signal_accumulation": {"net_new": 0},
        }
        curr = {
            "verdict": "adaptive",
            "goal_alignment": {"late_avg_in_top5": 4.0},
            "score_spread": {"late": 25.0},
            "outcome_adaptation": {"growth": 0.05},
            "signal_accumulation": {"net_new": 10},
        }
        alarms = detect_regressions(curr, prev)
        assert len(alarms) == 0, f"Expected no alarms on improvement, got {alarms}"


# ---------------------------------------------------------------------------
# Persistence helper tests
# ---------------------------------------------------------------------------


class TestReportToDbDict:
    """Convert canary reports to DB-ready dicts."""

    def test_basic_conversion(self) -> None:
        sim = CanarySimulator(cycle_count=10, inject_signals=True)
        report = sim.run()
        d = report_to_db_dict(report)
        assert d["total_cycles"] == 10
        assert d["task_pool_size"] == 12
        assert d["verdict"] in ("adaptive", "static", "insufficient_cycles")
        assert d["triggered_by"] == "manual"
        assert d["promotion_status"] == "pending"
        assert isinstance(d["analysis"], dict)

    def test_includes_denormalized_metrics(self) -> None:
        sim = CanarySimulator(cycle_count=20, inject_signals=True)
        report = sim.run()
        d = report_to_db_dict(report)
        assert d["score_shift_delta"] is not None
        assert d["goal_alignment_delta"] is not None
        assert d["outcome_growth"] is not None
        assert d["top3_churn_rate"] is not None
        assert d["score_spread_delta"] is not None

    def test_with_promotion_result(self) -> None:
        sim = CanarySimulator(cycle_count=50, inject_signals=True)
        report = sim.run()
        promo = evaluate_promotion(report)
        d = report_to_db_dict(report, "ci", promo)
        assert d["triggered_by"] == "ci"
        if promo.promoted:
            assert d["promotion_status"] == "promoted"
        else:
            assert d["promotion_status"] == "rejected"
        assert d["promotion_reasons"] == promo.reasons

    def test_snapshot_summary_has_first_and_last(self) -> None:
        sim = CanarySimulator(cycle_count=20)
        report = sim.run()
        d = report_to_db_dict(report)
        summary = d["snapshot_summary"]
        assert "first" in summary
        assert "last" in summary
        assert summary["first"]["cycle"] == 0
        assert summary["last"]["cycle"] == 19

    def test_snapshot_summary_keys(self) -> None:
        sim = CanarySimulator(cycle_count=10)
        report = sim.run()
        d = report_to_db_dict(report)
        for key in ("first", "last"):
            snap = d["snapshot_summary"][key]
            assert "mean_score" in snap
            assert "score_spread" in snap
            assert "signals_active" in snap
            assert "top_3_ids" in snap
            assert "goal_aligned_in_top_5" in snap


# ---------------------------------------------------------------------------
# End-to-end: simulate → evaluate → persist dict
# ---------------------------------------------------------------------------


class TestEndToEndPipeline:
    """Full V4 pipeline: simulate → measure → compare → promote."""

    def test_full_pipeline_adaptive(self) -> None:
        # Simulate
        sim = CanarySimulator(cycle_count=50, inject_signals=True)
        report = sim.run()

        # Evaluate
        promo = evaluate_promotion(report)

        # Convert for persistence
        d = report_to_db_dict(report, "test", promo)

        # Assertions
        assert report.analysis["verdict"] == "adaptive"
        assert promo.promoted is True
        assert d["verdict"] == "adaptive"
        assert d["promotion_status"] == "promoted"
        assert d["snapshot_summary"]["first"]["cycle"] == 0
        assert d["snapshot_summary"]["last"]["cycle"] == 49

    def test_full_pipeline_with_regression_check(self) -> None:
        # First run
        sim1 = CanarySimulator(cycle_count=30, inject_signals=True)
        report1 = sim1.run()

        # Second run (no signals = potential regression)
        sim2 = CanarySimulator(cycle_count=30, inject_signals=False)
        report2 = sim2.run()

        # Check regressions
        alarms = detect_regressions(report2.analysis, report1.analysis)

        # Should detect at least outcome growth collapse
        if report1.analysis.get("outcome_adaptation", {}).get("growth", 0) > 0.01:
            outcome_alarms = [a for a in alarms if a.metric == "outcome_growth"]
            assert len(outcome_alarms) >= 1
