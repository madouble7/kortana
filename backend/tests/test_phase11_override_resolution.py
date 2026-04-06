"""Tests for Phase 11 — Override Resolution / Human Covenant Interface.

Covers:
  - resolve_override: approve, deny, expire, revoke state transitions
  - State machine guards: only pending→approved/denied/expired, approved→revoked
  - Resolver identity and human rationale persistence
  - expire_stale_overrides: auto-expiry of old pending records
  - get_pending_overrides / get_resolved_overrides queries
  - Outcome learning feedback: approved/denied/expired/revoked signals
  - OutcomeLearningRecord.source_type for override-sourced records
  - Endpoint shapes: pending, resolved, resolve POST
"""

from datetime import datetime, timedelta

import pytest
from src.kortana.models import (
    CovenantEnforcementRecord,
)
from src.kortana.services.constitutional_service import (
    ConstitutionalService,
)
from src.kortana.services.outcome_learning_service import (
    OutcomeLearningService,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_pending_record(
    db_session,
    target_type: str = "candidate",
    target_summary: str = "Test override target",
) -> CovenantEnforcementRecord:
    """Create and add a pending override enforcement record."""
    record = CovenantEnforcementRecord(
        decision_id="dec_test",
        target_type=target_type,
        target_id="t_test",
        target_summary=target_summary,
        action="override_requested",
        override_status="pending",
        cycle_id="cyc_t",
    )
    db_session.add(record)
    return record


# ---------------------------------------------------------------
# 1. resolve_override — approve / deny / expire / revoke
# ---------------------------------------------------------------


class TestResolveOverride:
    """Test the resolve_override state machine on ConstitutionalService."""

    @pytest.mark.asyncio
    async def test_approve_pending_record(self, test_db_session) -> None:
        record = _make_pending_record(test_db_session)
        await test_db_session.commit()
        await test_db_session.refresh(record)

        svc = ConstitutionalService(test_db_session)
        result = await svc.resolve_override(
            record_id=record.id,
            resolution="approved",
            resolver="matt",
            rationale="This action is safe to proceed.",
        )
        assert result is not None
        assert result.override_status == "approved"
        assert result.resolution_outcome == "approved"
        assert result.resolver_identity == "matt"
        assert result.human_rationale == "This action is safe to proceed."
        assert result.override_resolved_at is not None

    @pytest.mark.asyncio
    async def test_deny_pending_record(self, test_db_session) -> None:
        record = _make_pending_record(test_db_session)
        await test_db_session.commit()
        await test_db_session.refresh(record)

        svc = ConstitutionalService(test_db_session)
        result = await svc.resolve_override(
            record_id=record.id,
            resolution="denied",
            resolver="matt",
            rationale="Too risky.",
        )
        assert result is not None
        assert result.override_status == "denied"
        assert result.resolution_outcome == "denied"
        assert result.resolver_identity == "matt"

    @pytest.mark.asyncio
    async def test_expire_pending_record(self, test_db_session) -> None:
        record = _make_pending_record(test_db_session)
        await test_db_session.commit()
        await test_db_session.refresh(record)

        svc = ConstitutionalService(test_db_session)
        result = await svc.resolve_override(
            record_id=record.id,
            resolution="expired",
            resolver="system:expiry",
            rationale="No action taken within time window.",
        )
        assert result is not None
        assert result.override_status == "expired"
        assert result.resolution_outcome == "expired"

    @pytest.mark.asyncio
    async def test_revoke_approved_record(self, test_db_session) -> None:
        """Revoke only works on approved records."""
        record = _make_pending_record(test_db_session)
        await test_db_session.commit()
        await test_db_session.refresh(record)

        svc = ConstitutionalService(test_db_session)
        # First approve
        await svc.resolve_override(
            record.id, "approved", "matt", "Go ahead."
        )
        # Then revoke
        result = await svc.resolve_override(
            record.id, "revoked", "matt", "Changed my mind."
        )
        assert result is not None
        assert result.override_status == "revoked"
        assert result.resolution_outcome == "revoked"
        assert result.human_rationale == "Changed my mind."

    @pytest.mark.asyncio
    async def test_cannot_approve_already_denied(self, test_db_session) -> None:
        record = _make_pending_record(test_db_session)
        await test_db_session.commit()
        await test_db_session.refresh(record)

        svc = ConstitutionalService(test_db_session)
        await svc.resolve_override(record.id, "denied", "matt", "No.")
        # Try to approve after denial — should fail
        result = await svc.resolve_override(
            record.id, "approved", "matt", "Wait, yes."
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_cannot_revoke_pending(self, test_db_session) -> None:
        """Revoke only works on approved, not pending."""
        record = _make_pending_record(test_db_session)
        await test_db_session.commit()
        await test_db_session.refresh(record)

        svc = ConstitutionalService(test_db_session)
        result = await svc.resolve_override(
            record.id, "revoked", "matt", "Nope."
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_invalid_resolution_returns_none(self, test_db_session) -> None:
        svc = ConstitutionalService(test_db_session)
        result = await svc.resolve_override(
            "nonexistent", "invalid_status", "matt", ""
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_nonexistent_record_returns_none(self, test_db_session) -> None:
        svc = ConstitutionalService(test_db_session)
        result = await svc.resolve_override(
            "does_not_exist", "approved", "matt", "Sure."
        )
        assert result is None


# ---------------------------------------------------------------
# 2. expire_stale_overrides — auto-expiry
# ---------------------------------------------------------------


class TestExpireStaleOverrides:
    """Test automatic expiry of old pending overrides."""

    @pytest.mark.asyncio
    async def test_expires_old_records(self, test_db_session) -> None:
        """Records older than max_age_hours get expired."""
        record = _make_pending_record(test_db_session)
        # Backdate created_at to 48 hours ago
        record.created_at = datetime.utcnow() - timedelta(hours=48)
        await test_db_session.commit()
        await test_db_session.refresh(record)

        svc = ConstitutionalService(test_db_session)
        expired = await svc.expire_stale_overrides(max_age_hours=24)
        assert len(expired) == 1
        assert expired[0].override_status == "expired"
        assert expired[0].resolver_identity == "system:expiry"
        assert expired[0].resolution_outcome == "expired"

    @pytest.mark.asyncio
    async def test_does_not_expire_fresh_records(self, test_db_session) -> None:
        """Records within max_age_hours are not expired."""
        _make_pending_record(test_db_session)
        await test_db_session.commit()

        svc = ConstitutionalService(test_db_session)
        expired = await svc.expire_stale_overrides(max_age_hours=24)
        assert len(expired) == 0


# ---------------------------------------------------------------
# 3. Query methods — pending / resolved
# ---------------------------------------------------------------


class TestOverrideQueries:
    """Test get_pending_overrides / get_resolved_overrides queries."""

    @pytest.mark.asyncio
    async def test_get_pending_overrides(self, test_db_session) -> None:
        _make_pending_record(test_db_session, target_summary="First")
        _make_pending_record(test_db_session, target_summary="Second")
        await test_db_session.commit()

        svc = ConstitutionalService(test_db_session)
        pending = await svc.get_pending_overrides(limit=10)
        assert len(pending) >= 2
        # FIFO order — oldest first
        summaries = [r.target_summary for r in pending]
        assert summaries.index("First") < summaries.index("Second")

    @pytest.mark.asyncio
    async def test_get_resolved_overrides(self, test_db_session) -> None:
        record = _make_pending_record(test_db_session)
        await test_db_session.commit()
        await test_db_session.refresh(record)

        svc = ConstitutionalService(test_db_session)
        await svc.resolve_override(record.id, "denied", "matt", "No.")
        resolved = await svc.get_resolved_overrides(limit=10)
        assert len(resolved) >= 1
        assert resolved[0].resolution_outcome == "denied"


# ---------------------------------------------------------------
# 4. Outcome learning feedback
# ---------------------------------------------------------------


class TestOverrideLearningFeedback:
    """Test that override resolutions produce correct adaptation signals."""

    @pytest.mark.asyncio
    async def test_approved_produces_positive_signal(
        self, test_db_session
    ) -> None:
        record = _make_pending_record(
            test_db_session, target_type="candidate"
        )
        await test_db_session.commit()
        await test_db_session.refresh(record)

        # Resolve as approved
        svc = ConstitutionalService(test_db_session)
        resolved = await svc.resolve_override(
            record.id, "approved", "matt", "Safe to proceed."
        )

        learner = OutcomeLearningService(test_db_session)
        lr = await learner.learn_from_override_resolution(resolved)
        assert lr is not None
        assert lr.adaptation_signal == "override_approved:candidate"
        assert lr.signal_weight == 0.15
        assert lr.source_type == "override_resolution"
        assert lr.outcome_verdict == "succeeded"
        assert lr.execution_record_id is None

    @pytest.mark.asyncio
    async def test_denied_produces_negative_signal(
        self, test_db_session
    ) -> None:
        record = _make_pending_record(
            test_db_session, target_type="execution"
        )
        await test_db_session.commit()
        await test_db_session.refresh(record)

        svc = ConstitutionalService(test_db_session)
        resolved = await svc.resolve_override(
            record.id, "denied", "matt", "Too risky."
        )

        learner = OutcomeLearningService(test_db_session)
        lr = await learner.learn_from_override_resolution(resolved)
        assert lr is not None
        assert lr.adaptation_signal == "override_denied:execution"
        assert lr.signal_weight == -0.15
        assert lr.source_type == "override_resolution"
        assert lr.outcome_verdict == "failed"

    @pytest.mark.asyncio
    async def test_expired_produces_weak_negative(
        self, test_db_session
    ) -> None:
        record = _make_pending_record(test_db_session)
        await test_db_session.commit()
        await test_db_session.refresh(record)

        svc = ConstitutionalService(test_db_session)
        resolved = await svc.resolve_override(
            record.id, "expired", "system:expiry", "Timed out."
        )

        learner = OutcomeLearningService(test_db_session)
        lr = await learner.learn_from_override_resolution(resolved)
        assert lr is not None
        assert lr.adaptation_signal == "override_expired:candidate"
        assert lr.signal_weight == -0.05

    @pytest.mark.asyncio
    async def test_revoked_produces_negative_signal(
        self, test_db_session
    ) -> None:
        record = _make_pending_record(
            test_db_session, target_type="goal"
        )
        await test_db_session.commit()
        await test_db_session.refresh(record)

        svc = ConstitutionalService(test_db_session)
        await svc.resolve_override(record.id, "approved", "matt", "OK.")
        resolved = await svc.resolve_override(
            record.id, "revoked", "matt", "Actually no."
        )

        learner = OutcomeLearningService(test_db_session)
        lr = await learner.learn_from_override_resolution(resolved)
        assert lr is not None
        assert lr.adaptation_signal == "override_revoked:goal"
        assert lr.signal_weight == -0.1


# ---------------------------------------------------------------
# 5. Endpoint shapes
# ---------------------------------------------------------------


class TestOverrideEndpoints:
    """Test Phase 11 API endpoint shapes and responses."""

    def test_pending_overrides_endpoint(self, client) -> None:
        resp = client.get("/api/consciousness/covenant/overrides/pending")
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data
        assert "pending" in data

    def test_resolved_overrides_endpoint(self, client) -> None:
        resp = client.get("/api/consciousness/covenant/overrides/resolved")
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data
        assert "resolved" in data

    def test_resolve_override_endpoint_requires_resolution(self, client) -> None:
        """POST without resolution param should fail validation."""
        resp = client.post(
            "/api/consciousness/covenant/overrides/fake_id/resolve"
        )
        assert resp.status_code == 422  # missing required 'resolution'

    def test_resolve_override_invalid_resolution(self, client) -> None:
        """POST with invalid resolution should fail pattern validation."""
        resp = client.post(
            "/api/consciousness/covenant/overrides/fake_id/resolve",
            params={"resolution": "invalid_value"},
        )
        assert resp.status_code == 422

    def test_resolve_override_nonexistent_record(self, client) -> None:
        """POST for nonexistent record returns error status."""
        resp = client.post(
            "/api/consciousness/covenant/overrides/nonexistent/resolve",
            params={"resolution": "approved", "resolver": "matt", "rationale": "Test"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "error"
