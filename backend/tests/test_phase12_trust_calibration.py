"""Tests for Phase 12 — Trust Calibration / Authority Boundaries.

Covers:
  - Authority policy: tier hierarchy, resolver lookup, policy config
  - Authority-checked resolution: owner can approve/deny/revoke, unknown rejected
  - Insufficient authority: system tier cannot approve
  - Audit trail: authorized, unauthorized, insufficient, invalid_state, not_found
  - Stale expiry audit: system_expiry audit records
  - Orchestrator step 3.97: expiry sweep integration
  - Endpoint shapes: policy, audit, unauthorized
"""

from datetime import datetime, timedelta

import pytest

from src.kortana.models import (
    CovenantEnforcementRecord,
)
from src.kortana.services.constitutional_service import (
    AUTHORITY_TIERS,
    RESOLUTION_REQUIRED_TIER,
    RESOLVER_AUTHORITY,
    ConstitutionalService,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_pending_record(
    db_session,
    target_type: str = "candidate",
    target_summary: str = "Test authority target",
) -> CovenantEnforcementRecord:
    """Create and add a pending override enforcement record."""
    record = CovenantEnforcementRecord(
        decision_id="dec_auth_test",
        target_type=target_type,
        target_id="t_auth",
        target_summary=target_summary,
        action="override_requested",
        override_status="pending",
        cycle_id="cyc_a",
    )
    db_session.add(record)
    return record


# ---------------------------------------------------------------
# 1. Authority Policy
# ---------------------------------------------------------------


class TestAuthorityPolicy:
    """Test the deterministic authority policy configuration."""

    def test_tier_hierarchy(self) -> None:
        """Owner > operator > system."""
        assert AUTHORITY_TIERS["owner"] > AUTHORITY_TIERS["operator"]
        assert AUTHORITY_TIERS["operator"] > AUTHORITY_TIERS["system"]

    def test_matt_is_owner(self) -> None:
        assert RESOLVER_AUTHORITY["matt"] == "owner"

    def test_system_expiry_is_system_tier(self) -> None:
        assert RESOLVER_AUTHORITY["system:expiry"] == "system"

    def test_approve_requires_owner(self) -> None:
        assert RESOLUTION_REQUIRED_TIER["approved"] == "owner"

    def test_expire_requires_system(self) -> None:
        assert RESOLUTION_REQUIRED_TIER["expired"] == "system"

    def test_get_authority_policy_returns_dict(self) -> None:
        policy = ConstitutionalService.get_authority_policy()
        assert "tiers" in policy
        assert "resolver_authority" in policy
        assert "resolution_required_tier" in policy

    def test_internal_tier_check(self) -> None:
        svc_cls = ConstitutionalService
        # Dummy instance not needed — use staticmethod-like approach
        # _has_sufficient_authority is an instance method but only uses args
        class FakeSvc:
            _has_sufficient_authority = svc_cls._has_sufficient_authority

        fake = FakeSvc()
        assert fake._has_sufficient_authority("owner", "owner") is True
        assert fake._has_sufficient_authority("owner", "system") is True
        assert fake._has_sufficient_authority("system", "owner") is False
        assert fake._has_sufficient_authority(None, "system") is False


# ---------------------------------------------------------------
# 2. Authority-checked override resolution
# ---------------------------------------------------------------


class TestResolveWithAuthority:
    """Test that resolve_override enforces authority checks."""

    @pytest.mark.asyncio
    async def test_owner_can_approve(self, test_db_session) -> None:
        record = _make_pending_record(test_db_session)
        await test_db_session.commit()
        await test_db_session.refresh(record)

        svc = ConstitutionalService(test_db_session)
        result = await svc.resolve_override(
            record.id, "approved", "matt", "Looks good."
        )
        assert result is not None
        assert result.override_status == "approved"
        assert result.resolver_identity == "matt"

    @pytest.mark.asyncio
    async def test_owner_can_deny(self, test_db_session) -> None:
        record = _make_pending_record(test_db_session)
        await test_db_session.commit()
        await test_db_session.refresh(record)

        svc = ConstitutionalService(test_db_session)
        result = await svc.resolve_override(
            record.id, "denied", "matt", "Too risky."
        )
        assert result is not None
        assert result.override_status == "denied"

    @pytest.mark.asyncio
    async def test_unknown_resolver_rejected(self, test_db_session) -> None:
        record = _make_pending_record(test_db_session)
        await test_db_session.commit()
        await test_db_session.refresh(record)

        svc = ConstitutionalService(test_db_session)
        result = await svc.resolve_override(
            record.id, "approved", "unknown_user", "I want in."
        )
        assert result is None  # unauthorized

    @pytest.mark.asyncio
    async def test_system_cannot_approve(self, test_db_session) -> None:
        """System tier cannot approve — insufficient authority."""
        record = _make_pending_record(test_db_session)
        await test_db_session.commit()
        await test_db_session.refresh(record)

        svc = ConstitutionalService(test_db_session)
        result = await svc.resolve_override(
            record.id, "approved", "system:expiry", "Auto-approve."
        )
        assert result is None  # insufficient authority

    @pytest.mark.asyncio
    async def test_system_can_expire(self, test_db_session) -> None:
        """System tier can expire — sufficient authority."""
        record = _make_pending_record(test_db_session)
        await test_db_session.commit()
        await test_db_session.refresh(record)

        svc = ConstitutionalService(test_db_session)
        result = await svc.resolve_override(
            record.id, "expired", "system:expiry", "Time's up."
        )
        assert result is not None
        assert result.override_status == "expired"

    @pytest.mark.asyncio
    async def test_owner_can_revoke_approved(self, test_db_session) -> None:
        record = _make_pending_record(test_db_session)
        await test_db_session.commit()
        await test_db_session.refresh(record)

        svc = ConstitutionalService(test_db_session)
        await svc.resolve_override(record.id, "approved", "matt", "OK.")
        result = await svc.resolve_override(
            record.id, "revoked", "matt", "Changed mind."
        )
        assert result is not None
        assert result.override_status == "revoked"


# ---------------------------------------------------------------
# 3. Audit trail
# ---------------------------------------------------------------


class TestAuditTrail:
    """Test that resolution attempts create proper audit records."""

    @pytest.mark.asyncio
    async def test_authorized_resolution_creates_audit(
        self, test_db_session
    ) -> None:
        record = _make_pending_record(test_db_session)
        await test_db_session.commit()
        await test_db_session.refresh(record)

        svc = ConstitutionalService(test_db_session)
        await svc.resolve_override(record.id, "approved", "matt", "Approved.")

        audits = await svc.get_audit_history(limit=5)
        authorized = [a for a in audits if a.outcome == "authorized"]
        assert len(authorized) >= 1
        assert authorized[0].resolver_identity == "matt"
        assert authorized[0].authority_tier == "owner"

    @pytest.mark.asyncio
    async def test_unauthorized_attempt_creates_audit(
        self, test_db_session
    ) -> None:
        record = _make_pending_record(test_db_session)
        await test_db_session.commit()
        await test_db_session.refresh(record)

        svc = ConstitutionalService(test_db_session)
        await svc.resolve_override(
            record.id, "approved", "hacker", "Let me in."
        )

        audits = await svc.get_unauthorized_attempts(limit=5)
        assert len(audits) >= 1
        assert audits[0].outcome == "unauthorized"
        assert audits[0].resolver_identity == "hacker"

    @pytest.mark.asyncio
    async def test_unauthorized_missing_record_uses_null_fk(
        self, test_db_session
    ) -> None:
        fake_id = "missing-unauthorized"
        svc = ConstitutionalService(test_db_session)

        await svc.resolve_override(fake_id, "approved", "hacker", "Let me in.")

        audits = await svc.get_unauthorized_attempts(limit=5)
        unauthorized = [a for a in audits if a.outcome == "unauthorized"]
        assert len(unauthorized) >= 1
        assert unauthorized[0].enforcement_record_id is None
        assert fake_id in (unauthorized[0].detail or "")

    @pytest.mark.asyncio
    async def test_insufficient_authority_creates_audit(
        self, test_db_session
    ) -> None:
        record = _make_pending_record(test_db_session)
        await test_db_session.commit()
        await test_db_session.refresh(record)

        svc = ConstitutionalService(test_db_session)
        await svc.resolve_override(
            record.id, "approved", "system:expiry", "Auto."
        )

        audits = await svc.get_unauthorized_attempts(limit=5)
        insufficient = [
            a for a in audits if a.outcome == "insufficient_authority"
        ]
        assert len(insufficient) >= 1
        assert insufficient[0].resolver_identity == "system:expiry"
        assert insufficient[0].authority_tier == "system"
        assert insufficient[0].required_tier == "owner"

    @pytest.mark.asyncio
    async def test_insufficient_missing_record_uses_null_fk(
        self, test_db_session
    ) -> None:
        fake_id = "missing-insufficient"
        svc = ConstitutionalService(test_db_session)

        await svc.resolve_override(fake_id, "approved", "system:expiry", "Auto.")

        audits = await svc.get_unauthorized_attempts(limit=5)
        insufficient = [
            a for a in audits if a.outcome == "insufficient_authority"
        ]
        assert len(insufficient) >= 1
        assert insufficient[0].enforcement_record_id is None
        assert fake_id in (insufficient[0].detail or "")

    @pytest.mark.asyncio
    async def test_invalid_state_creates_audit(
        self, test_db_session
    ) -> None:
        """Trying to approve an already-denied record creates invalid_state audit."""
        record = _make_pending_record(test_db_session)
        await test_db_session.commit()
        await test_db_session.refresh(record)

        svc = ConstitutionalService(test_db_session)
        await svc.resolve_override(record.id, "denied", "matt", "No.")
        await svc.resolve_override(record.id, "approved", "matt", "Wait.")

        audits = await svc.get_audit_history(limit=10)
        invalid = [a for a in audits if a.outcome == "invalid_state"]
        assert len(invalid) >= 1

    @pytest.mark.asyncio
    async def test_not_found_creates_audit(self, test_db_session) -> None:
        svc = ConstitutionalService(test_db_session)
        await svc.resolve_override("nonexistent", "approved", "matt", "OK.")

        audits = await svc.get_audit_history(limit=5)
        not_found = [a for a in audits if a.outcome == "not_found"]
        assert len(not_found) >= 1


# ---------------------------------------------------------------
# 4. Stale expiry with audit
# ---------------------------------------------------------------


class TestStaleExpiryAudit:
    """Test that auto-expiry creates system_expiry audit records."""

    @pytest.mark.asyncio
    async def test_expire_stale_creates_audit(self, test_db_session) -> None:
        record = _make_pending_record(test_db_session)
        record.created_at = datetime.utcnow() - timedelta(hours=48)
        await test_db_session.commit()
        await test_db_session.refresh(record)

        svc = ConstitutionalService(test_db_session)
        expired = await svc.expire_stale_overrides(max_age_hours=24)
        assert len(expired) == 1

        audits = await svc.get_audit_history(limit=5)
        system_expiry = [a for a in audits if a.outcome == "system_expiry"]
        assert len(system_expiry) >= 1
        assert system_expiry[0].resolver_identity == "system:expiry"
        assert system_expiry[0].authority_tier == "system"


# ---------------------------------------------------------------
# 5. Endpoint shapes
# ---------------------------------------------------------------


class TestAuthorityEndpoints:
    """Test Phase 12 API endpoint shapes."""

    def test_authority_policy_endpoint(self, client) -> None:
        resp = client.get("/api/consciousness/covenant/authority/policy")
        assert resp.status_code == 200
        data = resp.json()
        assert "tiers" in data
        assert "resolver_authority" in data
        assert "resolution_required_tier" in data
        assert data["resolver_authority"]["matt"] == "owner"

    def test_authority_audit_endpoint(self, client) -> None:
        resp = client.get("/api/consciousness/covenant/authority/audit")
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data
        assert "audit" in data

    def test_unauthorized_endpoint(self, client) -> None:
        resp = client.get("/api/consciousness/covenant/authority/unauthorized")
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data
        assert "unauthorized" in data

    def test_resolve_with_unknown_resolver_via_endpoint(
        self, authenticated_client
    ) -> None:
        """Resolve endpoint with auth now derives resolver from token,
        not from query params.  The 'unknown_intruder' resolver param is
        ignored — authority comes from the authenticated user context."""
        resp = authenticated_client.post(
            "/api/consciousness/covenant/overrides/fake_id/resolve",
            params={
                "resolution": "approved",
                "rationale": "Hack attempt",
            },
        )
        # With authentication, the endpoint processes the request (record not found)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "error"
