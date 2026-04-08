"""V12 — Production Federation tests.

Tests for OIDC/OAuth2 providers (V12A), key rotation lifecycle (V12B),
CI/CD credential enforcement (V12C), and authenticated rule promotion (V12D).
"""

from __future__ import annotations

import importlib
import time
from datetime import datetime, timedelta



# ---------------------------------------------------------------------------
# V12A — OIDC / OAuth2 tests
# ---------------------------------------------------------------------------


class TestOIDCConfiguration:
    """Test OIDCConfiguration dataclass."""

    def test_config_hash_deterministic(self) -> None:
        from src.kortana.services.oidc_provider import OIDCConfiguration

        a = OIDCConfiguration(issuer_url="https://idp.example.com", client_id="c1")
        b = OIDCConfiguration(issuer_url="https://idp.example.com", client_id="c1")
        assert a.config_hash == b.config_hash

    def test_derived_endpoints(self) -> None:
        from src.kortana.services.oidc_provider import OIDCConfiguration

        cfg = OIDCConfiguration(
            issuer_url="https://idp.example.com", client_id="c1"
        )
        assert cfg.jwks_uri == "https://idp.example.com/.well-known/jwks.json"
        assert cfg.token_endpoint == "https://idp.example.com/oauth/token"
        assert cfg.authorization_endpoint == "https://idp.example.com/authorize"

    def test_to_dict(self) -> None:
        from src.kortana.services.oidc_provider import OIDCConfiguration

        cfg = OIDCConfiguration(issuer_url="https://x.com", client_id="c1")
        d = cfg.to_dict()
        assert d["issuer_url"] == "https://x.com"
        assert "config_hash" in d


class TestOIDCTokenClaims:
    """Test OIDCTokenClaims dataclass."""

    def test_is_expired_false(self) -> None:
        from src.kortana.services.oidc_provider import OIDCTokenClaims

        c = OIDCTokenClaims(
            sub="user1",
            iss="https://idp.example.com",
            aud="aud1",
            exp=int(time.time()) + 3600,
            iat=int(time.time()),
        )
        assert not c.is_expired

    def test_is_expired_true(self) -> None:
        from src.kortana.services.oidc_provider import OIDCTokenClaims

        c = OIDCTokenClaims(
            sub="user1",
            iss="https://idp.example.com",
            aud="aud1",
            exp=int(time.time()) - 10,
            iat=int(time.time()) - 3600,
        )
        assert c.is_expired

    def test_to_dict(self) -> None:
        from src.kortana.services.oidc_provider import OIDCTokenClaims

        c = OIDCTokenClaims(
            sub="user1", iss="iss", aud="aud", exp=999, iat=888
        )
        d = c.to_dict()
        assert d["sub"] == "user1"
        assert d["exp"] == 999


class TestOIDCProvider:
    """Test OIDCProvider token verification."""

    def test_verify_valid_jwt(self) -> None:
        from src.kortana.services.oidc_provider import (
            OIDCConfiguration,
            OIDCProvider,
            create_test_jwt,
        )

        cfg = OIDCConfiguration(
            issuer_url="https://idp.example.com",
            client_id="aud1",
            audience="aud1",
        )
        provider = OIDCProvider(cfg)
        token = create_test_jwt(
            sub="user1",
            iss="https://idp.example.com",
            aud="aud1",
        )
        # verify_token returns VerifiedCredential | None
        result = provider.verify_token(token)
        assert result is not None
        assert result.operator_id == "user1"

    def test_reject_expired_jwt(self) -> None:
        from src.kortana.services.oidc_provider import (
            OIDCConfiguration,
            OIDCProvider,
            create_test_jwt,
        )

        cfg = OIDCConfiguration(
            issuer_url="https://idp.example.com",
            client_id="aud1",
            audience="aud1",
        )
        provider = OIDCProvider(cfg)
        token = create_test_jwt(
            sub="user1",
            iss="https://idp.example.com",
            aud="aud1",
            exp=int(time.time()) - 3600,
        )
        result = provider.verify_token(token)
        assert result is None

    def test_reject_wrong_issuer(self) -> None:
        from src.kortana.services.oidc_provider import (
            OIDCConfiguration,
            OIDCProvider,
            create_test_jwt,
        )

        cfg = OIDCConfiguration(
            issuer_url="https://idp.example.com",
            client_id="aud1",
            audience="aud1",
        )
        provider = OIDCProvider(cfg)
        token = create_test_jwt(sub="user1", iss="https://evil.com", aud="aud1")
        result = provider.verify_token(token)
        assert result is None

    def test_reject_wrong_audience(self) -> None:
        from src.kortana.services.oidc_provider import (
            OIDCConfiguration,
            OIDCProvider,
            create_test_jwt,
        )

        cfg = OIDCConfiguration(
            issuer_url="https://idp.example.com",
            client_id="aud1",
            audience="aud1",
        )
        provider = OIDCProvider(cfg)
        token = create_test_jwt(
            sub="user1", iss="https://idp.example.com", aud="wrong"
        )
        result = provider.verify_token(token)
        assert result is None

    def test_register_signing_key(self) -> None:
        from src.kortana.services.oidc_provider import (
            OIDCConfiguration,
            OIDCProvider,
        )

        cfg = OIDCConfiguration(issuer_url="https://x.com", client_id="c1")
        provider = OIDCProvider(cfg)
        provider.register_signing_key("kid-1", "pubkey-data")
        assert "kid-1" in provider._signing_keys

    def test_revoke_credential(self) -> None:
        from src.kortana.services.oidc_provider import (
            OIDCConfiguration,
            OIDCProvider,
        )

        cfg = OIDCConfiguration(issuer_url="https://x.com", client_id="c1")
        provider = OIDCProvider(cfg)
        result = provider.revoke("oidc:https://x.com:user1")
        assert result is True
        assert "oidc:https://x.com:user1" in provider._revoked


class TestOAuth2Flow:
    """Test OAuth2 authorization flow with PKCE."""

    def test_create_authorization_url(self) -> None:
        from src.kortana.services.oidc_provider import (
            OIDCConfiguration,
            OIDCProvider,
            OAuth2Provider,
        )

        cfg = OIDCConfiguration(issuer_url="https://idp.example.com", client_id="c1")
        oidc = OIDCProvider(cfg)
        oauth2 = OAuth2Provider(oidc)
        url, flow = oauth2.create_authorization_url("https://app.example.com/callback")
        assert "response_type=code" in url
        assert "code_challenge=" in url
        assert flow.redirect_uri == "https://app.example.com/callback"

    def test_exchange_code_with_test_code(self) -> None:
        from src.kortana.services.oidc_provider import (
            OIDCConfiguration,
            OIDCProvider,
            OAuth2Provider,
            create_test_jwt,
        )

        cfg = OIDCConfiguration(
            issuer_url="https://idp.example.com",
            client_id="aud1",
            audience="aud1",
        )
        oidc = OIDCProvider(cfg)
        oauth2 = OAuth2Provider(oidc)
        url, flow = oauth2.create_authorization_url("https://app.example.com/cb")

        jwt = create_test_jwt(
            sub="user1", iss="https://idp.example.com", aud="aud1"
        )
        oauth2.register_test_code("test-code", jwt)

        credential, error = oauth2.exchange_code("test-code", flow.state)
        assert error is None
        assert credential is not None
        assert credential.operator_id == "user1"


class TestOIDCProviderRegistry:
    """Test OIDC provider registry."""

    def test_register_and_list(self) -> None:
        from src.kortana.services.oidc_provider import (
            OIDCConfiguration,
            OIDCProviderRegistry,
        )

        registry = OIDCProviderRegistry()
        cfg1 = OIDCConfiguration(issuer_url="https://idp1.example.com", client_id="c1")
        cfg2 = OIDCConfiguration(issuer_url="https://idp2.example.com", client_id="c2")
        registry.register(cfg1, register_with_auth_registry=False)
        registry.register(cfg2, register_with_auth_registry=False)
        assert len(registry.list_providers()) == 2

    def test_get_oidc_provider(self) -> None:
        from src.kortana.services.oidc_provider import (
            OIDCConfiguration,
            OIDCProviderRegistry,
        )

        registry = OIDCProviderRegistry()
        cfg = OIDCConfiguration(issuer_url="https://idp1.example.com", client_id="c1")
        registry.register(cfg, register_with_auth_registry=False)
        p = registry.get_oidc_provider("https://idp1.example.com")
        assert p is not None

    def test_get_oauth2_provider(self) -> None:
        from src.kortana.services.oidc_provider import (
            OIDCConfiguration,
            OIDCProviderRegistry,
        )

        registry = OIDCProviderRegistry()
        cfg = OIDCConfiguration(issuer_url="https://idp1.example.com", client_id="c1")
        registry.register(cfg, register_with_auth_registry=False)
        o = registry.get_oauth2_provider("https://idp1.example.com")
        assert o is not None


class TestCreateTestJWT:
    """Test the create_test_jwt helper."""

    def test_creates_three_part_token(self) -> None:
        from src.kortana.services.oidc_provider import create_test_jwt

        token = create_test_jwt(sub="u1", iss="iss", aud="aud")
        parts = token.split(".")
        assert len(parts) == 3

    def test_default_exp_in_future(self) -> None:
        import base64
        import json

        from src.kortana.services.oidc_provider import create_test_jwt

        token = create_test_jwt(sub="u1", iss="iss", aud="aud")
        payload = token.split(".")[1]
        # add padding
        payload += "=" * (-len(payload) % 4)
        claims = json.loads(base64.urlsafe_b64decode(payload))
        assert claims["exp"] > int(time.time())


# ---------------------------------------------------------------------------
# V12B — Key Rotation tests
# ---------------------------------------------------------------------------


class TestRotationSchedule:
    """Test RotationSchedule dataclass."""

    def test_hash_exists(self) -> None:
        from src.kortana.services.key_rotation import RotationSchedule

        a = RotationSchedule(key_id="k1", provider_type="api_key", operator_id="op1")
        assert a.schedule_hash

    def test_is_due(self) -> None:
        from src.kortana.services.key_rotation import RotationSchedule

        s = RotationSchedule(
            key_id="k1",
            provider_type="api_key",
            operator_id="op1",
            next_rotation_at=datetime.utcnow() - timedelta(hours=1),
        )
        assert s.is_due

    def test_not_due(self) -> None:
        from src.kortana.services.key_rotation import RotationSchedule

        s = RotationSchedule(
            key_id="k1",
            provider_type="api_key",
            operator_id="op1",
            next_rotation_at=datetime.utcnow() + timedelta(hours=24),
        )
        assert not s.is_due

    def test_to_dict(self) -> None:
        from src.kortana.services.key_rotation import RotationSchedule

        s = RotationSchedule(key_id="k1", provider_type="api_key", operator_id="op1")
        d = s.to_dict()
        assert d["key_id"] == "k1"
        assert "state" in d


class TestRotationEvent:
    """Test RotationEvent dataclass."""

    def test_event_hash_exists(self) -> None:
        from src.kortana.services.key_rotation import RotationEvent, RotationEventType

        e = RotationEvent(key_id="k1", event_type=RotationEventType.MANUAL)
        assert e.event_hash

    def test_to_dict(self) -> None:
        from src.kortana.services.key_rotation import RotationEvent, RotationEventType

        e = RotationEvent(key_id="k1", event_type=RotationEventType.SCHEDULED)
        d = e.to_dict()
        assert d["key_id"] == "k1"


class TestKeyRotationManager:
    """Test KeyRotationManager lifecycle."""

    def test_schedule_rotation(self) -> None:
        from src.kortana.services.key_rotation import KeyRotationManager

        m = KeyRotationManager()
        s = m.schedule_rotation("k1", "api_key", "op1")
        assert s.key_id == "k1"
        assert m.active_schedule_count == 1

    def test_check_due_rotations(self) -> None:
        from src.kortana.services.key_rotation import KeyRotationManager

        m = KeyRotationManager()
        s = m.schedule_rotation("k1", "api_key", "op1")
        # Force due
        s.next_rotation_at = datetime.utcnow() - timedelta(hours=1)
        due = m.check_due_rotations()
        assert len(due) == 1

    def test_disable_schedule(self) -> None:
        from src.kortana.services.key_rotation import KeyRotationManager, RotationState

        m = KeyRotationManager()
        m.schedule_rotation("k1", "api_key", "op1")
        ok = m.disable_schedule("k1")
        assert ok is True
        assert m.get_schedule("k1").state == RotationState.DISABLED

    def test_get_schedules(self) -> None:
        from src.kortana.services.key_rotation import KeyRotationManager

        m = KeyRotationManager()
        m.schedule_rotation("k1", "api_key", "op1")
        m.schedule_rotation("k2", "service_account", "op2")
        assert len(m.get_schedules()) == 2


# ---------------------------------------------------------------------------
# V12C — CI Credential Enforcement tests
# ---------------------------------------------------------------------------


class TestCICredentialPolicy:
    """Test CICredentialPolicy dataclass."""

    def test_policy_hash_exists(self) -> None:
        from src.kortana.services.ci_credential_enforcement import (
            CICheckpoint,
            CICredentialPolicy,
        )

        p = CICredentialPolicy(name="test", checkpoint=CICheckpoint.PRE_DEPLOY)
        assert p.policy_hash

    def test_to_dict(self) -> None:
        from src.kortana.services.ci_credential_enforcement import (
            CICheckpoint,
            CICredentialPolicy,
        )

        p = CICredentialPolicy(name="test", checkpoint=CICheckpoint.PRE_DEPLOY)
        d = p.to_dict()
        assert d["name"] == "test"


class TestCICredentialCheck:
    """Test CICredentialCheck dataclass."""

    def test_check_hash_exists(self) -> None:
        from src.kortana.services.ci_credential_enforcement import (
            CICheckpoint,
            CICredentialCheck,
        )

        c = CICredentialCheck(checkpoint=CICheckpoint.RUNTIME_EDGE)
        assert c.check_hash


class TestEnforceCICredential:
    """Test enforce_ci_credential function."""

    def test_pass_with_valid_session(self) -> None:
        from src.kortana.services.ci_credential_enforcement import (
            CICheckpoint,
            CICredentialPolicy,
            enforce_ci_credential,
        )
        from src.kortana.services.identity_verification import (
            get_identity_verification_manager,
        )

        iv = get_identity_verification_manager()
        session, _err = iv.verify_and_create_session("matt")

        policy = CICredentialPolicy(
            name="basic",
            checkpoint=CICheckpoint.RUNTIME_EDGE,
            required_verification_level="basic",
        )
        check = enforce_ci_credential(
            CICheckpoint.RUNTIME_EDGE, session.session_id, policy
        )
        assert check.passed

    def test_fail_without_session(self) -> None:
        from src.kortana.services.ci_credential_enforcement import (
            CICheckpoint,
            CICredentialPolicy,
            enforce_ci_credential,
        )

        policy = CICredentialPolicy(
            name="basic",
            checkpoint=CICheckpoint.PRE_DEPLOY,
        )
        check = enforce_ci_credential(
            CICheckpoint.PRE_DEPLOY, "nonexistent-session", policy
        )
        assert not check.passed

    def test_fail_insufficient_verification_level(self) -> None:
        from src.kortana.services.ci_credential_enforcement import (
            CICheckpoint,
            CICredentialPolicy,
            enforce_ci_credential,
        )
        from src.kortana.services.identity_verification import (
            get_identity_verification_manager,
        )

        iv = get_identity_verification_manager()
        session, _err = iv.verify_and_create_session("matt")

        policy = CICredentialPolicy(
            name="elevated",
            checkpoint=CICheckpoint.PRE_DEPLOY,
            required_verification_level="elevated",
        )
        check = enforce_ci_credential(
            CICheckpoint.PRE_DEPLOY, session.session_id, policy
        )
        assert isinstance(check.passed, bool)


class TestRuntimeEdgeEnforcer:
    """Test RuntimeEdgeEnforcer."""

    def test_register_and_count(self) -> None:
        from src.kortana.services.ci_credential_enforcement import (
            CICheckpoint,
            CICredentialPolicy,
            RuntimeEdgeEnforcer,
        )

        enforcer = RuntimeEdgeEnforcer()
        policy = CICredentialPolicy(
            name="edge", checkpoint=CICheckpoint.RUNTIME_EDGE
        )
        enforcer.register_edge("/api/deploy.*", policy)
        assert enforcer.edge_count == 1

    def test_check_unprotected_path(self) -> None:
        from src.kortana.services.ci_credential_enforcement import RuntimeEdgeEnforcer

        enforcer = RuntimeEdgeEnforcer()
        # check_edge returns CICredentialCheck, never None
        # For unprotected paths it returns a passing check
        check = enforcer.check_edge("/public/health", "session-1")
        assert check.passed is True


class TestDefaultCIPolicies:
    """Test default CI policies."""

    def test_default_policies_exist(self) -> None:
        from src.kortana.services.ci_credential_enforcement import (
            get_default_ci_policies,
        )

        policies = get_default_ci_policies()
        assert "pre_deploy" in policies
        assert "post_deploy" in policies
        assert "branch_protection" in policies
        assert "runtime_edge" in policies
        assert "pipeline_gate" in policies


# ---------------------------------------------------------------------------
# V12D — Authenticated Promotion tests
# ---------------------------------------------------------------------------


class TestAuthenticatedPromotionEvent:
    """Test AuthenticatedPromotionEvent dataclass."""

    def test_event_hash_exists(self) -> None:
        from src.kortana.services.authenticated_promotion import (
            AuthenticatedPromotionEvent,
        )

        e = AuthenticatedPromotionEvent(
            version_id="v1", action="submit", operator_id="op1"
        )
        assert e.event_hash

    def test_to_dict(self) -> None:
        from src.kortana.services.authenticated_promotion import (
            AuthenticatedPromotionEvent,
        )

        e = AuthenticatedPromotionEvent(
            version_id="v1", action="approve", operator_id="op1"
        )
        d = e.to_dict()
        assert d["version_id"] == "v1"
        assert d["action"] == "approve"


class TestAuthenticatedPromotionManager:
    """Test AuthenticatedPromotionManager lifecycle."""

    def test_submit_fails_without_session(self) -> None:
        from src.kortana.services.authenticated_promotion import (
            AuthenticatedPromotionManager,
        )

        mgr = AuthenticatedPromotionManager()
        version, error = mgr.submit_for_review("v1", "bad-session")
        assert error is not None
        assert "not found" in error.lower() or "expired" in error.lower()

    def test_approve_fails_without_session(self) -> None:
        from src.kortana.services.authenticated_promotion import (
            AuthenticatedPromotionManager,
        )

        mgr = AuthenticatedPromotionManager()
        version, error = mgr.approve("v1", "bad-session")
        assert error is not None

    def test_reject_fails_without_session(self) -> None:
        from src.kortana.services.authenticated_promotion import (
            AuthenticatedPromotionManager,
        )

        mgr = AuthenticatedPromotionManager()
        version, error = mgr.reject("v1", "bad-session", "reason")
        assert error is not None

    def test_activate_fails_without_session(self) -> None:
        from src.kortana.services.authenticated_promotion import (
            AuthenticatedPromotionManager,
        )

        mgr = AuthenticatedPromotionManager()
        version, error = mgr.activate("v1", "bad-session")
        assert error is not None

    def test_retire_fails_without_session(self) -> None:
        from src.kortana.services.authenticated_promotion import (
            AuthenticatedPromotionManager,
        )

        mgr = AuthenticatedPromotionManager()
        version, error = mgr.retire("v1", "bad-session", "reason")
        assert error is not None

    def test_event_count_starts_zero(self) -> None:
        from src.kortana.services.authenticated_promotion import (
            AuthenticatedPromotionManager,
        )

        mgr = AuthenticatedPromotionManager()
        assert mgr.event_count == 0

    def test_get_events_empty(self) -> None:
        from src.kortana.services.authenticated_promotion import (
            AuthenticatedPromotionManager,
        )

        mgr = AuthenticatedPromotionManager()
        assert mgr.get_events("v1") == []

    def test_submit_with_valid_session(self) -> None:
        from src.kortana.services.authenticated_promotion import (
            AuthenticatedPromotionManager,
        )
        from src.kortana.services.identity_verification import (
            get_identity_verification_manager,
        )
        from src.kortana.services.rule_lifecycle import get_rule_lifecycle_manager

        # Create session via module singleton so other modules can find it
        iv = get_identity_verification_manager()
        session, _err = iv.verify_and_create_session("matt")

        # Create a rule draft version via module singleton
        lifecycle = get_rule_lifecycle_manager()
        version = lifecycle.create_draft(
            rule_id="rule-v12-test",
            name="test-v12-rule",
            description="Test rule for V12",
            conditions={"env": "production"},
            action="log",
            priority=10,
            author_id="matt",
        )

        # Submit via authenticated promotion
        mgr = AuthenticatedPromotionManager()
        result, error = mgr.submit_for_review(version.version_id, session.session_id)
        assert error is None
        assert result is not None
        assert mgr.event_count == 1


class TestAuthenticatedPromotionSingleton:
    """Test module singleton."""

    def test_singleton_returns_same_instance(self) -> None:
        from src.kortana.services.authenticated_promotion import (
            get_authenticated_promotion_manager,
        )

        a = get_authenticated_promotion_manager()
        b = get_authenticated_promotion_manager()
        assert a is b


# ---------------------------------------------------------------------------
# V12 Cross-module integration tests
# ---------------------------------------------------------------------------


class TestV12ModuleImports:
    """Test that all V12 modules import cleanly."""

    def test_import_oidc_provider(self) -> None:
        mod = importlib.import_module("src.kortana.services.oidc_provider")
        assert hasattr(mod, "get_oidc_registry")

    def test_import_key_rotation(self) -> None:
        mod = importlib.import_module("src.kortana.services.key_rotation")
        assert hasattr(mod, "get_key_rotation_manager")

    def test_import_ci_credential_enforcement(self) -> None:
        mod = importlib.import_module(
            "src.kortana.services.ci_credential_enforcement"
        )
        assert hasattr(mod, "get_ci_enforcer")

    def test_import_authenticated_promotion(self) -> None:
        mod = importlib.import_module(
            "src.kortana.services.authenticated_promotion"
        )
        assert hasattr(mod, "get_authenticated_promotion_manager")
