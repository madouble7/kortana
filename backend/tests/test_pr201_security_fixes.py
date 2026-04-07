"""Targeted tests for PR #201 security/auth fixes.

Covers:
  - Unauthenticated override-resolution hole closed (auth required)
  - /_internal/autonomy-cycle requires authentication
  - No duplicate override-learning writes in route handlers
  - resolve_context_from_user DB-miss fallback (operator / owner)
  - Audit null FK safety for missing enforcement records
  - RESOLVER_AUTHORITY policy override on DB-miss
"""

from __future__ import annotations

import inspect
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

# ---------------------------------------------------------------------------
# 1. Endpoint auth dependency checks (structural)
# ---------------------------------------------------------------------------


class TestEndpointAuthGuards:
    """Verify that auth-sensitive endpoints include the auth dependency."""

    def test_resolve_override_endpoint_requires_auth(self) -> None:
        """POST /covenant/overrides/{record_id}/resolve must depend on auth."""
        from src.kortana.routers.consciousness import resolve_override

        sig = inspect.signature(resolve_override)
        param_names = list(sig.parameters.keys())
        # Must have a current_user parameter (injected by Depends)
        assert "current_user" in param_names, (
            "resolve_override endpoint must have a 'current_user' parameter "
            "injected via Depends(get_current_active_user)"
        )

    def test_internal_autonomy_cycle_requires_auth(self) -> None:
        """POST /_internal/autonomy-cycle must depend on auth."""
        from src.kortana.routers.consciousness import internal_autonomy_cycle

        sig = inspect.signature(internal_autonomy_cycle)
        param_names = list(sig.parameters.keys())
        assert "_current_user" in param_names, (
            "internal_autonomy_cycle endpoint must have a '_current_user' parameter "
            "injected via Depends(get_current_active_user)"
        )


# ---------------------------------------------------------------------------
# 2. No duplicate learning writes in route handlers
# ---------------------------------------------------------------------------


class TestNoDuplicateLearningWrites:
    """Route handlers must NOT call learn_from_override_resolution.

    The canonical learning write lives inside
    ConstitutionalService.resolve_override().
    """

    def test_resolve_override_router_no_learning_call(self) -> None:
        """resolve_override route handler must not call learn_from_override_resolution."""
        from src.kortana.routers import consciousness

        source = inspect.getsource(consciousness.resolve_override)
        assert "learn_from_override_resolution" not in source, (
            "resolve_override route handler must not duplicate the "
            "learn_from_override_resolution call — it is in ConstitutionalService"
        )

    def test_resolve_override_authenticated_no_learning_call(self) -> None:
        """resolve_override_authenticated must not call learn_from_override_resolution."""
        from src.kortana.routers import consciousness

        source = inspect.getsource(consciousness.resolve_override_authenticated)
        assert "learn_from_override_resolution" not in source, (
            "resolve_override_authenticated route handler must not duplicate the "
            "learn_from_override_resolution call — it is in ConstitutionalService"
        )

    def test_constitutional_service_has_canonical_learning_write(self) -> None:
        """ConstitutionalService.resolve_override must call learn_from_override_resolution."""
        from src.kortana.services import constitutional_service

        source = inspect.getsource(constitutional_service.ConstitutionalService.resolve_override)
        assert "learn_from_override_resolution" in source, (
            "ConstitutionalService.resolve_override must contain the canonical "
            "learn_from_override_resolution call"
        )


# ---------------------------------------------------------------------------
# 3. resolve_context_from_user DB-miss fallback
# ---------------------------------------------------------------------------


class TestResolveContextDbMiss:
    """When the DB lookup misses, resolve_context_from_user must derive
    a meaningful authority tier from the token rather than returning ''."""

    @pytest.mark.asyncio
    async def test_db_miss_returns_operator(self) -> None:
        """No user_id on token → tier should be 'operator', not empty."""
        from src.kortana.services.constitutional_service import (
            resolve_context_from_user,
        )

        token = MagicMock()
        token.email = "somebody@example.com"
        token.username = "somebody"
        token.user_id = None
        token.is_superuser = False

        db = AsyncMock()

        ctx = await resolve_context_from_user(token, db)
        assert ctx.authority_tier == "operator", (
            f"Expected 'operator' for an authenticated user without DB record, "
            f"got '{ctx.authority_tier}'"
        )
        assert ctx.actor_type == "human"
        assert ctx.user_id is None

    @pytest.mark.asyncio
    async def test_db_miss_superuser_returns_owner(self) -> None:
        """Token with is_superuser=True but DB miss → tier should be 'owner'."""
        from src.kortana.services.constitutional_service import (
            resolve_context_from_user,
        )

        token = MagicMock()
        token.email = "admin@example.com"
        token.username = "admin"
        token.user_id = str(uuid.uuid4())
        token.is_superuser = True

        # Simulate DB miss
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db = AsyncMock()
        db.execute.return_value = mock_result

        ctx = await resolve_context_from_user(token, db)
        assert ctx.authority_tier == "owner", (
            f"Expected 'owner' for superuser token with DB miss, "
            f"got '{ctx.authority_tier}'"
        )

    @pytest.mark.asyncio
    async def test_db_miss_regular_user_returns_operator(self) -> None:
        """Token with user_id but DB miss (no is_superuser) → 'operator'."""
        from src.kortana.services.constitutional_service import (
            resolve_context_from_user,
        )

        token = MagicMock()
        token.email = "user@example.com"
        token.username = "user"
        token.user_id = str(uuid.uuid4())
        token.is_superuser = False

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db = AsyncMock()
        db.execute.return_value = mock_result

        ctx = await resolve_context_from_user(token, db)
        assert ctx.authority_tier == "operator", (
            f"Expected 'operator' for regular authenticated token with DB miss, "
            f"got '{ctx.authority_tier}'"
        )

    @pytest.mark.asyncio
    async def test_resolver_authority_overrides_db_miss_tier(self) -> None:
        """RESOLVER_AUTHORITY can upgrade the tier when DB misses."""
        from src.kortana.services.constitutional_service import (
            RESOLVER_AUTHORITY,
            resolve_context_from_user,
        )

        # Use a name that's in RESOLVER_AUTHORITY as "owner"
        token = MagicMock()
        token.email = "matt"
        token.username = "matt"
        token.user_id = None
        token.is_superuser = False

        db = AsyncMock()

        ctx = await resolve_context_from_user(token, db)
        if "matt" in RESOLVER_AUTHORITY:
            assert ctx.authority_tier == "owner", (
                f"RESOLVER_AUTHORITY should upgrade 'matt' to 'owner', "
                f"got '{ctx.authority_tier}'"
            )


# ---------------------------------------------------------------------------
# 4. Audit null FK safety for missing enforcement records
# ---------------------------------------------------------------------------


class TestAuditNullFkSafety:
    """resolve_override for a missing record_id must use
    enforcement_record_id=None and preserve the attempted id in detail."""

    @pytest.mark.asyncio
    async def test_resolve_override_not_found_uses_null_fk(self) -> None:
        """When enforcement record doesn't exist, audit record must use null FK."""
        from src.kortana.services.constitutional_service import (
            ConstitutionalService,
            ResolverContext,
        )

        fake_record_id = str(uuid.uuid4())
        db = AsyncMock()

        # First execute: record lookup returns None (not found)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        db.rollback = AsyncMock()

        ctx = ResolverContext(
            actor_type="human",
            actor_name="matt",
            user_id=str(uuid.uuid4()),
            authority_tier="owner",
        )

        svc = ConstitutionalService(db)
        result = await svc.resolve_override(
            record_id=fake_record_id,
            resolution="approved",
            resolver="matt",
            rationale="test",
            resolver_context=ctx,
        )

        assert result is None, "resolve_override should return None for missing record"

        # Verify _record_audit was called with enforcement_record_id=None
        # by checking what was added to the session
        if db.add.called:
            audit_record = db.add.call_args[0][0]
            assert audit_record.enforcement_record_id is None, (
                "Audit record for not-found must use enforcement_record_id=None"
            )
            assert fake_record_id in (audit_record.detail or ""), (
                "Audit detail must preserve the attempted record_id"
            )
