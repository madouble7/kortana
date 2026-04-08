"""Test V18 — Autonomous Reconciliation."""

import unittest

# ── V18A imports ──────────────────────────────────────────────────────────
from src.kortana.services.drift_detector import (
    DriftDetector,
    DesiredState,
    DriftSignal,
    DriftType,
    DriftSeverity,
    DriftStatus,
    get_drift_detector,
)

# ── V18B imports ──────────────────────────────────────────────────────────
from src.kortana.services.reconciliation_planner import (
    ReconciliationPlanner,
    ReconciliationPlan,
    ReconciliationActionType,
    PlanPriority,
    PlanStatus,
    get_reconciliation_planner,
)

# ── V18C imports ──────────────────────────────────────────────────────────
from src.kortana.services.reconciliation_executor import (
    ReconciliationExecutor,
    ExecutionStatus,
    StepOutcome,
    get_reconciliation_executor,
)

# ── V18D imports ──────────────────────────────────────────────────────────
from src.kortana.services.convergence_manager import (
    ConvergenceManager,
    ConvergenceStatus,
    SystemHealth,
    get_convergence_manager,
)


# ═══════════════════════════════════════════════════════════════════════════
# V18A — Drift Detector tests
# ═══════════════════════════════════════════════════════════════════════════


class TestDriftDetector(unittest.TestCase):
    """Tests for DriftDetector."""

    def setUp(self) -> None:
        self.detector = DriftDetector()

    def test_register_desired_state(self) -> None:
        state = DesiredState(provider_name="k8s", expected_version="v1.0")
        self.detector.register_desired_state(state)
        self.assertEqual(self.detector.desired_state_count, 1)

    def test_detect_version_mismatch(self) -> None:
        self.detector.register_desired_state(DesiredState(provider_name="k8s", expected_version="v1.0"))
        signals = self.detector.detect_provider_drift("k8s", actual_version="v0.9")
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].drift_type, DriftType.VERSION_MISMATCH)
        self.assertEqual(signals[0].severity, DriftSeverity.HIGH)

    def test_detect_connection_lost(self) -> None:
        self.detector.register_desired_state(DesiredState(provider_name="k8s"))
        signals = self.detector.detect_provider_drift("k8s", actual_connected=False)
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].drift_type, DriftType.CONNECTION_LOST)
        self.assertEqual(signals[0].severity, DriftSeverity.CRITICAL)

    def test_detect_health_degraded(self) -> None:
        self.detector.register_desired_state(DesiredState(provider_name="k8s"))
        signals = self.detector.detect_provider_drift("k8s", actual_healthy=False)
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].drift_type, DriftType.HEALTH_DEGRADED)

    def test_no_drift_when_matching(self) -> None:
        self.detector.register_desired_state(DesiredState(provider_name="k8s", expected_version="v1.0"))
        signals = self.detector.detect_provider_drift("k8s", actual_version="v1.0")
        self.assertEqual(len(signals), 0)

    def test_no_drift_unknown_provider(self) -> None:
        signals = self.detector.detect_provider_drift("unknown")
        self.assertEqual(len(signals), 0)

    def test_detect_rollout_stall(self) -> None:
        signal = self.detector.detect_rollout_stall("k8s", "rollout-1", 50.0)
        self.assertIsNotNone(signal)
        self.assertEqual(signal.drift_type, DriftType.ROLLOUT_STALLED)

    def test_no_stall_at_100(self) -> None:
        signal = self.detector.detect_rollout_stall("k8s", "rollout-1", 100.0)
        self.assertIsNone(signal)

    def test_detect_evidence_gap(self) -> None:
        signal = self.detector.detect_evidence_gap("chain-1", ["deployment", "convergence"])
        self.assertIsNotNone(signal)
        self.assertEqual(signal.drift_type, DriftType.EVIDENCE_GAP)

    def test_no_evidence_gap(self) -> None:
        signal = self.detector.detect_evidence_gap("chain-1", [])
        self.assertIsNone(signal)

    def test_detect_config_drift(self) -> None:
        signal = self.detector.detect_config_drift("k8s", "replicas", "3", "1")
        self.assertIsNotNone(signal)
        self.assertEqual(signal.drift_type, DriftType.CONFIG_DRIFT)

    def test_no_config_drift(self) -> None:
        signal = self.detector.detect_config_drift("k8s", "replicas", "3", "3")
        self.assertIsNone(signal)

    def test_acknowledge_drift(self) -> None:
        self.detector.register_desired_state(DesiredState(provider_name="k8s"))
        signals = self.detector.detect_provider_drift("k8s", actual_connected=False)
        ok = self.detector.acknowledge_drift(signals[0].signal_id)
        self.assertTrue(ok)
        self.assertEqual(signals[0].status, DriftStatus.ACKNOWLEDGED)

    def test_resolve_drift(self) -> None:
        self.detector.register_desired_state(DesiredState(provider_name="k8s"))
        signals = self.detector.detect_provider_drift("k8s", actual_connected=False)
        self.detector.resolve_drift(signals[0].signal_id)
        self.assertEqual(signals[0].status, DriftStatus.RESOLVED)
        self.assertNotEqual(signals[0].resolved_at, "")

    def test_ignore_drift(self) -> None:
        self.detector.register_desired_state(DesiredState(provider_name="k8s"))
        signals = self.detector.detect_provider_drift("k8s", actual_connected=False)
        self.detector.ignore_drift(signals[0].signal_id)
        self.assertEqual(signals[0].status, DriftStatus.IGNORED)

    def test_get_active_drifts(self) -> None:
        self.detector.register_desired_state(DesiredState(provider_name="k8s"))
        self.detector.detect_provider_drift("k8s", actual_connected=False)
        self.detector.detect_provider_drift("k8s", actual_healthy=False)
        self.assertEqual(self.detector.active_drift_count, 2)

    def test_signal_hash(self) -> None:
        self.detector.register_desired_state(DesiredState(provider_name="k8s"))
        signals = self.detector.detect_provider_drift("k8s", actual_connected=False)
        self.assertEqual(len(signals[0].signal_hash), 64)

    def test_module_singleton(self) -> None:
        d1 = get_drift_detector()
        d2 = get_drift_detector()
        self.assertIs(d1, d2)


# ═══════════════════════════════════════════════════════════════════════════
# V18B — Reconciliation Planner tests
# ═══════════════════════════════════════════════════════════════════════════


class TestReconciliationPlanner(unittest.TestCase):
    """Tests for ReconciliationPlanner."""

    def setUp(self) -> None:
        self.planner = ReconciliationPlanner()

    def _make_signal(self, drift_type: DriftType = DriftType.VERSION_MISMATCH,
                     severity: DriftSeverity = DriftSeverity.HIGH) -> DriftSignal:
        return DriftSignal(drift_type=drift_type, severity=severity, provider_name="k8s",
                           expected_value="v1.0", actual_value="v0.9")

    def test_plan_from_version_mismatch(self) -> None:
        signal = self._make_signal(DriftType.VERSION_MISMATCH)
        plan = self.planner.plan_from_drift(signal)
        self.assertEqual(plan.priority, PlanPriority.HIGH)
        self.assertEqual(plan.action_count, 2)  # REDEPLOY + REVERIFY
        types = [a.action_type for a in plan.actions]
        self.assertIn(ReconciliationActionType.REDEPLOY, types)
        self.assertIn(ReconciliationActionType.REVERIFY, types)

    def test_plan_from_connection_lost(self) -> None:
        signal = self._make_signal(DriftType.CONNECTION_LOST, DriftSeverity.CRITICAL)
        plan = self.planner.plan_from_drift(signal)
        self.assertEqual(plan.priority, PlanPriority.IMMEDIATE)
        types = [a.action_type for a in plan.actions]
        self.assertIn(ReconciliationActionType.RECONNECT, types)

    def test_plan_from_config_drift(self) -> None:
        signal = self._make_signal(DriftType.CONFIG_DRIFT, DriftSeverity.MEDIUM)
        plan = self.planner.plan_from_drift(signal)
        types = [a.action_type for a in plan.actions]
        self.assertIn(ReconciliationActionType.PATCH_CONFIG, types)

    def test_plan_from_evidence_gap(self) -> None:
        signal = self._make_signal(DriftType.EVIDENCE_GAP, DriftSeverity.MEDIUM)
        plan = self.planner.plan_from_drift(signal)
        types = [a.action_type for a in plan.actions]
        self.assertIn(ReconciliationActionType.RESEAL_EVIDENCE, types)

    def test_plan_from_rollout_stalled(self) -> None:
        signal = self._make_signal(DriftType.ROLLOUT_STALLED)
        plan = self.planner.plan_from_drift(signal)
        types = [a.action_type for a in plan.actions]
        self.assertIn(ReconciliationActionType.RESTART_ROLLOUT, types)

    def test_plan_from_batch(self) -> None:
        signals = [
            self._make_signal(DriftType.VERSION_MISMATCH, DriftSeverity.HIGH),
            self._make_signal(DriftType.CONNECTION_LOST, DriftSeverity.CRITICAL),
        ]
        plan = self.planner.plan_from_batch(signals)
        self.assertEqual(plan.priority, PlanPriority.IMMEDIATE)  # highest severity wins
        self.assertEqual(len(plan.drift_signal_ids), 2)
        self.assertTrue(plan.action_count >= 4)

    def test_plan_from_empty_batch(self) -> None:
        plan = self.planner.plan_from_batch([])
        self.assertEqual(plan.action_count, 0)

    def test_approve_plan(self) -> None:
        plan = self.planner.plan_from_drift(self._make_signal())
        ok = self.planner.approve_plan(plan.plan_id)
        self.assertTrue(ok)
        self.assertEqual(plan.status, PlanStatus.APPROVED)

    def test_cancel_plan(self) -> None:
        plan = self.planner.plan_from_drift(self._make_signal())
        ok = self.planner.cancel_plan(plan.plan_id)
        self.assertTrue(ok)
        self.assertEqual(plan.status, PlanStatus.CANCELLED)

    def test_plan_hash(self) -> None:
        plan = self.planner.plan_from_drift(self._make_signal())
        self.assertEqual(len(plan.plan_hash), 64)

    def test_get_plans_filter(self) -> None:
        self.planner.plan_from_drift(self._make_signal())
        self.planner.plan_from_drift(self._make_signal())
        plans = self.planner.get_plans(status=PlanStatus.CREATED)
        self.assertEqual(len(plans), 2)

    def test_module_singleton(self) -> None:
        p1 = get_reconciliation_planner()
        p2 = get_reconciliation_planner()
        self.assertIs(p1, p2)


# ═══════════════════════════════════════════════════════════════════════════
# V18C — Reconciliation Executor tests
# ═══════════════════════════════════════════════════════════════════════════


class TestReconciliationExecutor(unittest.TestCase):
    """Tests for ReconciliationExecutor."""

    def setUp(self) -> None:
        self.planner = ReconciliationPlanner()
        self.executor = ReconciliationExecutor()

    def _make_plan(self) -> ReconciliationPlan:
        signal = DriftSignal(drift_type=DriftType.VERSION_MISMATCH, severity=DriftSeverity.HIGH,
                             provider_name="k8s", expected_value="v1.0", actual_value="v0.9")
        return self.planner.plan_from_drift(signal)

    def test_execute_plan_success(self) -> None:
        plan = self._make_plan()
        execution = self.executor.execute_plan(plan)
        self.assertEqual(execution.status, ExecutionStatus.COMPLETED)
        self.assertTrue(execution.all_succeeded)
        self.assertEqual(plan.status, PlanStatus.COMPLETED)

    def test_execute_plan_failure(self) -> None:
        plan = self._make_plan()
        execution = self.executor.execute_plan(plan, simulate_failure=True)
        self.assertIn(execution.status, (ExecutionStatus.FAILED, ExecutionStatus.RETRYING))
        self.assertTrue(execution.failure_count > 0)

    def test_retry_step(self) -> None:
        plan = self._make_plan()
        execution = self.executor.execute_plan(plan, simulate_failure=True)
        failed_step = [s for s in execution.step_results if s.outcome == StepOutcome.FAILURE][0]
        result = self.executor.retry_step(execution.execution_id, failed_step.step_id)
        self.assertIsNotNone(result)
        self.assertEqual(result.outcome, StepOutcome.SUCCESS)
        self.assertEqual(result.attempts, 2)

    def test_escalate_step(self) -> None:
        plan = self._make_plan()
        execution = self.executor.execute_plan(plan, simulate_failure=True)
        failed_step = [s for s in execution.step_results if s.outcome == StepOutcome.FAILURE][0]
        result = self.executor.escalate_step(execution.execution_id, failed_step.step_id, "needs human")
        self.assertIsNotNone(result)
        self.assertEqual(result.action_type, ReconciliationActionType.ESCALATE_HUMAN)
        self.assertEqual(execution.status, ExecutionStatus.ESCALATED)

    def test_retry_nonexistent(self) -> None:
        result = self.executor.retry_step("fake", "fake")
        self.assertIsNone(result)

    def test_execution_hash(self) -> None:
        plan = self._make_plan()
        execution = self.executor.execute_plan(plan)
        self.assertEqual(len(execution.execution_hash), 64)

    def test_step_result_hash(self) -> None:
        plan = self._make_plan()
        execution = self.executor.execute_plan(plan)
        self.assertEqual(len(execution.step_results[0].result_hash), 64)

    def test_get_executions_filter(self) -> None:
        plan = self._make_plan()
        self.executor.execute_plan(plan)
        execs = self.executor.get_executions(status=ExecutionStatus.COMPLETED)
        self.assertEqual(len(execs), 1)

    def test_can_retry_property(self) -> None:
        plan = self._make_plan()
        execution = self.executor.execute_plan(plan, simulate_failure=True)
        failed = [s for s in execution.step_results if s.outcome == StepOutcome.FAILURE]
        self.assertTrue(all(s.can_retry for s in failed))

    def test_module_singleton(self) -> None:
        e1 = get_reconciliation_executor()
        e2 = get_reconciliation_executor()
        self.assertIs(e1, e2)


# ═══════════════════════════════════════════════════════════════════════════
# V18D — Convergence Manager tests
# ═══════════════════════════════════════════════════════════════════════════


class TestConvergenceManager(unittest.TestCase):
    """Tests for ConvergenceManager."""

    def setUp(self) -> None:
        self.mgr = ConvergenceManager()

    def test_snapshot_converged(self) -> None:
        snapshot = self.mgr.take_snapshot()
        self.assertEqual(snapshot.status, ConvergenceStatus.CONVERGED)
        self.assertEqual(snapshot.health, SystemHealth.HEALTHY)
        self.assertEqual(snapshot.score.overall_score, 100.0)

    def test_snapshot_with_drift(self) -> None:
        self.mgr.drift_detector.register_desired_state(DesiredState(provider_name="k8s"))
        self.mgr.drift_detector.detect_provider_drift("k8s", actual_connected=False)
        snapshot = self.mgr.take_snapshot()
        self.assertEqual(snapshot.status, ConvergenceStatus.DRIFTING)
        self.assertTrue(snapshot.score.overall_score < 100.0)
        self.assertEqual(snapshot.active_drift_count, 1)

    def test_snapshot_diverged(self) -> None:
        # 7 drifts → 7*15=105 penalty → 0 score → DIVERGED
        self.mgr.drift_detector.register_desired_state(DesiredState(provider_name="k8s"))
        for i in range(7):
            self.mgr.drift_detector.detect_provider_drift("k8s", actual_connected=False, actual_healthy=False)
        snapshot = self.mgr.take_snapshot()
        self.assertEqual(snapshot.status, ConvergenceStatus.DIVERGED)
        self.assertEqual(snapshot.health, SystemHealth.CRITICAL)

    def test_is_healthy_true(self) -> None:
        self.mgr.take_snapshot()
        self.assertTrue(self.mgr.is_healthy())

    def test_is_healthy_false_with_many_drifts(self) -> None:
        self.mgr.drift_detector.register_desired_state(DesiredState(provider_name="k8s"))
        for _ in range(5):
            self.mgr.drift_detector.detect_provider_drift("k8s", actual_connected=False)
        self.mgr.take_snapshot()
        self.assertFalse(self.mgr.is_healthy())

    def test_get_status(self) -> None:
        self.assertEqual(self.mgr.get_status(), ConvergenceStatus.UNKNOWN)
        self.mgr.take_snapshot()
        self.assertEqual(self.mgr.get_status(), ConvergenceStatus.CONVERGED)

    def test_get_history(self) -> None:
        self.mgr.take_snapshot()
        self.mgr.take_snapshot()
        self.assertEqual(len(self.mgr.get_history()), 2)

    def test_systemic_issues_widespread(self) -> None:
        self.mgr.drift_detector.register_desired_state(DesiredState(provider_name="k8s"))
        self.mgr.drift_detector.register_desired_state(DesiredState(provider_name="gke"))
        self.mgr.drift_detector.detect_provider_drift("k8s", actual_connected=False)
        self.mgr.drift_detector.detect_provider_drift("gke", actual_connected=False)
        self.mgr.drift_detector.detect_provider_drift("k8s", actual_healthy=False)
        snapshot = self.mgr.take_snapshot()
        categories = [i.category for i in snapshot.systemic_issues]
        self.assertIn("widespread_drift", categories)

    def test_systemic_issues_critical(self) -> None:
        self.mgr.drift_detector.register_desired_state(DesiredState(provider_name="k8s"))
        self.mgr.drift_detector.detect_provider_drift("k8s", actual_connected=False)
        snapshot = self.mgr.take_snapshot()
        # CONNECTION_LOST has CRITICAL severity
        categories = [i.category for i in snapshot.systemic_issues]
        self.assertIn("critical_drift", categories)

    def test_global_reconciliation_no_drifts(self) -> None:
        result = self.mgr.trigger_global_reconciliation()
        self.assertEqual(result["status"], "no_drifts")

    def test_global_reconciliation_with_drifts(self) -> None:
        self.mgr.drift_detector.register_desired_state(DesiredState(provider_name="k8s", expected_version="v1.0"))
        self.mgr.drift_detector.detect_provider_drift("k8s", actual_version="v0.9")
        result = self.mgr.trigger_global_reconciliation()
        self.assertEqual(result["status"], "reconciled")
        self.assertEqual(result["plans_created"], 1)

    def test_snapshot_hash(self) -> None:
        snapshot = self.mgr.take_snapshot()
        self.assertEqual(len(snapshot.snapshot_hash), 64)

    def test_convergence_score_breakdown(self) -> None:
        snapshot = self.mgr.take_snapshot()
        self.assertEqual(snapshot.score.drift_free_pct, 100.0)
        self.assertEqual(snapshot.score.provider_health_pct, 100.0)

    def test_module_singleton(self) -> None:
        m1 = get_convergence_manager()
        m2 = get_convergence_manager()
        self.assertIs(m1, m2)


if __name__ == "__main__":
    unittest.main()
