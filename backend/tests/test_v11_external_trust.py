"""V11 — External trust anchoring tests.

Tests for auth providers, identity verification, credential gate,
and rule lifecycle management.
"""

from datetime import datetime, timedelta



# ---------------------------------------------------------------------------
# V11A — Auth provider tests
# ---------------------------------------------------------------------------


class TestProviderType:
    """ProviderType enum tests."""

    def test_provider_types_defined(self):
        from src.kortana.services.auth_provider import ProviderType
        assert ProviderType.LOCAL == "local"
        assert ProviderType.API_KEY == "api_key"
        assert ProviderType.OAUTH2 == "oauth2"
        assert ProviderType.SERVICE_ACCOUNT == "service_account"
        assert ProviderType.OIDC == "oidc"


class TestVerifiedCredential:
    """VerifiedCredential tests."""

    def test_hash_generated(self):
        from src.kortana.services.auth_provider import ProviderType, VerifiedCredential
        vc = VerifiedCredential(
            operator_id="op1",
            provider_type=ProviderType.LOCAL,
            credential_id="cred-1",
            display_name="Op One",
            role_hint="admin",
        )
        assert len(vc.verification_hash) == 64

    def test_not_expired_by_default(self):
        from src.kortana.services.auth_provider import ProviderType, VerifiedCredential
        vc = VerifiedCredential(
            operator_id="op1",
            provider_type=ProviderType.LOCAL,
            credential_id="cred-1",
            display_name="Op One",
            role_hint="admin",
        )
        assert vc.is_expired is False

    def test_expired_when_past(self):
        from src.kortana.services.auth_provider import ProviderType, VerifiedCredential
        vc = VerifiedCredential(
            operator_id="op1",
            provider_type=ProviderType.LOCAL,
            credential_id="cred-1",
            display_name="Op One",
            role_hint="admin",
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        assert vc.is_expired is True

    def test_to_dict_keys(self):
        from src.kortana.services.auth_provider import ProviderType, VerifiedCredential
        vc = VerifiedCredential(
            operator_id="op1",
            provider_type=ProviderType.LOCAL,
            credential_id="cred-1",
            display_name="Op One",
            role_hint="admin",
        )
        d = vc.to_dict()
        assert "operator_id" in d
        assert "verification_hash" in d
        assert "is_expired" in d


class TestLocalAuthProvider:
    """LocalAuthProvider tests."""

    def test_verify_known_operator(self):
        from src.kortana.services.auth_provider import LocalAuthProvider
        provider = LocalAuthProvider()
        result = provider.verify_token("matt")
        assert result is not None
        assert result.operator_id == "matt"
        assert result.provider_type.value == "local"

    def test_verify_unknown_operator(self):
        from src.kortana.services.auth_provider import LocalAuthProvider
        provider = LocalAuthProvider()
        result = provider.verify_token("unknown-person")
        assert result is None


class TestAPIKeyProvider:
    """APIKeyProvider tests."""

    def test_issue_and_verify(self):
        from src.kortana.services.auth_provider import APIKeyProvider
        provider = APIKeyProvider()
        bearer, credential = provider.issue_key("api-op", "API Op")
        assert bearer
        assert credential.operator_id == "api-op"

        verified = provider.verify_token(bearer)
        assert verified is not None
        assert verified.operator_id == "api-op"

    def test_revoke_key(self):
        from src.kortana.services.auth_provider import APIKeyProvider
        provider = APIKeyProvider()
        bearer, credential = provider.issue_key("rev-op", "Rev Op")
        assert provider.revoke(credential.credential_id) is True
        assert provider.verify_token(bearer) is None

    def test_invalid_token_format(self):
        from src.kortana.services.auth_provider import APIKeyProvider
        provider = APIKeyProvider()
        assert provider.verify_token("no-colon-here") is None

    def test_wrong_token(self):
        from src.kortana.services.auth_provider import APIKeyProvider
        provider = APIKeyProvider()
        bearer, _ = provider.issue_key("wt-op", "WT Op")
        key_id = bearer.split(":")[0]
        assert provider.verify_token(f"{key_id}:wrongtoken") is None

    def test_active_key_count(self):
        from src.kortana.services.auth_provider import APIKeyProvider
        provider = APIKeyProvider()
        provider.issue_key("c1", "C1")
        provider.issue_key("c2", "C2")
        assert provider.active_key_count == 2


class TestServiceAccountProvider:
    """ServiceAccountProvider tests."""

    def test_register_and_verify(self):
        from src.kortana.services.auth_provider import ServiceAccountProvider
        provider = ServiceAccountProvider()
        secret, credential = provider.register("svc-1", "Service One")
        assert secret
        assert credential.operator_id == "svc-1"

        verified = provider.verify_token(f"svc-1:{secret}")
        assert verified is not None
        assert verified.operator_id == "svc-1"

    def test_wrong_secret(self):
        from src.kortana.services.auth_provider import ServiceAccountProvider
        provider = ServiceAccountProvider()
        provider.register("svc-2", "Service Two")
        assert provider.verify_token("svc-2:wrongsecret") is None

    def test_revoke_service_account(self):
        from src.kortana.services.auth_provider import ServiceAccountProvider
        provider = ServiceAccountProvider()
        secret, credential = provider.register("svc-3", "Service Three")
        assert provider.revoke(credential.credential_id) is True
        assert provider.verify_token(f"svc-3:{secret}") is None


class TestAuthProviderRegistry:
    """AuthProviderRegistry tests."""

    def test_default_registry_has_providers(self):
        from src.kortana.services.auth_provider import get_auth_provider_registry
        registry = get_auth_provider_registry()
        assert registry.count >= 3
        assert "local" in registry.provider_types

    def test_verify_dispatches_to_local(self):
        from src.kortana.services.auth_provider import get_auth_provider_registry
        registry = get_auth_provider_registry()
        result = registry.verify("matt")
        assert result is not None
        assert result.operator_id == "matt"

    def test_verify_unknown_returns_none(self):
        from src.kortana.services.auth_provider import AuthProviderRegistry
        registry = AuthProviderRegistry()
        assert registry.verify("anything") is None


# ---------------------------------------------------------------------------
# V11B — Identity verification tests
# ---------------------------------------------------------------------------


class TestVerificationLevel:
    """VerificationLevel enum tests."""

    def test_levels_defined(self):
        from src.kortana.services.identity_verification import VerificationLevel
        assert VerificationLevel.NONE == "none"
        assert VerificationLevel.BASIC == "basic"
        assert VerificationLevel.ELEVATED == "elevated"
        assert VerificationLevel.FULL == "full"


class TestIdentitySession:
    """IdentitySession tests."""

    def test_session_defaults(self):
        from src.kortana.services.identity_verification import (
            IdentitySession,
            VerificationLevel,
        )
        session = IdentitySession(
            session_id="s1",
            operator_id="op1",
            display_name="Op",
            role="admin",
            provider_type="local",
            credential_id="c1",
        )
        assert session.is_active is True
        assert session.verification_level == VerificationLevel.BASIC
        assert len(session.session_hash) == 64

    def test_session_elevate(self):
        from src.kortana.services.identity_verification import (
            IdentitySession,
            VerificationLevel,
        )
        session = IdentitySession(
            session_id="s2",
            operator_id="op1",
            display_name="Op",
            role="admin",
            provider_type="local",
            credential_id="c1",
        )
        session.elevate(VerificationLevel.FULL)
        assert session.verification_level == VerificationLevel.FULL

    def test_session_revoke(self):
        from src.kortana.services.identity_verification import IdentitySession
        session = IdentitySession(
            session_id="s3",
            operator_id="op1",
            display_name="Op",
            role="admin",
            provider_type="local",
            credential_id="c1",
        )
        session.revoke()
        assert session.is_active is False

    def test_to_dict(self):
        from src.kortana.services.identity_verification import IdentitySession
        session = IdentitySession(
            session_id="s4",
            operator_id="op1",
            display_name="Op",
            role="admin",
            provider_type="local",
            credential_id="c1",
        )
        d = session.to_dict()
        assert "session_id" in d
        assert "verification_level" in d
        assert "session_hash" in d


class TestIdentityBinding:
    """IdentityBinding tests."""

    def test_binding_hash(self):
        from src.kortana.services.identity_verification import IdentityBinding
        binding = IdentityBinding(
            binding_id="b1",
            operator_id="op1",
            provider_type="github",
            external_id="github:12345",
            display_name="Op GitHub",
        )
        assert len(binding.binding_hash) == 64
        assert binding.active is True

    def test_to_dict(self):
        from src.kortana.services.identity_verification import IdentityBinding
        binding = IdentityBinding(
            binding_id="b2",
            operator_id="op1",
            provider_type="github",
            external_id="github:12345",
            display_name="Op",
        )
        d = binding.to_dict()
        assert "binding_id" in d
        assert "binding_hash" in d


class TestIdentityVerificationManager:
    """IdentityVerificationManager tests."""

    def test_verify_and_create_session(self):
        from src.kortana.services.identity_verification import (
            IdentityVerificationManager,
        )
        manager = IdentityVerificationManager()
        session, error = manager.verify_and_create_session("matt")
        assert session is not None
        assert error is None
        assert session.operator_id == "matt"

    def test_verify_invalid_token(self):
        from src.kortana.services.identity_verification import (
            IdentityVerificationManager,
        )
        manager = IdentityVerificationManager()
        session, error = manager.verify_and_create_session("nonexistent")
        assert session is None
        assert error is not None

    def test_get_session(self):
        from src.kortana.services.identity_verification import (
            IdentityVerificationManager,
        )
        manager = IdentityVerificationManager()
        session, _ = manager.verify_and_create_session("matt")
        retrieved = manager.get_session(session.session_id)
        assert retrieved is not None
        assert retrieved.operator_id == "matt"

    def test_revoke_session(self):
        from src.kortana.services.identity_verification import (
            IdentityVerificationManager,
        )
        manager = IdentityVerificationManager()
        session, _ = manager.verify_and_create_session("matt")
        assert manager.revoke_session(session.session_id) is True
        assert manager.get_session(session.session_id) is None

    def test_elevate_session(self):
        from src.kortana.services.identity_verification import (
            IdentityVerificationManager,
            VerificationLevel,
        )
        manager = IdentityVerificationManager()
        session, _ = manager.verify_and_create_session("matt")
        assert manager.elevate_session(session.session_id, VerificationLevel.ELEVATED)
        s = manager.get_session(session.session_id)
        assert s.verification_level == VerificationLevel.ELEVATED

    def test_bind_and_get_bindings(self):
        from src.kortana.services.identity_verification import (
            IdentityVerificationManager,
        )
        manager = IdentityVerificationManager()
        manager.bind_identity("matt", "github", "gh:matt", "Matt GH")
        bindings = manager.get_bindings("matt")
        assert len(bindings) == 1
        assert bindings[0].external_id == "gh:matt"

    def test_revoke_binding(self):
        from src.kortana.services.identity_verification import (
            IdentityVerificationManager,
        )
        manager = IdentityVerificationManager()
        binding = manager.bind_identity("op1", "github", "gh:op1", "Op1")
        assert manager.revoke_binding(binding.binding_id) is True  # noqa: F841
        bindings = manager.get_bindings("op1")
        assert bindings[0].active is False

    def test_active_sessions_count(self):
        from src.kortana.services.identity_verification import (
            IdentityVerificationManager,
        )
        manager = IdentityVerificationManager()
        manager.verify_and_create_session("matt")
        assert manager.active_session_count == 1
        assert manager.session_count == 1


# ---------------------------------------------------------------------------
# V11C — Credential gate tests
# ---------------------------------------------------------------------------


class TestCredentialRequirement:
    """CredentialRequirement tests."""

    def test_default_requirement(self):
        from src.kortana.services.credential_gate import DEFAULT_DEPLOY_REQUIREMENT
        d = DEFAULT_DEPLOY_REQUIREMENT.to_dict()
        assert d["min_verification_level"] == "basic"
        assert d["require_binding"] is False

    def test_production_requirement(self):
        from src.kortana.services.credential_gate import PRODUCTION_REQUIREMENT
        d = PRODUCTION_REQUIREMENT.to_dict()
        assert d["min_verification_level"] == "full"
        assert d["require_binding"] is True
        assert "deploy" in d["required_scopes"]

    def test_get_requirements(self):
        from src.kortana.services.credential_gate import get_credential_requirements
        reqs = get_credential_requirements()
        assert "default" in reqs
        assert "elevated" in reqs
        assert "production" in reqs


class TestCredentialGateBasic:
    """Basic credential gate tests."""

    def test_gate_passes_with_valid_session(self):
        from src.kortana.services.credential_gate import evaluate_credential_gate
        from src.kortana.services.identity_verification import (
            IdentityVerificationManager,
        )

        manager = IdentityVerificationManager()
        session, _ = manager.verify_and_create_session("matt")
        assert session is not None

        # Patch the module singleton temporarily
        import src.kortana.services.identity_verification as iv_mod
        old = iv_mod._manager
        iv_mod._manager = manager

        try:
            result = evaluate_credential_gate(
                session_id=session.session_id,
                current_mode="manual",
            )
            assert result.allowed is True
            assert result.operator_id == "matt"
            assert len(result.gate_hash) == 64
        finally:
            iv_mod._manager = old

    def test_gate_fails_invalid_session(self):
        from src.kortana.services.credential_gate import evaluate_credential_gate
        result = evaluate_credential_gate(
            session_id="nonexistent-session",
            current_mode="manual",
        )
        assert result.allowed is False
        assert any(c.name == "session_valid" for c in result.checks)

    def test_gate_result_to_dict(self):
        from src.kortana.services.credential_gate import evaluate_credential_gate
        result = evaluate_credential_gate(
            session_id="missing",
            current_mode="manual",
        )
        d = result.to_dict()
        assert "allowed" in d
        assert "gate_hash" in d
        assert "checks" in d


class TestCredentialGateChecks:
    """Credential gate individual check tests."""

    def test_verification_level_blocks_when_low(self):
        from src.kortana.services.credential_gate import (
            CredentialRequirement,
            evaluate_credential_gate,
        )
        from src.kortana.services.identity_verification import (
            IdentityVerificationManager,
        )

        manager = IdentityVerificationManager()
        session, _ = manager.verify_and_create_session("matt")

        import src.kortana.services.identity_verification as iv_mod
        old = iv_mod._manager
        iv_mod._manager = manager

        try:
            req = CredentialRequirement(
                name="high",
                min_verification_level="full",
            )
            result = evaluate_credential_gate(
                session_id=session.session_id,
                requirement=req,
                current_mode="manual",
            )
            level_check = next(c for c in result.checks if c.name == "verification_level")
            assert level_check.passed is False
        finally:
            iv_mod._manager = old

    def test_binding_required_fails_without_binding(self):
        from src.kortana.services.credential_gate import (
            CredentialRequirement,
            evaluate_credential_gate,
        )
        from src.kortana.services.identity_verification import (
            IdentityVerificationManager,
        )

        manager = IdentityVerificationManager()
        session, _ = manager.verify_and_create_session("matt")

        import src.kortana.services.identity_verification as iv_mod
        old = iv_mod._manager
        iv_mod._manager = manager

        try:
            req = CredentialRequirement(
                name="binding_req",
                min_verification_level="basic",
                require_binding=True,
            )
            result = evaluate_credential_gate(
                session_id=session.session_id,
                requirement=req,
                current_mode="manual",
            )
            binding_check = next(c for c in result.checks if c.name == "binding_check")
            assert binding_check.passed is False
        finally:
            iv_mod._manager = old


# ---------------------------------------------------------------------------
# V11D — Rule lifecycle tests
# ---------------------------------------------------------------------------


class TestRuleStage:
    """RuleStage enum tests."""

    def test_stages_defined(self):
        from src.kortana.services.rule_lifecycle import RuleStage
        assert RuleStage.DRAFT == "draft"
        assert RuleStage.REVIEW == "review"
        assert RuleStage.ACTIVE == "active"
        assert RuleStage.RETIRED == "retired"
        assert RuleStage.REJECTED == "rejected"


class TestRuleVersion:
    """RuleVersion tests."""

    def test_version_hash(self):
        from src.kortana.services.rule_lifecycle import RuleStage, RuleVersion
        v = RuleVersion(
            version_id="rv1",
            rule_id="r1",
            stage=RuleStage.DRAFT,
            name="Test Rule",
            description="A test",
            conditions={},
            action="allow",
            priority=100,
            author_id="matt",
        )
        assert len(v.version_hash) == 64

    def test_rule_snapshot(self):
        from src.kortana.services.rule_lifecycle import RuleStage, RuleVersion
        v = RuleVersion(
            version_id="rv2",
            rule_id="r1",
            stage=RuleStage.DRAFT,
            name="Test",
            description="desc",
            conditions={"x": 1},
            action="deny",
            priority=10,
            author_id="matt",
        )
        snap = v.rule_snapshot
        assert snap["rule_id"] == "r1"
        assert snap["action"] == "deny"
        assert snap["conditions"] == {"x": 1}

    def test_to_dict(self):
        from src.kortana.services.rule_lifecycle import RuleStage, RuleVersion
        v = RuleVersion(
            version_id="rv3",
            rule_id="r1",
            stage=RuleStage.DRAFT,
            name="T",
            description="d",
            conditions={},
            action="hold",
            priority=50,
            author_id="matt",
        )
        d = v.to_dict()
        assert "version_id" in d
        assert "version_hash" in d
        assert "stage" in d


class TestRuleLifecycleManager:
    """RuleLifecycleManager tests."""

    def test_create_draft(self):
        from src.kortana.services.rule_lifecycle import RuleLifecycleManager
        manager = RuleLifecycleManager()
        v = manager.create_draft("r1", "Rule 1", "desc", {}, "allow", 100, "matt")
        assert v.stage.value == "draft"
        assert v.author_id == "matt"
        assert manager.version_count == 1

    def test_submit_for_review(self):
        from src.kortana.services.rule_lifecycle import RuleLifecycleManager
        manager = RuleLifecycleManager()
        v = manager.create_draft("r1", "Rule 1", "desc", {}, "allow", 100, "matt")
        result, err = manager.submit_for_review(v.version_id, "matt")
        assert result is not None
        assert err is None
        assert result.stage.value == "review"

    def test_submit_wrong_author_fails(self):
        from src.kortana.services.rule_lifecycle import RuleLifecycleManager
        manager = RuleLifecycleManager()
        v = manager.create_draft("r1", "Rule 1", "desc", {}, "allow", 100, "matt")
        result, err = manager.submit_for_review(v.version_id, "someone-else")
        assert result is None
        assert "author" in err.lower()

    def test_full_lifecycle(self):
        from src.kortana.services.rule_lifecycle import RuleLifecycleManager
        manager = RuleLifecycleManager()
        v = manager.create_draft("r1", "Rule 1", "desc", {}, "allow", 100, "matt")
        manager.submit_for_review(v.version_id, "matt")
        approved, _ = manager.approve(v.version_id, "reviewer-1")
        assert approved is not None
        assert approved.stage.value == "active"
        assert approved.reviewer_id == "reviewer-1"

        retired, _ = manager.retire(v.version_id, "matt")
        assert retired is not None
        assert retired.stage.value == "retired"

    def test_approve_same_author_fails(self):
        from src.kortana.services.rule_lifecycle import RuleLifecycleManager
        manager = RuleLifecycleManager()
        v = manager.create_draft("r1", "Rule 1", "desc", {}, "allow", 100, "matt")
        manager.submit_for_review(v.version_id, "matt")
        result, err = manager.approve(v.version_id, "matt")
        assert result is None
        assert "same as the author" in err.lower()

    def test_reject(self):
        from src.kortana.services.rule_lifecycle import RuleLifecycleManager
        manager = RuleLifecycleManager()
        v = manager.create_draft("r2", "Rule 2", "desc", {}, "deny", 10, "matt")
        manager.submit_for_review(v.version_id, "matt")
        rejected, _ = manager.reject(v.version_id, "reviewer-1", "Bad rule")
        assert rejected is not None
        assert rejected.stage.value == "rejected"

    def test_active_rules(self):
        from src.kortana.services.rule_lifecycle import RuleLifecycleManager
        manager = RuleLifecycleManager()
        v = manager.create_draft("r1", "R1", "d", {}, "allow", 100, "matt")
        manager.submit_for_review(v.version_id, "matt")
        manager.approve(v.version_id, "reviewer-1")
        assert len(manager.active_rules) == 1

    def test_draft_rules(self):
        from src.kortana.services.rule_lifecycle import RuleLifecycleManager
        manager = RuleLifecycleManager()
        manager.create_draft("r1", "R1", "d", {}, "allow", 100, "matt")
        assert len(manager.draft_rules) == 1


class TestRulePromotion:
    """RulePromotion tracking tests."""

    def test_promotions_tracked(self):
        from src.kortana.services.rule_lifecycle import RuleLifecycleManager
        manager = RuleLifecycleManager()
        v = manager.create_draft("r1", "R1", "d", {}, "allow", 100, "matt")
        manager.submit_for_review(v.version_id, "matt")
        manager.approve(v.version_id, "reviewer-1")

        promos = manager.get_promotions("r1")
        assert len(promos) == 2  # draft→review, review→active

    def test_promotion_hash(self):
        from src.kortana.services.rule_lifecycle import RuleLifecycleManager
        manager = RuleLifecycleManager()
        v = manager.create_draft("r1", "R1", "d", {}, "allow", 100, "matt")
        manager.submit_for_review(v.version_id, "matt")
        promos = manager.get_promotions("r1")
        assert len(promos[0].promotion_hash) == 64

    def test_promotion_to_dict(self):
        from src.kortana.services.rule_lifecycle import RuleLifecycleManager
        manager = RuleLifecycleManager()
        v = manager.create_draft("r1", "R1", "d", {}, "allow", 100, "matt")
        manager.submit_for_review(v.version_id, "matt")
        promos = manager.get_promotions("r1")
        d = promos[0].to_dict()
        assert "from_stage" in d
        assert "to_stage" in d
        assert "promotion_hash" in d


class TestRuleDiff:
    """Rule version diff tests."""

    def test_diff_identical(self):
        from src.kortana.services.rule_lifecycle import RuleLifecycleManager
        manager = RuleLifecycleManager()
        v1 = manager.create_draft("r1", "R1", "d", {}, "allow", 100, "matt")
        v2 = manager.create_draft("r1", "R1", "d", {}, "allow", 100, "matt")
        diff = manager.diff_versions(v1.version_id, v2.version_id)
        assert diff is not None
        assert diff["identical"] is True

    def test_diff_changed(self):
        from src.kortana.services.rule_lifecycle import RuleLifecycleManager
        manager = RuleLifecycleManager()
        v1 = manager.create_draft("r1", "R1", "d", {}, "allow", 100, "matt")
        v2 = manager.create_draft("r1", "R1 Updated", "d", {"x": 1}, "deny", 10, "matt")
        diff = manager.diff_versions(v1.version_id, v2.version_id)
        assert diff is not None
        assert diff["identical"] is False
        assert "name" in diff["changes"]
        assert "action" in diff["changes"]

    def test_diff_missing_version(self):
        from src.kortana.services.rule_lifecycle import RuleLifecycleManager
        manager = RuleLifecycleManager()
        assert manager.diff_versions("x", "y") is None
