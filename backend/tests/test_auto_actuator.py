"""Tests for V7 — automatic actuation, audit trail, deploy gate HTTP codes."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock


from src.kortana.services.auto_actuator import (
    ActuationDecision,
    apply_actuation,
    compute_audit_hash,
    decision_to_log_dict,
    evaluate_actuation,
    evaluate_auto_de_escalation,
    evaluate_auto_escalation,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _promoted_runs(n: int) -> list[dict]:
    return [
        {
            "promotion_status": "promoted",
            "verdict": "adaptive",
            "commit_sha": f"sha{i}",
            "created_at": datetime.utcnow().isoformat(),
        }
        for i in range(n)
    ]


def _rejected_run() -> dict:
    return {
        "promotion_status": "rejected",
        "verdict": "static",
        "commit_sha": "bad_sha",
        "created_at": datetime.utcnow().isoformat(),
    }


# ---------------------------------------------------------------------------
# Audit hash tests
# ---------------------------------------------------------------------------


class TestAuditHash:
    """Test tamper-evident audit hash computation."""

    def test_deterministic(self) -> None:
        d1 = ActuationDecision(
            action="hold", from_mode="self-aware", to_mode="self-aware",
            timestamp="2026-04-08T00:00:00",
        )
        d2 = ActuationDecision(
            action="hold", from_mode="self-aware", to_mode="self-aware",
            timestamp="2026-04-08T00:00:00",
        )
        assert d1.audit_hash == d2.audit_hash

    def test_different_inputs_different_hash(self) -> None:
        d1 = ActuationDecision(
            action="hold", from_mode="self-aware", to_mode="self-aware",
            timestamp="2026-04-08T00:00:00",
        )
        d2 = ActuationDecision(
            action="escalate", from_mode="self-aware", to_mode="auto",
            timestamp="2026-04-08T00:00:00",
        )
        assert d1.audit_hash != d2.audit_hash

    def test_hash_is_sha256_hex(self) -> None:
        d = ActuationDecision(action="hold", from_mode="m", to_mode="m")
        assert len(d.audit_hash) == 64
        int(d.audit_hash, 16)  # valid hex

    def test_compute_matches_auto(self) -> None:
        d = ActuationDecision(
            action="hold", from_mode="self-aware", to_mode="self-aware",
            timestamp="2026-04-08T00:00:00",
        )
        expected = compute_audit_hash(d)
        assert d.audit_hash == expected


# ---------------------------------------------------------------------------
# Auto-escalation tests
# ---------------------------------------------------------------------------


class TestAutoEscalation:
    """Test automatic escalation evaluation."""

    def test_hold_at_max_mode(self) -> None:
        result = evaluate_auto_escalation("auto", _promoted_runs(5), max_mode="auto")
        assert result.action == "hold"
        assert "max mode" in result.reasons[0]

    def test_hold_insufficient_runs(self) -> None:
        result = evaluate_auto_escalation("self-aware", _promoted_runs(2), min_consecutive_promoted=3)
        assert result.action == "hold"
        assert "Need 3" in result.reasons[0]

    def test_hold_not_all_promoted(self) -> None:
        runs = _promoted_runs(2) + [_rejected_run()]
        runs[0]["promotion_status"] = "rejected"
        result = evaluate_auto_escalation("self-aware", runs, min_consecutive_promoted=3)
        assert result.action == "hold"

    def test_escalate_on_consecutive_promoted(self) -> None:
        runs = _promoted_runs(3)
        result = evaluate_auto_escalation("self-aware", runs, min_consecutive_promoted=3)
        assert result.action == "escalate"
        assert result.to_mode == "auto"

    def test_escalate_from_manual(self) -> None:
        runs = _promoted_runs(3)
        result = evaluate_auto_escalation("manual", runs, min_consecutive_promoted=3)
        assert result.action == "escalate"
        assert result.to_mode == "self-aware"

    def test_holds_when_not_all_adaptive(self) -> None:
        runs = _promoted_runs(3)
        runs[0]["verdict"] = "static"
        result = evaluate_auto_escalation("self-aware", runs, min_consecutive_promoted=3)
        assert result.action == "hold"
        assert "adaptive" in result.reasons[0]


# ---------------------------------------------------------------------------
# Auto-de-escalation tests
# ---------------------------------------------------------------------------


class TestAutoDeEscalation:
    """Test automatic de-escalation evaluation."""

    def test_hold_at_lowest(self) -> None:
        result = evaluate_auto_de_escalation("manual", None)
        assert result.action == "hold"
        assert "lowest" in result.reasons[0]

    def test_de_escalate_no_run(self) -> None:
        result = evaluate_auto_de_escalation("auto", None)
        assert result.action == "de-escalate"
        assert result.to_mode == "self-aware"

    def test_de_escalate_on_rejected(self) -> None:
        result = evaluate_auto_de_escalation("auto", _rejected_run())
        assert result.action == "de-escalate"
        assert result.to_mode == "self-aware"

    def test_de_escalate_on_static(self) -> None:
        run = {"verdict": "static", "promotion_status": "pending", "commit_sha": "s1"}
        result = evaluate_auto_de_escalation("self-aware", run)
        assert result.action == "de-escalate"
        assert result.to_mode == "manual"

    def test_hold_when_healthy(self) -> None:
        run = _promoted_runs(1)[0]
        result = evaluate_auto_de_escalation("auto", run)
        assert result.action == "hold"


# ---------------------------------------------------------------------------
# Combined evaluation tests
# ---------------------------------------------------------------------------


class TestEvaluateActuation:
    """Test the combined actuation pipeline."""

    def test_de_escalation_priority(self) -> None:
        """De-escalation takes priority over escalation."""
        runs = [_rejected_run()] + _promoted_runs(5)
        result = evaluate_actuation("auto", runs)
        assert result.action == "de-escalate"

    def test_escalation_when_healthy(self) -> None:
        runs = _promoted_runs(3)
        result = evaluate_actuation("self-aware", runs, min_consecutive_promoted=3)
        assert result.action == "escalate"

    def test_hold_when_mixed(self) -> None:
        runs = _promoted_runs(2) + [_rejected_run()]
        result = evaluate_actuation("self-aware", runs, min_consecutive_promoted=3)
        assert result.action == "hold"


# ---------------------------------------------------------------------------
# Apply actuation tests
# ---------------------------------------------------------------------------


class TestApplyActuation:
    """Test applying actuation decisions to the daemon."""

    def test_hold_does_not_change_mode(self) -> None:
        daemon = MagicMock()
        daemon.default_approval_mode = "self-aware"
        decision = ActuationDecision(action="hold", from_mode="self-aware", to_mode="self-aware")
        applied = apply_actuation(daemon, decision)
        assert applied is False
        assert daemon.default_approval_mode == "self-aware"

    def test_escalate_changes_mode(self) -> None:
        daemon = MagicMock()
        daemon.default_approval_mode = "self-aware"
        decision = ActuationDecision(action="escalate", from_mode="self-aware", to_mode="auto")
        applied = apply_actuation(daemon, decision)
        assert applied is True
        assert daemon.default_approval_mode == "auto"

    def test_de_escalate_changes_mode(self) -> None:
        daemon = MagicMock()
        daemon.default_approval_mode = "auto"
        decision = ActuationDecision(action="de-escalate", from_mode="auto", to_mode="self-aware")
        applied = apply_actuation(daemon, decision)
        assert applied is True
        assert daemon.default_approval_mode == "self-aware"


# ---------------------------------------------------------------------------
# decision_to_log_dict tests
# ---------------------------------------------------------------------------


class TestDecisionToLogDict:
    """Test conversion to audit log dict."""

    def test_contains_all_fields(self) -> None:
        decision = ActuationDecision(
            action="escalate", from_mode="self-aware", to_mode="auto",
            reasons=["3 promoted runs"], actor="daemon",
            decision_type="escalation", commit_sha="abc123",
        )
        d = decision_to_log_dict(decision)
        assert d["decision_type"] == "escalation"
        assert d["actor"] == "daemon"
        assert d["action"] == "escalate"
        assert d["from_state"] == "self-aware"
        assert d["to_state"] == "auto"
        assert d["audit_hash"]
        assert len(d["audit_hash"]) == 64

    def test_deploy_gate_log(self) -> None:
        decision = ActuationDecision(
            action="blocked", from_mode="deploy-gate", to_mode="blocked",
            actor="ci", decision_type="deployment",
        )
        d = decision_to_log_dict(decision)
        assert d["actor"] == "ci"
        assert d["decision_type"] == "deployment"
