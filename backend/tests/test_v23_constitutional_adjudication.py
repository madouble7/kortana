"""V23 — constitutional adjudication tests."""

from __future__ import annotations

import sys
sys.path.insert(0, "src")

from kortana.services.constitution import (
    Constitution,
    Sensitivity,
)
from kortana.services.boundary_enforcer import (
    BoundaryEnforcer,
    BoundaryCheck,
)
from kortana.services.exception_handler import (
    ExceptionHandler,
    WaiverCondition,
    WaiverScope,
    WaiverStatus,
    MAX_WAIVER_HOURS,
    get_exception_handler,
)
from kortana.services.appeals import (
    AppealsCourt,
    AppealEvidence,
    AppealGrounds,
    AppealStatus,
    get_appeals_court,
)
from kortana.services.emergency_powers import (
    EmergencyPowersManager,
    EmergencyScope,
    EmergencyStatus,
    MAX_EMERGENCY_HOURS,
    get_emergency_powers,
)
from kortana.services.precedent_tracker import (
    PrecedentTracker,
    CitedArticle,
    DecisionType,
    PrecedentStrength,
    get_precedent_tracker,
)
from kortana.services.policy_feedback_loop import PolicyArea
from kortana.services.proposal_registry import PolicyProposal


def _make_proposal(
    area: PolicyArea = PolicyArea.ROLLOUT,
    confidence: float = 0.8,
    proposal_id: str = "prop-test-001",
) -> PolicyProposal:
    return PolicyProposal(
        proposal_id=proposal_id,
        source_amendment_id="amend-test",
        policy_area=area,
        current_rule="old rule",
        proposed_rule="new rule",
        justification="test justification",
        confidence=confidence,
        evidence_count=10,
    )


def _make_check(
    proposal_id: str = "prop-test-001",
    passed: bool = False,
    policy_area: str = "governance",
    sensitivity: str = "critical",
) -> BoundaryCheck:
    return BoundaryCheck(
        check_id="bc-test-001",
        proposal_id=proposal_id,
        passed=passed,
        violations=[],
        warnings=[],
        articles_checked=1,
        policy_area=policy_area,
        classification="immutable",
        sensitivity=sensitivity,
    )


# ═══ V23A: Exception Handler ═══


class TestExceptionHandler:
    """Tests for constitutional waivers."""

    def test_request_waiver(self) -> None:
        handler = ExceptionHandler()
        waiver = handler.request_waiver(
            article_id="art-001",
            proposal_id="prop-1",
            reason="urgent operational need",
            requested_by="matt",
        )
        assert waiver.status == WaiverStatus.REQUESTED
        assert waiver.waiver_id.startswith("waiver-")
        assert handler.waiver_count == 1

    def test_grant_waiver(self) -> None:
        handler = ExceptionHandler()
        waiver = handler.request_waiver("art-001", "prop-1", "reason", "matt")
        assert handler.grant_waiver(waiver.waiver_id)
        assert waiver.status == WaiverStatus.ACTIVE
        assert waiver.expires_at != ""
        assert waiver.is_active

    def test_deny_waiver(self) -> None:
        handler = ExceptionHandler()
        waiver = handler.request_waiver("art-001", "prop-1", "reason", "matt")
        assert handler.deny_waiver(waiver.waiver_id, "too risky")
        assert waiver.status == WaiverStatus.DENIED
        assert not waiver.is_active

    def test_revoke_waiver(self) -> None:
        handler = ExceptionHandler()
        waiver = handler.request_waiver("art-001", "prop-1", "reason", "matt")
        handler.grant_waiver(waiver.waiver_id)
        assert handler.revoke_waiver(waiver.waiver_id)
        assert waiver.status == WaiverStatus.REVOKED
        assert not waiver.is_active

    def test_check_waiver_single_proposal(self) -> None:
        handler = ExceptionHandler()
        waiver = handler.request_waiver(
            "art-001", "prop-1", "reason", "matt",
            scope=WaiverScope.SINGLE_PROPOSAL,
        )
        handler.grant_waiver(waiver.waiver_id)
        found = handler.check_waiver("art-001", "prop-1")
        assert found is not None
        assert found.waiver_id == waiver.waiver_id
        # Different proposal should not match
        assert handler.check_waiver("art-001", "prop-other") is None

    def test_check_waiver_policy_area_scope(self) -> None:
        handler = ExceptionHandler()
        waiver = handler.request_waiver(
            "art-001", "prop-1", "reason", "matt",
            scope=WaiverScope.POLICY_AREA,
        )
        handler.grant_waiver(waiver.waiver_id)
        # Should match any proposal for that article
        found = handler.check_waiver("art-001", "prop-other")
        assert found is not None

    def test_duration_cap(self) -> None:
        handler = ExceptionHandler()
        waiver = handler.request_waiver(
            "art-001", "prop-1", "reason", "matt",
            duration_hours=999,
        )
        assert waiver.duration_hours == MAX_WAIVER_HOURS

    def test_waiver_hash(self) -> None:
        handler = ExceptionHandler()
        waiver = handler.request_waiver("art-001", "prop-1", "reason", "matt")
        assert len(waiver.waiver_hash) == 16

    def test_waiver_to_dict(self) -> None:
        handler = ExceptionHandler()
        waiver = handler.request_waiver("art-001", "prop-1", "reason", "matt")
        d = waiver.to_dict()
        assert "waiver_id" in d
        assert "status" in d
        assert "is_active" in d

    def test_get_waivers_filtered(self) -> None:
        handler = ExceptionHandler()
        handler.request_waiver("art-001", "prop-1", "r1", "matt")
        handler.request_waiver("art-002", "prop-2", "r2", "matt")
        assert len(handler.get_waivers(article_id="art-001")) == 1
        assert len(handler.get_waivers()) == 2

    def test_get_waiver_by_id(self) -> None:
        handler = ExceptionHandler()
        waiver = handler.request_waiver("art-001", "prop-1", "r", "matt")
        assert handler.get_waiver(waiver.waiver_id) is not None
        assert handler.get_waiver("fake") is None

    def test_waiver_conditions(self) -> None:
        handler = ExceptionHandler()
        conditions = [
            WaiverCondition("cond-1", "must log all actions", "audit_log", required=True),
        ]
        waiver = handler.request_waiver(
            "art-001", "prop-1", "reason", "matt",
            conditions=conditions,
        )
        assert len(waiver.conditions) == 1
        assert waiver.conditions[0].condition_id == "cond-1"

    def test_summary(self) -> None:
        handler = ExceptionHandler()
        handler.request_waiver("art-001", "prop-1", "r", "matt")
        s = handler.get_summary()
        assert s["total_waivers"] == 1
        assert s["max_duration_hours"] == MAX_WAIVER_HOURS

    def test_grant_nonexistent(self) -> None:
        handler = ExceptionHandler()
        assert not handler.grant_waiver("fake")

    def test_revoke_nonexistent(self) -> None:
        handler = ExceptionHandler()
        assert not handler.revoke_waiver("fake")

    def test_module_singleton(self) -> None:
        h1 = get_exception_handler()
        h2 = get_exception_handler()
        assert h1 is h2


# ═══ V23B: Appeals Court ═══


class TestAppealsCourt:
    """Tests for the appeals process."""

    def test_file_appeal(self) -> None:
        court = AppealsCourt()
        check = _make_check()
        appeal = court.file_appeal(
            proposal_id="prop-1",
            original_check=check,
            appellant="matt",
            grounds=AppealGrounds.FACTUAL_ERROR,
            argument="the data was wrong",
        )
        assert appeal.status == AppealStatus.FILED
        assert appeal.appeal_id.startswith("appeal-")
        assert court.appeal_count == 1

    def test_escalated_sensitivity(self) -> None:
        court = AppealsCourt()
        # Standard → High escalation
        check = _make_check(sensitivity="standard")
        appeal = court.file_appeal("prop-1", check, "matt", AppealGrounds.DISPROPORTIONATE, "arg")
        assert appeal.escalated_sensitivity == Sensitivity.HIGH

        # Critical stays Critical
        check2 = _make_check(sensitivity="critical")
        appeal2 = court.file_appeal("prop-2", check2, "matt", AppealGrounds.EMERGENCY_NEED, "arg")
        assert appeal2.escalated_sensitivity == Sensitivity.CRITICAL

    def test_begin_review(self) -> None:
        court = AppealsCourt()
        appeal = court.file_appeal("prop-1", _make_check(), "matt", AppealGrounds.FACTUAL_ERROR, "arg")
        assert court.begin_review(appeal.appeal_id)
        assert appeal.status == AppealStatus.UNDER_REVIEW

    def test_decide_upheld(self) -> None:
        court = AppealsCourt()
        appeal = court.file_appeal("prop-1", _make_check(), "matt", AppealGrounds.FACTUAL_ERROR, "arg")
        court.begin_review(appeal.appeal_id)
        assert court.decide(appeal.appeal_id, "admin", AppealStatus.UPHELD, "violation was correct")
        assert appeal.status == AppealStatus.UPHELD
        assert appeal.decision is not None
        assert appeal.decision.outcome == AppealStatus.UPHELD

    def test_decide_overturned(self) -> None:
        court = AppealsCourt()
        appeal = court.file_appeal("prop-1", _make_check(), "matt", AppealGrounds.NEW_EVIDENCE, "arg")
        assert court.decide(appeal.appeal_id, "admin", AppealStatus.OVERTURNED, "new evidence valid")
        assert appeal.status == AppealStatus.OVERTURNED

    def test_decide_remanded(self) -> None:
        court = AppealsCourt()
        appeal = court.file_appeal("prop-1", _make_check(), "matt", AppealGrounds.MISCLASSIFICATION, "arg")
        assert court.decide(
            appeal.appeal_id, "admin", AppealStatus.REMANDED,
            "needs reclassification", conditions=["re-check classification"],
        )
        assert appeal.status == AppealStatus.REMANDED
        assert len(appeal.decision.conditions) == 1

    def test_decide_invalid_outcome(self) -> None:
        court = AppealsCourt()
        appeal = court.file_appeal("prop-1", _make_check(), "matt", AppealGrounds.FACTUAL_ERROR, "arg")
        assert not court.decide(appeal.appeal_id, "admin", AppealStatus.FILED, "invalid")

    def test_withdraw(self) -> None:
        court = AppealsCourt()
        appeal = court.file_appeal("prop-1", _make_check(), "matt", AppealGrounds.FACTUAL_ERROR, "arg")
        assert court.withdraw(appeal.appeal_id)
        assert appeal.status == AppealStatus.WITHDRAWN

    def test_get_appeals_filtered(self) -> None:
        court = AppealsCourt()
        court.file_appeal("prop-1", _make_check(), "matt", AppealGrounds.FACTUAL_ERROR, "arg1")
        court.file_appeal("prop-2", _make_check(), "alice", AppealGrounds.NEW_EVIDENCE, "arg2")
        assert len(court.get_appeals(appellant="matt")) == 1
        assert len(court.get_appeals(proposal_id="prop-2")) == 1
        assert len(court.get_appeals()) == 2

    def test_pending_count(self) -> None:
        court = AppealsCourt()
        court.file_appeal("prop-1", _make_check(), "matt", AppealGrounds.FACTUAL_ERROR, "arg")
        assert court.pending_count == 1
        court.decide(court.get_appeals()[0].appeal_id, "admin", AppealStatus.UPHELD, "done")
        assert court.pending_count == 0

    def test_appeal_hash(self) -> None:
        court = AppealsCourt()
        appeal = court.file_appeal("prop-1", _make_check(), "matt", AppealGrounds.FACTUAL_ERROR, "arg")
        assert len(appeal.appeal_hash) == 16

    def test_appeal_to_dict(self) -> None:
        court = AppealsCourt()
        appeal = court.file_appeal("prop-1", _make_check(), "matt", AppealGrounds.FACTUAL_ERROR, "arg")
        d = appeal.to_dict()
        assert "appeal_id" in d
        assert "grounds" in d
        assert "escalated_sensitivity" in d

    def test_appeal_evidence(self) -> None:
        court = AppealsCourt()
        evidence = [AppealEvidence("ev-1", "new data", "metric", "99.5")]
        appeal = court.file_appeal(
            "prop-1", _make_check(), "matt", AppealGrounds.NEW_EVIDENCE, "arg",
            evidence=evidence,
        )
        assert len(appeal.evidence) == 1

    def test_summary(self) -> None:
        court = AppealsCourt()
        court.file_appeal("prop-1", _make_check(), "matt", AppealGrounds.FACTUAL_ERROR, "arg")
        s = court.get_summary()
        assert s["total_appeals"] == 1
        assert "by_grounds" in s

    def test_overturn_rate(self) -> None:
        court = AppealsCourt()
        a1 = court.file_appeal("prop-1", _make_check(), "matt", AppealGrounds.FACTUAL_ERROR, "arg")
        a2 = court.file_appeal("prop-2", _make_check(), "matt", AppealGrounds.NEW_EVIDENCE, "arg")
        court.decide(a1.appeal_id, "admin", AppealStatus.UPHELD, "correct")
        court.decide(a2.appeal_id, "admin", AppealStatus.OVERTURNED, "new evidence")
        s = court.get_summary()
        assert s["overturn_rate"] == 0.5

    def test_module_singleton(self) -> None:
        c1 = get_appeals_court()
        c2 = get_appeals_court()
        assert c1 is c2


# ═══ V23C: Emergency Powers ═══


class TestEmergencyPowers:
    """Tests for time-boxed emergency powers."""

    def test_declare_emergency(self) -> None:
        mgr = EmergencyPowersManager()
        decl = mgr.declare_emergency(
            declared_by="matt",
            reason="critical outage",
            affected_areas=[PolicyArea.AUTONOMY],
        )
        assert decl.status == EmergencyStatus.DECLARED
        assert decl.declaration_id.startswith("emer-")
        assert mgr.declaration_count == 1

    def test_activate_emergency(self) -> None:
        mgr = EmergencyPowersManager()
        decl = mgr.declare_emergency("matt", "outage", [PolicyArea.AUTONOMY])
        assert mgr.activate(decl.declaration_id)
        assert decl.status == EmergencyStatus.ACTIVE
        assert decl.expires_at != ""
        assert decl.is_active

    def test_revoke_emergency(self) -> None:
        mgr = EmergencyPowersManager()
        decl = mgr.declare_emergency("matt", "outage", [PolicyArea.AUTONOMY])
        mgr.activate(decl.declaration_id)
        assert mgr.revoke(decl.declaration_id)
        assert decl.status == EmergencyStatus.REVOKED
        assert not decl.is_active

    def test_needs_review_after_revoke(self) -> None:
        mgr = EmergencyPowersManager()
        decl = mgr.declare_emergency("matt", "outage", [PolicyArea.AUTONOMY])
        mgr.activate(decl.declaration_id)
        mgr.revoke(decl.declaration_id)
        assert decl.needs_review
        assert mgr.needs_review_count == 1

    def test_submit_review(self) -> None:
        mgr = EmergencyPowersManager()
        decl = mgr.declare_emergency("matt", "outage", [PolicyArea.AUTONOMY])
        mgr.activate(decl.declaration_id)
        mgr.revoke(decl.declaration_id)
        assert mgr.submit_review(
            decl.declaration_id,
            reviewer="matt",
            actions_taken=["relaxed autonomy threshold"],
            justified=True,
            findings="action was necessary",
        )
        assert decl.status == EmergencyStatus.REVIEWED
        assert decl.review is not None
        assert decl.review.justified
        assert not decl.needs_review

    def test_check_emergency_power(self) -> None:
        mgr = EmergencyPowersManager()
        decl = mgr.declare_emergency("matt", "outage", [PolicyArea.AUTONOMY])
        mgr.activate(decl.declaration_id)
        assert mgr.is_area_under_emergency(PolicyArea.AUTONOMY)
        assert not mgr.is_area_under_emergency(PolicyArea.ROLLOUT)

    def test_duration_cap(self) -> None:
        mgr = EmergencyPowersManager()
        decl = mgr.declare_emergency("matt", "outage", [PolicyArea.AUTONOMY], duration_hours=999)
        assert decl.duration_hours == MAX_EMERGENCY_HOURS

    def test_multiple_areas(self) -> None:
        mgr = EmergencyPowersManager()
        decl = mgr.declare_emergency(
            "matt", "outage",
            [PolicyArea.AUTONOMY, PolicyArea.ESCALATION],
            scope=EmergencyScope.MULTIPLE_AREAS,
        )
        assert len(decl.affected_areas) == 2
        assert len(decl.powers) == 2

    def test_declaration_hash(self) -> None:
        mgr = EmergencyPowersManager()
        decl = mgr.declare_emergency("matt", "outage", [PolicyArea.AUTONOMY])
        assert len(decl.declaration_hash) == 16

    def test_declaration_to_dict(self) -> None:
        mgr = EmergencyPowersManager()
        decl = mgr.declare_emergency("matt", "outage", [PolicyArea.AUTONOMY])
        d = decl.to_dict()
        assert "declaration_id" in d
        assert "is_active" in d
        assert "needs_review" in d

    def test_get_declarations_filtered(self) -> None:
        mgr = EmergencyPowersManager()
        mgr.declare_emergency("matt", "outage1", [PolicyArea.AUTONOMY])
        d2 = mgr.declare_emergency("matt", "outage2", [PolicyArea.ROLLOUT])
        mgr.activate(d2.declaration_id)
        # Both DECLARED and ACTIVE count as is_active
        assert len(mgr.get_declarations(active_only=True)) == 2
        assert len(mgr.get_declarations()) == 2

    def test_review_to_dict(self) -> None:
        mgr = EmergencyPowersManager()
        decl = mgr.declare_emergency("matt", "outage", [PolicyArea.AUTONOMY])
        mgr.activate(decl.declaration_id)
        mgr.revoke(decl.declaration_id)
        mgr.submit_review(decl.declaration_id, "matt", ["action"], True, "ok")
        d = decl.review.to_dict()
        assert "review_id" in d
        assert "justified" in d

    def test_summary(self) -> None:
        mgr = EmergencyPowersManager()
        mgr.declare_emergency("matt", "outage", [PolicyArea.AUTONOMY])
        s = mgr.get_summary()
        assert s["total_declarations"] == 1
        assert s["constitutional_floor"] == "immutable"

    def test_activate_nonexistent(self) -> None:
        mgr = EmergencyPowersManager()
        assert not mgr.activate("fake")

    def test_submit_review_not_needed(self) -> None:
        mgr = EmergencyPowersManager()
        decl = mgr.declare_emergency("matt", "outage", [PolicyArea.AUTONOMY])
        # Not yet revoked/expired, so review not needed
        assert not mgr.submit_review(decl.declaration_id, "matt", [], True, "ok")

    def test_module_singleton(self) -> None:
        m1 = get_emergency_powers()
        m2 = get_emergency_powers()
        assert m1 is m2


# ═══ V23D: Precedent Tracker ═══


class TestPrecedentTracker:
    """Tests for adjudication precedent tracking."""

    def test_record_precedent(self) -> None:
        tracker = PrecedentTracker()
        p = tracker.record_precedent(
            decision_type=DecisionType.WAIVER_GRANTED,
            reference_id="waiver-001",
            policy_area=PolicyArea.AUTONOMY,
            decision_summary="granted waiver for autonomy change",
            reasoning="operational necessity",
            outcome="granted",
        )
        assert p.precedent_id.startswith("prec-")
        assert p.is_active
        assert tracker.precedent_count == 1

    def test_supersede(self) -> None:
        tracker = PrecedentTracker()
        p1 = tracker.record_precedent(
            DecisionType.APPEAL_UPHELD, "appeal-1", PolicyArea.GOVERNANCE,
            "block upheld", "immutable area", "upheld",
        )
        p2 = tracker.record_precedent(
            DecisionType.APPEAL_UPHELD, "appeal-2", PolicyArea.GOVERNANCE,
            "block upheld with clarification", "immutable + rationale", "upheld",
        )
        assert tracker.supersede(p1.precedent_id, p2.precedent_id)
        assert not p1.is_active
        assert p2.is_active

    def test_find_by_area(self) -> None:
        tracker = PrecedentTracker()
        tracker.record_precedent(
            DecisionType.WAIVER_GRANTED, "w-1", PolicyArea.AUTONOMY,
            "autonomy waiver", "needed", "granted",
        )
        tracker.record_precedent(
            DecisionType.APPEAL_OVERTURNED, "a-1", PolicyArea.ROLLOUT,
            "rollout appeal", "not disproportionate", "overturned",
        )
        assert len(tracker.find_precedents(policy_area=PolicyArea.AUTONOMY)) == 1
        assert len(tracker.find_precedents(policy_area=PolicyArea.ROLLOUT)) == 1

    def test_find_by_type(self) -> None:
        tracker = PrecedentTracker()
        tracker.record_precedent(
            DecisionType.WAIVER_GRANTED, "w-1", PolicyArea.AUTONOMY,
            "s", "r", "granted",
        )
        tracker.record_precedent(
            DecisionType.EMERGENCY_DECLARED, "e-1", PolicyArea.ROLLOUT,
            "s", "r", "declared",
        )
        assert len(tracker.find_precedents(decision_type=DecisionType.WAIVER_GRANTED)) == 1

    def test_find_by_strength(self) -> None:
        tracker = PrecedentTracker()
        tracker.record_precedent(
            DecisionType.APPEAL_UPHELD, "a-1", PolicyArea.GOVERNANCE,
            "s", "r", "upheld", strength=PrecedentStrength.BINDING,
        )
        tracker.record_precedent(
            DecisionType.WAIVER_GRANTED, "w-1", PolicyArea.AUTONOMY,
            "s", "r", "granted", strength=PrecedentStrength.INFORMATIONAL,
        )
        assert len(tracker.find_precedents(strength=PrecedentStrength.BINDING)) == 1

    def test_find_by_tag(self) -> None:
        tracker = PrecedentTracker()
        tracker.record_precedent(
            DecisionType.WAIVER_GRANTED, "w-1", PolicyArea.AUTONOMY,
            "s", "r", "granted", tags=["urgent", "operational"],
        )
        assert len(tracker.find_precedents(tag="urgent")) == 1
        assert len(tracker.find_precedents(tag="other")) == 0

    def test_binding_precedents(self) -> None:
        tracker = PrecedentTracker()
        tracker.record_precedent(
            DecisionType.APPEAL_UPHELD, "a-1", PolicyArea.GOVERNANCE,
            "immutable block", "law", "upheld",
            strength=PrecedentStrength.BINDING,
        )
        binding = tracker.get_binding_precedents(PolicyArea.GOVERNANCE)
        assert len(binding) == 1

    def test_check_conflicts(self) -> None:
        tracker = PrecedentTracker()
        tracker.record_precedent(
            DecisionType.APPEAL_UPHELD, "a-1", PolicyArea.GOVERNANCE,
            "immutable block", "law", "upheld",
            strength=PrecedentStrength.BINDING,
        )
        conflicts = tracker.check_conflicts(PolicyArea.GOVERNANCE, "overturned")
        assert len(conflicts) == 1
        no_conflict = tracker.check_conflicts(PolicyArea.GOVERNANCE, "upheld")
        assert len(no_conflict) == 0

    def test_cited_articles(self) -> None:
        tracker = PrecedentTracker()
        p = tracker.record_precedent(
            DecisionType.WAIVER_GRANTED, "w-1", PolicyArea.AUTONOMY,
            "s", "r", "granted",
            cited_articles=[CitedArticle("art-002", "directly relevant")],
        )
        assert len(p.cited_articles) == 1
        assert p.cited_articles[0].article_id == "art-002"

    def test_precedent_hash(self) -> None:
        tracker = PrecedentTracker()
        p = tracker.record_precedent(
            DecisionType.WAIVER_GRANTED, "w-1", PolicyArea.AUTONOMY,
            "s", "r", "granted",
        )
        assert len(p.precedent_hash) == 16

    def test_precedent_to_dict(self) -> None:
        tracker = PrecedentTracker()
        p = tracker.record_precedent(
            DecisionType.WAIVER_GRANTED, "w-1", PolicyArea.AUTONOMY,
            "s", "r", "granted",
        )
        d = p.to_dict()
        assert "precedent_id" in d
        assert "strength" in d
        assert "is_active" in d

    def test_supersede_nonexistent(self) -> None:
        tracker = PrecedentTracker()
        assert not tracker.supersede("fake", "also-fake")

    def test_summary(self) -> None:
        tracker = PrecedentTracker()
        tracker.record_precedent(
            DecisionType.WAIVER_GRANTED, "w-1", PolicyArea.AUTONOMY,
            "s", "r", "granted", strength=PrecedentStrength.BINDING,
        )
        s = tracker.get_summary()
        assert s["total_precedents"] == 1
        assert s["binding"] == 1

    def test_module_singleton(self) -> None:
        t1 = get_precedent_tracker()
        t2 = get_precedent_tracker()
        assert t1 is t2


# ═══ Integration: Full V23 Pipeline ═══


class TestV23Pipeline:
    """Integration: waiver → appeal → emergency → precedent."""

    def test_blocked_proposal_gets_waiver_and_precedent(self) -> None:
        """Proposal blocked by V22 boundary → waiver requested → granted → precedent recorded."""
        const = Constitution()
        enforcer = BoundaryEnforcer(const)
        handler = ExceptionHandler(const)
        tracker = PrecedentTracker()

        # 1. Restricted area proposal
        proposal = _make_proposal(area=PolicyArea.AUTONOMY, confidence=0.9)

        # 2. Boundary check — passes (restricted = warnings only)
        check = enforcer.check_proposal(proposal)
        assert check.passed
        assert len(check.warnings) > 0

        # 3. Request waiver for the article that generated warning
        waiver = handler.request_waiver(
            article_id="art-002",
            proposal_id=proposal.proposal_id,
            reason="planned autonomy expansion",
            requested_by="matt",
        )
        handler.grant_waiver(waiver.waiver_id)

        # 4. Record precedent
        tracker.record_precedent(
            decision_type=DecisionType.WAIVER_GRANTED,
            reference_id=waiver.waiver_id,
            policy_area=PolicyArea.AUTONOMY,
            decision_summary="waiver granted for autonomy expansion",
            reasoning="planned change with operational justification",
            outcome="granted",
            strength=PrecedentStrength.PERSUASIVE,
            cited_articles=[CitedArticle("art-002", "directly applicable")],
        )
        assert tracker.precedent_count == 1

    def test_appeal_overturned_creates_precedent(self) -> None:
        """Blocked proposal → appeal → overturned → precedent created."""
        const = Constitution()
        enforcer = BoundaryEnforcer(const)
        court = AppealsCourt()
        tracker = PrecedentTracker()

        # 1. Immutable proposal blocked
        proposal = _make_proposal(area=PolicyArea.GOVERNANCE)
        check = enforcer.check_proposal(proposal)
        assert not check.passed

        # 2. File appeal
        appeal = court.file_appeal(
            proposal.proposal_id, check, "matt",
            AppealGrounds.CHANGED_CIRCUMSTANCES,
            "circumstances have fundamentally changed",
        )

        # 3. Decide: overturned (exceptional)
        court.decide(
            appeal.appeal_id, "admin", AppealStatus.OVERTURNED,
            "extraordinary circumstances justify exception",
            conditions=["must create waiver", "time-bound to 24h"],
        )

        # 4. Record binding precedent
        p = tracker.record_precedent(
            decision_type=DecisionType.APPEAL_OVERTURNED,
            reference_id=appeal.appeal_id,
            policy_area=PolicyArea.GOVERNANCE,
            decision_summary="governance block overturned due to changed circumstances",
            reasoning="extraordinary + time-bounded exception",
            outcome="overturned",
            strength=PrecedentStrength.BINDING,
        )
        assert p.strength == PrecedentStrength.BINDING

        # 5. Future check: conflict exists
        conflicts = tracker.check_conflicts(PolicyArea.GOVERNANCE, "upheld")
        assert len(conflicts) == 1

    def test_emergency_to_review_to_precedent(self) -> None:
        """Emergency declared → activated → revoked → reviewed → precedent."""
        mgr = EmergencyPowersManager()
        tracker = PrecedentTracker()

        # 1. Declare and activate emergency
        decl = mgr.declare_emergency(
            "matt", "critical production outage",
            [PolicyArea.AUTONOMY, PolicyArea.ESCALATION],
            scope=EmergencyScope.MULTIPLE_AREAS,
            duration_hours=4,
        )
        mgr.activate(decl.declaration_id)
        assert decl.is_active

        # 2. Revoke after resolution
        mgr.revoke(decl.declaration_id)
        assert decl.needs_review

        # 3. Submit review
        mgr.submit_review(
            decl.declaration_id,
            reviewer="matt",
            actions_taken=["relaxed autonomy", "bypassed escalation"],
            justified=True,
            findings="actions were necessary and proportionate",
            recommendations=["update escalation thresholds"],
        )
        assert decl.status == EmergencyStatus.REVIEWED

        # 4. Record precedent
        tracker.record_precedent(
            decision_type=DecisionType.EMERGENCY_REVIEWED,
            reference_id=decl.declaration_id,
            policy_area=PolicyArea.AUTONOMY,
            decision_summary="emergency justified for production outage",
            reasoning="actions proportionate, reviewed and approved",
            outcome="justified",
            strength=PrecedentStrength.PERSUASIVE,
            tags=["production", "outage", "autonomy"],
        )
        assert len(tracker.find_precedents(tag="production")) == 1

    def test_full_adjudication_lifecycle(self) -> None:
        """Complete lifecycle: block → appeal → waiver → emergency → precedent chain."""
        const = Constitution()
        enforcer = BoundaryEnforcer(const)
        handler = ExceptionHandler(const)
        court = AppealsCourt()
        mgr = EmergencyPowersManager()
        tracker = PrecedentTracker()

        # 1. Proposal blocked
        proposal = _make_proposal(area=PolicyArea.GOVERNANCE, proposal_id="lifecycle-1")
        check = enforcer.check_proposal(proposal)
        assert not check.passed

        # 2. Appeal filed and upheld (block stands)
        appeal = court.file_appeal(
            proposal.proposal_id, check, "matt",
            AppealGrounds.DISPROPORTIONATE, "seems too strict",
        )
        court.decide(appeal.appeal_id, "admin", AppealStatus.UPHELD, "immutable is immutable")

        # 3. Record binding precedent
        _ = tracker.record_precedent(
            DecisionType.APPEAL_UPHELD, appeal.appeal_id, PolicyArea.GOVERNANCE,
            "governance block upheld", "immutable classification correct", "upheld",
            strength=PrecedentStrength.BINDING,
        )

        # 4. Emergency declared for different area
        decl = mgr.declare_emergency("matt", "escalation failure", [PolicyArea.ESCALATION])
        mgr.activate(decl.declaration_id)

        # 5. Waiver granted for restricted area during emergency
        waiver = handler.request_waiver(
            "art-003", "lifecycle-1", "emergency requires escalation change", "matt",
            scope=WaiverScope.TIME_BOUNDED, duration_hours=4,
        )
        handler.grant_waiver(waiver.waiver_id)

        # 6. Verify state
        assert court.appeal_count == 1
        assert handler.active_waiver_count == 1
        assert mgr.active_count == 1
        assert tracker.precedent_count == 1
        assert tracker.binding_count == 1
