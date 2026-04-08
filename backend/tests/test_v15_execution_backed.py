"""Test V15 — Execution-Backed Orchestration."""

import unittest
from datetime import datetime, timedelta


class TestMetadataFetchExecutor(unittest.TestCase):
    """Tests for V15A — MetadataFetchExecutor."""

    def setUp(self) -> None:
        from src.kortana.services.metadata_fetch_executor import MetadataFetchExecutor
        self.executor = MetadataFetchExecutor()

    def test_register_endpoint(self) -> None:
        sched = self.executor.register_endpoint("https://idp.example.com", interval_seconds=1800)
        assert sched.provider_url == "https://idp.example.com"
        assert sched.interval_seconds == 1800
        assert self.executor.endpoint_count == 1

    def test_execute_fetch_success(self) -> None:
        self.executor.register_endpoint("https://idp.example.com")
        result = self.executor.execute_fetch("https://idp.example.com", simulated_payload={"issuer": "test"})
        from src.kortana.services.metadata_fetch_executor import FetchStatus
        assert result.status == FetchStatus.SUCCESS
        assert result.payload["issuer"] == "test"
        assert result.content_hash

    def test_execute_fetch_failure(self) -> None:
        self.executor.register_endpoint("https://idp.fail.com")
        result = self.executor.execute_fetch("https://idp.fail.com", simulated_failure=True)
        from src.kortana.services.metadata_fetch_executor import FetchStatus
        assert result.status == FetchStatus.FAILURE
        assert result.error_message

    def test_circuit_breaker_opens(self) -> None:
        from src.kortana.services.metadata_fetch_executor import (
            CircuitBreaker,
            CircuitState,
        )
        cb = CircuitBreaker(failure_threshold=3)
        for _ in range(3):
            cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert not cb.can_execute()

    def test_circuit_breaker_recovery(self) -> None:
        from src.kortana.services.metadata_fetch_executor import (
            CircuitBreaker,
            CircuitState,
        )
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout_seconds=0)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        cb.last_failure_at = datetime.utcnow() - timedelta(seconds=1)
        assert cb.can_execute()
        assert cb.state == CircuitState.HALF_OPEN

    def test_retry_policy_delay(self) -> None:
        from src.kortana.services.metadata_fetch_executor import RetryPolicy
        rp = RetryPolicy(base_delay_seconds=1.0, backoff_multiplier=2.0, max_delay_seconds=10.0)
        assert rp.delay_for_attempt(0) == 1.0
        assert rp.delay_for_attempt(1) == 2.0
        assert rp.delay_for_attempt(2) == 4.0
        assert rp.delay_for_attempt(10) == 10.0  # capped

    def test_due_endpoints(self) -> None:
        self.executor.register_endpoint("https://due.example.com", interval_seconds=0)
        assert len(self.executor.get_due_endpoints()) == 1

    def test_disable_enable_endpoint(self) -> None:
        self.executor.register_endpoint("https://toggle.example.com")
        assert self.executor.disable_endpoint("https://toggle.example.com")
        assert len(self.executor.get_due_endpoints()) == 0
        assert self.executor.enable_endpoint("https://toggle.example.com")

    def test_fetch_history(self) -> None:
        self.executor.register_endpoint("https://hist.example.com")
        self.executor.execute_fetch("https://hist.example.com")
        history = self.executor.get_fetch_history("https://hist.example.com")
        assert len(history) == 1

    def test_audit_log(self) -> None:
        self.executor.register_endpoint("https://audit.example.com")
        self.executor.execute_fetch("https://audit.example.com")
        log = self.executor.get_audit_log("https://audit.example.com")
        assert len(log) == 1
        assert log[0].audit_hash

    def test_cached_payload(self) -> None:
        self.executor.register_endpoint("https://cache.example.com")
        self.executor.execute_fetch("https://cache.example.com", simulated_payload={"key": "val"})
        cached = self.executor.get_cached_payload("https://cache.example.com")
        assert cached == {"key": "val"}

    def test_fetch_result_hash(self) -> None:
        from src.kortana.services.metadata_fetch_executor import FetchResult
        r = FetchResult(payload={"a": 1})
        assert r.content_hash
        assert len(r.content_hash) == 64

    def test_module_singleton(self) -> None:
        from src.kortana.services.metadata_fetch_executor import (
            get_metadata_fetch_executor,
        )
        a = get_metadata_fetch_executor()
        b = get_metadata_fetch_executor()
        assert a is b


class TestSecretManagerClient(unittest.TestCase):
    """Tests for V15B — SecretManagerClient."""

    def setUp(self) -> None:
        from src.kortana.services.secret_manager_client import (
            ClientConfig,
            SecretManagerClientRegistry,
        )
        self.registry = SecretManagerClientRegistry()
        self.config = ClientConfig(
            backend_name="test_vault",
            endpoint_url="https://vault.test.com",
            pool_size=3,
        )

    def test_register_client(self) -> None:
        client = self.registry.register_client(self.config)
        from src.kortana.services.secret_manager_client import ClientState
        assert client.state == ClientState.DISCONNECTED
        assert self.registry.client_count == 1

    def test_connect_disconnect(self) -> None:
        from src.kortana.services.secret_manager_client import ClientState
        self.registry.register_client(self.config)
        probe = self.registry.connect_client("test_vault")
        assert probe is not None
        assert probe.healthy
        client = self.registry.get_client("test_vault")
        assert client.state == ClientState.CONNECTED
        client.disconnect()
        assert client.state == ClientState.DISCONNECTED

    def test_health_check_connected(self) -> None:
        self.registry.register_client(self.config)
        self.registry.connect_client("test_vault")
        client = self.registry.get_client("test_vault")
        probe = client.health_check()
        assert probe.healthy

    def test_health_check_disconnected(self) -> None:
        self.registry.register_client(self.config)
        client = self.registry.get_client("test_vault")
        probe = client.health_check()
        assert not probe.healthy
        assert "not connected" in probe.error_message

    def test_execute_write_read(self) -> None:
        self.registry.register_client(self.config)
        self.registry.connect_client("test_vault")
        client = self.registry.get_client("test_vault")
        rec = client.write_secret("db_pass", "s3cret")
        assert rec.success
        val, rec2 = client.read_secret("db_pass")
        assert val == "s3cret"

    def test_execute_rotate(self) -> None:
        self.registry.register_client(self.config)
        self.registry.connect_client("test_vault")
        client = self.registry.get_client("test_vault")
        client.write_secret("api_key", "old")
        rec = client.rotate_secret("api_key", "new")
        assert rec.success
        val, _ = client.read_secret("api_key")
        assert val == "new"

    def test_execute_failure(self) -> None:
        from src.kortana.services.secret_manager_client import OperationType
        self.registry.register_client(self.config)
        self.registry.connect_client("test_vault")
        client = self.registry.get_client("test_vault")
        rec = client.execute_operation(OperationType.READ, secret_id="x", simulate_failure=True)
        assert not rec.success

    def test_degraded_state(self) -> None:
        from src.kortana.services.secret_manager_client import (
            ClientState,
            OperationType,
        )
        self.registry.register_client(self.config)
        self.registry.connect_client("test_vault")
        client = self.registry.get_client("test_vault")
        for _ in range(3):
            client.execute_operation(OperationType.READ, simulate_failure=True)
        client.health_check()
        assert client.state == ClientState.DEGRADED

    def test_pool_status(self) -> None:
        self.registry.register_client(self.config)
        self.registry.connect_client("test_vault")
        client = self.registry.get_client("test_vault")
        pool = client.get_pool_status()
        assert len(pool) == 3  # pool_size=3

    def test_operation_record_hash(self) -> None:
        from src.kortana.services.secret_manager_client import OperationRecord
        rec = OperationRecord(backend_name="test")
        assert rec.operation_hash
        assert len(rec.operation_hash) == 64

    def test_client_registry_list(self) -> None:
        self.registry.register_client(self.config)
        clients = self.registry.list_clients()
        assert len(clients) == 1
        assert clients[0]["backend_name"] == "test_vault"

    def test_connect_all(self) -> None:
        from src.kortana.services.secret_manager_client import ClientConfig
        self.registry.register_client(self.config)
        self.registry.register_client(ClientConfig(backend_name="test_aws"))
        probes = self.registry.connect_all()
        assert len(probes) == 2
        assert all(p.healthy for p in probes)

    def test_module_singleton(self) -> None:
        from src.kortana.services.secret_manager_client import (
            get_secret_manager_client_registry,
        )
        a = get_secret_manager_client_registry()
        b = get_secret_manager_client_registry()
        assert a is b


class TestCASignerSource(unittest.TestCase):
    """Tests for V15C — CASignerSource."""

    def setUp(self) -> None:
        from src.kortana.services.ca_signer_source import (
            CASignerSource,
            CASourceConfig,
            CASourceType,
        )
        self.source = CASignerSource()
        self.ca_config = CASourceConfig(
            ca_name="Test CA",
            ca_type=CASourceType.PUBLIC_CA,
            crl_endpoint="https://ca.test.com/crl",
            ocsp_endpoint="https://ca.test.com/ocsp",
        )

    def test_register_ca(self) -> None:
        result = self.source.register_ca(self.ca_config)
        assert result.ca_name == "Test CA"
        assert self.source.ca_count == 1

    def test_fetch_crl(self) -> None:
        from src.kortana.services.ca_signer_source import CRLEntry
        self.source.register_ca(self.ca_config)
        entries = [CRLEntry(serial_number="ABC123", reason="key_compromise")]
        result = self.source.fetch_crl(self.ca_config.ca_id, simulated_entries=entries)
        assert result.success
        assert len(result.entries) == 1

    def test_fetch_crl_failure(self) -> None:
        self.source.register_ca(self.ca_config)
        result = self.source.fetch_crl(self.ca_config.ca_id, simulate_failure=True)
        assert not result.success

    def test_check_ocsp_good(self) -> None:
        from src.kortana.services.ca_signer_source import RevocationStatus
        self.source.register_ca(self.ca_config)
        result = self.source.check_ocsp(self.ca_config.ca_id, "SERIAL001")
        assert result.status == RevocationStatus.GOOD

    def test_check_ocsp_revoked(self) -> None:
        from src.kortana.services.ca_signer_source import CRLEntry, RevocationStatus
        self.source.register_ca(self.ca_config)
        self.source.fetch_crl(self.ca_config.ca_id, simulated_entries=[
            CRLEntry(serial_number="REVOKED001", reason="key_compromise"),
        ])
        result = self.source.check_ocsp(self.ca_config.ca_id, "REVOKED001")
        assert result.status == RevocationStatus.REVOKED

    def test_check_ocsp_unknown_ca(self) -> None:
        from src.kortana.services.ca_signer_source import RevocationStatus
        result = self.source.check_ocsp("unknown_ca", "SERIAL001")
        assert result.status == RevocationStatus.ERROR

    def test_validate_chain_valid(self) -> None:
        self.source.register_ca(self.ca_config)
        result = self.source.validate_chain("signer1", self.ca_config.ca_id)
        assert result.valid
        assert result.chain_depth == 3

    def test_validate_chain_revoked(self) -> None:
        from src.kortana.services.ca_signer_source import CRLEntry
        self.source.register_ca(self.ca_config)
        self.source.fetch_crl(self.ca_config.ca_id, simulated_entries=[
            CRLEntry(serial_number="CERT_REV", reason="compromised"),
        ])
        result = self.source.validate_chain("signer1", self.ca_config.ca_id, serial_number="CERT_REV")
        assert not result.valid
        assert "revoked" in result.reason

    def test_validate_chain_unknown_ca(self) -> None:
        result = self.source.validate_chain("signer1", "no_ca")
        assert not result.valid

    def test_sync_from_ca(self) -> None:
        self.source.register_ca(self.ca_config)
        snapshot = self.source.sync_from_ca(self.ca_config.ca_id)
        assert snapshot.active_signers >= 0
        assert snapshot.snapshot_hash

    def test_is_certificate_revoked(self) -> None:
        from src.kortana.services.ca_signer_source import CRLEntry
        self.source.register_ca(self.ca_config)
        self.source.fetch_crl(self.ca_config.ca_id, simulated_entries=[
            CRLEntry(serial_number="REV_CERT"),
        ])
        assert self.source.is_certificate_revoked(self.ca_config.ca_id, "REV_CERT")
        assert not self.source.is_certificate_revoked(self.ca_config.ca_id, "GOOD_CERT")

    def test_get_all_revoked(self) -> None:
        from src.kortana.services.ca_signer_source import CRLEntry
        self.source.register_ca(self.ca_config)
        self.source.fetch_crl(self.ca_config.ca_id, simulated_entries=[
            CRLEntry(serial_number="A"), CRLEntry(serial_number="B"),
        ])
        revoked = self.source.get_all_revoked()
        assert self.ca_config.ca_id in revoked
        assert len(revoked[self.ca_config.ca_id]) == 2

    def test_sync_snapshots(self) -> None:
        self.source.register_ca(self.ca_config)
        self.source.sync_from_ca(self.ca_config.ca_id)
        snaps = self.source.get_sync_snapshots(self.ca_config.ca_id)
        assert len(snaps) == 1

    def test_module_singleton(self) -> None:
        from src.kortana.services.ca_signer_source import get_ca_signer_source
        a = get_ca_signer_source()
        b = get_ca_signer_source()
        assert a is b


class TestDeployPipelineEnforcement(unittest.TestCase):
    """Tests for V15D — PipelineEnforcer."""

    def setUp(self) -> None:
        from src.kortana.services.deploy_pipeline_enforcement import PipelineEnforcer
        self.enforcer = PipelineEnforcer()

    def test_configure_gate(self) -> None:
        from src.kortana.services.deploy_pipeline_enforcement import (
            DeploymentStage,
            PipelineGateConfig,
        )
        config = PipelineGateConfig(
            stage=DeploymentStage.SCAN,
            required_artifact_types=["vulnerability_scan"],
            max_allowed_vulnerabilities=5,
        )
        result = self.enforcer.configure_gate(config)
        assert result.stage == DeploymentStage.SCAN

    def test_evaluate_gate_pass(self) -> None:
        from src.kortana.services.deploy_pipeline_enforcement import (
            DeploymentStage,
            GateVerdict,
            PipelineGateConfig,
        )
        self.enforcer.configure_gate(PipelineGateConfig(
            stage=DeploymentStage.SCAN,
            required_artifact_types=["vulnerability_scan"],
            max_allowed_vulnerabilities=5,
        ))
        result = self.enforcer.evaluate_gate(
            DeploymentStage.SCAN, "v1.0",
            available_artifacts=["vulnerability_scan"],
            vulnerability_count=3,
        )
        assert result.verdict == GateVerdict.PASS

    def test_evaluate_gate_fail_artifacts(self) -> None:
        from src.kortana.services.deploy_pipeline_enforcement import (
            DeploymentStage,
            GateVerdict,
            PipelineGateConfig,
        )
        self.enforcer.configure_gate(PipelineGateConfig(
            stage=DeploymentStage.SCAN,
            required_artifact_types=["vulnerability_scan", "sbom"],
        ))
        result = self.enforcer.evaluate_gate(
            DeploymentStage.SCAN, "v1.0",
            available_artifacts=["vulnerability_scan"],
        )
        assert result.verdict == GateVerdict.FAIL
        assert "Missing artifacts" in result.failures[0]

    def test_evaluate_gate_fail_signer(self) -> None:
        from src.kortana.services.deploy_pipeline_enforcement import (
            DeploymentStage,
            GateVerdict,
            PipelineGateConfig,
        )
        self.enforcer.configure_gate(PipelineGateConfig(
            stage=DeploymentStage.BUILD,
            require_signer_validation=True,
        ))
        result = self.enforcer.evaluate_gate(
            DeploymentStage.BUILD, "v1.0", signer_valid=False,
        )
        assert result.verdict == GateVerdict.FAIL

    def test_evaluate_gate_fail_vulnerabilities(self) -> None:
        from src.kortana.services.deploy_pipeline_enforcement import (
            DeploymentStage,
            GateVerdict,
            PipelineGateConfig,
        )
        self.enforcer.configure_gate(PipelineGateConfig(
            stage=DeploymentStage.SCAN,
            max_allowed_vulnerabilities=0,
        ))
        result = self.enforcer.evaluate_gate(
            DeploymentStage.SCAN, "v1.0", vulnerability_count=5,
        )
        assert result.verdict == GateVerdict.FAIL

    def test_evaluate_gate_no_config(self) -> None:
        from src.kortana.services.deploy_pipeline_enforcement import (
            DeploymentStage,
            GateVerdict,
        )
        result = self.enforcer.evaluate_gate(DeploymentStage.BUILD, "v1.0")
        assert result.verdict == GateVerdict.SKIP

    def test_create_pipeline(self) -> None:
        from src.kortana.services.deploy_pipeline_enforcement import PipelineStatus
        pipeline = self.enforcer.create_pipeline("v2.0")
        assert pipeline.version_id == "v2.0"
        assert pipeline.status == PipelineStatus.PENDING
        assert self.enforcer.pipeline_count == 1

    def test_advance_pipeline_pass(self) -> None:
        from src.kortana.services.deploy_pipeline_enforcement import (
            DeploymentStage,
            PipelineStatus,
        )
        pipeline = self.enforcer.create_pipeline("v2.0")
        execution = self.enforcer.advance_pipeline(pipeline.pipeline_id)
        assert execution.status == PipelineStatus.PASSED
        p = self.enforcer.get_pipeline(pipeline.pipeline_id)
        assert p.current_stage == DeploymentStage.TEST

    def test_advance_pipeline_fail_rollback(self) -> None:
        from src.kortana.services.deploy_pipeline_enforcement import (
            DeploymentStage,
            PipelineGateConfig,
            PipelineStatus,
        )
        self.enforcer.configure_gate(PipelineGateConfig(
            stage=DeploymentStage.BUILD,
            required_artifact_types=["signed_manifest"],
            auto_rollback_on_failure=True,
        ))
        pipeline = self.enforcer.create_pipeline("v3.0")
        execution = self.enforcer.advance_pipeline(
            pipeline.pipeline_id, available_artifacts=[],
        )
        assert execution.status == PipelineStatus.FAILED
        p = self.enforcer.get_pipeline(pipeline.pipeline_id)
        assert p.status == PipelineStatus.ROLLED_BACK
        assert len(p.rollbacks) == 1

    def test_advance_through_stages(self) -> None:
        from src.kortana.services.deploy_pipeline_enforcement import (
            STAGE_ORDER,
            PipelineStatus,
        )
        pipeline = self.enforcer.create_pipeline("v4.0")
        for _ in range(len(STAGE_ORDER)):
            self.enforcer.advance_pipeline(pipeline.pipeline_id)
        p = self.enforcer.get_pipeline(pipeline.pipeline_id)
        assert p.status == PipelineStatus.PASSED
        assert p.completed_at is not None

    def test_rollback_record_hash(self) -> None:
        from src.kortana.services.deploy_pipeline_enforcement import RollbackRecord
        rb = RollbackRecord(pipeline_id="p1", version_id="v1")
        assert rb.rollback_hash
        assert len(rb.rollback_hash) == 64

    def test_pipeline_to_dict(self) -> None:
        pipeline = self.enforcer.create_pipeline("v5.0")
        d = pipeline.to_dict()
        assert d["version_id"] == "v5.0"
        assert "pipeline_hash" in d

    def test_gate_check_history(self) -> None:
        pipeline = self.enforcer.create_pipeline("v6.0")
        self.enforcer.advance_pipeline(pipeline.pipeline_id)
        checks = self.enforcer.get_check_history("v6.0")
        assert len(checks) >= 1

    def test_module_singleton(self) -> None:
        from src.kortana.services.deploy_pipeline_enforcement import (
            get_pipeline_enforcer,
        )
        a = get_pipeline_enforcer()
        b = get_pipeline_enforcer()
        assert a is b
