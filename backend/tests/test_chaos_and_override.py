"""Tests for V8C chaos engine and V8D human override protocol."""

from datetime import datetime, timedelta

from src.kortana.services.chaos_engine import (
    SCENARIO_CATALOGUE,
    DrillResult,
    run_all_scenarios,
    run_scenario,
    run_stale_canary,
    run_rejected_after_escalation,
    run_conflicting_signals,
    run_static_verdict,
    run_rate_limit_storm,
    run_webhook_failure,
)
from src.kortana.services.human_override import (
    OverrideManager,
    OverrideRecord,
    check_active_override,
    compute_override_hash,
    should_override_actuation,
)


# ===================================================================
# V8C — Chaos engine tests
# ===================================================================


class TestStaleCanary:
    """Stale canary scenario."""

    def test_de_escalates_from_auto(self) -> None:
        result = run_stale_canary("auto")
        assert result.passed is True
        assert result.scenario == "stale_canary"

    def test_de_escalates_from_self_aware(self) -> None:
        result = run_stale_canary("self-aware")
        assert result.passed is True

    def test_holds_at_manual(self) -> None:
        result = run_stale_canary("manual")
        assert result.passed is True


class TestRejectedAfterEscalation:
    """Rejected canary after escalation → rollback."""

    def test_rollback_from_auto(self) -> None:
        result = run_rejected_after_escalation("auto")
        assert result.passed is True
        assert result.rollback_triggered is True

    def test_rollback_from_self_aware(self) -> None:
        result = run_rejected_after_escalation("self-aware")
        assert result.passed is True
        assert result.rollback_triggered is True

    def test_no_rollback_at_manual(self) -> None:
        result = run_rejected_after_escalation("manual")
        assert result.passed is True
        assert result.rollback_triggered is False


class TestConflictingSignals:
    """Mixed promoted/rejected runs → no escalation."""

    def test_does_not_escalate(self) -> None:
        result = run_conflicting_signals("self-aware")
        assert result.passed is True
        assert any(c["check"] == "does_not_escalate" for c in result.checks)

    def test_from_auto(self) -> None:
        result = run_conflicting_signals("auto")
        assert result.passed is True


class TestStaticVerdict:
    """Static verdict → de-escalation."""

    def test_de_escalates_from_auto(self) -> None:
        result = run_static_verdict("auto")
        assert result.passed is True

    def test_holds_at_manual(self) -> None:
        result = run_static_verdict("manual")
        assert result.passed is True


class TestRateLimitStorm:
    """Rapid changes → rate limiter blocks."""

    def test_rate_limit_fires(self) -> None:
        result = run_rate_limit_storm("self-aware")
        assert result.passed is True
        assert result.rate_limit_blocked is True


class TestWebhookFailure:
    """Alert publisher with no sinks → graceful degradation."""

    def test_no_crash(self) -> None:
        result = run_webhook_failure()
        assert result.passed is True
        assert result.scenario == "webhook_failure"


class TestScenarioDispatcher:
    """Scenario dispatcher and run_all_scenarios."""

    def test_unknown_scenario(self) -> None:
        result = run_scenario("nonexistent")
        assert result.passed is False

    def test_run_all(self) -> None:
        results = run_all_scenarios("self-aware")
        assert len(results) == len(SCENARIO_CATALOGUE)
        for r in results:
            assert isinstance(r, DrillResult)
            assert r.duration_ms >= 0

    def test_all_pass_from_auto(self) -> None:
        results = run_all_scenarios("auto")
        for r in results:
            assert r.passed is True, f"Scenario {r.scenario} failed: {r.checks}"

    def test_all_pass_from_manual(self) -> None:
        results = run_all_scenarios("manual")
        for r in results:
            assert r.passed is True, f"Scenario {r.scenario} failed: {r.checks}"


# ===================================================================
# V8D — Human override tests
# ===================================================================


class TestOverrideHash:
    """Test override audit hash."""

    def test_deterministic(self) -> None:
        h1 = compute_override_hash("manual", "test", "2026-01-01T00:00:00", "matt", "2026-01-01T00:00:00")
        h2 = compute_override_hash("manual", "test", "2026-01-01T00:00:00", "matt", "2026-01-01T00:00:00")
        assert h1 == h2

    def test_different_inputs(self) -> None:
        h1 = compute_override_hash("manual", "a", "2026-01-01T00:00:00", "matt", "2026-01-01T00:00:00")
        h2 = compute_override_hash("auto", "b", "2026-01-01T00:00:00", "matt", "2026-01-01T00:00:00")
        assert h1 != h2

    def test_is_sha256(self) -> None:
        h = compute_override_hash("manual", "test", "2026-01-01T00:00:00", "matt", "2026-01-01T00:00:00")
        assert len(h) == 64
        int(h, 16)  # valid hex


class TestOverrideRecord:
    """Test OverrideRecord creation and properties."""

    def test_auto_hash(self) -> None:
        now = datetime(2026, 1, 1, 12, 0, 0)
        o = OverrideRecord(
            mode="manual", reason="incident", expires_at=now + timedelta(hours=1),
            created_by="matt", created_at=now,
        )
        assert len(o.audit_hash) == 64

    def test_is_active(self) -> None:
        future = datetime.utcnow() + timedelta(hours=1)
        o = OverrideRecord(mode="manual", reason="t", expires_at=future, created_by="matt")
        assert o.is_active is True
        assert o.is_expired is False

    def test_expired(self) -> None:
        past = datetime.utcnow() - timedelta(hours=1)
        o = OverrideRecord(mode="manual", reason="t", expires_at=past, created_by="matt")
        assert o.is_active is False
        assert o.is_expired is True

    def test_revoked(self) -> None:
        future = datetime.utcnow() + timedelta(hours=1)
        o = OverrideRecord(mode="manual", reason="t", expires_at=future,
                           created_by="matt", revoked=True)
        assert o.is_active is False

    def test_to_dict(self) -> None:
        future = datetime.utcnow() + timedelta(hours=1)
        o = OverrideRecord(mode="manual", reason="test", expires_at=future,
                           created_by="matt", override_id=1)
        d = o.to_dict()
        assert d["mode"] == "manual"
        assert d["override_id"] == 1
        assert "audit_hash" in d
        assert "is_active" in d


class TestCheckActiveOverride:
    """Test override precedence logic."""

    def test_no_overrides(self) -> None:
        assert check_active_override([]) is None

    def test_single_active(self) -> None:
        future = datetime.utcnow() + timedelta(hours=1)
        o = OverrideRecord(mode="manual", reason="t", expires_at=future, created_by="matt")
        result = check_active_override([o])
        assert result is o

    def test_latest_wins(self) -> None:
        now = datetime.utcnow()
        future = now + timedelta(hours=1)
        o1 = OverrideRecord(mode="manual", reason="t1", expires_at=future,
                            created_by="matt", created_at=now - timedelta(minutes=10))
        o2 = OverrideRecord(mode="self-aware", reason="t2", expires_at=future,
                            created_by="matt", created_at=now)
        result = check_active_override([o1, o2])
        assert result is o2
        assert result.mode == "self-aware"

    def test_expired_excluded(self) -> None:
        past = datetime.utcnow() - timedelta(hours=1)
        o = OverrideRecord(mode="manual", reason="t", expires_at=past, created_by="matt")
        assert check_active_override([o]) is None

    def test_revoked_excluded(self) -> None:
        future = datetime.utcnow() + timedelta(hours=1)
        o = OverrideRecord(mode="manual", reason="t", expires_at=future,
                           created_by="matt", revoked=True)
        assert check_active_override([o]) is None


class TestShouldOverrideActuation:
    """Test override vs actuation decision."""

    def test_no_override(self) -> None:
        block, reason = should_override_actuation(None, "auto")
        assert block is False

    def test_expired_override(self) -> None:
        past = datetime.utcnow() - timedelta(hours=1)
        o = OverrideRecord(mode="manual", reason="t", expires_at=past, created_by="matt")
        block, reason = should_override_actuation(o, "auto")
        assert block is False

    def test_same_mode_no_block(self) -> None:
        future = datetime.utcnow() + timedelta(hours=1)
        o = OverrideRecord(mode="manual", reason="t", expires_at=future, created_by="matt")
        block, reason = should_override_actuation(o, "manual")
        assert block is False

    def test_blocks_different_mode(self) -> None:
        future = datetime.utcnow() + timedelta(hours=1)
        o = OverrideRecord(mode="manual", reason="safety hold", expires_at=future,
                           created_by="matt")
        block, reason = should_override_actuation(o, "auto")
        assert block is True
        assert "manual" in reason
        assert "matt" in reason


class TestOverrideManager:
    """Test the in-memory override manager."""

    def test_empty(self) -> None:
        mgr = OverrideManager()
        assert mgr.active() is None
        assert mgr.count == 0

    def test_create_sets_active(self) -> None:
        mgr = OverrideManager()
        o = mgr.create("manual", "testing", expires_in_minutes=30)
        assert mgr.active() is o
        assert mgr.count == 1

    def test_revoke(self) -> None:
        mgr = OverrideManager()
        o = mgr.create("manual", "testing", expires_in_minutes=30)
        assert mgr.revoke(o.override_id, "matt") is True
        assert mgr.active() is None

    def test_revoke_nonexistent(self) -> None:
        mgr = OverrideManager()
        assert mgr.revoke(999) is False

    def test_history(self) -> None:
        mgr = OverrideManager()
        mgr.create("manual", "r1", expires_in_minutes=30)
        mgr.create("auto", "r2", expires_in_minutes=30)
        h = mgr.history()
        assert len(h) == 2
        assert h[0]["reason"] == "r2"  # newest first

    def test_all_active(self) -> None:
        mgr = OverrideManager()
        mgr.create("manual", "r1", expires_in_minutes=30)
        mgr.create("auto", "r2", expires_in_minutes=30)
        active = mgr.all_active()
        assert len(active) == 2

    def test_latest_override_wins(self) -> None:
        mgr = OverrideManager()
        mgr.create("manual", "r1", expires_in_minutes=30)
        mgr.create("auto", "r2", expires_in_minutes=30)
        assert mgr.active().mode == "auto"
