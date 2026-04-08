"""V13 — Enterprise Control Integration tests.

Tests for:
  V13A — IdP Discovery & Config Sync
  V13B — Secret Store Abstraction
  V13C — Webhook Attestation & CI Verification
  V13D — Trust Signal Consumer & Deploy Gate
"""

from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# V13A — IdP Discovery tests
# ---------------------------------------------------------------------------


class TestIdPDiscovery:
    """Tests for idp_discovery.py."""

    def test_register_and_list_providers(self):
        from src.kortana.services.idp_discovery import IdPDiscoveryManager

        mgr = IdPDiscoveryManager()
        payload = {"issuer": "https://auth.example.com", "token_endpoint": "https://auth.example.com/token"}
        provider = mgr.register_discovery_payload("https://auth.example.com/.well-known/openid-configuration", payload)
        assert provider.issuer == "https://auth.example.com"
        assert mgr.provider_count == 1

    def test_sync_event_recorded(self):
        from src.kortana.services.idp_discovery import IdPDiscoveryManager

        mgr = IdPDiscoveryManager()
        payload = {"issuer": "https://x.com"}
        mgr.register_discovery_payload("https://x.com/.well-known/openid-configuration", payload)
        events = mgr.get_sync_events()
        assert len(events) >= 1

    def test_discover_creates_provider(self):
        from src.kortana.services.idp_discovery import IdPDiscoveryManager

        mgr = IdPDiscoveryManager()
        payload = {"issuer": "https://y.com", "jwks_uri": "https://y.com/jwks"}
        provider = mgr.register_discovery_payload("https://y.com/.well-known", payload)
        assert provider.jwks_uri == "https://y.com/jwks"
        assert provider.config_hash

    def test_sync_state_transitions(self):
        from src.kortana.services.idp_discovery import IdPDiscoveryManager, IdPSyncState

        mgr = IdPDiscoveryManager()
        payload = {"issuer": "https://z.com"}
        mgr.register_discovery_payload("https://z.com/.well-known", payload)
        status = mgr.get_sync_status("https://z.com/.well-known")
        assert status == IdPSyncState.SYNCED

    def test_sync_unknown_provider(self):
        from src.kortana.services.idp_discovery import IdPDiscoveryManager

        mgr = IdPDiscoveryManager()
        provider, err = mgr.sync_provider("https://none.com")
        assert err is not None

    def test_check_stale_providers(self):
        from src.kortana.services.idp_discovery import IdPDiscoveryManager, IdPDiscoveryConfig

        mgr = IdPDiscoveryManager()
        cfg = IdPDiscoveryConfig(discovery_url="https://stale.com", refresh_interval_hours=0)
        mgr.register_discovery_payload("https://stale.com", {"issuer": "stale"})
        mgr._configs["https://stale.com"] = cfg
        stale = mgr.check_stale_providers()
        assert isinstance(stale, list)

    def test_provider_to_dict(self):
        from src.kortana.services.idp_discovery import IdPDiscoveryManager

        mgr = IdPDiscoveryManager()
        payload = {"issuer": "https://d.com"}
        provider = mgr.register_discovery_payload("https://d.com", payload)
        d = provider.to_dict()
        assert "issuer" in d
        assert "config_hash" in d

    def test_sync_event_hash(self):
        from src.kortana.services.idp_discovery import IdPDiscoveryManager

        mgr = IdPDiscoveryManager()
        mgr.register_discovery_payload("https://e.com", {"issuer": "e"})
        events = mgr.get_sync_events()
        assert events[0].event_hash

    def test_module_singleton(self):
        from src.kortana.services.idp_discovery import get_idp_discovery_manager

        mgr1 = get_idp_discovery_manager()
        mgr2 = get_idp_discovery_manager()
        assert mgr1 is mgr2


# ---------------------------------------------------------------------------
# V13B — Secret Store tests
# ---------------------------------------------------------------------------


class TestSecretStore:
    """Tests for secret_store.py."""

    def test_store_and_fetch(self):
        from src.kortana.services.secret_store import SecretStoreRegistry

        registry = SecretStoreRegistry()
        ref = registry.store_secret("db-pass", "hunter2", "local")
        assert ref.secret_id == "db-pass"
        val = registry.fetch_secret("db-pass", "local")
        assert val is not None
        assert val.value == "hunter2"

    def test_rotate_increments_version(self):
        from src.kortana.services.secret_store import SecretStoreRegistry

        registry = SecretStoreRegistry()
        registry.store_secret("key", "v1", "local")
        ref = registry.rotate_secret("key", "v2", "local")
        assert ref.version == 2

    def test_delete_secret(self):
        from src.kortana.services.secret_store import SecretStoreRegistry

        registry = SecretStoreRegistry()
        registry.store_secret("del-me", "x", "local")
        deleted = registry.delete_secret("del-me", "local")
        assert deleted is True
        assert registry.fetch_secret("del-me", "local") is None

    def test_list_secrets(self):
        from src.kortana.services.secret_store import SecretStoreRegistry

        registry = SecretStoreRegistry()
        registry.store_secret("a", "1", "local")
        registry.store_secret("b", "2", "local")
        refs = registry.list_secrets("local")
        assert len(refs) >= 2

    def test_value_redacted_in_to_dict(self):
        from src.kortana.services.secret_store import SecretStoreRegistry

        registry = SecretStoreRegistry()
        registry.store_secret("s1", "supersecret", "local")
        val = registry.fetch_secret("s1", "local")
        d = val.to_dict()
        assert d["value"] == "***REDACTED***"

    def test_list_backends(self):
        from src.kortana.services.secret_store import SecretStoreRegistry

        registry = SecretStoreRegistry()
        backends = registry.list_backends()
        assert "local" in backends

    def test_fetch_nonexistent(self):
        from src.kortana.services.secret_store import SecretStoreRegistry

        registry = SecretStoreRegistry()
        val = registry.fetch_secret("nope", "local")
        assert val is None

    def test_ref_hash(self):
        from src.kortana.services.secret_store import SecretStoreRegistry

        registry = SecretStoreRegistry()
        ref = registry.store_secret("h", "val", "local")
        assert ref.ref_hash

    def test_secret_expiry(self):
        from src.kortana.services.secret_store import SecretBackend, SecretReference, SecretValue
        from datetime import datetime, timedelta

        ref = SecretReference(secret_id="x", backend=SecretBackend.LOCAL, path="")
        val = SecretValue(ref=ref, value="v", expires_at=datetime.utcnow() - timedelta(hours=1))
        assert val.is_expired is True

    def test_module_singleton(self):
        from src.kortana.services.secret_store import get_secret_store_registry

        r1 = get_secret_store_registry()
        r2 = get_secret_store_registry()
        assert r1 is r2


# ---------------------------------------------------------------------------
# V13C — Webhook Attestation tests
# ---------------------------------------------------------------------------


class TestWebhookAttestation:
    """Tests for webhook_attestation.py."""

    def test_sign_and_verify(self):
        from src.kortana.services.webhook_attestation import WebhookSigner

        payload = b'{"event": "deploy"}'
        sig = WebhookSigner.sign(payload, "my-secret")
        assert WebhookSigner.verify(payload, sig, "my-secret") is True

    def test_verify_fails_wrong_secret(self):
        from src.kortana.services.webhook_attestation import WebhookSigner

        payload = b"test"
        sig = WebhookSigner.sign(payload, "correct")
        assert WebhookSigner.verify(payload, sig, "wrong") is False

    def test_verify_fails_tampered(self):
        from src.kortana.services.webhook_attestation import WebhookSigner

        sig = WebhookSigner.sign(b"original", "secret")
        assert WebhookSigner.verify(b"tampered", sig, "secret") is False

    def test_register_and_verify_signer(self):
        from src.kortana.services.webhook_attestation import (
            AttestationPayload,
            CIAttestationVerifier,
            WebhookSigner,
        )

        verifier = CIAttestationVerifier()
        verifier.register_trusted_signer("github-ci", "ci-secret")
        att = AttestationPayload(signer_id="github-ci", subject="deploy-v1")
        att.signature = WebhookSigner.sign(att.payload_hash.encode(), "ci-secret")
        ok, err = verifier.verify_attestation(att)
        assert ok is True
        assert err is None

    def test_untrusted_signer_rejected(self):
        from src.kortana.services.webhook_attestation import (
            AttestationPayload,
            CIAttestationVerifier,
        )

        verifier = CIAttestationVerifier()
        att = AttestationPayload(signer_id="unknown")
        ok, err = verifier.verify_attestation(att)
        assert ok is False
        assert "not trusted" in err

    def test_bad_signature_rejected(self):
        from src.kortana.services.webhook_attestation import (
            AttestationPayload,
            CIAttestationVerifier,
        )

        verifier = CIAttestationVerifier()
        verifier.register_trusted_signer("s1", "key")
        att = AttestationPayload(signer_id="s1", signature="badhex")
        ok, err = verifier.verify_attestation(att)
        assert ok is False
        assert "Signature verification failed" in err

    def test_attestation_chain_integrity(self):
        from src.kortana.services.webhook_attestation import (
            AttestationChain,
            AttestationPayload,
        )

        chain = AttestationChain()
        chain.append(AttestationPayload(subject="step1"))
        chain.append(AttestationPayload(subject="step2"))
        ok, err = chain.verify_chain()
        assert ok is True
        assert chain.chain_length == 2

    def test_chain_tamper_detection(self):
        from src.kortana.services.webhook_attestation import (
            AttestationChain,
            AttestationPayload,
        )

        chain = AttestationChain()
        att = AttestationPayload(subject="original")
        chain.append(att)
        att.payload_hash = "tampered"
        ok, err = chain.verify_chain()
        assert ok is False

    def test_attestation_type_enum(self):
        from src.kortana.services.webhook_attestation import AttestationType

        assert AttestationType.CI_PIPELINE.value == "ci_pipeline"
        assert AttestationType.WEBHOOK_SIGNATURE.value == "webhook_signature"

    def test_payload_to_dict(self):
        from src.kortana.services.webhook_attestation import AttestationPayload

        att = AttestationPayload(subject="x")
        d = att.to_dict()
        assert "attestation_id" in d
        assert "payload_hash" in d

    def test_list_trusted_signers(self):
        from src.kortana.services.webhook_attestation import CIAttestationVerifier

        verifier = CIAttestationVerifier()
        verifier.register_trusted_signer("a", "k1")
        verifier.register_trusted_signer("b", "k2")
        assert "a" in verifier.list_trusted_signers()
        assert verifier.signer_count == 2

    def test_module_singleton(self):
        from src.kortana.services.webhook_attestation import get_attestation_verifier

        v1 = get_attestation_verifier()
        v2 = get_attestation_verifier()
        assert v1 is v2


# ---------------------------------------------------------------------------
# V13D — Trust Signal Consumer tests
# ---------------------------------------------------------------------------


class TestTrustSignalConsumer:
    """Tests for trust_signal_consumer.py."""

    def test_register_signal(self):
        from src.kortana.services.trust_signal_consumer import (
            TrustSignal,
            TrustSignalConsumer,
            TrustSignalType,
        )

        consumer = TrustSignalConsumer()
        sig = consumer.register_signal(
            TrustSignal(signal_type=TrustSignalType.IDP_VERIFIED, source="okta")
        )
        assert sig.signal_id.startswith("ts_")
        assert consumer.signal_count == 1

    def test_evaluate_all_pass(self):
        from src.kortana.services.trust_signal_consumer import (
            TrustRequirement,
            TrustSignal,
            TrustSignalConsumer,
            TrustSignalType,
        )

        consumer = TrustSignalConsumer()
        consumer.register_signal(TrustSignal(signal_type=TrustSignalType.IDP_VERIFIED, confidence=0.95))
        consumer.register_signal(TrustSignal(signal_type=TrustSignalType.CI_ATTESTED, confidence=0.9))
        req = TrustRequirement(
            required_signals=[TrustSignalType.IDP_VERIFIED, TrustSignalType.CI_ATTESTED],
            min_confidence=0.8,
        )
        evaluation = consumer.evaluate(req)
        assert evaluation.passed is True
        assert evaluation.score > 0

    def test_evaluate_missing_signal(self):
        from src.kortana.services.trust_signal_consumer import (
            TrustRequirement,
            TrustSignal,
            TrustSignalConsumer,
            TrustSignalType,
        )

        consumer = TrustSignalConsumer()
        consumer.register_signal(TrustSignal(signal_type=TrustSignalType.IDP_VERIFIED, confidence=0.9))
        req = TrustRequirement(
            required_signals=[TrustSignalType.IDP_VERIFIED, TrustSignalType.CI_ATTESTED],
        )
        evaluation = consumer.evaluate(req)
        assert evaluation.passed is False
        assert "ci_attested" in evaluation.missing_signals

    def test_evaluate_low_confidence(self):
        from src.kortana.services.trust_signal_consumer import (
            TrustRequirement,
            TrustSignal,
            TrustSignalConsumer,
            TrustSignalType,
        )

        consumer = TrustSignalConsumer()
        consumer.register_signal(TrustSignal(signal_type=TrustSignalType.IDP_VERIFIED, confidence=0.5))
        req = TrustRequirement(
            required_signals=[TrustSignalType.IDP_VERIFIED],
            min_confidence=0.8,
        )
        evaluation = consumer.evaluate(req)
        assert evaluation.passed is False

    def test_evaluate_require_any(self):
        from src.kortana.services.trust_signal_consumer import (
            TrustRequirement,
            TrustSignal,
            TrustSignalConsumer,
            TrustSignalType,
        )

        consumer = TrustSignalConsumer()
        consumer.register_signal(TrustSignal(signal_type=TrustSignalType.WEBHOOK_SIGNED, confidence=0.95))
        req = TrustRequirement(
            required_signals=[TrustSignalType.IDP_VERIFIED, TrustSignalType.WEBHOOK_SIGNED],
            require_all=False,
        )
        evaluation = consumer.evaluate(req)
        assert evaluation.passed is True

    def test_expired_signal_ignored(self):
        from src.kortana.services.trust_signal_consumer import (
            TrustRequirement,
            TrustSignal,
            TrustSignalConsumer,
            TrustSignalType,
        )

        consumer = TrustSignalConsumer()
        consumer.register_signal(
            TrustSignal(
                signal_type=TrustSignalType.CI_ATTESTED,
                confidence=0.95,
                expires_at=datetime.utcnow() - timedelta(hours=1),
            )
        )
        req = TrustRequirement(required_signals=[TrustSignalType.CI_ATTESTED])
        evaluation = consumer.evaluate(req)
        assert evaluation.passed is False

    def test_signal_to_dict(self):
        from src.kortana.services.trust_signal_consumer import TrustSignal, TrustSignalType

        sig = TrustSignal(signal_type=TrustSignalType.DEPLOY_APPROVED, source="ops")
        d = sig.to_dict()
        assert d["signal_type"] == "deploy_approved"
        assert d["source"] == "ops"
        assert d["signal_hash"]

    def test_evaluation_to_dict(self):
        from src.kortana.services.trust_signal_consumer import (
            TrustRequirement,
            TrustSignal,
            TrustSignalConsumer,
            TrustSignalType,
        )

        consumer = TrustSignalConsumer()
        consumer.register_signal(TrustSignal(signal_type=TrustSignalType.IDP_VERIFIED))
        req = TrustRequirement(required_signals=[TrustSignalType.IDP_VERIFIED])
        evaluation = consumer.evaluate(req)
        d = evaluation.to_dict()
        assert "passed" in d
        assert "eval_hash" in d

    def test_get_signals_by_type(self):
        from src.kortana.services.trust_signal_consumer import (
            TrustSignal,
            TrustSignalConsumer,
            TrustSignalType,
        )

        consumer = TrustSignalConsumer()
        consumer.register_signal(TrustSignal(signal_type=TrustSignalType.IDP_VERIFIED))
        consumer.register_signal(TrustSignal(signal_type=TrustSignalType.CI_ATTESTED))
        idp_only = consumer.get_signals(TrustSignalType.IDP_VERIFIED)
        assert len(idp_only) == 1

    def test_get_evaluations_by_version(self):
        from src.kortana.services.trust_signal_consumer import (
            TrustRequirement,
            TrustSignal,
            TrustSignalConsumer,
            TrustSignalType,
        )

        consumer = TrustSignalConsumer()
        consumer.register_signal(TrustSignal(signal_type=TrustSignalType.IDP_VERIFIED))
        req = TrustRequirement(required_signals=[TrustSignalType.IDP_VERIFIED])
        consumer.evaluate(req, version_id="v1")
        consumer.evaluate(req, version_id="v2")
        v1_evals = consumer.get_evaluations("v1")
        assert len(v1_evals) == 1

    def test_deploy_trust_gate_fails_missing(self):
        from src.kortana.services.trust_signal_consumer import (
            DeployTrustGate,
            TrustRequirement,
            TrustSignalConsumer,
            TrustSignalType,
        )

        consumer = TrustSignalConsumer()
        gate = DeployTrustGate(consumer)
        req = TrustRequirement(
            required_signals=[TrustSignalType.IDP_VERIFIED, TrustSignalType.CI_ATTESTED]
        )
        result, error = gate.promote_with_trust("v1", "s1", req)
        assert error is not None
        assert "Trust evaluation failed" in error

    def test_signal_version_filter(self):
        from src.kortana.services.trust_signal_consumer import (
            TrustRequirement,
            TrustSignal,
            TrustSignalConsumer,
            TrustSignalType,
        )

        consumer = TrustSignalConsumer()
        consumer.register_signal(
            TrustSignal(signal_type=TrustSignalType.IDP_VERIFIED, version_id="v2", confidence=0.9)
        )
        req = TrustRequirement(required_signals=[TrustSignalType.IDP_VERIFIED])
        # version_id=v1 should NOT match v2
        e = consumer.evaluate(req, version_id="v1")
        assert e.passed is False

    def test_trust_signal_type_values(self):
        from src.kortana.services.trust_signal_consumer import TrustSignalType

        assert TrustSignalType.IDP_VERIFIED.value == "idp_verified"
        assert TrustSignalType.SECRET_ROTATED.value == "secret_rotated"

    def test_requirement_to_dict(self):
        from src.kortana.services.trust_signal_consumer import TrustRequirement, TrustSignalType

        req = TrustRequirement(
            required_signals=[TrustSignalType.CI_ATTESTED],
            min_confidence=0.9,
        )
        d = req.to_dict()
        assert d["min_confidence"] == 0.9
        assert "ci_attested" in d["required_signals"]

    def test_module_singleton(self):
        from src.kortana.services.trust_signal_consumer import get_trust_signal_consumer

        c1 = get_trust_signal_consumer()
        c2 = get_trust_signal_consumer()
        assert c1 is c2
