"""V9 — Operator-grade governance tests.

Tests for quorum override, drill scheduler, policy comparison,
and audit bundle functionality.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta


# ===================================================================
# V9A — Quorum Override Tests
# ===================================================================


class TestApprovalHash:
    """Approval hashes are deterministic and tamper-evident."""

    def test_deterministic(self) -> None:
        from src.kortana.services.quorum_override import compute_approval_hash

        h1 = compute_approval_hash("qo-1", "matt", True, "lgtm", "2026-01-01T00:00:00")
        h2 = compute_approval_hash("qo-1", "matt", True, "lgtm", "2026-01-01T00:00:00")
        assert h1 == h2

    def test_different_inputs(self) -> None:
        from src.kortana.services.quorum_override import compute_approval_hash

        h1 = compute_approval_hash("qo-1", "matt", True, "lgtm", "2026-01-01T00:00:00")
        h2 = compute_approval_hash("qo-1", "matt", False, "nope", "2026-01-01T00:00:00")
        assert h1 != h2

    def test_sha256_length(self) -> None:
        from src.kortana.services.quorum_override import compute_approval_hash

        h = compute_approval_hash("qo-1", "matt", True, "ok", "2026-01-01T00:00:00")
        assert len(h) == 64


class TestApprovalRecord:
    """ApprovalRecord auto-computes its hash."""

    def test_auto_hash(self) -> None:
        from src.kortana.services.quorum_override import ApprovalRecord

        r = ApprovalRecord(override_id="qo-1", approver="matt", approved=True)
        assert r.audit_hash
        assert len(r.audit_hash) == 64

    def test_to_dict(self) -> None:
        from src.kortana.services.quorum_override import ApprovalRecord

        r = ApprovalRecord(override_id="qo-1", approver="matt", approved=True, reason="ok")
        d = r.to_dict()
        assert d["approver"] == "matt"
        assert d["approved"] is True
        assert d["reason"] == "ok"


class TestQuorumPolicy:
    """QuorumPolicy serialises correctly."""

    def test_defaults(self) -> None:
        from src.kortana.services.quorum_override import QuorumPolicy

        p = QuorumPolicy()
        assert p.required_approvals == 2
        assert p.timeout_minutes == 60

    def test_to_dict(self) -> None:
        from src.kortana.services.quorum_override import QuorumPolicy

        p = QuorumPolicy(required_approvals=3, allowed_approvers=["a", "b", "c"])
        d = p.to_dict()
        assert d["required_approvals"] == 3
        assert len(d["allowed_approvers"]) == 3


class TestPendingQuorumOverride:
    """PendingQuorumOverride manages approvals and evaluates quorum."""

    def test_starts_pending(self) -> None:
        from src.kortana.services.quorum_override import PendingQuorumOverride, QuorumPolicy

        p = PendingQuorumOverride(
            override_id="qo-1", mode="manual", reason="test",
            policy=QuorumPolicy(required_approvals=2, allowed_approvers=["a", "b", "c"]),
            requested_by="matt",
        )
        assert p.status == "pending"
        assert not p.has_quorum
        assert p.approval_count == 0

    def test_reaches_quorum(self) -> None:
        from src.kortana.services.quorum_override import PendingQuorumOverride, QuorumPolicy

        p = PendingQuorumOverride(
            override_id="qo-1", mode="manual", reason="test",
            policy=QuorumPolicy(required_approvals=2, allowed_approvers=["a", "b", "c"]),
            requested_by="matt",
        )
        p.add_approval("a", True, "lgtm")
        assert p.status == "pending"

        p.add_approval("b", True, "lgtm")
        status = p.evaluate()
        assert status == "activated"
        assert p.activated

    def test_auto_rejects_when_impossible(self) -> None:
        from src.kortana.services.quorum_override import PendingQuorumOverride, QuorumPolicy

        p = PendingQuorumOverride(
            override_id="qo-1", mode="manual", reason="test",
            policy=QuorumPolicy(required_approvals=2, allowed_approvers=["a", "b"]),
            requested_by="matt",
        )
        p.add_approval("a", False, "nope")
        status = p.evaluate()
        assert status == "rejected"

    def test_duplicate_vote_raises(self) -> None:
        from src.kortana.services.quorum_override import PendingQuorumOverride, QuorumPolicy

        p = PendingQuorumOverride(
            override_id="qo-1", mode="manual", reason="test",
            policy=QuorumPolicy(required_approvals=2, allowed_approvers=["a", "b"]),
            requested_by="matt",
        )
        p.add_approval("a", True)
        with pytest.raises(ValueError, match="already voted"):
            p.add_approval("a", True)

    def test_unauthorized_voter_raises(self) -> None:
        from src.kortana.services.quorum_override import PendingQuorumOverride, QuorumPolicy

        p = PendingQuorumOverride(
            override_id="qo-1", mode="manual", reason="test",
            policy=QuorumPolicy(required_approvals=1, allowed_approvers=["a"]),
            requested_by="matt",
        )
        with pytest.raises(ValueError, match="not in allowed list"):
            p.add_approval("intruder", True)

    def test_expired_override(self) -> None:
        from src.kortana.services.quorum_override import PendingQuorumOverride, QuorumPolicy

        p = PendingQuorumOverride(
            override_id="qo-1", mode="manual", reason="test",
            policy=QuorumPolicy(required_approvals=1, allowed_approvers=["a"]),
            requested_by="matt",
            expires_at=datetime.utcnow() - timedelta(minutes=1),
        )
        assert p.is_expired
        assert p.status == "expired"

    def test_to_dict(self) -> None:
        from src.kortana.services.quorum_override import PendingQuorumOverride, QuorumPolicy

        p = PendingQuorumOverride(
            override_id="qo-1", mode="manual", reason="test",
            policy=QuorumPolicy(required_approvals=1, allowed_approvers=["a"]),
            requested_by="matt",
        )
        d = p.to_dict()
        assert d["override_id"] == "qo-1"
        assert d["status"] == "pending"
        assert d["policy"]["required_approvals"] == 1


class TestQuorumManager:
    """QuorumManager coordinates the lifecycle of quorum overrides."""

    def test_request_creates_pending(self) -> None:
        from src.kortana.services.quorum_override import QuorumManager, QuorumPolicy

        m = QuorumManager(QuorumPolicy(required_approvals=2, allowed_approvers=["a", "b"]))
        p = m.request("manual", "test", "matt")
        assert p.status == "pending"
        assert m.count == 1

    def test_vote_and_activate(self) -> None:
        from src.kortana.services.quorum_override import QuorumManager, QuorumPolicy

        m = QuorumManager(QuorumPolicy(required_approvals=2, allowed_approvers=["a", "b", "c"]))
        p = m.request("manual", "test", "matt")
        oid = p.override_id

        _, s1 = m.vote(oid, "a", True, "lgtm")
        assert s1 == "pending"

        _, s2 = m.vote(oid, "b", True, "lgtm")
        assert s2 == "activated"

        assert m.count == 0
        assert len(m.history) == 1

    def test_vote_and_reject(self) -> None:
        from src.kortana.services.quorum_override import QuorumManager, QuorumPolicy

        m = QuorumManager(QuorumPolicy(required_approvals=2, allowed_approvers=["a", "b"]))
        p = m.request("manual", "test", "matt")

        _, s = m.vote(p.override_id, "a", False, "disagree")
        assert s == "rejected"

    def test_vote_not_found_raises(self) -> None:
        from src.kortana.services.quorum_override import QuorumManager

        m = QuorumManager()
        with pytest.raises(KeyError):
            m.vote("nonexistent", "matt", True)

    def test_pending_list(self) -> None:
        from src.kortana.services.quorum_override import QuorumManager, QuorumPolicy

        m = QuorumManager(QuorumPolicy(required_approvals=2, allowed_approvers=["a", "b"]))
        m.request("manual", "r1", "matt")
        m.request("auto", "r2", "matt")
        assert len(m.pending) == 2


# ===================================================================
# V9B — Drill Scheduler Tests
# ===================================================================


class TestDrillSchedule:
    """DrillSchedule tracks interval and pass rate."""

    def test_new_schedule_is_due(self) -> None:
        from src.kortana.services.drill_scheduler import DrillSchedule

        s = DrillSchedule(scenario="stale_canary", interval_minutes=60)
        assert s.is_due

    def test_not_due_after_run(self) -> None:
        from src.kortana.services.drill_scheduler import DrillSchedule

        s = DrillSchedule(scenario="stale_canary", interval_minutes=60)
        s.record_result(True)
        assert not s.is_due

    def test_pass_rate_tracking(self) -> None:
        from src.kortana.services.drill_scheduler import DrillSchedule

        s = DrillSchedule(scenario="test")
        s.record_result(True)
        s.record_result(True)
        s.record_result(False)
        assert abs(s.pass_rate - 2 / 3) < 0.01

    def test_disabled_not_due(self) -> None:
        from src.kortana.services.drill_scheduler import DrillSchedule

        s = DrillSchedule(scenario="test", enabled=False)
        assert not s.is_due


class TestDrillSLO:
    """SLO evaluation against drill history."""

    def test_insufficient_data_passes(self) -> None:
        from src.kortana.services.drill_scheduler import DrillSLO, evaluate_slo

        slo = DrillSLO(scenario="test", min_pass_rate=0.95, min_runs=3)
        result = evaluate_slo(slo, [])
        assert result.met
        assert result.insufficient_data

    def test_slo_met(self) -> None:
        from src.kortana.services.drill_scheduler import DrillSLO, evaluate_slo

        now = datetime.utcnow()
        history = [
            {"scenario": "test", "passed": True, "created_at": (now - timedelta(minutes=i)).isoformat()}
            for i in range(5)
        ]
        slo = DrillSLO(scenario="test", min_pass_rate=0.95, min_runs=3)
        result = evaluate_slo(slo, history, now=now)
        assert result.met
        assert result.actual_pass_rate == 1.0

    def test_slo_violated(self) -> None:
        from src.kortana.services.drill_scheduler import DrillSLO, evaluate_slo

        now = datetime.utcnow()
        history = [
            {"scenario": "test", "passed": True, "created_at": (now - timedelta(minutes=1)).isoformat()},
            {"scenario": "test", "passed": False, "created_at": (now - timedelta(minutes=2)).isoformat()},
            {"scenario": "test", "passed": False, "created_at": (now - timedelta(minutes=3)).isoformat()},
            {"scenario": "test", "passed": False, "created_at": (now - timedelta(minutes=4)).isoformat()},
        ]
        slo = DrillSLO(scenario="test", min_pass_rate=0.5, min_runs=3)
        result = evaluate_slo(slo, history, now=now)
        assert not result.met
        assert result.actual_pass_rate == 0.25

    def test_slo_ignores_other_scenarios(self) -> None:
        from src.kortana.services.drill_scheduler import DrillSLO, evaluate_slo

        now = datetime.utcnow()
        history = [
            {"scenario": "other", "passed": False, "created_at": now.isoformat()},
            {"scenario": "test", "passed": True, "created_at": now.isoformat()},
        ]
        slo = DrillSLO(scenario="test", min_pass_rate=0.95, min_runs=1)
        result = evaluate_slo(slo, history, now=now)
        assert result.met
        assert result.total_runs == 1


class TestDrillScheduler:
    """DrillScheduler manages schedules, runs drills, and evaluates SLOs."""

    def test_add_and_remove_schedule(self) -> None:
        from src.kortana.services.drill_scheduler import DrillScheduler

        s = DrillScheduler()
        s.add_schedule("stale_canary", 30)
        assert len(s.schedules) == 1
        assert s.remove_schedule("stale_canary")
        assert len(s.schedules) == 0

    def test_get_due_drills(self) -> None:
        from src.kortana.services.drill_scheduler import DrillScheduler

        s = DrillScheduler()
        s.add_schedule("stale_canary", 60)
        s.add_schedule("webhook_failure", 60, enabled=False)
        due = s.get_due_drills()
        assert len(due) == 1
        assert due[0].scenario == "stale_canary"

    def test_run_due_drills(self) -> None:
        from src.kortana.services.drill_scheduler import DrillScheduler

        s = DrillScheduler()
        s.add_schedule("stale_canary", 60)
        results = s.run_due_drills("self-aware")
        assert len(results) == 1
        assert results[0]["scenario"] == "stale_canary"
        # After running, should not be due again
        assert len(s.get_due_drills()) == 0

    def test_set_and_evaluate_slo(self) -> None:
        from src.kortana.services.drill_scheduler import DrillScheduler

        s = DrillScheduler()
        s.set_slo("stale_canary", min_pass_rate=0.95, min_runs=1)

        # Record a passing result
        s.record_external_result("stale_canary", True)
        result = s.evaluate_slo("stale_canary")
        assert result is not None
        assert result.met

    def test_evaluate_all_slos(self) -> None:
        from src.kortana.services.drill_scheduler import DrillScheduler

        s = DrillScheduler()
        s.set_slo("a", min_pass_rate=0.5, min_runs=1)
        s.set_slo("b", min_pass_rate=0.5, min_runs=1)
        s.record_external_result("a", True)
        s.record_external_result("b", False)
        results = s.evaluate_all_slos()
        assert len(results) == 2


# ===================================================================
# V9C — Policy Comparison Tests
# ===================================================================


class TestPolicyComparison:
    """PolicyComparison provides current-vs-proposed view."""

    def test_basic_comparison(self) -> None:
        from src.kortana.services.policy_comparison import compute_policy_comparison

        comp = compute_policy_comparison("self-aware", [])
        assert comp.current_mode == "self-aware"
        assert comp.proposed_action in ("hold", "de-escalate", "escalate")

    def test_decision_differs_flag(self) -> None:
        from src.kortana.services.policy_comparison import compute_policy_comparison

        # Empty runs from auto → should de-escalate
        comp = compute_policy_comparison("auto", [])
        assert comp.decision_differs  # de-escalate changes mode

    def test_override_context(self) -> None:
        from src.kortana.services.human_override import OverrideRecord
        from src.kortana.services.policy_comparison import compute_policy_comparison

        override = OverrideRecord(
            mode="manual",
            reason="maintenance",
            expires_at=datetime.utcnow() + timedelta(hours=1),
            created_by="matt",
        )
        comp = compute_policy_comparison(
            "auto", [], override=override,
        )
        assert comp.override_active
        assert comp.override_mode == "manual"
        assert comp.override_blocking  # manual != auto decision

    def test_drill_health(self) -> None:
        from src.kortana.services.policy_comparison import compute_policy_comparison

        slo_results = [
            {"scenario": "a", "met": True},
            {"scenario": "b", "met": False},
        ]
        comp = compute_policy_comparison(
            "self-aware", [], drill_slo_results=slo_results,
        )
        assert not comp.drills_healthy

    def test_to_dict_structure(self) -> None:
        from src.kortana.services.policy_comparison import compute_policy_comparison

        comp = compute_policy_comparison("manual", [])
        d = comp.to_dict()
        assert "current" in d
        assert "proposed" in d
        assert "override" in d
        assert "quorum" in d
        assert "rollback" in d
        assert "drill_health" in d
        assert "policy" in d

    def test_quorum_context(self) -> None:
        from src.kortana.services.policy_comparison import compute_policy_comparison
        from src.kortana.services.quorum_override import PendingQuorumOverride, QuorumPolicy

        pending = PendingQuorumOverride(
            override_id="qo-1", mode="manual", reason="test",
            policy=QuorumPolicy(required_approvals=2, allowed_approvers=["a", "b"]),
            requested_by="matt",
        )
        comp = compute_policy_comparison(
            "self-aware", [], quorum_pending=[pending],
        )
        assert comp.quorum_pending == 1


# ===================================================================
# V9D — Audit Bundle Tests
# ===================================================================


class TestAuditBundle:
    """AuditBundle packages and hashes audit data."""

    def test_empty_bundle(self) -> None:
        from src.kortana.services.audit_bundle import build_audit_bundle

        now = datetime.utcnow()
        bundle = build_audit_bundle(
            "test-1", now - timedelta(hours=1), now,
        )
        assert bundle.total_decisions == 0
        assert bundle.total_drills == 0
        assert bundle.content_hash
        assert len(bundle.content_hash) == 64

    def test_bundle_with_data(self) -> None:
        from src.kortana.services.audit_bundle import build_audit_bundle

        now = datetime.utcnow()
        bundle = build_audit_bundle(
            "test-2",
            now - timedelta(hours=1),
            now,
            decisions=[
                {"action": "escalate", "created_at": now.isoformat()},
                {"action": "hold", "created_at": now.isoformat()},
            ],
            drills=[
                {"scenario": "test", "passed": True, "created_at": now.isoformat()},
                {"scenario": "test", "passed": False, "created_at": now.isoformat()},
            ],
        )
        assert bundle.total_decisions == 2
        assert bundle.total_drills == 2
        assert bundle.drill_pass_rate == 0.5

    def test_time_filtering(self) -> None:
        from src.kortana.services.audit_bundle import build_audit_bundle

        now = datetime.utcnow()
        old = now - timedelta(hours=48)
        bundle = build_audit_bundle(
            "test-3",
            now - timedelta(hours=1),
            now,
            decisions=[
                {"action": "hold", "created_at": old.isoformat()},  # should be filtered
                {"action": "escalate", "created_at": now.isoformat()},
            ],
        )
        assert bundle.total_decisions == 1

    def test_content_hash_changes(self) -> None:
        from src.kortana.services.audit_bundle import build_audit_bundle

        now = datetime.utcnow()
        b1 = build_audit_bundle("a", now - timedelta(hours=1), now)
        b2 = build_audit_bundle(
            "b", now - timedelta(hours=1), now,
            decisions=[{"action": "x", "created_at": now.isoformat()}],
        )
        assert b1.content_hash != b2.content_hash

    def test_to_dict(self) -> None:
        from src.kortana.services.audit_bundle import build_audit_bundle

        now = datetime.utcnow()
        bundle = build_audit_bundle("test-4", now - timedelta(hours=1), now)
        d = bundle.to_dict()
        assert "summary" in d
        assert "decisions" in d
        assert "content_hash" in d
        assert d["bundle_id"] == "test-4"


class TestAuditMarkdown:
    """Markdown renderer produces human-readable output."""

    def test_empty_bundle_markdown(self) -> None:
        from src.kortana.services.audit_bundle import build_audit_bundle, render_bundle_markdown

        now = datetime.utcnow()
        bundle = build_audit_bundle("md-1", now - timedelta(hours=1), now)
        md = render_bundle_markdown(bundle)
        assert "# Audit Bundle: md-1" in md
        assert "Content Hash" in md

    def test_markdown_with_data(self) -> None:
        from src.kortana.services.audit_bundle import build_audit_bundle, render_bundle_markdown

        now = datetime.utcnow()
        bundle = build_audit_bundle(
            "md-2",
            now - timedelta(hours=1),
            now,
            decisions=[{
                "decision_type": "escalation",
                "actor": "daemon",
                "action": "escalate",
                "from_state": "manual",
                "to_state": "self-aware",
                "audit_hash": "abc123def456",
                "created_at": now.isoformat(),
            }],
            drills=[{
                "scenario": "stale_canary",
                "passed": True,
                "duration_ms": 42,
                "created_at": now.isoformat(),
            }],
            overrides=[{
                "mode": "manual",
                "reason": "maintenance",
                "created_by": "matt",
                "revoked": False,
                "created_at": now.isoformat(),
            }],
        )
        md = render_bundle_markdown(bundle)
        assert "Policy Decisions" in md
        assert "Chaos Drills" in md
        assert "Human Overrides" in md
        assert "stale_canary" in md
