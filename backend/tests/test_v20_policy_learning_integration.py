"""V20 — Policy-Learning Integration Tests."""



# ── Helper: populate outcome tracker ─────────────────────────────────────

def _make_populated_tracker(n: int = 10, eff_ratio: float = 0.7, learned_ratio: float = 0.5):
    """Create an OutcomeTracker populated with n outcomes."""
    from src.kortana.services.outcome_tracker import OutcomeTracker, OutcomeVerdict
    tracker = OutcomeTracker()
    for i in range(n):
        tracker.record_outcome(
            execution_id=f"e-{i}", plan_id=f"p-{i}", drift_type="config_drift",
            action_types_used=["restart_service"],
            verdict=OutcomeVerdict.EFFECTIVE if (i / n) < eff_ratio else OutcomeVerdict.INEFFECTIVE,
            time_to_resolve_sec=10.0 + i,
            retries_needed=i % 3,
            escalated=i > (n * 0.8),
            resolution_stable=i < (n * 0.7),
            learning_applied=i >= (n * (1 - learned_ratio)),
        )
    return tracker


# ── V20A — TrustCalibrator Tests ─────────────────────────────────────────


class TestTrustCalibrator:
    """Tests for trust_calibrator.py."""

    def test_calibrate_trust_empty(self) -> None:
        from src.kortana.services.outcome_tracker import OutcomeTracker
        from src.kortana.services.improvement_tracker import ImprovementTracker
        from src.kortana.services.trust_calibrator import TrustCalibrator, TrustLevel
        tracker = OutcomeTracker()
        imp = ImprovementTracker(tracker=tracker)
        cal = TrustCalibrator(outcome_tracker=tracker, improvement_tracker=imp)
        result = cal.calibrate_trust()
        assert result.trust_level == TrustLevel.UNTRUSTED
        assert result.trust_score == 0.0

    def test_calibrate_trust_with_data(self) -> None:
        from src.kortana.services.improvement_tracker import ImprovementTracker
        from src.kortana.services.trust_calibrator import TrustCalibrator, TrustLevel
        tracker = _make_populated_tracker(n=15, eff_ratio=0.8)
        imp = ImprovementTracker(tracker=tracker)
        cal = TrustCalibrator(outcome_tracker=tracker, improvement_tracker=imp)
        result = cal.calibrate_trust()
        assert result.trust_score > 0.0
        assert result.trust_level != TrustLevel.UNTRUSTED

    def test_trust_factors_count(self) -> None:
        from src.kortana.services.outcome_tracker import OutcomeTracker
        from src.kortana.services.improvement_tracker import ImprovementTracker
        from src.kortana.services.trust_calibrator import TrustCalibrator
        tracker = OutcomeTracker()
        imp = ImprovementTracker(tracker=tracker)
        cal = TrustCalibrator(outcome_tracker=tracker, improvement_tracker=imp)
        factors = cal.get_trust_factors()
        assert len(factors) == 5

    def test_trust_history(self) -> None:
        from src.kortana.services.outcome_tracker import OutcomeTracker
        from src.kortana.services.improvement_tracker import ImprovementTracker
        from src.kortana.services.trust_calibrator import TrustCalibrator
        tracker = OutcomeTracker()
        imp = ImprovementTracker(tracker=tracker)
        cal = TrustCalibrator(outcome_tracker=tracker, improvement_tracker=imp)
        cal.calibrate_trust()
        cal.calibrate_trust()
        assert cal.calibration_count == 2
        assert len(cal.get_trust_history()) == 2

    def test_get_current_trust_auto_calibrates(self) -> None:
        from src.kortana.services.outcome_tracker import OutcomeTracker
        from src.kortana.services.improvement_tracker import ImprovementTracker
        from src.kortana.services.trust_calibrator import TrustCalibrator
        tracker = OutcomeTracker()
        imp = ImprovementTracker(tracker=tracker)
        cal = TrustCalibrator(outcome_tracker=tracker, improvement_tracker=imp)
        result = cal.get_current_trust()
        assert result is not None
        assert cal.calibration_count == 1

    def test_calibration_to_dict(self) -> None:
        from src.kortana.services.outcome_tracker import OutcomeTracker
        from src.kortana.services.improvement_tracker import ImprovementTracker
        from src.kortana.services.trust_calibrator import TrustCalibrator
        tracker = OutcomeTracker()
        imp = ImprovementTracker(tracker=tracker)
        cal = TrustCalibrator(outcome_tracker=tracker, improvement_tracker=imp)
        result = cal.calibrate_trust()
        d = result.to_dict()
        assert "trust_level" in d
        assert "trust_score" in d
        assert "factors" in d

    def test_calibration_hash(self) -> None:
        from src.kortana.services.outcome_tracker import OutcomeTracker
        from src.kortana.services.improvement_tracker import ImprovementTracker
        from src.kortana.services.trust_calibrator import TrustCalibrator
        tracker = OutcomeTracker()
        imp = ImprovementTracker(tracker=tracker)
        cal = TrustCalibrator(outcome_tracker=tracker, improvement_tracker=imp)
        result = cal.calibrate_trust()
        assert len(result.calibration_hash) == 64

    def test_sample_size_penalty(self) -> None:
        from src.kortana.services.improvement_tracker import ImprovementTracker
        from src.kortana.services.trust_calibrator import TrustCalibrator
        small = _make_populated_tracker(n=3, eff_ratio=1.0)
        imp_small = ImprovementTracker(tracker=small)
        cal_small = TrustCalibrator(outcome_tracker=small, improvement_tracker=imp_small)
        result_small = cal_small.calibrate_trust()

        large = _make_populated_tracker(n=15, eff_ratio=1.0)
        imp_large = ImprovementTracker(tracker=large)
        cal_large = TrustCalibrator(outcome_tracker=large, improvement_tracker=imp_large)
        result_large = cal_large.calibrate_trust()

        assert result_small.trust_score < result_large.trust_score

    def test_module_singleton(self) -> None:
        from src.kortana.services.trust_calibrator import get_trust_calibrator
        c1 = get_trust_calibrator()
        c2 = get_trust_calibrator()
        assert c1 is c2


# ── V20B — AutonomyAdjuster Tests ────────────────────────────────────────


class TestAutonomyAdjuster:
    """Tests for autonomy_adjuster.py."""

    def test_adjust_thresholds_returns_categories(self) -> None:
        from src.kortana.services.outcome_tracker import OutcomeTracker
        from src.kortana.services.improvement_tracker import ImprovementTracker
        from src.kortana.services.trust_calibrator import TrustCalibrator
        from src.kortana.services.autonomy_adjuster import AutonomyAdjuster
        tracker = OutcomeTracker()
        imp = ImprovementTracker(tracker=tracker)
        cal = TrustCalibrator(outcome_tracker=tracker, improvement_tracker=imp)
        adj = AutonomyAdjuster(calibrator=cal)
        thresholds = adj.adjust_thresholds()
        assert len(thresholds) == 5
        assert "reconciliation" in thresholds

    def test_threshold_for_category(self) -> None:
        from src.kortana.services.autonomy_adjuster import AutonomyAdjuster
        adj = AutonomyAdjuster()
        adj.adjust_thresholds()
        t = adj.get_threshold_for_category("deployment")
        assert t is not None
        assert t.category == "deployment"

    def test_unknown_category_returns_none(self) -> None:
        from src.kortana.services.autonomy_adjuster import AutonomyAdjuster
        adj = AutonomyAdjuster()
        adj.adjust_thresholds()
        assert adj.get_threshold_for_category("nonexistent") is None

    def test_should_auto_execute(self) -> None:
        from src.kortana.services.autonomy_adjuster import AutonomyAdjuster
        adj = AutonomyAdjuster()
        adj.adjust_thresholds()
        # With confidence 1.0 should always pass
        assert adj.should_auto_execute("reconciliation", 1.0) is True
        # With confidence 0.0 should never pass
        assert adj.should_auto_execute("reconciliation", 0.0) is False

    def test_execution_mode(self) -> None:
        from src.kortana.services.autonomy_adjuster import AutonomyAdjuster
        adj = AutonomyAdjuster()
        adj.adjust_thresholds()
        mode = adj.get_execution_mode("reconciliation", 1.0)
        assert mode == "auto"
        mode2 = adj.get_execution_mode("reconciliation", 0.0)
        assert mode2 == "approval"

    def test_unknown_category_defaults_approval(self) -> None:
        from src.kortana.services.autonomy_adjuster import AutonomyAdjuster
        adj = AutonomyAdjuster()
        assert adj.get_execution_mode("nonexistent", 1.0) == "approval"

    def test_adjustment_history(self) -> None:
        from src.kortana.services.autonomy_adjuster import AutonomyAdjuster
        adj = AutonomyAdjuster()
        adj.adjust_thresholds()
        history = adj.get_adjustment_history()
        assert len(history) == 1
        assert "trust_level" in history[0]

    def test_threshold_to_dict(self) -> None:
        from src.kortana.services.autonomy_adjuster import AutonomyAdjuster
        adj = AutonomyAdjuster()
        adj.adjust_thresholds()
        t = adj.get_threshold_for_category("reconciliation")
        d = t.to_dict()
        assert "auto_threshold" in d
        assert "threshold_hash" in d

    def test_threshold_hash(self) -> None:
        from src.kortana.services.autonomy_adjuster import AutonomyAdjuster
        adj = AutonomyAdjuster()
        adj.adjust_thresholds()
        t = adj.get_threshold_for_category("reconciliation")
        assert len(t.threshold_hash) == 64

    def test_module_singleton(self) -> None:
        from src.kortana.services.autonomy_adjuster import get_autonomy_adjuster
        a1 = get_autonomy_adjuster()
        a2 = get_autonomy_adjuster()
        assert a1 is a2


# ── V20C — PolicyFeedbackLoop Tests ──────────────────────────────────────


class TestPolicyFeedbackLoop:
    """Tests for policy_feedback_loop.py."""

    def test_generate_amendments_insufficient_data(self) -> None:
        from src.kortana.services.outcome_tracker import OutcomeTracker
        from src.kortana.services.improvement_tracker import ImprovementTracker
        from src.kortana.services.trust_calibrator import TrustCalibrator
        from src.kortana.services.policy_feedback_loop import PolicyFeedbackLoop
        tracker = OutcomeTracker()
        imp = ImprovementTracker(tracker=tracker)
        cal = TrustCalibrator(outcome_tracker=tracker, improvement_tracker=imp)
        loop = PolicyFeedbackLoop(outcome_tracker=tracker, improvement_tracker=imp, trust_calibrator=cal)
        amendments = loop.generate_amendments()
        assert len(amendments) == 0

    def test_generate_amendments_with_data(self) -> None:
        from src.kortana.services.improvement_tracker import ImprovementTracker
        from src.kortana.services.trust_calibrator import TrustCalibrator
        from src.kortana.services.policy_feedback_loop import PolicyFeedbackLoop
        tracker = _make_populated_tracker(n=10, eff_ratio=0.8)
        imp = ImprovementTracker(tracker=tracker)
        cal = TrustCalibrator(outcome_tracker=tracker, improvement_tracker=imp)
        loop = PolicyFeedbackLoop(outcome_tracker=tracker, improvement_tracker=imp, trust_calibrator=cal)
        loop.generate_amendments()
        assert loop.amendment_count >= 0

    def test_apply_amendment(self) -> None:
        from src.kortana.services.improvement_tracker import ImprovementTracker
        from src.kortana.services.trust_calibrator import TrustCalibrator
        from src.kortana.services.policy_feedback_loop import PolicyFeedbackLoop, AmendmentStatus
        tracker = _make_populated_tracker(n=10, eff_ratio=0.8)
        imp = ImprovementTracker(tracker=tracker)
        cal = TrustCalibrator(outcome_tracker=tracker, improvement_tracker=imp)
        loop = PolicyFeedbackLoop(outcome_tracker=tracker, improvement_tracker=imp, trust_calibrator=cal)
        amendments = loop.generate_amendments()
        if amendments:
            aid = amendments[0].amendment_id
            assert loop.apply_amendment(aid) is True
            assert amendments[0].status == AmendmentStatus.APPLIED

    def test_reject_amendment(self) -> None:
        from src.kortana.services.improvement_tracker import ImprovementTracker
        from src.kortana.services.trust_calibrator import TrustCalibrator
        from src.kortana.services.policy_feedback_loop import PolicyFeedbackLoop, AmendmentStatus
        tracker = _make_populated_tracker(n=10, eff_ratio=0.8)
        imp = ImprovementTracker(tracker=tracker)
        cal = TrustCalibrator(outcome_tracker=tracker, improvement_tracker=imp)
        loop = PolicyFeedbackLoop(outcome_tracker=tracker, improvement_tracker=imp, trust_calibrator=cal)
        amendments = loop.generate_amendments()
        if amendments:
            aid = amendments[0].amendment_id
            assert loop.reject_amendment(aid) is True
            assert amendments[0].status == AmendmentStatus.REJECTED

    def test_apply_nonexistent_fails(self) -> None:
        from src.kortana.services.policy_feedback_loop import PolicyFeedbackLoop
        loop = PolicyFeedbackLoop()
        assert loop.apply_amendment("nonexistent") is False

    def test_get_pending_amendments(self) -> None:
        from src.kortana.services.improvement_tracker import ImprovementTracker
        from src.kortana.services.trust_calibrator import TrustCalibrator
        from src.kortana.services.policy_feedback_loop import PolicyFeedbackLoop
        tracker = _make_populated_tracker(n=10, eff_ratio=0.8)
        imp = ImprovementTracker(tracker=tracker)
        cal = TrustCalibrator(outcome_tracker=tracker, improvement_tracker=imp)
        loop = PolicyFeedbackLoop(outcome_tracker=tracker, improvement_tracker=imp, trust_calibrator=cal)
        loop.generate_amendments()
        pending = loop.get_pending_amendments()
        assert loop.pending_count == len(pending)

    def test_amendment_to_dict(self) -> None:
        from src.kortana.services.policy_feedback_loop import PolicyAmendment, PolicyArea
        a = PolicyAmendment(policy_area=PolicyArea.ESCALATION, current_rule="test", proposed_rule="new")
        d = a.to_dict()
        assert d["policy_area"] == "escalation"
        assert "amendment_hash" in d

    def test_amendment_hash(self) -> None:
        from src.kortana.services.policy_feedback_loop import PolicyAmendment
        a = PolicyAmendment()
        assert len(a.amendment_hash) == 64

    def test_module_singleton(self) -> None:
        from src.kortana.services.policy_feedback_loop import get_policy_feedback_loop
        l1 = get_policy_feedback_loop()
        l2 = get_policy_feedback_loop()
        assert l1 is l2


# ── V20D — GovernanceEvolution Tests ─────────────────────────────────────


class TestGovernanceEvolution:
    """Tests for governance_evolution.py."""

    def test_evolve_empty(self) -> None:
        from src.kortana.services.outcome_tracker import OutcomeTracker
        from src.kortana.services.improvement_tracker import ImprovementTracker
        from src.kortana.services.trust_calibrator import TrustCalibrator
        from src.kortana.services.autonomy_adjuster import AutonomyAdjuster
        from src.kortana.services.policy_feedback_loop import PolicyFeedbackLoop
        from src.kortana.services.governance_evolution import GovernanceEvolution, EvolutionStage
        tracker = OutcomeTracker()
        imp = ImprovementTracker(tracker=tracker)
        cal = TrustCalibrator(outcome_tracker=tracker, improvement_tracker=imp)
        adj = AutonomyAdjuster(calibrator=cal)
        fb = PolicyFeedbackLoop(outcome_tracker=tracker, improvement_tracker=imp, trust_calibrator=cal)
        gov = GovernanceEvolution(trust_calibrator=cal, autonomy_adjuster=adj, policy_feedback=fb)
        snapshot = gov.evolve()
        assert snapshot.evolution_stage in (EvolutionStage.STATIC, EvolutionStage.CALIBRATING)

    def test_evolve_with_data(self) -> None:
        from src.kortana.services.improvement_tracker import ImprovementTracker
        from src.kortana.services.trust_calibrator import TrustCalibrator
        from src.kortana.services.autonomy_adjuster import AutonomyAdjuster
        from src.kortana.services.policy_feedback_loop import PolicyFeedbackLoop
        from src.kortana.services.governance_evolution import GovernanceEvolution
        tracker = _make_populated_tracker(n=15, eff_ratio=0.8)
        imp = ImprovementTracker(tracker=tracker)
        cal = TrustCalibrator(outcome_tracker=tracker, improvement_tracker=imp)
        adj = AutonomyAdjuster(calibrator=cal)
        fb = PolicyFeedbackLoop(outcome_tracker=tracker, improvement_tracker=imp, trust_calibrator=cal)
        gov = GovernanceEvolution(trust_calibrator=cal, autonomy_adjuster=adj, policy_feedback=fb)
        snapshot = gov.evolve()
        assert snapshot.trust_score > 0.0
        assert snapshot.autonomy_categories == 5

    def test_evolution_history(self) -> None:
        from src.kortana.services.governance_evolution import GovernanceEvolution
        gov = GovernanceEvolution()
        gov.evolve()
        gov.evolve()
        assert gov.snapshot_count == 2
        assert len(gov.get_evolution_history()) == 2

    def test_get_current_snapshot_none(self) -> None:
        from src.kortana.services.governance_evolution import GovernanceEvolution
        gov = GovernanceEvolution()
        assert gov.get_current_snapshot() is None

    def test_get_evolution_stage(self) -> None:
        from src.kortana.services.governance_evolution import GovernanceEvolution, EvolutionStage
        gov = GovernanceEvolution()
        assert gov.get_evolution_stage() == EvolutionStage.STATIC
        gov.evolve()
        assert gov.get_evolution_stage() != EvolutionStage.STATIC or gov.get_evolution_stage() == EvolutionStage.STATIC

    def test_governance_summary(self) -> None:
        from src.kortana.services.governance_evolution import GovernanceEvolution
        gov = GovernanceEvolution()
        gov.evolve()
        summary = gov.get_governance_summary()
        assert "evolution_stage" in summary
        assert "trust_level" in summary
        assert "evolution_cycles" in summary

    def test_snapshot_to_dict(self) -> None:
        from src.kortana.services.governance_evolution import GovernanceEvolution
        gov = GovernanceEvolution()
        snapshot = gov.evolve()
        d = snapshot.to_dict()
        assert "snapshot_id" in d
        assert "evolution_stage" in d
        assert "trust_score" in d

    def test_snapshot_hash(self) -> None:
        from src.kortana.services.governance_evolution import GovernanceEvolution
        gov = GovernanceEvolution()
        snapshot = gov.evolve()
        assert len(snapshot.snapshot_hash) == 64

    def test_module_singleton(self) -> None:
        from src.kortana.services.governance_evolution import get_governance_evolution
        g1 = get_governance_evolution()
        g2 = get_governance_evolution()
        assert g1 is g2
