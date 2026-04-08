"""Test V16 — Live Production Bindings."""

import unittest

# ── V16A imports ──────────────────────────────────────────────────────────
from src.kortana.services.external_call_adapter import (
    CallRouter,
    HTTPCallAdapter,
    MockCallAdapter,
    CallMethod,
    CallOutcome,
    CallResult,
    EndpointConfig,
    get_call_router,
)

# ── V16B imports ──────────────────────────────────────────────────────────
from src.kortana.services.persistent_stage_store import (
    StagePersistenceStore,
    PersistenceStatus,
    SideEffectType,
    get_stage_persistence_store,
)

# ── V16C imports ──────────────────────────────────────────────────────────
from src.kortana.services.deployment_binding import (
    DeploymentBinding,
    TargetEnvironment,
    ActionType,
    ActionStatus,
    get_deployment_binding,
)

# ── V16D imports ──────────────────────────────────────────────────────────
from src.kortana.services.external_verification import (
    ExternalVerifier,
    ProbeType,
    ProbeStatus,
    CampaignStatus,
    get_external_verifier,
)


# ═══════════════════════════════════════════════════════════════════════════
# V16A — External Call Adapter tests
# ═══════════════════════════════════════════════════════════════════════════


class TestCallRouter(unittest.TestCase):
    """Tests for CallRouter + adapters."""

    def setUp(self) -> None:
        self.router = CallRouter()

    def test_http_adapter_returns_success(self) -> None:
        adapter = HTTPCallAdapter()
        result = adapter.execute("https://example.com", CallMethod.GET, None, None, 30)
        self.assertEqual(result.outcome, CallOutcome.SUCCESS)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(adapter.call_count, 1)

    def test_mock_adapter_default(self) -> None:
        adapter = MockCallAdapter()
        result = adapter.execute("https://test.com", CallMethod.POST, None, None, 10)
        self.assertEqual(result.outcome, CallOutcome.SUCCESS)
        self.assertTrue(result.body.get("mock"))

    def test_mock_adapter_preconfigured(self) -> None:
        adapter = MockCallAdapter()
        custom = CallResult(status_code=404, outcome=CallOutcome.FAILURE, error="not found")
        adapter.set_response("https://fail.com", custom)
        result = adapter.execute("https://fail.com", CallMethod.GET, None, None, 30)
        self.assertEqual(result.status_code, 404)
        self.assertEqual(result.outcome, CallOutcome.FAILURE)

    def test_mock_adapter_default_override(self) -> None:
        adapter = MockCallAdapter()
        default = CallResult(status_code=503, outcome=CallOutcome.FAILURE, error="down")
        adapter.set_default(default)
        result = adapter.execute("https://any.com", CallMethod.GET, None, None, 30)
        self.assertEqual(result.status_code, 503)

    def test_register_endpoint(self) -> None:
        config = EndpointConfig(url="https://api.example.com/v1", adapter_name="http")
        self.router.register_endpoint(config)
        self.assertEqual(self.router.endpoint_count, 1)

    def test_route_call_default_adapter(self) -> None:
        result = self.router.route_call("https://unknown.com")
        self.assertEqual(result.outcome, CallOutcome.SUCCESS)

    def test_route_call_registered_endpoint(self) -> None:
        config = EndpointConfig(url="https://api.test.com", adapter_name="http", timeout_seconds=10)
        self.router.register_endpoint(config)
        result = self.router.route_call("https://api.test.com")
        self.assertEqual(result.outcome, CallOutcome.SUCCESS)

    def test_route_call_unknown_adapter(self) -> None:
        config = EndpointConfig(url="https://bad.com", adapter_name="nonexistent")
        self.router.register_endpoint(config)
        result = self.router.route_call("https://bad.com")
        self.assertEqual(result.outcome, CallOutcome.FAILURE)
        self.assertIn("No adapter", result.error)

    def test_reconcile_match(self) -> None:
        result = self.router.route_call("https://ok.com")
        rec = self.router.reconcile(result, CallOutcome.SUCCESS, 200)
        self.assertTrue(rec.matched)
        self.assertEqual(self.router.total_reconciliations, 1)

    def test_reconcile_mismatch(self) -> None:
        result = self.router.route_call("https://ok.com")
        rec = self.router.reconcile(result, CallOutcome.FAILURE, 500)
        self.assertFalse(rec.matched)

    def test_call_history(self) -> None:
        self.router.route_call("https://a.com")
        self.router.route_call("https://b.com")
        self.assertEqual(self.router.total_calls, 2)
        limited = self.router.get_call_history(1)
        self.assertEqual(len(limited), 1)

    def test_call_result_hash(self) -> None:
        result = CallResult(call_id="test_1", status_code=200)
        self.assertTrue(len(result.call_hash) == 64)

    def test_module_singleton(self) -> None:
        r1 = get_call_router()
        r2 = get_call_router()
        self.assertIs(r1, r2)


# ═══════════════════════════════════════════════════════════════════════════
# V16B — Persistent Stage Store tests
# ═══════════════════════════════════════════════════════════════════════════


class TestStagePersistenceStore(unittest.TestCase):
    """Tests for StagePersistenceStore."""

    def setUp(self) -> None:
        self.store = StagePersistenceStore()

    def test_persist_transition(self) -> None:
        rec = self.store.persist_transition("pipe1", "v1.0", "", "build", "pass")
        self.assertEqual(rec.pipeline_id, "pipe1")
        self.assertEqual(rec.to_stage, "build")
        self.assertEqual(rec.persistence_status, PersistenceStatus.COMMITTED)

    def test_get_transitions(self) -> None:
        self.store.persist_transition("pipe1", "v1", "", "build")
        self.store.persist_transition("pipe1", "v1", "build", "test")
        transitions = self.store.get_transitions("pipe1")
        self.assertEqual(len(transitions), 2)

    def test_get_all_transitions(self) -> None:
        self.store.persist_transition("pipe1", "v1", "", "build")
        self.store.persist_transition("pipe2", "v2", "", "build")
        all_t = self.store.get_all_transitions()
        self.assertEqual(len(all_t), 2)

    def test_persist_rollback_effect(self) -> None:
        effect = self.store.persist_rollback_effect(
            "rb_1", "pipe1", "v1", SideEffectType.TRAFFIC_SHIFTED,
            "service-a", "shifted traffic back",
        )
        self.assertEqual(effect.effect_type, SideEffectType.TRAFFIC_SHIFTED)
        self.assertEqual(effect.affected_resource, "service-a")

    def test_get_rollback_effects(self) -> None:
        self.store.persist_rollback_effect("rb_1", "p1", "v1", SideEffectType.CONFIG_REVERTED, "cfg")
        self.store.persist_rollback_effect("rb_1", "p1", "v1", SideEffectType.CACHE_INVALIDATED, "cache")
        effects = self.store.get_rollback_effects("rb_1")
        self.assertEqual(len(effects), 2)

    def test_get_all_effects(self) -> None:
        self.store.persist_rollback_effect("rb_1", "p1", "v1", SideEffectType.CONFIG_REVERTED, "cfg")
        self.store.persist_rollback_effect("rb_2", "p2", "v2", SideEffectType.ALERT_TRIGGERED, "pager")
        all_e = self.store.get_all_effects()
        self.assertEqual(len(all_e), 2)

    def test_verify_integrity_valid(self) -> None:
        self.store.persist_transition("pipe1", "v1", "", "build")
        self.store.persist_transition("pipe1", "v1", "build", "test")
        self.store.persist_transition("pipe1", "v1", "test", "scan")
        check = self.store.verify_persistence_integrity("pipe1")
        self.assertTrue(check.all_hashes_valid)
        self.assertTrue(check.chain_continuous)
        self.assertEqual(check.transitions_count, 3)

    def test_verify_integrity_broken_chain(self) -> None:
        self.store.persist_transition("pipe2", "v2", "", "build")
        self.store.persist_transition("pipe2", "v2", "scan", "approve")  # skip test
        check = self.store.verify_persistence_integrity("pipe2")
        self.assertFalse(check.chain_continuous)

    def test_transition_hash(self) -> None:
        rec = self.store.persist_transition("p", "v", "", "build")
        self.assertTrue(len(rec.transition_hash) == 64)

    def test_integrity_check_hash(self) -> None:
        check = self.store.verify_persistence_integrity("empty")
        self.assertTrue(len(check.integrity_hash) == 64)

    def test_total_properties(self) -> None:
        self.store.persist_transition("p1", "v1", "", "build")
        self.store.persist_rollback_effect("rb", "p1", "v1", SideEffectType.CONFIG_REVERTED, "r")
        self.assertEqual(self.store.total_transitions, 1)
        self.assertEqual(self.store.total_effects, 1)
        self.assertEqual(self.store.pipeline_count, 1)

    def test_module_singleton(self) -> None:
        s1 = get_stage_persistence_store()
        s2 = get_stage_persistence_store()
        self.assertIs(s1, s2)


# ═══════════════════════════════════════════════════════════════════════════
# V16C — Deployment Binding tests
# ═══════════════════════════════════════════════════════════════════════════


class TestDeploymentBinding(unittest.TestCase):
    """Tests for DeploymentBinding."""

    def setUp(self) -> None:
        self.binding = DeploymentBinding()

    def test_register_target(self) -> None:
        target = self.binding.register_target("prod-east", TargetEnvironment.PRODUCTION,
                                               endpoint_url="https://prod.example.com")
        self.assertEqual(target.name, "prod-east")
        self.assertEqual(target.environment, TargetEnvironment.PRODUCTION)
        self.assertTrue(target.active)

    def test_list_targets(self) -> None:
        self.binding.register_target("staging-1", TargetEnvironment.STAGING)
        self.binding.register_target("prod-1", TargetEnvironment.PRODUCTION)
        all_targets = self.binding.list_targets()
        self.assertEqual(len(all_targets), 2)
        prod_only = self.binding.list_targets(TargetEnvironment.PRODUCTION)
        self.assertEqual(len(prod_only), 1)

    def test_deactivate_target(self) -> None:
        target = self.binding.register_target("tmp", TargetEnvironment.STAGING)
        self.assertTrue(self.binding.deactivate_target(target.target_id))
        self.assertFalse(target.active)

    def test_bind_pipeline(self) -> None:
        target = self.binding.register_target("stg", TargetEnvironment.STAGING)
        bind = self.binding.bind_pipeline("pipe_1", target.target_id, "v1.0")
        self.assertIsNotNone(bind)
        self.assertEqual(bind.pipeline_id, "pipe_1")

    def test_bind_pipeline_unknown_target(self) -> None:
        bind = self.binding.bind_pipeline("pipe_1", "nonexistent")
        self.assertIsNone(bind)

    def test_execute_deployment(self) -> None:
        target = self.binding.register_target("stg", TargetEnvironment.STAGING)
        action = self.binding.execute_deployment(target.target_id, "pipe_1", "v1.0", "canary")
        self.assertEqual(action.status, ActionStatus.SUCCEEDED)
        self.assertEqual(action.action_type, ActionType.DEPLOY)

    def test_execute_deployment_failure(self) -> None:
        target = self.binding.register_target("stg", TargetEnvironment.STAGING)
        action = self.binding.execute_deployment(target.target_id, "pipe_1", "v1.0",
                                                  simulate_failure=True)
        self.assertEqual(action.status, ActionStatus.FAILED)

    def test_execute_deployment_inactive_target(self) -> None:
        target = self.binding.register_target("stg", TargetEnvironment.STAGING)
        self.binding.deactivate_target(target.target_id)
        action = self.binding.execute_deployment(target.target_id, "pipe_1", "v1.0")
        self.assertEqual(action.status, ActionStatus.FAILED)

    def test_verify_deployment_ok(self) -> None:
        target = self.binding.register_target("stg", TargetEnvironment.STAGING)
        action = self.binding.execute_deployment(target.target_id, "pipe_1", "v1.0")
        v = self.binding.verify_deployment(action.action_id, expected_version="v1.0")
        self.assertTrue(v.verified)
        self.assertEqual(action.status, ActionStatus.VERIFIED)

    def test_verify_deployment_mismatch(self) -> None:
        target = self.binding.register_target("stg", TargetEnvironment.STAGING)
        action = self.binding.execute_deployment(target.target_id, "pipe_1", "v1.0")
        v = self.binding.verify_deployment(action.action_id, expected_version="v1.0",
                                            simulate_mismatch=True)
        self.assertFalse(v.verified)

    def test_verify_deployment_unhealthy(self) -> None:
        target = self.binding.register_target("stg", TargetEnvironment.STAGING)
        action = self.binding.execute_deployment(target.target_id, "pipe_1", "v1.0")
        v = self.binding.verify_deployment(action.action_id, expected_version="v1.0",
                                            simulate_unhealthy=True)
        self.assertFalse(v.verified)

    def test_get_actions(self) -> None:
        target = self.binding.register_target("stg", TargetEnvironment.STAGING)
        self.binding.execute_deployment(target.target_id, "pipe_1", "v1.0")
        self.binding.execute_deployment(target.target_id, "pipe_2", "v2.0")
        all_actions = self.binding.get_actions()
        self.assertEqual(len(all_actions), 2)
        filtered = self.binding.get_actions(pipeline_id="pipe_1")
        self.assertEqual(len(filtered), 1)

    def test_target_hash(self) -> None:
        target = self.binding.register_target("hashtest", TargetEnvironment.STAGING)
        self.assertTrue(len(target.target_hash) == 64)

    def test_module_singleton(self) -> None:
        b1 = get_deployment_binding()
        b2 = get_deployment_binding()
        self.assertIs(b1, b2)


# ═══════════════════════════════════════════════════════════════════════════
# V16D — External Verification tests
# ═══════════════════════════════════════════════════════════════════════════


class TestExternalVerifier(unittest.TestCase):
    """Tests for ExternalVerifier."""

    def setUp(self) -> None:
        self.verifier = ExternalVerifier()

    def test_create_campaign(self) -> None:
        camp = self.verifier.create_campaign("v1.0", "pipe_1", "post-deploy check")
        self.assertEqual(camp.version_id, "v1.0")
        self.assertEqual(camp.status, CampaignStatus.CREATED)

    def test_add_probe(self) -> None:
        camp = self.verifier.create_campaign("v1.0")
        probe = self.verifier.add_probe(
            camp.campaign_id, "service-a", ProbeType.VERSION_CHECK,
            {"version": "v1.0"},
        )
        self.assertIsNotNone(probe)
        self.assertEqual(probe.target_system, "service-a")

    def test_add_probe_unknown_campaign(self) -> None:
        probe = self.verifier.add_probe("no_such", "svc", ProbeType.HEALTH_CHECK)
        self.assertIsNone(probe)

    def test_execute_probe_matched(self) -> None:
        camp = self.verifier.create_campaign("v1.0")
        probe = self.verifier.add_probe(camp.campaign_id, "svc-a", ProbeType.VERSION_CHECK,
                                         {"version": "v1.0"})
        executed = self.verifier.execute_probe(camp.campaign_id, probe.probe_id,
                                                observed_state={"version": "v1.0"})
        self.assertEqual(executed.status, ProbeStatus.MATCHED)
        self.assertTrue(executed.matched)

    def test_execute_probe_mismatched(self) -> None:
        camp = self.verifier.create_campaign("v1.0")
        probe = self.verifier.add_probe(camp.campaign_id, "svc-a", ProbeType.VERSION_CHECK,
                                         {"version": "v1.0"})
        executed = self.verifier.execute_probe(camp.campaign_id, probe.probe_id,
                                                observed_state={"version": "v0.9"})
        self.assertEqual(executed.status, ProbeStatus.MISMATCHED)
        self.assertFalse(executed.matched)

    def test_execute_probe_unreachable(self) -> None:
        camp = self.verifier.create_campaign("v1.0")
        probe = self.verifier.add_probe(camp.campaign_id, "svc-a", ProbeType.HEALTH_CHECK)
        executed = self.verifier.execute_probe(camp.campaign_id, probe.probe_id,
                                                simulate_unreachable=True)
        self.assertEqual(executed.status, ProbeStatus.UNREACHABLE)

    def test_execute_probe_error(self) -> None:
        camp = self.verifier.create_campaign("v1.0")
        probe = self.verifier.add_probe(camp.campaign_id, "svc-a", ProbeType.CONFIG_CHECK)
        executed = self.verifier.execute_probe(camp.campaign_id, probe.probe_id,
                                                simulate_error="connection reset")
        self.assertEqual(executed.status, ProbeStatus.ERROR)
        self.assertEqual(executed.error, "connection reset")

    def test_execute_campaign_all_matched(self) -> None:
        camp = self.verifier.create_campaign("v1.0")
        self.verifier.add_probe(camp.campaign_id, "svc-a", ProbeType.VERSION_CHECK, {"v": "1"})
        self.verifier.add_probe(camp.campaign_id, "svc-b", ProbeType.VERSION_CHECK, {"v": "1"})
        result = self.verifier.execute_campaign(
            camp.campaign_id,
            observed_states={"svc-a": {"v": "1"}, "svc-b": {"v": "1"}},
        )
        self.assertEqual(result.status, CampaignStatus.COMPLETED)
        self.assertTrue(result.all_matched)

    def test_execute_campaign_partial(self) -> None:
        camp = self.verifier.create_campaign("v1.0")
        self.verifier.add_probe(camp.campaign_id, "svc-a", ProbeType.VERSION_CHECK, {"v": "1"})
        self.verifier.add_probe(camp.campaign_id, "svc-b", ProbeType.HEALTH_CHECK, {"ok": True})
        result = self.verifier.execute_campaign(
            camp.campaign_id,
            observed_states={"svc-a": {"v": "1"}},
            simulate_unreachable=["svc-b"],
        )
        self.assertEqual(result.status, CampaignStatus.PARTIAL)

    def test_execute_campaign_failed(self) -> None:
        camp = self.verifier.create_campaign("v1.0")
        self.verifier.add_probe(camp.campaign_id, "svc-a", ProbeType.VERSION_CHECK, {"v": "1"})
        result = self.verifier.execute_campaign(
            camp.campaign_id,
            simulate_unreachable=["svc-a"],
        )
        self.assertEqual(result.status, CampaignStatus.FAILED)

    def test_verify_campaign_success(self) -> None:
        camp = self.verifier.create_campaign("v1.0")
        self.verifier.add_probe(camp.campaign_id, "svc", ProbeType.VERSION_CHECK, {"v": "1"})
        self.verifier.execute_campaign(camp.campaign_id, {"svc": {"v": "1"}})
        ok, reason = self.verifier.verify_campaign(camp.campaign_id)
        self.assertTrue(ok)
        self.assertIn("matched", reason)

    def test_verify_campaign_not_executed(self) -> None:
        camp = self.verifier.create_campaign("v1.0")
        ok, reason = self.verifier.verify_campaign(camp.campaign_id)
        self.assertFalse(ok)
        self.assertIn("not yet executed", reason)

    def test_get_campaigns_filter(self) -> None:
        self.verifier.create_campaign("v1.0")
        self.verifier.create_campaign("v2.0")
        self.verifier.create_campaign("v1.0")
        all_c = self.verifier.get_campaigns()
        self.assertEqual(len(all_c), 3)
        v1_only = self.verifier.get_campaigns(version_id="v1.0")
        self.assertEqual(len(v1_only), 2)

    def test_probe_hash(self) -> None:
        camp = self.verifier.create_campaign("v1.0")
        probe = self.verifier.add_probe(camp.campaign_id, "svc", ProbeType.HEALTH_CHECK)
        self.assertTrue(len(probe.probe_hash) == 64)

    def test_campaign_hash(self) -> None:
        camp = self.verifier.create_campaign("v1.0")
        self.assertTrue(len(camp.campaign_hash) == 64)

    def test_module_singleton(self) -> None:
        v1 = get_external_verifier()
        v2 = get_external_verifier()
        self.assertIs(v1, v2)


if __name__ == "__main__":
    unittest.main()
