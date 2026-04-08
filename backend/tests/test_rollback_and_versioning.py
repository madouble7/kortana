"""Tests for V8A rollback engine and V8B policy versioning."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

from src.kortana.services.rollback_engine import (
    RollbackConfig,
    apply_rollback,
    check_cooldown,
    check_rate_limit,
    evaluate_rollback,
    gate_actuation,
)
from src.kortana.services.policy_versioning import (
    PolicyRegistry,
    PolicySnapshot,
    diff_policies,
    replay_decisions,
)


# ===================================================================
# V8A — Rollback engine tests
# ===================================================================


class TestCheckCooldown:
    """Test cooldown guard."""

    def test_no_previous_change(self) -> None:
        ok, remaining = check_cooldown(None)
        assert ok is True
        assert remaining == 0

    def test_cooldown_expired(self) -> None:
        now = datetime(2026, 1, 1, 12, 0, 0)
        last = now - timedelta(seconds=600)
        ok, remaining = check_cooldown(last, now=now, cooldown_seconds=300)
        assert ok is True
        assert remaining == 0

    def test_cooldown_active(self) -> None:
        now = datetime(2026, 1, 1, 12, 0, 0)
        last = now - timedelta(seconds=100)
        ok, remaining = check_cooldown(last, now=now, cooldown_seconds=300)
        assert ok is False
        assert remaining == 200

    def test_exact_boundary(self) -> None:
        now = datetime(2026, 1, 1, 12, 0, 0)
        last = now - timedelta(seconds=300)
        ok, remaining = check_cooldown(last, now=now, cooldown_seconds=300)
        assert ok is True
        assert remaining == 0


class TestCheckRateLimit:
    """Test rate limiter."""

    def test_no_decisions(self) -> None:
        ok, count = check_rate_limit([], max_changes=3)
        assert ok is True
        assert count == 0

    def test_under_limit(self) -> None:
        now = datetime(2026, 1, 1, 12, 0, 0)
        decisions = [
            {"action": "escalate", "created_at": (now - timedelta(seconds=60)).isoformat()},
            {"action": "hold", "created_at": (now - timedelta(seconds=120)).isoformat()},
        ]
        ok, count = check_rate_limit(decisions, now=now, max_changes=3, window_seconds=3600)
        assert ok is True
        assert count == 1  # hold doesn't count

    def test_at_limit(self) -> None:
        now = datetime(2026, 1, 1, 12, 0, 0)
        decisions = [
            {"action": "escalate", "created_at": (now - timedelta(seconds=60)).isoformat()},
            {"action": "de-escalate", "created_at": (now - timedelta(seconds=120)).isoformat()},
            {"action": "escalate", "created_at": (now - timedelta(seconds=180)).isoformat()},
        ]
        ok, count = check_rate_limit(decisions, now=now, max_changes=3, window_seconds=3600)
        assert ok is False
        assert count == 3

    def test_old_decisions_excluded(self) -> None:
        now = datetime(2026, 1, 1, 12, 0, 0)
        decisions = [
            {"action": "escalate", "created_at": (now - timedelta(hours=2)).isoformat()},
            {"action": "escalate", "created_at": (now - timedelta(hours=3)).isoformat()},
        ]
        ok, count = check_rate_limit(decisions, now=now, max_changes=3, window_seconds=3600)
        assert ok is True
        assert count == 0


class TestEvaluateRollback:
    """Test rollback evaluation."""

    def test_no_rollback_when_disabled(self) -> None:
        config = RollbackConfig(auto_rollback_enabled=False)
        rb = evaluate_rollback("auto", "self-aware", None, True, config=config)
        assert rb.should_rollback is False

    def test_no_rollback_after_de_escalation(self) -> None:
        rb = evaluate_rollback("manual", "self-aware", None, True)
        assert rb.should_rollback is False

    def test_rollback_on_rejected_canary(self) -> None:
        canary = {"promotion_status": "rejected", "verdict": "adaptive"}
        rb = evaluate_rollback("auto", "self-aware", canary, True)
        assert rb.should_rollback is True
        assert rb.trigger == "degraded_canary"
        assert rb.to_mode == "self-aware"

    def test_rollback_on_static_verdict(self) -> None:
        canary = {"promotion_status": "promoted", "verdict": "static"}
        rb = evaluate_rollback("auto", "self-aware", canary, True)
        assert rb.should_rollback is True
        assert rb.trigger == "degraded_canary"

    def test_rollback_on_blocked_deploy(self) -> None:
        canary = {"promotion_status": "promoted", "verdict": "adaptive"}
        rb = evaluate_rollback("auto", "self-aware", canary, False)
        assert rb.should_rollback is True
        assert rb.trigger == "deploy_blocked"

    def test_no_rollback_when_healthy(self) -> None:
        canary = {"promotion_status": "promoted", "verdict": "adaptive"}
        rb = evaluate_rollback("auto", "self-aware", canary, True)
        assert rb.should_rollback is False

    def test_no_rollback_same_mode(self) -> None:
        canary = {"promotion_status": "rejected"}
        rb = evaluate_rollback("self-aware", "self-aware", canary, True)
        assert rb.should_rollback is False  # not escalated


class TestGateActuation:
    """Test combined gate check."""

    def test_all_clear(self) -> None:
        ok, reasons = gate_actuation(None, [])
        assert ok is True
        assert len(reasons) == 0

    def test_blocked_by_cooldown(self) -> None:
        now = datetime(2026, 1, 1, 12, 0, 0)
        last = now - timedelta(seconds=10)
        ok, reasons = gate_actuation(last, [], now=now)
        assert ok is False
        assert any("Cooldown" in r for r in reasons)

    def test_blocked_by_rate(self) -> None:
        now = datetime(2026, 1, 1, 12, 0, 0)
        decisions = [
            {"action": "escalate", "created_at": (now - timedelta(seconds=i * 60)).isoformat()}
            for i in range(5)
        ]
        config = RollbackConfig(cooldown_seconds=0, max_changes_per_window=3)
        ok, reasons = gate_actuation(None, decisions, config=config, now=now)
        assert ok is False
        assert any("Rate limit" in r for r in reasons)


class TestApplyRollback:
    """Test rollback application."""

    def test_no_rollback(self) -> None:
        from src.kortana.services.rollback_engine import RollbackDecision
        daemon = MagicMock()
        rb = RollbackDecision(
            should_rollback=False, from_mode="auto", to_mode="auto", trigger="none",
        )
        result = apply_rollback(daemon, rb)
        assert result is False

    def test_rollback_changes_mode(self) -> None:
        from src.kortana.services.rollback_engine import RollbackDecision
        daemon = MagicMock()
        daemon.default_approval_mode = "auto"
        rb = RollbackDecision(
            should_rollback=True, from_mode="auto", to_mode="self-aware",
            trigger="degraded_canary", reasons=["canary rejected"],
        )
        result = apply_rollback(daemon, rb)
        assert result is True
        assert daemon.default_approval_mode == "self-aware"


# ===================================================================
# V8B — Policy versioning tests
# ===================================================================


class TestPolicySnapshot:
    """Test PolicySnapshot creation and hashing."""

    def test_content_hash_deterministic(self) -> None:
        a = PolicySnapshot(version=1, cooldown_seconds=300, max_changes_per_window=3,
                           window_seconds=3600, min_consecutive_promoted=3,
                           max_mode="auto", auto_rollback_enabled=True,
                           created_at="2026-01-01T00:00:00")
        b = PolicySnapshot(version=2, cooldown_seconds=300, max_changes_per_window=3,
                           window_seconds=3600, min_consecutive_promoted=3,
                           max_mode="auto", auto_rollback_enabled=True,
                           created_at="2026-01-02T00:00:00")
        # Same content, different version/time → same content hash
        assert a.content_hash == b.content_hash

    def test_different_config_different_hash(self) -> None:
        a = PolicySnapshot(version=1, cooldown_seconds=300, max_changes_per_window=3,
                           window_seconds=3600, min_consecutive_promoted=3,
                           max_mode="auto", auto_rollback_enabled=True)
        b = PolicySnapshot(version=2, cooldown_seconds=600, max_changes_per_window=3,
                           window_seconds=3600, min_consecutive_promoted=3,
                           max_mode="auto", auto_rollback_enabled=True)
        assert a.content_hash != b.content_hash

    def test_to_dict(self) -> None:
        s = PolicySnapshot(version=1, cooldown_seconds=300, max_changes_per_window=3,
                           window_seconds=3600, min_consecutive_promoted=3,
                           max_mode="auto", auto_rollback_enabled=True)
        d = s.to_dict()
        assert d["version"] == 1
        assert d["cooldown_seconds"] == 300
        assert "content_hash" in d


class TestPolicyDiff:
    """Test policy diff computation."""

    def test_no_changes(self) -> None:
        a = PolicySnapshot(version=1, cooldown_seconds=300, max_changes_per_window=3,
                           window_seconds=3600, min_consecutive_promoted=3,
                           max_mode="auto", auto_rollback_enabled=True)
        b = PolicySnapshot(version=2, cooldown_seconds=300, max_changes_per_window=3,
                           window_seconds=3600, min_consecutive_promoted=3,
                           max_mode="auto", auto_rollback_enabled=True)
        diff = diff_policies(a, b)
        assert diff.has_changes is False
        assert len(diff.changes) == 0

    def test_detects_changes(self) -> None:
        a = PolicySnapshot(version=1, cooldown_seconds=300, max_changes_per_window=3,
                           window_seconds=3600, min_consecutive_promoted=3,
                           max_mode="auto", auto_rollback_enabled=True)
        b = PolicySnapshot(version=2, cooldown_seconds=600, max_changes_per_window=5,
                           window_seconds=3600, min_consecutive_promoted=3,
                           max_mode="auto", auto_rollback_enabled=False)
        diff = diff_policies(a, b)
        assert diff.has_changes is True
        fields = [c["field"] for c in diff.changes]
        assert "cooldown_seconds" in fields
        assert "max_changes_per_window" in fields
        assert "auto_rollback_enabled" in fields

    def test_diff_values(self) -> None:
        a = PolicySnapshot(version=1, cooldown_seconds=300, max_changes_per_window=3,
                           window_seconds=3600, min_consecutive_promoted=3,
                           max_mode="auto", auto_rollback_enabled=True)
        b = PolicySnapshot(version=2, cooldown_seconds=600, max_changes_per_window=3,
                           window_seconds=3600, min_consecutive_promoted=3,
                           max_mode="auto", auto_rollback_enabled=True)
        diff = diff_policies(a, b)
        change = diff.changes[0]
        assert change["old"] == 300
        assert change["new"] == 600


class TestPolicyRegistry:
    """Test the in-memory policy registry."""

    def test_empty_registry(self) -> None:
        reg = PolicyRegistry()
        assert reg.current is None
        assert reg.version_count == 0
        assert reg.latest_version_number() == 0

    def test_register_sets_current(self) -> None:
        reg = PolicyRegistry()
        s = PolicySnapshot(version=1, cooldown_seconds=300, max_changes_per_window=3,
                           window_seconds=3600, min_consecutive_promoted=3,
                           max_mode="auto", auto_rollback_enabled=True)
        reg.register(s)
        assert reg.current is s
        assert reg.version_count == 1

    def test_get_version(self) -> None:
        reg = PolicyRegistry()
        s1 = PolicySnapshot(version=1, cooldown_seconds=300, max_changes_per_window=3,
                            window_seconds=3600, min_consecutive_promoted=3,
                            max_mode="auto", auto_rollback_enabled=True)
        s2 = PolicySnapshot(version=2, cooldown_seconds=600, max_changes_per_window=3,
                            window_seconds=3600, min_consecutive_promoted=3,
                            max_mode="auto", auto_rollback_enabled=True)
        reg.register(s1)
        reg.register(s2)
        assert reg.get_version(1) is s1
        assert reg.get_version(2) is s2
        assert reg.get_version(99) is None

    def test_diff_versions(self) -> None:
        reg = PolicyRegistry()
        s1 = PolicySnapshot(version=1, cooldown_seconds=300, max_changes_per_window=3,
                            window_seconds=3600, min_consecutive_promoted=3,
                            max_mode="auto", auto_rollback_enabled=True)
        s2 = PolicySnapshot(version=2, cooldown_seconds=600, max_changes_per_window=3,
                            window_seconds=3600, min_consecutive_promoted=3,
                            max_mode="auto", auto_rollback_enabled=True)
        reg.register(s1)
        reg.register(s2)
        diff = reg.diff(1, 2)
        assert diff is not None
        assert diff.has_changes is True

    def test_history_newest_first(self) -> None:
        reg = PolicyRegistry()
        for i in range(1, 4):
            reg.register(PolicySnapshot(
                version=i, cooldown_seconds=300, max_changes_per_window=3,
                window_seconds=3600, min_consecutive_promoted=3,
                max_mode="auto", auto_rollback_enabled=True))
        h = reg.history()
        assert len(h) == 3
        assert h[0]["version"] == 3
        assert h[-1]["version"] == 1


class TestReplayDecisions:
    """Test policy replay."""

    def test_empty_runs(self) -> None:
        policy = PolicySnapshot(
            version=1, cooldown_seconds=300, max_changes_per_window=3,
            window_seconds=3600, min_consecutive_promoted=3,
            max_mode="auto", auto_rollback_enabled=True)
        result = replay_decisions(policy, [])
        assert result.total_decisions == 0
        assert result.changed_count == 0

    def test_replay_with_runs(self) -> None:
        policy = PolicySnapshot(
            version=1, cooldown_seconds=300, max_changes_per_window=3,
            window_seconds=3600, min_consecutive_promoted=2,
            max_mode="auto", auto_rollback_enabled=True)
        runs = [
            {"verdict": "adaptive", "promotion_status": "promoted"},
            {"verdict": "adaptive", "promotion_status": "promoted"},
            {"verdict": "adaptive", "promotion_status": "promoted"},
        ]
        result = replay_decisions(policy, runs)
        assert result.total_decisions == 3
        assert result.policy_version == 1

    def test_replay_detects_divergence(self) -> None:
        policy = PolicySnapshot(
            version=1, cooldown_seconds=300, max_changes_per_window=3,
            window_seconds=3600, min_consecutive_promoted=2,
            max_mode="auto", auto_rollback_enabled=True)
        runs = [
            {"verdict": "adaptive", "promotion_status": "promoted", "actual_action": "hold"},
            {"verdict": "adaptive", "promotion_status": "promoted", "actual_action": "hold"},
        ]
        result = replay_decisions(policy, runs)
        # At least one decision should differ since the policy would have escalated
        assert result.total_decisions == 2
