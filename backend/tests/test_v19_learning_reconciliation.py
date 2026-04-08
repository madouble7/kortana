"""V19 — Learning Reconciliation Tests."""

import pytest


# ── V19A — OutcomeTracker Tests ───────────────────────────────────────────


class TestOutcomeTracker:
    """Tests for outcome_tracker.py."""

    def test_record_outcome(self) -> None:
        from src.kortana.services.outcome_tracker import OutcomeTracker, OutcomeVerdict
        tracker = OutcomeTracker()
        outcome = tracker.record_outcome(
            execution_id="exec-1", plan_id="plan-1", drift_type="config_drift",
            action_types_used=["restart_service"], verdict=OutcomeVerdict.EFFECTIVE,
            time_to_resolve_sec=12.5, retries_needed=1,
        )
        assert tracker.outcome_count == 1
        assert outcome.execution_id == "exec-1"

    def test_get_outcomes_empty(self) -> None:
        from src.kortana.services.outcome_tracker import OutcomeTracker
        tracker = OutcomeTracker()
        assert tracker.get_outcomes() == []

    def test_get_outcomes_filter_verdict(self) -> None:
        from src.kortana.services.outcome_tracker import OutcomeTracker, OutcomeVerdict
        tracker = OutcomeTracker()
        for i in range(5):
            tracker.record_outcome(
                execution_id=f"exec-{i}", plan_id=f"plan-{i}", drift_type="config_drift",
                action_types_used=["restart"],
                verdict=OutcomeVerdict.EFFECTIVE if i < 3 else OutcomeVerdict.INEFFECTIVE,
            )
        assert len(tracker.get_outcomes(verdict=OutcomeVerdict.EFFECTIVE)) == 3

    def test_get_outcomes_for_drift_type(self) -> None:
        from src.kortana.services.outcome_tracker import OutcomeTracker, OutcomeVerdict
        tracker = OutcomeTracker()
        tracker.record_outcome(
            execution_id="e1", plan_id="p1", drift_type="config_drift",
            action_types_used=["restart"], verdict=OutcomeVerdict.EFFECTIVE,
        )
        tracker.record_outcome(
            execution_id="e2", plan_id="p2", drift_type="schema_drift",
            action_types_used=["apply"], verdict=OutcomeVerdict.INEFFECTIVE,
        )
        assert len(tracker.get_outcomes_for_drift_type("config_drift")) == 1

    def test_get_outcomes_for_action_type(self) -> None:
        from src.kortana.services.outcome_tracker import OutcomeTracker, OutcomeVerdict
        tracker = OutcomeTracker()
        tracker.record_outcome(
            execution_id="e1", plan_id="p1", drift_type="config_drift",
            action_types_used=["restart_service", "apply_config"],
            verdict=OutcomeVerdict.EFFECTIVE,
        )
        assert len(tracker.get_outcomes_for_action_type("restart_service")) == 1
        assert len(tracker.get_outcomes_for_action_type("rollback")) == 0

    def test_effectiveness_rate(self) -> None:
        from src.kortana.services.outcome_tracker import OutcomeTracker, OutcomeVerdict
        tracker = OutcomeTracker()
        tracker.record_outcome(
            execution_id="e1", plan_id="p1", drift_type="d",
            action_types_used=["a"], verdict=OutcomeVerdict.EFFECTIVE,
        )
        tracker.record_outcome(
            execution_id="e2", plan_id="p2", drift_type="d",
            action_types_used=["a"], verdict=OutcomeVerdict.INEFFECTIVE,
        )
        assert tracker.get_effectiveness_rate() == pytest.approx(0.5, abs=0.01)

    def test_avg_resolution_time(self) -> None:
        from src.kortana.services.outcome_tracker import OutcomeTracker, OutcomeVerdict
        tracker = OutcomeTracker()
        tracker.record_outcome(
            execution_id="e1", plan_id="p1", drift_type="d",
            action_types_used=["a"], verdict=OutcomeVerdict.EFFECTIVE, time_to_resolve_sec=10.0,
        )
        tracker.record_outcome(
            execution_id="e2", plan_id="p2", drift_type="d",
            action_types_used=["a"], verdict=OutcomeVerdict.EFFECTIVE, time_to_resolve_sec=20.0,
        )
        assert tracker.get_avg_resolution_time() == pytest.approx(15.0, abs=0.1)

    def test_avg_retries(self) -> None:
        from src.kortana.services.outcome_tracker import OutcomeTracker, OutcomeVerdict
        tracker = OutcomeTracker()
        tracker.record_outcome(
            execution_id="e1", plan_id="p1", drift_type="d",
            action_types_used=["a"], verdict=OutcomeVerdict.EFFECTIVE, retries_needed=2,
        )
        tracker.record_outcome(
            execution_id="e2", plan_id="p2", drift_type="d",
            action_types_used=["a"], verdict=OutcomeVerdict.EFFECTIVE, retries_needed=4,
        )
        assert tracker.get_avg_retries() == pytest.approx(3.0, abs=0.1)

    def test_escalation_rate(self) -> None:
        from src.kortana.services.outcome_tracker import OutcomeTracker, OutcomeVerdict
        tracker = OutcomeTracker()
        tracker.record_outcome(
            execution_id="e1", plan_id="p1", drift_type="d",
            action_types_used=["a"], verdict=OutcomeVerdict.EFFECTIVE, escalated=True,
        )
        tracker.record_outcome(
            execution_id="e2", plan_id="p2", drift_type="d",
            action_types_used=["a"], verdict=OutcomeVerdict.EFFECTIVE, escalated=False,
        )
        assert tracker.get_escalation_rate() == pytest.approx(0.5, abs=0.01)

    def test_stability_rate(self) -> None:
        from src.kortana.services.outcome_tracker import OutcomeTracker, OutcomeVerdict
        tracker = OutcomeTracker()
        tracker.record_outcome(
            execution_id="e1", plan_id="p1", drift_type="d",
            action_types_used=["a"], verdict=OutcomeVerdict.EFFECTIVE, resolution_stable=True,
        )
        tracker.record_outcome(
            execution_id="e2", plan_id="p2", drift_type="d",
            action_types_used=["a"], verdict=OutcomeVerdict.EFFECTIVE, resolution_stable=False,
        )
        assert tracker.get_stability_rate() == pytest.approx(0.5, abs=0.01)

    def test_summary(self) -> None:
        from src.kortana.services.outcome_tracker import OutcomeTracker, OutcomeVerdict
        tracker = OutcomeTracker()
        tracker.record_outcome(
            execution_id="e1", plan_id="p1", drift_type="config_drift",
            action_types_used=["a"], verdict=OutcomeVerdict.EFFECTIVE, time_to_resolve_sec=10.0,
        )
        summary = tracker.get_summary()
        assert summary["total_outcomes"] == 1
        assert "effectiveness_rate" in summary

    def test_outcome_to_dict(self) -> None:
        from src.kortana.services.outcome_tracker import OutcomeTracker, OutcomeVerdict
        tracker = OutcomeTracker()
        outcome = tracker.record_outcome(
            execution_id="exec-1", plan_id="plan-1", drift_type="config_drift",
            action_types_used=["restart"], verdict=OutcomeVerdict.EFFECTIVE,
        )
        d = outcome.to_dict()
        assert d["execution_id"] == "exec-1"
        assert d["verdict"] == "effective"

    def test_outcome_hash_generated(self) -> None:
        from src.kortana.services.outcome_tracker import OutcomeTracker, OutcomeVerdict
        tracker = OutcomeTracker()
        outcome = tracker.record_outcome(
            execution_id="e1", plan_id="p1", drift_type="d",
            action_types_used=["a"], verdict=OutcomeVerdict.EFFECTIVE,
        )
        assert len(outcome.outcome_hash) == 64

    def test_module_singleton(self) -> None:
        from src.kortana.services.outcome_tracker import get_outcome_tracker
        t1 = get_outcome_tracker()
        t2 = get_outcome_tracker()
        assert t1 is t2


# ── V19B — StrategyLearner Tests ─────────────────────────────────────────


class TestStrategyLearner:
    """Tests for strategy_learner.py."""

    def _populate_tracker(self, n: int = 5):
        from src.kortana.services.outcome_tracker import OutcomeTracker, OutcomeVerdict
        self._tracker = OutcomeTracker()
        for i in range(n):
            self._tracker.record_outcome(
                execution_id=f"exec-{i}", plan_id=f"plan-{i}", drift_type="config_drift",
                action_types_used=["restart_service"],
                verdict=OutcomeVerdict.EFFECTIVE if i % 2 == 0 else OutcomeVerdict.INEFFECTIVE,
                time_to_resolve_sec=10.0 + i,
                retries_needed=i,
                escalated=i > 3,
                resolution_stable=i < 4,
            )

    def test_action_effectiveness_empty(self) -> None:
        from src.kortana.services.outcome_tracker import OutcomeTracker
        from src.kortana.services.strategy_learner import StrategyLearner
        learner = StrategyLearner(tracker=OutcomeTracker())
        eff = learner.get_action_effectiveness("restart_service")
        assert eff.sample_size == 0

    def test_action_effectiveness_populated(self) -> None:
        from src.kortana.services.strategy_learner import StrategyLearner
        self._populate_tracker(5)
        learner = StrategyLearner(tracker=self._tracker)
        result = learner.get_action_effectiveness("restart_service")
        assert result.action_type == "restart_service"
        assert result.sample_size == 5

    def test_recommend_no_data(self) -> None:
        from src.kortana.services.outcome_tracker import OutcomeTracker
        from src.kortana.services.strategy_learner import StrategyLearner
        learner = StrategyLearner(tracker=OutcomeTracker())
        rec = learner.recommend_for_drift_type("config_drift")
        assert rec.confidence_score == 0.0
        assert "insufficient" in rec.reasoning.lower()

    def test_recommend_with_data(self) -> None:
        from src.kortana.services.strategy_learner import StrategyLearner
        self._populate_tracker(5)
        learner = StrategyLearner(tracker=self._tracker)
        rec = learner.recommend_for_drift_type("config_drift")
        assert rec.confidence_score > 0
        assert len(rec.recommended_actions) > 0

    def test_priority_adjustment(self) -> None:
        from src.kortana.services.strategy_learner import StrategyLearner
        self._populate_tracker(5)
        learner = StrategyLearner(tracker=self._tracker)
        adj = learner.get_priority_adjustment("config_drift")
        assert isinstance(adj, str)

    def test_retry_recommendation(self) -> None:
        from src.kortana.services.strategy_learner import StrategyLearner
        self._populate_tracker(5)
        learner = StrategyLearner(tracker=self._tracker)
        rec = learner.get_retry_recommendation("config_drift")
        assert isinstance(rec, int)
        assert rec >= 3

    def test_escalation_timing(self) -> None:
        from src.kortana.services.strategy_learner import StrategyLearner
        self._populate_tracker(5)
        learner = StrategyLearner(tracker=self._tracker)
        timing = learner.get_escalation_timing("config_drift")
        assert "escalation_rate" in timing

    def test_recommendation_to_dict(self) -> None:
        from src.kortana.services.strategy_learner import StrategyLearner
        self._populate_tracker(5)
        learner = StrategyLearner(tracker=self._tracker)
        rec = learner.recommend_for_drift_type("config_drift")
        d = rec.to_dict()
        assert "recommendation_id" in d
        assert "confidence_score" in d

    def test_recommendation_hash(self) -> None:
        from src.kortana.services.strategy_learner import StrategyLearner
        self._populate_tracker(5)
        learner = StrategyLearner(tracker=self._tracker)
        rec = learner.recommend_for_drift_type("config_drift")
        assert len(rec.recommendation_hash) == 64

    def test_module_singleton(self) -> None:
        from src.kortana.services.strategy_learner import get_strategy_learner
        l1 = get_strategy_learner()
        l2 = get_strategy_learner()
        assert l1 is l2


# ── V19C — AdaptivePlanner Tests ─────────────────────────────────────────


class TestAdaptivePlanner:
    """Tests for adaptive_planner.py."""

    def _make_signal(self, drift_type: str = "config_drift"):
        from src.kortana.services.drift_detector import DriftSignal, DriftType, DriftSeverity
        dt = DriftType(drift_type) if drift_type in [d.value for d in DriftType] else DriftType.CONFIG_DRIFT
        return DriftSignal(drift_type=dt, severity=DriftSeverity.MEDIUM, provider_name="test")

    def test_plan_from_drift_adaptive_no_learning(self) -> None:
        from src.kortana.services.outcome_tracker import OutcomeTracker
        from src.kortana.services.strategy_learner import StrategyLearner
        from src.kortana.services.adaptive_planner import AdaptivePlanner
        tracker = OutcomeTracker()
        learner = StrategyLearner(tracker=tracker)
        planner = AdaptivePlanner(learner=learner)
        plan = planner.plan_from_drift_adaptive(self._make_signal())
        assert plan.learning_applied is False
        assert plan.confidence_score == 0.0

    def test_plan_from_drift_adaptive_with_learning(self) -> None:
        from src.kortana.services.outcome_tracker import OutcomeTracker, OutcomeVerdict
        from src.kortana.services.strategy_learner import StrategyLearner
        from src.kortana.services.adaptive_planner import AdaptivePlanner
        tracker = OutcomeTracker()
        for i in range(5):
            tracker.record_outcome(
                execution_id=f"e{i}", plan_id=f"p{i}", drift_type="config_drift",
                action_types_used=["restart_service"],
                verdict=OutcomeVerdict.EFFECTIVE,
                time_to_resolve_sec=5.0, retries_needed=1,
                resolution_stable=True,
            )
        learner = StrategyLearner(tracker=tracker)
        planner = AdaptivePlanner(learner=learner)
        plan = planner.plan_from_drift_adaptive(self._make_signal())
        assert plan.confidence_score > 0.0
        assert plan.confidence_score <= 1.0

    def test_plan_batch(self) -> None:
        from src.kortana.services.adaptive_planner import AdaptivePlanner
        planner = AdaptivePlanner()
        signals = [self._make_signal(), self._make_signal("schema_drift")]
        plans = planner.plan_from_batch_adaptive(signals)
        assert len(plans) == 2

    def test_learning_stats(self) -> None:
        from src.kortana.services.adaptive_planner import AdaptivePlanner
        planner = AdaptivePlanner()
        planner.plan_from_drift_adaptive(self._make_signal())
        stats = planner.get_learning_stats()
        assert "total_plans" in stats
        assert stats["total_plans"] == 1

    def test_get_adaptive_plans(self) -> None:
        from src.kortana.services.adaptive_planner import AdaptivePlanner
        planner = AdaptivePlanner()
        planner.plan_from_drift_adaptive(self._make_signal())
        assert planner.plan_count == 1
        assert len(planner.get_adaptive_plans()) == 1

    def test_filter_by_learning_applied(self) -> None:
        from src.kortana.services.adaptive_planner import AdaptivePlanner
        planner = AdaptivePlanner()
        planner.plan_from_drift_adaptive(self._make_signal())
        learned = planner.get_adaptive_plans(learning_applied=True)
        not_learned = planner.get_adaptive_plans(learning_applied=False)
        assert len(learned) + len(not_learned) == planner.plan_count

    def test_adaptive_plan_to_dict(self) -> None:
        from src.kortana.services.adaptive_planner import AdaptivePlanner
        planner = AdaptivePlanner()
        plan = planner.plan_from_drift_adaptive(self._make_signal())
        d = plan.to_dict()
        assert "learning_applied" in d
        assert "confidence_score" in d
        assert "plan_hash" in d

    def test_adaptive_override_to_dict(self) -> None:
        from src.kortana.services.adaptive_planner import AdaptiveOverride
        override = AdaptiveOverride(
            field_name="priority", original_value="normal",
            learned_value="high", confidence=0.85,
        )
        d = override.to_dict()
        assert d["field_name"] == "priority"
        assert d["confidence"] == 0.85

    def test_plan_hash_generated(self) -> None:
        from src.kortana.services.adaptive_planner import AdaptivePlanner
        planner = AdaptivePlanner()
        plan = planner.plan_from_drift_adaptive(self._make_signal())
        assert len(plan.plan_hash) == 64

    def test_module_singleton(self) -> None:
        from src.kortana.services.adaptive_planner import get_adaptive_planner
        p1 = get_adaptive_planner()
        p2 = get_adaptive_planner()
        assert p1 is p2


# ── V19D — ImprovementTracker Tests ──────────────────────────────────────


class TestImprovementTracker:
    """Tests for improvement_tracker.py."""

    def _build_tracker_with_outcomes(self, n_default: int = 5, n_learned: int = 5):
        from src.kortana.services.outcome_tracker import OutcomeTracker, OutcomeVerdict
        from src.kortana.services.improvement_tracker import ImprovementTracker
        tracker = OutcomeTracker()
        for i in range(n_default):
            tracker.record_outcome(
                execution_id=f"d-{i}", plan_id=f"dp-{i}", drift_type="config_drift",
                action_types_used=["restart"],
                verdict=OutcomeVerdict.EFFECTIVE if i % 2 == 0 else OutcomeVerdict.INEFFECTIVE,
                time_to_resolve_sec=20.0, learning_applied=False,
            )
        for i in range(n_learned):
            tracker.record_outcome(
                execution_id=f"l-{i}", plan_id=f"lp-{i}", drift_type="config_drift",
                action_types_used=["restart"],
                verdict=OutcomeVerdict.EFFECTIVE,
                time_to_resolve_sec=10.0, learning_applied=True,
            )
        return ImprovementTracker(tracker=tracker)

    def test_generate_report_empty(self) -> None:
        from src.kortana.services.outcome_tracker import OutcomeTracker
        from src.kortana.services.improvement_tracker import ImprovementTracker
        it = ImprovementTracker(tracker=OutcomeTracker())
        report = it.generate_report()
        assert report.total_outcomes_analyzed == 0

    def test_generate_report_with_data(self) -> None:
        it = self._build_tracker_with_outcomes()
        report = it.generate_report()
        assert report.total_outcomes_analyzed == 10
        assert report.total_default_outcomes == 5
        assert report.total_learned_outcomes == 5
        assert len(report.metrics) >= 1

    def test_improvement_pct(self) -> None:
        it = self._build_tracker_with_outcomes()
        report = it.generate_report()
        assert report.overall_improvement_pct > 0

    def test_maturity_nascent(self) -> None:
        from src.kortana.services.outcome_tracker import OutcomeTracker
        from src.kortana.services.improvement_tracker import ImprovementTracker, LearningMaturity
        it = ImprovementTracker(tracker=OutcomeTracker())
        assert it.get_learning_maturity() == LearningMaturity.NASCENT

    def test_maturity_upgrades(self) -> None:
        from src.kortana.services.improvement_tracker import LearningMaturity
        it = self._build_tracker_with_outcomes(n_default=10, n_learned=15)
        report = it.generate_report()
        assert report.learning_maturity in (LearningMaturity.MATURE, LearningMaturity.EXPERT)

    def test_improvement_trend(self) -> None:
        it = self._build_tracker_with_outcomes()
        it.generate_report()
        it.generate_report()
        trend = it.get_improvement_trend()
        assert len(trend) == 2

    def test_latest_report(self) -> None:
        it = self._build_tracker_with_outcomes()
        assert it.get_latest_report() is None
        it.generate_report()
        assert it.get_latest_report() is not None

    def test_report_count(self) -> None:
        it = self._build_tracker_with_outcomes()
        assert it.report_count == 0
        it.generate_report()
        assert it.report_count == 1

    def test_report_to_dict(self) -> None:
        it = self._build_tracker_with_outcomes()
        report = it.generate_report()
        d = report.to_dict()
        assert "overall_improvement_pct" in d
        assert "learning_maturity" in d

    def test_metric_to_dict(self) -> None:
        it = self._build_tracker_with_outcomes()
        report = it.generate_report()
        if report.metrics:
            d = report.metrics[0].to_dict()
            assert "drift_type" in d
            assert "improvement_pct" in d

    def test_report_hash(self) -> None:
        it = self._build_tracker_with_outcomes()
        report = it.generate_report()
        assert len(report.report_hash) == 64

    def test_module_singleton(self) -> None:
        from src.kortana.services.improvement_tracker import get_improvement_tracker
        t1 = get_improvement_tracker()
        t2 = get_improvement_tracker()
        assert t1 is t2
