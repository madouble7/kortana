"""Tests for Phase 13 — Auth-Bound Authority / Signed Resolver Identity.

Covers:
  - ResolverContext creation: from system actor, from user
  - Authority derived from User.is_superuser / is_active
  - Resolve with trusted ResolverContext: owner succeeds, operator fails for approve
  - System expiry with ResolverContext: audit captures actor_type=system
  - Audit trail captures trusted identity fields (resolver_user_id, resolver_actor_type)
  - Authenticated endpoint: auth-bound resolution, unauthenticated rejection
"""

import uuid
from datetime import datetime, timedelta

import pytest
from src.kortana.models import (
    CovenantEnforcementRecord,
    User,
)
from src.kortana.services.constitutional_service import (
    ConstitutionalService,
    ResolverContext,
    resolve_context_for_system,
    resolve_context_from_user,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_pending_record(
    db_session,
    target_type: str = "candidate",
    target_summary: str = "Test auth-bound target",
) -> CovenantEnforcementRecord:
    """Create and add a pending override enforcement record."""
    record = CovenantEnforcementRecord(
        decision_id="dec_p13_test",
        target_type=target_type,
        target_id="t_p13",
        target_summary=target_summary,
        action="override_requested",
        override_status="pending",
        cycle_id="cyc_p13",
    )
    db_session.add(record)
    return record


def _make_user(
    db_session,
    username: str = "matt",
    email: str = "matt@kortana.ai",
    is_superuser: bool = True,
    is_active: bool = True,
) -> User:
    """Create and add a user record."""
    user = User(
        id=str(uuid.uuid4()),
        username=username,
        email=email,
        hashed_password="hashed_not_real",
        is_superuser=is_superuser,
        is_active=is_active,
    )
    db_session.add(user)
    return user


class FakeTokenData:
    """Mimics auth.TokenData for resolve_context_from_user."""

    def __init__(
        self,
        user_id: str,
        email: str = "test@kortana.ai",
        username: str = "test",
    ) -> None:
        self.user_id = user_id
        self.email = email
        self.username = username


# ---------------------------------------------------------------
# 1. ResolverContext creation
# ---------------------------------------------------------------


class TestResolverContext:
    """Test ResolverContext construction from system and user sources."""

    def test_system_context_known_actor(self) -> None:
        ctx = resolve_context_for_system("system:expiry")
        assert ctx.actor_type == "system"
        assert ctx.actor_name == "system:expiry"
        assert ctx.user_id is None
        assert ctx.authority_tier == "system"

    def test_system_context_unknown_actor(self) -> None:
        ctx = resolve_context_for_system("system:unknown")
        assert ctx.actor_type == "system"
        assert ctx.authority_tier == ""  # no authority

    @pytest.mark.asyncio
    async def test_user_context_superuser(self, test_db_session) -> None:
        user = _make_user(test_db_session, username="matt", is_superuser=True)
        await test_db_session.commit()
        await test_db_session.refresh(user)

        token = FakeTokenData(user_id=user.id, email=user.email, username="matt")
        ctx = await resolve_context_from_user(token, test_db_session)
        assert ctx.actor_type == "human"
        assert ctx.actor_name == "matt"
        assert ctx.user_id == user.id
        assert ctx.authority_tier == "owner"

    @pytest.mark.asyncio
    async def test_user_context_regular_user(self, test_db_session) -> None:
        user = _make_user(
            test_db_session,
            username="jane",
            email="jane@kortana.ai",
            is_superuser=False,
        )
        await test_db_session.commit()
        await test_db_session.refresh(user)

        token = FakeTokenData(user_id=user.id, email=user.email, username="jane")
        ctx = await resolve_context_from_user(token, test_db_session)
        assert ctx.actor_type == "human"
        assert ctx.actor_name == "jane"
        assert ctx.user_id == user.id
        assert ctx.authority_tier == "operator"

    @pytest.mark.asyncio
    async def test_user_context_nonexistent_user(self, test_db_session) -> None:
        token = FakeTokenData(
            user_id="nonexistent-id", email="ghost@x.com", username="ghost"
        )
        ctx = await resolve_context_from_user(token, test_db_session)
        assert ctx.actor_type == "human"
        assert ctx.user_id is None
        assert ctx.authority_tier == ""  # no authority


# ---------------------------------------------------------------
# 2. Resolve with trusted ResolverContext
# ---------------------------------------------------------------


class TestResolveWithContext:
    """Test resolve_override using ResolverContext (Phase 13 path)."""

    @pytest.mark.asyncio
    async def test_owner_context_approve(self, test_db_session) -> None:
        record = _make_pending_record(test_db_session)
        await test_db_session.commit()
        await test_db_session.refresh(record)

        ctx = ResolverContext(
            actor_type="human",
            actor_name="matt",
            user_id="usr_matt",
            authority_tier="owner",
        )
        svc = ConstitutionalService(test_db_session)
        result = await svc.resolve_override(
            record.id,
            "approved",
            "matt",
            "Auth-bound approval.",
            resolver_context=ctx,
        )
        assert result is not None
        assert result.override_status == "approved"
        assert result.resolver_identity == "matt"
        assert result.resolver_user_id == "usr_matt"
        assert result.resolver_actor_type == "human"

    @pytest.mark.asyncio
    async def test_operator_context_cannot_approve(self, test_db_session) -> None:
        record = _make_pending_record(test_db_session)
        await test_db_session.commit()
        await test_db_session.refresh(record)

        ctx = ResolverContext(
            actor_type="human",
            actor_name="jane",
            user_id="usr_jane",
            authority_tier="operator",
        )
        svc = ConstitutionalService(test_db_session)
        result = await svc.resolve_override(
            record.id,
            "approved",
            "jane",
            "I want to approve.",
            resolver_context=ctx,
        )
        assert result is None  # insufficient authority

    @pytest.mark.asyncio
    async def test_empty_tier_context_rejected(self, test_db_session) -> None:
        """Context with empty authority tier (unknown user) is rejected."""
        record = _make_pending_record(test_db_session)
        await test_db_session.commit()
        await test_db_session.refresh(record)

        ctx = ResolverContext(
            actor_type="human",
            actor_name="ghost",
            user_id=None,
            authority_tier="",
        )
        svc = ConstitutionalService(test_db_session)
        result = await svc.resolve_override(
            record.id,
            "approved",
            "ghost",
            "No auth.",
            resolver_context=ctx,
        )
        assert result is None  # unauthorized (empty tier → None)

    @pytest.mark.asyncio
    async def test_system_context_expire(self, test_db_session) -> None:
        record = _make_pending_record(test_db_session)
        await test_db_session.commit()
        await test_db_session.refresh(record)

        ctx = resolve_context_for_system("system:expiry")
        svc = ConstitutionalService(test_db_session)
        result = await svc.resolve_override(
            record.id,
            "expired",
            "system:expiry",
            "Timed out.",
            resolver_context=ctx,
        )
        assert result is not None
        assert result.override_status == "expired"
        assert result.resolver_actor_type == "system"
        assert result.resolver_user_id is None


# ---------------------------------------------------------------
# 3. Audit trail captures trusted identity
# ---------------------------------------------------------------


class TestAuditTrustedIdentity:
    """Test that audit records capture resolver_user_id and resolver_actor_type."""

    @pytest.mark.asyncio
    async def test_authorized_audit_has_trusted_fields(self, test_db_session) -> None:
        record = _make_pending_record(test_db_session)
        await test_db_session.commit()
        await test_db_session.refresh(record)

        ctx = ResolverContext(
            actor_type="human",
            actor_name="matt",
            user_id="usr_matt_123",
            authority_tier="owner",
        )
        svc = ConstitutionalService(test_db_session)
        await svc.resolve_override(
            record.id,
            "approved",
            "matt",
            "Approved.",
            resolver_context=ctx,
        )

        audits = await svc.get_audit_history(limit=5)
        authorized = [a for a in audits if a.outcome == "authorized"]
        assert len(authorized) >= 1
        audit = authorized[0]
        assert audit.resolver_user_id == "usr_matt_123"
        assert audit.resolver_actor_type == "human"

    @pytest.mark.asyncio
    async def test_unauthorized_audit_has_actor_type(self, test_db_session) -> None:
        """Even failed attempts with context capture actor_type."""
        record = _make_pending_record(test_db_session)
        await test_db_session.commit()
        await test_db_session.refresh(record)

        ctx = ResolverContext(
            actor_type="human",
            actor_name="nobody",
            user_id=None,
            authority_tier="",
        )
        svc = ConstitutionalService(test_db_session)
        await svc.resolve_override(
            record.id,
            "approved",
            "nobody",
            "Try.",
            resolver_context=ctx,
        )

        audits = await svc.get_unauthorized_attempts(limit=5)
        assert len(audits) >= 1
        assert audits[0].resolver_actor_type == "human"
        assert audits[0].resolver_user_id is None

    @pytest.mark.asyncio
    async def test_system_expiry_audit_has_system_fields(self, test_db_session) -> None:
        record = _make_pending_record(test_db_session)
        record.created_at = datetime.utcnow() - timedelta(hours=48)
        await test_db_session.commit()
        await test_db_session.refresh(record)

        svc = ConstitutionalService(test_db_session)
        expired = await svc.expire_stale_overrides(max_age_hours=24)
        assert len(expired) == 1

        audits = await svc.get_audit_history(limit=5)
        sys_exp = [a for a in audits if a.outcome == "system_expiry"]
        assert len(sys_exp) >= 1
        assert sys_exp[0].resolver_actor_type == "system"
        assert sys_exp[0].resolver_user_id is None

    @pytest.mark.asyncio
    async def test_legacy_resolve_no_context(self, test_db_session) -> None:
        """Phase 12 compat: resolve without context still works."""
        record = _make_pending_record(test_db_session)
        await test_db_session.commit()
        await test_db_session.refresh(record)

        svc = ConstitutionalService(test_db_session)
        result = await svc.resolve_override(
            record.id,
            "approved",
            "matt",
            "Old-style.",
        )
        assert result is not None
        assert result.override_status == "approved"
        # No resolver_context → no trusted fields on enforcement record
        assert result.resolver_user_id is None
        assert result.resolver_actor_type is None


# ---------------------------------------------------------------
# 4. Authenticated endpoint
# ---------------------------------------------------------------


class TestAuthenticatedEndpoint:
    """Test the auth-protected override resolution endpoint."""

    def test_no_auth_returns_401(self, client) -> None:
        """Request without Bearer token is rejected."""
        resp = client.post(
            "/api/consciousness/covenant/overrides/fake_id/resolve/authenticated",
            params={"resolution": "approved", "rationale": "test"},
        )
        assert resp.status_code == 401

    def test_auth_endpoint_with_token(self, client) -> None:
        """Request with valid Bearer token reaches the endpoint logic."""
        from src.kortana.auth import create_access_token

        token = create_access_token(
            data={"sub": "test-user-id", "email": "test@kortana.ai", "role": "user"}
        )
        resp = client.post(
            "/api/consciousness/covenant/overrides/nonexistent_id/resolve/authenticated",
            params={"resolution": "approved", "rationale": "auth test"},
            headers={"Authorization": f"Bearer {token}"},
        )
        # Should reach the endpoint and return error (nonexistent record)
        # but NOT 401 — auth succeeded
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "error"
        assert "resolver" in data

    def test_enforcement_record_trusted_fields_via_endpoint(self, client) -> None:
        """Audit records from authenticated endpoint include trusted fields."""
        resp = client.get("/api/consciousness/covenant/authority/audit")
        assert resp.status_code == 200
        data = resp.json()
        # Structural check: audit records include new fields
        if data["count"] > 0:
            sample = data["audit"][0]
            assert "resolver_user_id" in sample
            assert "resolver_actor_type" in sample
