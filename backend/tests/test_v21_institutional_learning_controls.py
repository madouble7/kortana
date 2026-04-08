"""V21 — institutional learning controls tests."""

from __future__ import annotations

import sys
sys.path.insert(0, "src")

from kortana.services.proposal_registry import (
    ProposalRegistry,
    ProposalStatus,
    get_proposal_registry,
)
from kortana.services.approval_gate import (
    ApprovalGate,
    ApprovalPolicy,
    DecisionType,
    get_approval_gate,
)
from kortana.services.policy_rollback import (
    PolicyRollback,
    get_policy_rollback,
)
from kortana.services.evolution_observer import (
    EvolutionObserver,
    EventType,
    EvolutionEvent,
    get_evolution_observer,
)
from kortana.services.policy_feedback_loop import (
    PolicyAmendment,
    AmendmentStatus,
    PolicyArea,
)
from kortana.services.trust_calibrator import TrustLevel


def _make_amendment(
    confidence: float = 0.8,
    area: PolicyArea = PolicyArea.ROLLOUT,
) -> PolicyAmendment:
    """Helper to create a test amendment."""
    return PolicyAmendment(
        amendment_id="amend-test-001",
        policy_area=area,
        current_rule="rollout in 30 min windows",
        proposed_rule="rollout in 20 min windows",
        justification="faster rollouts reduce exposure",
        confidence=confidence,
        evidence_count=12,
        status=AmendmentStatus.PENDING,
    )


# ═══ V21A: Proposal Registry ═══


class TestProposalRegistry:
    """Tests for proposal lifecycle management."""

    def test_create_proposal_from_amendment(self) -> None:
        reg = ProposalRegistry()
        amendment = _make_amendment()
        proposal = reg.create_proposal(amendment)
        assert proposal.status == ProposalStatus.DRAFT
        assert proposal.source_amendment_id == "amend-test-001"
        assert proposal.policy_area == PolicyArea.ROLLOUT
        assert proposal.proposal_id.startswith("prop-")

    def test_create_proposal_direct(self) -> None:
        reg = ProposalRegistry()
        proposal = reg.create_proposal_direct(
            policy_area=PolicyArea.AUTONOMY,
            current_rule="manual approval required",
            proposed_rule="auto-approve above 0.9 confidence",
            justification="high trust earned",
        )
        assert proposal.status == ProposalStatus.DRAFT
        assert proposal.source_amendment_id == "manual"

    def test_full_lifecycle_happy_path(self) -> None:
        reg = ProposalRegistry()
        amendment = _make_amendment()
        p = reg.create_proposal(amendment)
        pid = p.proposal_id

        assert reg.submit_proposal(pid)
        assert reg.get_proposal(pid).status == ProposalStatus.SUBMITTED

        assert reg.begin_review(pid)
        assert reg.get_proposal(pid).status == ProposalStatus.UNDER_REVIEW

        assert reg.mark_approved(pid, reviewer="matt", notes="looks good")
        assert reg.get_proposal(pid).status == ProposalStatus.APPROVED
        assert reg.get_proposal(pid).reviewer == "matt"

        assert reg.promote(pid)
        assert reg.get_proposal(pid).status == ProposalStatus.PROMOTED
        assert reg.get_proposal(pid).promoted_at != ""

    def test_invalid_transition_fails(self) -> None:
        reg = ProposalRegistry()
        p = reg.create_proposal(_make_amendment())
        # Cannot approve from DRAFT (must go through SUBMITTED → UNDER_REVIEW)
        assert not reg.mark_approved(p.proposal_id)

    def test_withdraw_from_draft(self) -> None:
        reg = ProposalRegistry()
        p = reg.create_proposal(_make_amendment())
        assert reg.withdraw(p.proposal_id)
        assert reg.get_proposal(p.proposal_id).status == ProposalStatus.WITHDRAWN

    def test_withdraw_from_submitted(self) -> None:
        reg = ProposalRegistry()
        p = reg.create_proposal(_make_amendment())
        reg.submit_proposal(p.proposal_id)
        assert reg.withdraw(p.proposal_id)

    def test_reject_from_review(self) -> None:
        reg = ProposalRegistry()
        p = reg.create_proposal(_make_amendment())
        reg.submit_proposal(p.proposal_id)
        reg.begin_review(p.proposal_id)
        assert reg.mark_rejected(p.proposal_id, reviewer="matt", notes="not ready")
        assert reg.get_proposal(p.proposal_id).status == ProposalStatus.REJECTED

    def test_list_proposals_by_status(self) -> None:
        reg = ProposalRegistry()
        reg.create_proposal(_make_amendment())
        p2 = reg.create_proposal(_make_amendment())
        reg.submit_proposal(p2.proposal_id)
        assert len(reg.list_proposals(ProposalStatus.DRAFT)) == 1
        assert len(reg.list_proposals(ProposalStatus.SUBMITTED)) == 1
        assert len(reg.list_proposals()) == 2

    def test_get_proposals_by_area(self) -> None:
        reg = ProposalRegistry()
        reg.create_proposal(_make_amendment(area=PolicyArea.ROLLOUT))
        reg.create_proposal(_make_amendment(area=PolicyArea.AUTONOMY))
        assert len(reg.get_proposals_by_area(PolicyArea.ROLLOUT)) == 1

    def test_history_records_transitions(self) -> None:
        reg = ProposalRegistry()
        p = reg.create_proposal(_make_amendment())
        reg.submit_proposal(p.proposal_id)
        history = reg.get_history()
        assert len(history) >= 2
        assert history[0]["action"] == "created"
        assert history[1]["action"] == "transition"

    def test_proposal_hash(self) -> None:
        reg = ProposalRegistry()
        p = reg.create_proposal(_make_amendment())
        assert len(p.proposal_hash) == 16

    def test_proposal_to_dict(self) -> None:
        reg = ProposalRegistry()
        p = reg.create_proposal(_make_amendment())
        d = p.to_dict()
        assert "proposal_id" in d
        assert "status" in d
        assert d["status"] == "draft"

    def test_module_singleton(self) -> None:
        r1 = get_proposal_registry()
        r2 = get_proposal_registry()
        assert r1 is r2

    def test_cannot_promote_rejected(self) -> None:
        reg = ProposalRegistry()
        p = reg.create_proposal(_make_amendment())
        reg.submit_proposal(p.proposal_id)
        reg.begin_review(p.proposal_id)
        reg.mark_rejected(p.proposal_id)
        assert not reg.promote(p.proposal_id)


# ═══ V21B: Approval Gate ═══


class TestApprovalGate:
    """Tests for the approval gate between suggest and accept."""

    def test_auto_approve_high_confidence_high_trust(self) -> None:
        gate = ApprovalGate()
        reg = ProposalRegistry()
        p = reg.create_proposal(_make_amendment(confidence=0.9))
        decision = gate.evaluate(p, TrustLevel.AUTONOMOUS)
        assert decision.approved
        assert decision.decision_type == DecisionType.AUTO

    def test_requires_human_low_confidence(self) -> None:
        gate = ApprovalGate()
        reg = ProposalRegistry()
        p = reg.create_proposal(_make_amendment(confidence=0.3))
        decision = gate.evaluate(p, TrustLevel.AUTONOMOUS)
        assert not decision.approved
        assert decision.decision_type == DecisionType.HUMAN

    def test_requires_human_low_trust(self) -> None:
        gate = ApprovalGate()
        reg = ProposalRegistry()
        p = reg.create_proposal(_make_amendment(confidence=0.9))
        decision = gate.evaluate(p, TrustLevel.PROVISIONAL)
        assert not decision.approved

    def test_max_auto_approve_per_cycle(self) -> None:
        gate = ApprovalGate()
        gate.set_policy(ApprovalPolicy(max_auto_approve_per_cycle=2))
        reg = ProposalRegistry()

        for _ in range(3):
            p = reg.create_proposal(_make_amendment(confidence=0.9))
            gate.evaluate(p, TrustLevel.AUTONOMOUS)

        # Third should be denied (limit = 2)
        assert gate.get_auto_approve_count() == 2

    def test_reset_cycle(self) -> None:
        gate = ApprovalGate()
        reg = ProposalRegistry()
        p = reg.create_proposal(_make_amendment(confidence=0.9))
        gate.evaluate(p, TrustLevel.AUTONOMOUS)
        assert gate.get_auto_approve_count() == 1
        gate.reset_cycle()
        assert gate.get_auto_approve_count() == 0

    def test_manual_approve(self) -> None:
        gate = ApprovalGate()
        decision = gate.approve_manual("prop-test", decided_by="matt", reason="approved by me")
        assert decision.approved
        assert decision.decision_type == DecisionType.HUMAN
        assert decision.decided_by == "matt"

    def test_manual_reject(self) -> None:
        gate = ApprovalGate()
        decision = gate.reject_manual("prop-test", decided_by="matt", reason="not ready")
        assert not decision.approved

    def test_get_decisions_filtered(self) -> None:
        gate = ApprovalGate()
        gate.approve_manual("prop-1")
        gate.reject_manual("prop-2")
        assert len(gate.get_decisions("prop-1")) == 1
        assert len(gate.get_decisions()) == 2

    def test_set_custom_policy(self) -> None:
        gate = ApprovalGate()
        policy = ApprovalPolicy(min_confidence=0.5, min_trust_level=TrustLevel.TRUSTED)
        gate.set_policy(policy)
        assert gate.get_policy().min_confidence == 0.5

    def test_decision_hash(self) -> None:
        gate = ApprovalGate()
        d = gate.approve_manual("prop-test")
        assert len(d.decision_hash) == 16

    def test_decision_to_dict(self) -> None:
        gate = ApprovalGate()
        d = gate.approve_manual("prop-test")
        dd = d.to_dict()
        assert "decision_id" in dd
        assert dd["approved"] is True

    def test_module_singleton(self) -> None:
        g1 = get_approval_gate()
        g2 = get_approval_gate()
        assert g1 is g2


# ═══ V21C: Policy Rollback ═══


class TestPolicyRollback:
    """Tests for reversible policy changes."""

    def test_create_rollback_point(self) -> None:
        rb = PolicyRollback()
        point = rb.create_point("prop-1", {"rule": "old"}, {"rule": "new"})
        assert point.proposal_id == "prop-1"
        assert point.prior_state == {"rule": "old"}
        assert not point.rolled_back

    def test_execute_rollback(self) -> None:
        rb = PolicyRollback()
        point = rb.create_point("prop-1", {"rule": "old"}, {"rule": "new"})
        result = rb.rollback(point.point_id, reason="regression detected")
        assert result is not None
        assert result.rolled_back
        assert result.rollback_reason == "regression detected"

    def test_cannot_rollback_twice(self) -> None:
        rb = PolicyRollback()
        point = rb.create_point("prop-1", {"rule": "old"}, {"rule": "new"})
        rb.rollback(point.point_id)
        assert rb.rollback(point.point_id) is None

    def test_can_rollback_check(self) -> None:
        rb = PolicyRollback()
        point = rb.create_point("prop-1", {"rule": "old"}, {"rule": "new"})
        assert rb.can_rollback(point.point_id)
        rb.rollback(point.point_id)
        assert not rb.can_rollback(point.point_id)

    def test_get_active_points(self) -> None:
        rb = PolicyRollback()
        p1 = rb.create_point("prop-1", {"rule": "a"}, {"rule": "b"})
        rb.create_point("prop-2", {"rule": "c"}, {"rule": "d"})
        rb.rollback(p1.point_id)
        assert rb.active_count == 1
        assert rb.point_count == 2

    def test_get_point_for_proposal(self) -> None:
        rb = PolicyRollback()
        rb.create_point("prop-1", {"rule": "old"}, {"rule": "new"})
        point = rb.get_point_for_proposal("prop-1")
        assert point is not None
        assert point.proposal_id == "prop-1"

    def test_nonexistent_rollback(self) -> None:
        rb = PolicyRollback()
        assert rb.rollback("fake-id") is None
        assert not rb.can_rollback("fake-id")

    def test_rollback_history(self) -> None:
        rb = PolicyRollback()
        point = rb.create_point("prop-1", {"rule": "old"}, {"rule": "new"})
        rb.rollback(point.point_id)
        history = rb.get_history()
        assert len(history) == 2
        assert history[0]["action"] == "created"
        assert history[1]["action"] == "rolled_back"

    def test_rollback_hash(self) -> None:
        rb = PolicyRollback()
        point = rb.create_point("prop-1", {"a": 1}, {"b": 2})
        assert len(point.rollback_hash) == 16

    def test_rollback_to_dict(self) -> None:
        rb = PolicyRollback()
        point = rb.create_point("prop-1", {"a": 1}, {"b": 2})
        d = point.to_dict()
        assert "point_id" in d
        assert d["rolled_back"] is False

    def test_module_singleton(self) -> None:
        r1 = get_policy_rollback()
        r2 = get_policy_rollback()
        assert r1 is r2


# ═══ V21D: Evolution Observer ═══


class TestEvolutionObserver:
    """Tests for observable evolution timeline."""

    def test_emit_event(self) -> None:
        obs = EvolutionObserver()
        event = obs.emit(EventType.PROPOSAL_CREATED, "prop-1", {"source": "test"})
        assert event.event_type == EventType.PROPOSAL_CREATED
        assert event.subject_id == "prop-1"
        assert obs.event_count == 1

    def test_timeline_ordering(self) -> None:
        obs = EvolutionObserver()
        obs.emit(EventType.PROPOSAL_CREATED, "prop-1")
        obs.emit(EventType.PROPOSAL_SUBMITTED, "prop-1")
        obs.emit(EventType.PROPOSAL_APPROVED, "prop-1")
        timeline = obs.get_timeline()
        assert len(timeline) == 3
        assert timeline[0].event_type == EventType.PROPOSAL_CREATED
        assert timeline[2].event_type == EventType.PROPOSAL_APPROVED

    def test_timeline_limit(self) -> None:
        obs = EvolutionObserver()
        for _ in range(5):
            obs.emit(EventType.PROPOSAL_CREATED, "prop-x")
        assert len(obs.get_timeline(limit=3)) == 3

    def test_events_by_type(self) -> None:
        obs = EvolutionObserver()
        obs.emit(EventType.PROPOSAL_CREATED, "prop-1")
        obs.emit(EventType.ROLLBACK_EXECUTED, "rb-1")
        obs.emit(EventType.PROPOSAL_CREATED, "prop-2")
        created = obs.get_events_by_type(EventType.PROPOSAL_CREATED)
        assert len(created) == 2

    def test_events_for_subject(self) -> None:
        obs = EvolutionObserver()
        obs.emit(EventType.PROPOSAL_CREATED, "prop-1")
        obs.emit(EventType.PROPOSAL_SUBMITTED, "prop-1")
        obs.emit(EventType.PROPOSAL_CREATED, "prop-2")
        events = obs.get_events_for_subject("prop-1")
        assert len(events) == 2

    def test_audit_trail(self) -> None:
        obs = EvolutionObserver()
        obs.emit(EventType.PROPOSAL_CREATED, "prop-1")
        obs.emit(EventType.APPROVAL_AUTO, "prop-1")
        obs.emit(EventType.PROPOSAL_PROMOTED, "prop-1")
        audit = obs.get_audit_trail()
        assert audit["total_events"] == 3
        assert audit["unique_subjects"] == 1
        assert "proposal_created" in audit["event_type_counts"]

    def test_subscribe_and_notify(self) -> None:
        obs = EvolutionObserver()
        received: list[EvolutionEvent] = []
        sub_id = obs.subscribe(lambda e: received.append(e))
        obs.emit(EventType.PROPOSAL_CREATED, "prop-1")
        assert len(received) == 1
        assert received[0].event_type == EventType.PROPOSAL_CREATED
        assert obs.subscriber_count == 1
        obs.unsubscribe(sub_id)
        assert obs.subscriber_count == 0

    def test_unsubscribe_nonexistent(self) -> None:
        obs = EvolutionObserver()
        assert not obs.unsubscribe("fake-id")

    def test_event_hash(self) -> None:
        obs = EvolutionObserver()
        event = obs.emit(EventType.PROPOSAL_CREATED, "prop-1")
        assert len(event.event_hash) == 16

    def test_event_to_dict(self) -> None:
        obs = EvolutionObserver()
        event = obs.emit(EventType.ROLLBACK_CREATED, "rb-1", {"proposal_id": "prop-1"})
        d = event.to_dict()
        assert d["event_type"] == "rollback_created"
        assert d["subject_id"] == "rb-1"

    def test_module_singleton(self) -> None:
        o1 = get_evolution_observer()
        o2 = get_evolution_observer()
        assert o1 is o2


# ═══ Integration: Full V21 Pipeline ═══


class TestV21Pipeline:
    """Integration tests: proposal → approval → promote → observe → rollback."""

    def test_full_pipeline(self) -> None:
        """End-to-end: create proposal, evaluate, approve, promote, observe, rollback."""
        reg = ProposalRegistry()
        gate = ApprovalGate()
        rb = PolicyRollback()
        obs = EvolutionObserver()

        # 1. Create proposal from amendment
        amendment = _make_amendment(confidence=0.9)
        proposal = reg.create_proposal(amendment)
        obs.emit(EventType.PROPOSAL_CREATED, proposal.proposal_id)

        # 2. Submit and review
        reg.submit_proposal(proposal.proposal_id)
        obs.emit(EventType.PROPOSAL_SUBMITTED, proposal.proposal_id)
        reg.begin_review(proposal.proposal_id)
        obs.emit(EventType.REVIEW_STARTED, proposal.proposal_id)

        # 3. Evaluate approval
        decision = gate.evaluate(proposal, TrustLevel.AUTONOMOUS)
        assert decision.approved  # High confidence + high trust

        # 4. Approve and promote
        reg.mark_approved(proposal.proposal_id, reviewer="system")
        obs.emit(EventType.PROPOSAL_APPROVED, proposal.proposal_id)

        point = rb.create_point(
            proposal.proposal_id,
            {"rule": proposal.current_rule},
            {"rule": proposal.proposed_rule},
        )
        obs.emit(EventType.ROLLBACK_CREATED, point.point_id)

        reg.promote(proposal.proposal_id)
        obs.emit(EventType.PROPOSAL_PROMOTED, proposal.proposal_id)

        assert reg.get_proposal(proposal.proposal_id).status == ProposalStatus.PROMOTED

        # 5. Verify timeline
        timeline = obs.get_timeline()
        assert len(timeline) == 6
        types = [e.event_type for e in timeline]
        assert EventType.PROPOSAL_CREATED in types
        assert EventType.PROPOSAL_PROMOTED in types

        # 6. Rollback
        assert rb.can_rollback(point.point_id)
        rolled = rb.rollback(point.point_id, reason="regression")
        obs.emit(EventType.ROLLBACK_EXECUTED, point.point_id)
        assert rolled.rolled_back
        assert not rb.can_rollback(point.point_id)

        # 7. Audit
        audit = obs.get_audit_trail()
        assert audit["total_events"] == 7
        assert audit["unique_subjects"] == 2  # proposal + rollback point

    def test_pipeline_with_human_rejection(self) -> None:
        """Proposal rejected by human after low-confidence evaluation."""
        reg = ProposalRegistry()
        gate = ApprovalGate()
        obs = EvolutionObserver()

        amendment = _make_amendment(confidence=0.3)
        proposal = reg.create_proposal(amendment)
        obs.emit(EventType.PROPOSAL_CREATED, proposal.proposal_id)

        reg.submit_proposal(proposal.proposal_id)
        reg.begin_review(proposal.proposal_id)

        # Low confidence → requires human
        decision = gate.evaluate(proposal, TrustLevel.TRUSTED)
        assert not decision.approved

        # Human rejects
        reg.mark_rejected(proposal.proposal_id, reviewer="matt", notes="not enough evidence")
        obs.emit(EventType.PROPOSAL_REJECTED, proposal.proposal_id)

        assert reg.get_proposal(proposal.proposal_id).status == ProposalStatus.REJECTED
        assert obs.event_count == 2

    def test_pipeline_withdraw_approved(self) -> None:
        """Withdraw an approved-but-not-promoted proposal."""
        reg = ProposalRegistry()
        p = reg.create_proposal(_make_amendment())
        reg.submit_proposal(p.proposal_id)
        reg.begin_review(p.proposal_id)
        reg.mark_approved(p.proposal_id)
        assert reg.withdraw(p.proposal_id)
        assert reg.get_proposal(p.proposal_id).status == ProposalStatus.WITHDRAWN
