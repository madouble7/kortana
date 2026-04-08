"""V14 — Policy Orchestration Across Real Enterprise Systems tests.

Tests for:
  V14A — IdP Metadata Sync
  V14B — External Secret Backend
  V14C — Live Signer Inventory
  V14D — Trust Artifact Policy
"""

from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# V14A — IdP Metadata Sync tests
# ---------------------------------------------------------------------------


class TestIdPMetadataSync:
    """Tests for idp_metadata_sync.py."""

    def test_register_provider(self):
        from src.kortana.services.idp_metadata_sync import IdPMetadataSyncScheduler

        scheduler = IdPMetadataSyncScheduler()
        policy = scheduler.register_provider("https://auth.example.com")
        assert policy.sync_interval_minutes == 60
        assert scheduler.provider_count == 1

    def test_update_and_check_drift(self):
        from src.kortana.services.idp_metadata_sync import IdPMetadataSyncScheduler

        scheduler = IdPMetadataSyncScheduler()
        scheduler.register_provider("https://idp.io")
        scheduler.update_snapshot("https://idp.io", {"issuer": "https://idp.io", "jwks_uri": "/jwks"})
        drifts = scheduler.check_drift("https://idp.io", {"issuer": "https://idp2.io", "jwks_uri": "/jwks"})
        assert len(drifts) == 1
        assert drifts[0].field_name == "issuer"

    def test_drift_severity_classification(self):
        from src.kortana.services.idp_metadata_sync import DriftSeverity, IdPMetadataSyncScheduler

        scheduler = IdPMetadataSyncScheduler()
        scheduler.register_provider("https://y.com")
        scheduler.update_snapshot("https://y.com", {"issuer": "a", "jwks_uri": "b"})
        drifts = scheduler.check_drift("https://y.com", {"issuer": "c", "jwks_uri": "d"})
        severities = {d.field_name: d.severity for d in drifts}
        assert severities["issuer"] == DriftSeverity.CRITICAL
        assert severities["jwks_uri"] == DriftSeverity.HIGH

    def test_reconcile_auto_remediate(self):
        from src.kortana.services.idp_metadata_sync import (
            IdPMetadataSyncScheduler,
            MetadataSyncPolicy,
            ReconcileAction,
        )

        scheduler = IdPMetadataSyncScheduler()
        policy = MetadataSyncPolicy(auto_remediate=True)
        scheduler.register_provider("https://z.com", policy)
        scheduler.update_snapshot("https://z.com", {"issuer": "old"})
        rec = scheduler.reconcile("https://z.com", {"issuer": "new"})
        assert rec.action_taken == ReconcileAction.ACCEPTED

    def test_reconcile_alert_only(self):
        from src.kortana.services.idp_metadata_sync import (
            IdPMetadataSyncScheduler,
            MetadataSyncPolicy,
            ReconcileAction,
        )

        scheduler = IdPMetadataSyncScheduler()
        policy = MetadataSyncPolicy(alert_on_drift=True, auto_remediate=False)
        scheduler.register_provider("https://a.com", policy)
        scheduler.update_snapshot("https://a.com", {"issuer": "old"})
        rec = scheduler.reconcile("https://a.com", {"issuer": "new"})
        assert rec.action_taken == ReconcileAction.ALERTED

    def test_reconcile_no_drift(self):
        from src.kortana.services.idp_metadata_sync import IdPMetadataSyncScheduler, ReconcileAction

        scheduler = IdPMetadataSyncScheduler()
        scheduler.register_provider("https://b.com")
        rec = scheduler.reconcile("https://b.com")
        assert rec.action_taken == ReconcileAction.SKIPPED

    def test_sync_history(self):
        from src.kortana.services.idp_metadata_sync import IdPMetadataSyncScheduler

        scheduler = IdPMetadataSyncScheduler()
        scheduler.register_provider("https://c.com")
        scheduler.update_snapshot("https://c.com", {"issuer": "v1"})
        history = scheduler.get_sync_history("https://c.com")
        assert len(history) == 1

    def test_drift_report(self):
        from src.kortana.services.idp_metadata_sync import IdPMetadataSyncScheduler

        scheduler = IdPMetadataSyncScheduler()
        scheduler.register_provider("https://d.com")
        scheduler.update_snapshot("https://d.com", {"issuer": "a"})
        scheduler.check_drift("https://d.com", {"issuer": "b"})
        report = scheduler.get_drift_report()
        assert report["total_drifts"] >= 1

    def test_metadata_drift_to_dict(self):
        from src.kortana.services.idp_metadata_sync import MetadataDrift

        d = MetadataDrift(provider_url="https://e.com", field_name="issuer")
        dd = d.to_dict()
        assert "drift_id" in dd
        assert dd["field_name"] == "issuer"

    def test_reconciliation_hash(self):
        from src.kortana.services.idp_metadata_sync import MetadataReconciliation

        rec = MetadataReconciliation(provider_url="https://f.com")
        assert rec.reconciliation_hash

    def test_module_singleton(self):
        from src.kortana.services.idp_metadata_sync import get_idp_metadata_sync_scheduler

        s1 = get_idp_metadata_sync_scheduler()
        s2 = get_idp_metadata_sync_scheduler()
        assert s1 is s2


# ---------------------------------------------------------------------------
# V14B — External Secret Backend tests
# ---------------------------------------------------------------------------


class TestExternalSecretBackend:
    """Tests for external_secret_backend.py."""

    def test_vault_store_and_fetch(self):
        from src.kortana.services.external_secret_backend import VaultSecretStore
        from src.kortana.services.secret_store import SecretBackend

        vault = VaultSecretStore()
        ref = vault.store_secret("db-pass", "hunter2")
        assert ref.backend == SecretBackend.VAULT
        val = vault.fetch_secret("db-pass")
        assert val is not None
        assert val.value == "hunter2"

    def test_aws_store_and_rotate(self):
        from src.kortana.services.external_secret_backend import AWSSecretStore
        from src.kortana.services.secret_store import SecretBackend

        aws = AWSSecretStore()
        aws.store_secret("key", "v1")
        ref = aws.rotate_secret("key", "v2")
        assert ref.backend == SecretBackend.AWS_SM
        assert ref.version == 2

    def test_gcp_store_path(self):
        from src.kortana.services.external_secret_backend import GCPSecretStore

        gcp = GCPSecretStore()
        ref = gcp.store_secret("token", "abc")
        assert "projects" in ref.path

    def test_azure_store_path(self):
        from src.kortana.services.external_secret_backend import AzureKeyVaultStore

        azure = AzureKeyVaultStore()
        ref = azure.store_secret("cert", "xyz")
        assert "vault.azure.net" in ref.path

    def test_rotation_scheduler(self):
        from src.kortana.services.external_secret_backend import RotationScheduler

        scheduler = RotationScheduler()
        entry = scheduler.schedule_rotation("key1", "local", 24)
        assert entry.interval_hours == 24
        assert scheduler.schedule_count == 1

    def test_rotation_due_check(self):
        from src.kortana.services.external_secret_backend import RotationScheduler

        scheduler = RotationScheduler()
        entry = scheduler.schedule_rotation("key2", "local", 0)
        entry.next_rotation_at = datetime.utcnow() - timedelta(hours=1)
        due = scheduler.check_due()
        assert len(due) >= 1

    def test_health_monitor(self):
        from src.kortana.services.external_secret_backend import (
            SecretHealthMonitor,
            get_external_secret_registry,
        )

        registry = get_external_secret_registry()
        monitor = SecretHealthMonitor(registry)
        health = monitor.check_health("local")
        assert health.healthy is True

    def test_health_all_backends(self):
        from src.kortana.services.external_secret_backend import (
            SecretHealthMonitor,
            get_external_secret_registry,
        )

        registry = get_external_secret_registry()
        monitor = SecretHealthMonitor(registry)
        results = monitor.check_all()
        assert len(results) >= 4  # local + vault + aws + gcp + azure

    def test_external_registry_singleton(self):
        from src.kortana.services.external_secret_backend import get_external_secret_registry

        r1 = get_external_secret_registry()
        r2 = get_external_secret_registry()
        assert r1 is r2

    def test_external_registry_backends(self):
        from src.kortana.services.external_secret_backend import get_external_secret_registry

        registry = get_external_secret_registry()
        backends = registry.list_backends()
        assert "vault" in backends
        assert "aws_sm" in backends

    def test_health_unknown_backend(self):
        from src.kortana.services.external_secret_backend import SecretHealthMonitor
        from src.kortana.services.secret_store import SecretStoreRegistry

        monitor = SecretHealthMonitor(SecretStoreRegistry())
        health = monitor.check_health("nonexistent")
        assert health.healthy is False

    def test_rotation_schedule_to_dict(self):
        from src.kortana.services.external_secret_backend import RotationScheduleEntry

        entry = RotationScheduleEntry(secret_id="x", backend="local")
        d = entry.to_dict()
        assert "secret_id" in d
        assert "is_due" in d


# ---------------------------------------------------------------------------
# V14C — Live Signer Inventory tests
# ---------------------------------------------------------------------------


class TestLiveSignerInventory:
    """Tests for live_signer_inventory.py."""

    def test_register_signer(self):
        from src.kortana.services.live_signer_inventory import LiveSignerRegistry

        reg = LiveSignerRegistry()
        cert = reg.register_signer("github-ci", "GitHub")
        assert cert.signer_id == "github-ci"
        assert cert.is_valid is True
        assert reg.signer_count == 1

    def test_revoke_signer(self):
        from src.kortana.services.live_signer_inventory import LiveSignerRegistry, SignerStatus

        reg = LiveSignerRegistry()
        reg.register_signer("s1", "issuer")
        entry = reg.revoke_signer("s1", "compromised", "admin")
        assert entry is not None
        assert reg.check_signer_status("s1") == SignerStatus.REVOKED

    def test_revoke_nonexistent(self):
        from src.kortana.services.live_signer_inventory import LiveSignerRegistry

        reg = LiveSignerRegistry()
        assert reg.revoke_signer("nope") is None

    def test_validate_active_chain(self):
        from src.kortana.services.live_signer_inventory import LiveSignerRegistry

        reg = LiveSignerRegistry()
        reg.register_signer("s2", "issuer")
        valid, err = reg.validate_certificate_chain("s2")
        assert valid is True
        assert err is None

    def test_validate_revoked_chain(self):
        from src.kortana.services.live_signer_inventory import LiveSignerRegistry

        reg = LiveSignerRegistry()
        reg.register_signer("s3")
        reg.revoke_signer("s3")
        valid, err = reg.validate_certificate_chain("s3")
        assert valid is False
        assert "revoked" in err

    def test_validate_expired_chain(self):
        from src.kortana.services.live_signer_inventory import LiveSignerRegistry

        reg = LiveSignerRegistry()
        cert = reg.register_signer("s4", expires_in_days=0)
        cert.expires_at = datetime.utcnow() - timedelta(hours=1)
        valid, err = reg.validate_certificate_chain("s4")
        assert valid is False
        assert "expired" in err

    def test_sync_inventory(self):
        from src.kortana.services.live_signer_inventory import LiveSignerRegistry

        reg = LiveSignerRegistry()
        reg.register_signer("a")
        reg.register_signer("b")
        reg.revoke_signer("b")
        inventory = reg.sync_inventory()
        assert len(inventory.signers) == 1

    def test_revocation_list(self):
        from src.kortana.services.live_signer_inventory import LiveSignerRegistry

        reg = LiveSignerRegistry()
        reg.register_signer("x")
        reg.revoke_signer("x", "test")
        revocations = reg.get_revocation_list()
        assert len(revocations) == 1

    def test_validate_attestation_against_inventory(self):
        from src.kortana.services.live_signer_inventory import LiveSignerRegistry

        reg = LiveSignerRegistry()
        reg.register_signer("ci-bot")
        valid, err = reg.validate_attestation_against_inventory("ci-bot")
        assert valid is True

    def test_validate_attestation_unknown_signer(self):
        from src.kortana.services.live_signer_inventory import LiveSignerRegistry

        reg = LiveSignerRegistry()
        valid, err = reg.validate_attestation_against_inventory("unknown")
        assert valid is False

    def test_certificate_to_dict(self):
        from src.kortana.services.live_signer_inventory import SignerCertificate

        cert = SignerCertificate(signer_id="test")
        d = cert.to_dict()
        assert "is_valid" in d
        assert "certificate_hash" in d

    def test_inventory_hash(self):
        from src.kortana.services.live_signer_inventory import SignerInventory

        inv = SignerInventory()
        assert inv.inventory_hash

    def test_module_singleton(self):
        from src.kortana.services.live_signer_inventory import get_live_signer_registry

        r1 = get_live_signer_registry()
        r2 = get_live_signer_registry()
        assert r1 is r2


# ---------------------------------------------------------------------------
# V14D — Trust Artifact Policy tests
# ---------------------------------------------------------------------------


class TestTrustArtifactPolicy:
    """Tests for trust_artifact_policy.py."""

    def test_register_artifact(self):
        from src.kortana.services.trust_artifact_policy import (
            ArtifactType,
            PolicyOrchestrator,
            TrustArtifact,
        )

        orch = PolicyOrchestrator()
        art = orch.register_artifact(
            TrustArtifact(artifact_type=ArtifactType.SIGNED_MANIFEST, issuer="ci")
        )
        assert art.artifact_id.startswith("art_")
        assert orch.artifact_count == 1

    def test_define_policy(self):
        from src.kortana.services.trust_artifact_policy import ArtifactType, PolicyOrchestrator

        orch = PolicyOrchestrator()
        policy = orch.define_policy("prod-deploy", [ArtifactType.SIGNED_MANIFEST, ArtifactType.SBOM_ATTESTATION])
        assert len(policy.required_artifacts) == 2
        assert orch.policy_count == 1

    def test_verify_artifact_ok(self):
        from src.kortana.services.trust_artifact_policy import (
            ArtifactPolicy,
            ArtifactType,
            PolicyOrchestrator,
            TrustArtifact,
        )

        orch = PolicyOrchestrator()
        art = TrustArtifact(artifact_type=ArtifactType.SIGNED_MANIFEST)
        policy = ArtifactPolicy(required_artifacts=[ArtifactType.SIGNED_MANIFEST])
        v = orch.verify_artifact(art, policy)
        assert v.verified is True

    def test_verify_artifact_expired(self):
        from src.kortana.services.trust_artifact_policy import (
            ArtifactPolicy,
            ArtifactType,
            PolicyOrchestrator,
            TrustArtifact,
        )

        orch = PolicyOrchestrator()
        art = TrustArtifact(
            artifact_type=ArtifactType.VULNERABILITY_SCAN,
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        policy = ArtifactPolicy(required_artifacts=[ArtifactType.VULNERABILITY_SCAN])
        v = orch.verify_artifact(art, policy)
        assert v.verified is False
        assert "expired" in v.reason

    def test_verify_artifact_too_old(self):
        from src.kortana.services.trust_artifact_policy import (
            ArtifactPolicy,
            ArtifactType,
            PolicyOrchestrator,
            TrustArtifact,
        )

        orch = PolicyOrchestrator()
        art = TrustArtifact(
            artifact_type=ArtifactType.COMPLIANCE_CERT,
            issued_at=datetime.utcnow() - timedelta(hours=800),
        )
        policy = ArtifactPolicy(
            required_artifacts=[ArtifactType.COMPLIANCE_CERT],
            max_artifact_age_hours=720.0,
        )
        v = orch.verify_artifact(art, policy)
        assert v.verified is False
        assert "too old" in v.reason

    def test_evaluate_deployment_all_pass(self):
        from src.kortana.services.trust_artifact_policy import (
            ArtifactPolicy,
            ArtifactType,
            PolicyOrchestrator,
            TrustArtifact,
        )

        orch = PolicyOrchestrator()
        orch.register_artifact(TrustArtifact(artifact_type=ArtifactType.SIGNED_MANIFEST, version_id="v1"))
        orch.register_artifact(TrustArtifact(artifact_type=ArtifactType.SBOM_ATTESTATION, version_id="v1"))
        policy = ArtifactPolicy(
            required_artifacts=[ArtifactType.SIGNED_MANIFEST, ArtifactType.SBOM_ATTESTATION]
        )
        passed, verifications = orch.evaluate_deployment("v1", policy)
        assert passed is True
        assert len(verifications) == 2

    def test_evaluate_deployment_missing(self):
        from src.kortana.services.trust_artifact_policy import (
            ArtifactPolicy,
            ArtifactType,
            PolicyOrchestrator,
            TrustArtifact,
        )

        orch = PolicyOrchestrator()
        orch.register_artifact(TrustArtifact(artifact_type=ArtifactType.SIGNED_MANIFEST))
        policy = ArtifactPolicy(
            required_artifacts=[ArtifactType.SIGNED_MANIFEST, ArtifactType.VULNERABILITY_SCAN]
        )
        passed, verifications = orch.evaluate_deployment("v1", policy)
        assert passed is False

    def test_evaluate_deployment_require_any(self):
        from src.kortana.services.trust_artifact_policy import (
            ArtifactPolicy,
            ArtifactType,
            PolicyOrchestrator,
            TrustArtifact,
        )

        orch = PolicyOrchestrator()
        orch.register_artifact(TrustArtifact(artifact_type=ArtifactType.AUDIT_REPORT))
        policy = ArtifactPolicy(
            required_artifacts=[ArtifactType.AUDIT_REPORT, ArtifactType.COMPLIANCE_CERT],
            require_all=False,
        )
        passed, _ = orch.evaluate_deployment("", policy)
        assert passed is True

    def test_promote_with_artifacts_fails(self):
        from src.kortana.services.trust_artifact_policy import (
            ArtifactPolicy,
            ArtifactType,
            PolicyOrchestrator,
        )

        orch = PolicyOrchestrator()
        policy = ArtifactPolicy(required_artifacts=[ArtifactType.SIGNED_MANIFEST])
        result, error = orch.promote_with_artifacts("v1", "s1", policy)
        assert error is not None
        assert "Artifact policy failed" in error

    def test_artifact_to_dict(self):
        from src.kortana.services.trust_artifact_policy import ArtifactType, TrustArtifact

        art = TrustArtifact(artifact_type=ArtifactType.SBOM_ATTESTATION, issuer="ci")
        d = art.to_dict()
        assert d["artifact_type"] == "sbom_attestation"
        assert "artifact_hash" in d

    def test_policy_to_dict(self):
        from src.kortana.services.trust_artifact_policy import ArtifactPolicy, ArtifactType

        policy = ArtifactPolicy(
            policy_name="test", required_artifacts=[ArtifactType.SIGNED_MANIFEST]
        )
        d = policy.to_dict()
        assert d["policy_name"] == "test"
        assert "policy_hash" in d

    def test_verification_to_dict(self):
        from src.kortana.services.trust_artifact_policy import ArtifactVerification

        v = ArtifactVerification(verified=True, reason="OK")
        d = v.to_dict()
        assert d["verified"] is True

    def test_artifact_type_values(self):
        from src.kortana.services.trust_artifact_policy import ArtifactType

        assert ArtifactType.SIGNED_MANIFEST.value == "signed_manifest"
        assert ArtifactType.AUDIT_REPORT.value == "audit_report"

    def test_module_singleton(self):
        from src.kortana.services.trust_artifact_policy import get_policy_orchestrator

        o1 = get_policy_orchestrator()
        o2 = get_policy_orchestrator()
        assert o1 is o2
