"""Test V17 — Closed-Loop Real-World Enforcement."""

import unittest

# ── V17A imports ──────────────────────────────────────────────────────────
from src.kortana.services.provider_client_registry import (
    ProviderClientRegistry,
    ProviderClientConfig,
    ProviderType,
    ClientConnectionState,
    OperationOutcome,
    get_provider_client_registry,
)

# ── V17B imports ──────────────────────────────────────────────────────────
from src.kortana.services.rollout_action_executor import (
    RolloutExecutor,
    RolloutStrategy,
    RolloutStatus,
    RolloutStepStatus,
    get_rollout_executor,
)

# ── V17C imports ──────────────────────────────────────────────────────────
from src.kortana.services.feedback_policy_engine import (
    FeedbackPolicyEngine,
    FeedbackSignal,
    TriggerCondition,
    FeedbackAction,
    EvaluationOutcome,
    get_feedback_policy_engine,
)

# ── V17D imports ──────────────────────────────────────────────────────────
from src.kortana.services.evidence_chain import (
    EvidenceChainRegistry,
    EvidenceType,
    ChainStatus,
    get_evidence_chain_registry,
)


# ═══════════════════════════════════════════════════════════════════════════
# V17A — Provider Client Registry tests
# ═══════════════════════════════════════════════════════════════════════════


class TestProviderClientRegistry(unittest.TestCase):
    """Tests for ProviderClientRegistry."""

    def setUp(self) -> None:
        self.reg = ProviderClientRegistry()

    def test_register_provider(self) -> None:
        config = ProviderClientConfig(name="k8s-prod", provider_type=ProviderType.KUBERNETES)
        client = self.reg.register(config)
        self.assertIsNotNone(client)
        self.assertEqual(self.reg.provider_count, 1)

    def test_connect_provider(self) -> None:
        self.reg.register(ProviderClientConfig(name="k8s"))
        record = self.reg.connect("k8s")
        self.assertEqual(record.outcome, OperationOutcome.SUCCESS)
        client = self.reg.get_client("k8s")
        self.assertEqual(client.state, ClientConnectionState.CONNECTED)

    def test_connect_unknown_provider(self) -> None:
        record = self.reg.connect("nonexistent")
        self.assertEqual(record.outcome, OperationOutcome.FAILURE)

    def test_disconnect_provider(self) -> None:
        self.reg.register(ProviderClientConfig(name="k8s"))
        self.reg.connect("k8s")
        record = self.reg.disconnect("k8s")
        self.assertEqual(record.outcome, OperationOutcome.SUCCESS)

    def test_deploy_version(self) -> None:
        self.reg.register(ProviderClientConfig(name="k8s"))
        self.reg.connect("k8s")
        record = self.reg.deploy_version("k8s", "v1.0")
        self.assertEqual(record.outcome, OperationOutcome.SUCCESS)
        self.assertEqual(record.version_id, "v1.0")

    def test_deploy_failure(self) -> None:
        self.reg.register(ProviderClientConfig(name="k8s"))
        self.reg.connect("k8s")
        client = self.reg.get_client("k8s")
        client.set_fail_next()
        record = self.reg.deploy_version("k8s", "v2.0")
        self.assertEqual(record.outcome, OperationOutcome.FAILURE)

    def test_rollback_version(self) -> None:
        self.reg.register(ProviderClientConfig(name="k8s"))
        self.reg.connect("k8s")
        self.reg.deploy_version("k8s", "v2.0")
        record = self.reg.rollback_version("k8s", "v1.0")
        self.assertEqual(record.outcome, OperationOutcome.SUCCESS)

    def test_health_check(self) -> None:
        self.reg.register(ProviderClientConfig(name="k8s"))
        self.reg.connect("k8s")
        report = self.reg.health_check("k8s")
        self.assertTrue(report.healthy)

    def test_health_check_disconnected(self) -> None:
        self.reg.register(ProviderClientConfig(name="k8s"))
        report = self.reg.health_check("k8s")
        self.assertFalse(report.healthy)

    def test_get_status(self) -> None:
        self.reg.register(ProviderClientConfig(name="k8s", provider_type=ProviderType.KUBERNETES))
        status = self.reg.get_status("k8s")
        self.assertEqual(status["provider_type"], "kubernetes")

    def test_list_providers(self) -> None:
        self.reg.register(ProviderClientConfig(name="k8s"))
        self.reg.register(ProviderClientConfig(name="cloudrun"))
        providers = self.reg.list_providers()
        self.assertEqual(len(providers), 2)

    def test_get_operations(self) -> None:
        self.reg.register(ProviderClientConfig(name="k8s"))
        self.reg.connect("k8s")
        self.reg.deploy_version("k8s", "v1")
        ops = self.reg.get_operations("k8s")
        self.assertEqual(len(ops), 2)  # connect + deploy

    def test_operation_hash(self) -> None:
        self.reg.register(ProviderClientConfig(name="k8s"))
        record = self.reg.connect("k8s")
        self.assertEqual(len(record.operation_hash), 64)

    def test_module_singleton(self) -> None:
        r1 = get_provider_client_registry()
        r2 = get_provider_client_registry()
        self.assertIs(r1, r2)


# ═══════════════════════════════════════════════════════════════════════════
# V17B — Rollout Action Executor tests
# ═══════════════════════════════════════════════════════════════════════════


class TestRolloutExecutor(unittest.TestCase):
    """Tests for RolloutExecutor."""

    def setUp(self) -> None:
        self.executor = RolloutExecutor()

    def test_plan_rolling(self) -> None:
        action = self.executor.plan_rollout("k8s", "v1.0", RolloutStrategy.ROLLING)
        self.assertEqual(len(action.steps), 4)
        self.assertEqual(action.status, RolloutStatus.PLANNED)

    def test_plan_canary(self) -> None:
        action = self.executor.plan_rollout("k8s", "v1.0", RolloutStrategy.CANARY_PROGRESSIVE)
        self.assertEqual(len(action.steps), 5)

    def test_plan_blue_green(self) -> None:
        action = self.executor.plan_rollout("k8s", "v1.0", RolloutStrategy.BLUE_GREEN)
        self.assertEqual(len(action.steps), 2)

    def test_plan_immediate(self) -> None:
        action = self.executor.plan_rollout("k8s", "v1.0", RolloutStrategy.IMMEDIATE)
        self.assertEqual(len(action.steps), 1)

    def test_execute_step(self) -> None:
        action = self.executor.plan_rollout("k8s", "v1.0", RolloutStrategy.IMMEDIATE)
        step = self.executor.execute_step(action.action_id)
        self.assertEqual(step.status, RolloutStepStatus.PASSED)
        self.assertEqual(action.status, RolloutStatus.COMPLETED)

    def test_execute_all_steps_rolling(self) -> None:
        action = self.executor.plan_rollout("k8s", "v1.0", RolloutStrategy.ROLLING)
        for _ in range(4):
            self.executor.execute_step(action.action_id)
        self.assertEqual(action.status, RolloutStatus.COMPLETED)
        self.assertEqual(action.progress_pct, 100.0)

    def test_step_failure_with_auto_rollback(self) -> None:
        action = self.executor.plan_rollout("k8s", "v1.0", RolloutStrategy.ROLLING, auto_rollback=True)
        self.executor.execute_step(action.action_id)  # step 0 passes
        self.executor.execute_step(action.action_id, simulate_failure=True)  # step 1 fails
        self.assertEqual(action.status, RolloutStatus.ROLLED_BACK)

    def test_step_failure_without_auto_rollback(self) -> None:
        action = self.executor.plan_rollout("k8s", "v1.0", RolloutStrategy.ROLLING, auto_rollback=False)
        self.executor.execute_step(action.action_id, simulate_failure=True)
        self.assertEqual(action.status, RolloutStatus.FAILED)

    def test_observe_step(self) -> None:
        action = self.executor.plan_rollout("k8s", "v1.0", RolloutStrategy.IMMEDIATE)
        step = self.executor.execute_step(action.action_id)
        obs = self.executor.observe_step(action.action_id, step.step_id, error_rate=1.0)
        self.assertTrue(obs.healthy)
        self.assertEqual(obs.observation_hash[:3], obs.observation_hash[:3])  # hash exists

    def test_observe_unhealthy(self) -> None:
        action = self.executor.plan_rollout("k8s", "v1.0")
        step = self.executor.execute_step(action.action_id)
        obs = self.executor.observe_step(action.action_id, step.step_id, error_rate=10.0, success_rate=80.0)
        self.assertFalse(obs.healthy)

    def test_manual_rollback(self) -> None:
        action = self.executor.plan_rollout("k8s", "v1.0", RolloutStrategy.ROLLING)
        self.executor.execute_step(action.action_id)
        result = self.executor.rollback_action(action.action_id)
        self.assertEqual(result.status, RolloutStatus.ROLLED_BACK)

    def test_cancel_action(self) -> None:
        action = self.executor.plan_rollout("k8s", "v1.0")
        result = self.executor.cancel_action(action.action_id)
        self.assertEqual(result.status, RolloutStatus.CANCELLED)

    def test_action_hash(self) -> None:
        action = self.executor.plan_rollout("k8s", "v1.0")
        self.assertEqual(len(action.action_hash), 64)

    def test_module_singleton(self) -> None:
        e1 = get_rollout_executor()
        e2 = get_rollout_executor()
        self.assertIs(e1, e2)


# ═══════════════════════════════════════════════════════════════════════════
# V17C — Feedback Policy Engine tests
# ═══════════════════════════════════════════════════════════════════════════


class TestFeedbackPolicyEngine(unittest.TestCase):
    """Tests for FeedbackPolicyEngine."""

    def setUp(self) -> None:
        self.engine = FeedbackPolicyEngine()

    def test_register_trigger(self) -> None:
        trigger = self.engine.register_trigger("high_errors", TriggerCondition.ERROR_RATE_ABOVE, 5.0, FeedbackAction.ROLLBACK)
        self.assertEqual(trigger.name, "high_errors")
        self.assertEqual(self.engine.trigger_count, 1)

    def test_evaluate_clean(self) -> None:
        self.engine.register_trigger("high_err", TriggerCondition.ERROR_RATE_ABOVE, 5.0, FeedbackAction.ALERT)
        signal = FeedbackSignal(error_rate=1.0, success_rate=99.0)
        result = self.engine.evaluate_signal(signal)
        self.assertEqual(result.outcome, EvaluationOutcome.CLEAN)

    def test_evaluate_triggered_alert(self) -> None:
        self.engine.register_trigger("high_err", TriggerCondition.ERROR_RATE_ABOVE, 5.0, FeedbackAction.ALERT)
        signal = FeedbackSignal(error_rate=10.0)
        result = self.engine.evaluate_signal(signal)
        self.assertEqual(result.outcome, EvaluationOutcome.TRIGGERED)

    def test_evaluate_triggered_rollback(self) -> None:
        self.engine.register_trigger("critical_err", TriggerCondition.ERROR_RATE_ABOVE, 10.0, FeedbackAction.ROLLBACK)
        signal = FeedbackSignal(error_rate=15.0)
        result = self.engine.evaluate_signal(signal)
        self.assertEqual(result.outcome, EvaluationOutcome.ROLLED_BACK)
        self.assertTrue(result.has_rollback)

    def test_evaluate_triggered_escalation(self) -> None:
        self.engine.register_trigger("low_success", TriggerCondition.SUCCESS_RATE_BELOW, 90.0, FeedbackAction.ESCALATE)
        signal = FeedbackSignal(success_rate=80.0)
        result = self.engine.evaluate_signal(signal)
        self.assertEqual(result.outcome, EvaluationOutcome.ESCALATED)
        self.assertTrue(result.has_escalation)

    def test_health_failed_trigger(self) -> None:
        self.engine.register_trigger("health", TriggerCondition.HEALTH_FAILED, 0, FeedbackAction.ROLLBACK)
        signal = FeedbackSignal(health_ok=False)
        result = self.engine.evaluate_signal(signal)
        self.assertTrue(result.has_rollback)

    def test_probe_mismatched_trigger(self) -> None:
        self.engine.register_trigger("probe", TriggerCondition.PROBE_MISMATCHED, 0, FeedbackAction.ALERT)
        signal = FeedbackSignal(probe_matched=False)
        result = self.engine.evaluate_signal(signal)
        self.assertEqual(result.outcome, EvaluationOutcome.TRIGGERED)

    def test_latency_trigger(self) -> None:
        self.engine.register_trigger("slow", TriggerCondition.LATENCY_ABOVE, 100.0, FeedbackAction.ALERT)
        signal = FeedbackSignal(latency_ms=200.0)
        result = self.engine.evaluate_signal(signal)
        self.assertEqual(result.outcome, EvaluationOutcome.TRIGGERED)

    def test_consecutive_failures_trigger(self) -> None:
        self.engine.register_trigger("failures", TriggerCondition.CONSECUTIVE_FAILURES, 3, FeedbackAction.ESCALATE)
        signal = FeedbackSignal(consecutive_failures=5)
        result = self.engine.evaluate_signal(signal)
        self.assertTrue(result.has_escalation)

    def test_disabled_trigger_ignored(self) -> None:
        trigger = self.engine.register_trigger("err", TriggerCondition.ERROR_RATE_ABOVE, 1.0, FeedbackAction.ROLLBACK)
        self.engine.disable_trigger(trigger.trigger_id)
        signal = FeedbackSignal(error_rate=50.0)
        result = self.engine.evaluate_signal(signal)
        self.assertEqual(result.outcome, EvaluationOutcome.CLEAN)

    def test_enable_trigger(self) -> None:
        trigger = self.engine.register_trigger("err", TriggerCondition.ERROR_RATE_ABOVE, 1.0, FeedbackAction.ALERT)
        self.engine.disable_trigger(trigger.trigger_id)
        self.engine.enable_trigger(trigger.trigger_id)
        signal = FeedbackSignal(error_rate=50.0)
        result = self.engine.evaluate_signal(signal)
        self.assertEqual(result.outcome, EvaluationOutcome.TRIGGERED)

    def test_scoped_trigger(self) -> None:
        self.engine.register_trigger("scoped", TriggerCondition.ERROR_RATE_ABOVE, 5.0,
                                      FeedbackAction.ALERT, pipeline_scope="pipe_1")
        signal_match = FeedbackSignal(pipeline_id="pipe_1", error_rate=10.0)
        signal_no = FeedbackSignal(pipeline_id="pipe_2", error_rate=10.0)
        r1 = self.engine.evaluate_signal(signal_match)
        r2 = self.engine.evaluate_signal(signal_no)
        self.assertEqual(r1.outcome, EvaluationOutcome.TRIGGERED)
        self.assertEqual(r2.outcome, EvaluationOutcome.CLEAN)

    def test_evaluation_hash(self) -> None:
        self.engine.register_trigger("t", TriggerCondition.ERROR_RATE_ABOVE, 5.0, FeedbackAction.ALERT)
        signal = FeedbackSignal(error_rate=1.0)
        result = self.engine.evaluate_signal(signal)
        self.assertEqual(len(result.evaluation_hash), 64)

    def test_module_singleton(self) -> None:
        e1 = get_feedback_policy_engine()
        e2 = get_feedback_policy_engine()
        self.assertIs(e1, e2)


# ═══════════════════════════════════════════════════════════════════════════
# V17D — Evidence Chain tests
# ═══════════════════════════════════════════════════════════════════════════


class TestEvidenceChain(unittest.TestCase):
    """Tests for EvidenceChain and EvidenceChainRegistry."""

    def setUp(self) -> None:
        self.reg = EvidenceChainRegistry()

    def test_create_chain(self) -> None:
        chain = self.reg.create_chain("v1.0", "deploy evidence")
        self.assertEqual(chain.version_id, "v1.0")
        self.assertEqual(chain.status, ChainStatus.OPEN)

    def test_append_entry(self) -> None:
        chain = self.reg.create_chain("v1.0")
        entry = chain.append_entry(EvidenceType.DECISION, "control-plane", "Deploy v1.0")
        self.assertEqual(entry.sequence, 0)
        self.assertEqual(entry.previous_hash, "")

    def test_chain_linking(self) -> None:
        chain = self.reg.create_chain("v1.0")
        e1 = chain.append_entry(EvidenceType.DECISION, "cp", "decide")
        e2 = chain.append_entry(EvidenceType.DEPLOYMENT, "cp", "deploy")
        self.assertEqual(e2.previous_hash, e1.entry_hash)

    def test_verify_chain_valid(self) -> None:
        chain = self.reg.create_chain("v1.0")
        chain.append_entry(EvidenceType.DECISION, "cp", "decide")
        chain.append_entry(EvidenceType.DEPLOYMENT, "cp", "deploy")
        chain.append_entry(EvidenceType.OBSERVATION, "probe", "observe")
        ok, reason = chain.verify_chain()
        self.assertTrue(ok)
        self.assertIn("3 entries", reason)

    def test_verify_empty_chain(self) -> None:
        chain = self.reg.create_chain("v1.0")
        ok, reason = chain.verify_chain()
        self.assertTrue(ok)
        self.assertIn("Empty", reason)

    def test_seal_chain(self) -> None:
        chain = self.reg.create_chain("v1.0")
        chain.append_entry(EvidenceType.DECISION, "cp")
        sealed = self.reg.seal_chain(chain.chain_id)
        self.assertEqual(sealed.status, ChainStatus.VERIFIED)

    def test_cannot_append_to_sealed(self) -> None:
        chain = self.reg.create_chain("v1.0")
        chain.append_entry(EvidenceType.DECISION, "cp")
        self.reg.seal_chain(chain.chain_id)
        with self.assertRaises(ValueError):
            chain.append_entry(EvidenceType.DEPLOYMENT, "cp")

    def test_convergence_proof_complete(self) -> None:
        chain = self.reg.create_chain("v1.0")
        chain.append_entry(EvidenceType.DECISION, "cp", "decide to deploy v1.0")
        chain.append_entry(EvidenceType.DEPLOYMENT, "cp", "deployed to k8s")
        chain.append_entry(EvidenceType.OBSERVATION, "probe", "observed v1.0 running")
        chain.append_entry(EvidenceType.CONVERGENCE, "verify", "confirmed convergence")
        proof = chain.get_convergence_proof()
        self.assertTrue(proof.is_valid)
        self.assertTrue(proof.all_stages_present)
        self.assertTrue(proof.chain_integrity)

    def test_convergence_proof_incomplete(self) -> None:
        chain = self.reg.create_chain("v1.0")
        chain.append_entry(EvidenceType.DECISION, "cp")
        # Missing DEPLOYMENT, OBSERVATION, CONVERGENCE
        proof = chain.get_convergence_proof()
        self.assertFalse(proof.is_valid)
        self.assertFalse(proof.all_stages_present)

    def test_verify_all(self) -> None:
        chain1 = self.reg.create_chain("v1.0")
        chain1.append_entry(EvidenceType.DECISION, "cp")
        chain2 = self.reg.create_chain("v2.0")
        chain2.append_entry(EvidenceType.DECISION, "cp")
        results = self.reg.verify_all()
        self.assertEqual(len(results), 2)
        for cid, (ok, _) in results.items():
            self.assertTrue(ok)

    def test_get_chains_filter(self) -> None:
        self.reg.create_chain("v1.0")
        self.reg.create_chain("v2.0")
        self.reg.create_chain("v1.0")
        v1_chains = self.reg.get_chains(version_id="v1.0")
        self.assertEqual(len(v1_chains), 2)

    def test_entry_hash(self) -> None:
        chain = self.reg.create_chain("v1.0")
        entry = chain.append_entry(EvidenceType.DECISION, "cp")
        self.assertEqual(len(entry.entry_hash), 64)

    def test_convergence_proof_hash(self) -> None:
        chain = self.reg.create_chain("v1.0")
        chain.append_entry(EvidenceType.DECISION, "cp")
        proof = chain.get_convergence_proof()
        self.assertEqual(len(proof.proof_hash), 64)

    def test_module_singleton(self) -> None:
        r1 = get_evidence_chain_registry()
        r2 = get_evidence_chain_registry()
        self.assertIs(r1, r2)


if __name__ == "__main__":
    unittest.main()
