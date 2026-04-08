"""V25 — constitutional transparency tests.

Tests for public docket, procedural timeline, notice service, and decision registry.
"""



# ═══════════════════════════════════════════════════════════════════════════════
# V25A: Public Docket Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestPublicDocket:
    """Tests for the public docket of constitutional proceedings."""

    def _make(self):
        from src.kortana.services.public_docket import PublicDocket
        return PublicDocket()

    def test_open_case(self):
        from src.kortana.services.public_docket import CaseStatus, CaseType
        d = self._make()
        e = d.open_case(CaseType.APPEAL, "Test appeal", ["alice", "bob"])
        assert e.case_type == CaseType.APPEAL
        assert e.status == CaseStatus.OPENED
        assert "alice" in e.parties
        assert d.case_count == 1

    def test_case_number_format(self):
        from src.kortana.services.public_docket import CaseType
        d = self._make()
        e = d.open_case(CaseType.APPEAL, "Appeal 1", ["alice"])
        assert e.case_number.startswith("APP-2026-")

    def test_update_status(self):
        from src.kortana.services.public_docket import CaseStatus, CaseType
        d = self._make()
        e = d.open_case(CaseType.WAIVER, "Waiver request", ["bob"])
        assert d.update_status(e.case_number, CaseStatus.IN_PROGRESS) is True
        assert e.status == CaseStatus.IN_PROGRESS

    def test_close_case(self):
        from src.kortana.services.public_docket import CaseStatus, CaseType
        d = self._make()
        e = d.open_case(CaseType.APPEAL, "Appeal to close", ["alice"])
        assert d.close_case(e.case_number, "Appeal upheld") is True
        assert e.status == CaseStatus.CLOSED
        assert e.outcome == "Appeal upheld"
        assert e.closed_at != ""

    def test_dismiss_case(self):
        from src.kortana.services.public_docket import CaseStatus, CaseType
        d = self._make()
        e = d.open_case(CaseType.EMERGENCY, "Emergency review", ["system"])
        assert d.dismiss_case(e.case_number, "No standing") is True
        assert e.status == CaseStatus.DISMISSED
        assert "Dismissed" in e.outcome

    def test_get_case(self):
        from src.kortana.services.public_docket import CaseType
        d = self._make()
        e = d.open_case(CaseType.APPEAL, "Find me", ["alice"])
        found = d.get_case(e.case_number)
        assert found is not None
        assert found.title == "Find me"

    def test_get_nonexistent_case(self):
        d = self._make()
        assert d.get_case("NONEXISTENT") is None

    def test_search_by_type(self):
        from src.kortana.services.public_docket import CaseType
        d = self._make()
        d.open_case(CaseType.APPEAL, "Appeal 1", ["a"])
        d.open_case(CaseType.WAIVER, "Waiver 1", ["b"])
        d.open_case(CaseType.APPEAL, "Appeal 2", ["c"])
        results = d.search(case_type=CaseType.APPEAL)
        assert len(results) == 2

    def test_search_by_party(self):
        from src.kortana.services.public_docket import CaseType
        d = self._make()
        d.open_case(CaseType.APPEAL, "A1", ["alice", "bob"])
        d.open_case(CaseType.WAIVER, "W1", ["charlie"])
        results = d.search(party="alice")
        assert len(results) == 1

    def test_search_by_query(self):
        from src.kortana.services.public_docket import CaseType
        d = self._make()
        d.open_case(CaseType.APPEAL, "Security policy dispute", ["alice"])
        d.open_case(CaseType.WAIVER, "Runtime exception", ["bob"])
        results = d.search(query="security")
        assert len(results) == 1

    def test_search_by_reference_id(self):
        from src.kortana.services.public_docket import CaseType
        d = self._make()
        d.open_case(CaseType.APPEAL, "A1", ["a"], reference_id="ref-123")
        d.open_case(CaseType.WAIVER, "W1", ["b"], reference_id="ref-456")
        results = d.search(reference_id="ref-123")
        assert len(results) == 1

    def test_open_count(self):
        from src.kortana.services.public_docket import CaseType
        d = self._make()
        e1 = d.open_case(CaseType.APPEAL, "A1", ["a"])
        d.open_case(CaseType.WAIVER, "W1", ["b"])
        d.close_case(e1.case_number, "Done")
        assert d.open_count == 1

    def test_docket_hash(self):
        from src.kortana.services.public_docket import CaseType
        d = self._make()
        e = d.open_case(CaseType.APPEAL, "A1", ["a"])
        assert len(e.docket_hash) == 16

    def test_to_dict(self):
        from src.kortana.services.public_docket import CaseType
        d = self._make()
        e = d.open_case(CaseType.APPEAL, "A1", ["alice"])
        data = e.to_dict()
        assert data["case_type"] == "appeal"
        assert data["status"] == "opened"
        assert "alice" in data["parties"]

    def test_summary(self):
        from src.kortana.services.public_docket import CaseType
        d = self._make()
        d.open_case(CaseType.APPEAL, "A1", ["a"])
        d.open_case(CaseType.WAIVER, "W1", ["b"])
        summary = d.get_summary()
        assert summary["total_cases"] == 2
        assert summary["open_cases"] == 2

    def test_module_singleton(self):
        from src.kortana.services.public_docket import get_public_docket
        d1 = get_public_docket()
        d2 = get_public_docket()
        assert d1 is d2


# ═══════════════════════════════════════════════════════════════════════════════
# V25B: Procedural Timeline Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestProceduralTimeline:
    """Tests for procedural timeline event logging."""

    def _make(self):
        from src.kortana.services.procedural_timeline import ProceduralTimeline
        return ProceduralTimeline()

    def test_record_event(self):
        from src.kortana.services.procedural_timeline import EventType
        t = self._make()
        e = t.record_event("CASE-001", EventType.CASE_OPENED, "system", "Case opened")
        assert e.case_number == "CASE-001"
        assert e.event_type == EventType.CASE_OPENED
        assert t.event_count == 1

    def test_timeline_chronological(self):
        from src.kortana.services.procedural_timeline import EventType
        t = self._make()
        t.record_event("CASE-001", EventType.CASE_OPENED, "system", "Opened")
        t.record_event("CASE-001", EventType.STANDING_CHECKED, "alice", "Standing OK")
        t.record_event("CASE-001", EventType.DEADLINE_CREATED, "system", "Deadline set")
        timeline = t.get_timeline("CASE-001")
        assert len(timeline) == 3
        # Should be chronological
        assert timeline[0].event_type == EventType.CASE_OPENED
        assert timeline[-1].event_type == EventType.DEADLINE_CREATED

    def test_timeline_filter_by_type(self):
        from src.kortana.services.procedural_timeline import EventType
        t = self._make()
        t.record_event("CASE-001", EventType.CASE_OPENED, "system", "Opened")
        t.record_event("CASE-001", EventType.STANDING_CHECKED, "alice", "OK")
        t.record_event("CASE-001", EventType.STANDING_CHECKED, "bob", "OK")
        timeline = t.get_timeline("CASE-001", event_type=EventType.STANDING_CHECKED)
        assert len(timeline) == 2

    def test_timeline_filter_by_actor(self):
        from src.kortana.services.procedural_timeline import EventType
        t = self._make()
        t.record_event("CASE-001", EventType.CASE_OPENED, "system", "Opened")
        t.record_event("CASE-001", EventType.STANDING_CHECKED, "alice", "OK")
        timeline = t.get_timeline("CASE-001", actor="alice")
        assert len(timeline) == 1

    def test_get_events_across_cases(self):
        from src.kortana.services.procedural_timeline import EventType
        t = self._make()
        t.record_event("CASE-001", EventType.CASE_OPENED, "system", "Opened 1")
        t.record_event("CASE-002", EventType.CASE_OPENED, "system", "Opened 2")
        events = t.get_events(event_type=EventType.CASE_OPENED)
        assert len(events) == 2

    def test_get_events_with_limit(self):
        from src.kortana.services.procedural_timeline import EventType
        t = self._make()
        for i in range(10):
            t.record_event(f"CASE-{i:03d}", EventType.CASE_OPENED, "system", f"Opened {i}")
        events = t.get_events(limit=5)
        assert len(events) == 5

    def test_extra_data(self):
        from src.kortana.services.procedural_timeline import EventType
        t = self._make()
        e = t.record_event("CASE-001", EventType.VOTE_CAST, "alice", "Voted yes",
                           extra_data={"vote": "approve", "weight": 1})
        assert e.extra_data["vote"] == "approve"

    def test_event_hash(self):
        from src.kortana.services.procedural_timeline import EventType
        t = self._make()
        e = t.record_event("CASE-001", EventType.CASE_OPENED, "system", "Opened")
        assert len(e.event_hash) == 16

    def test_to_dict(self):
        from src.kortana.services.procedural_timeline import EventType
        t = self._make()
        e = t.record_event("CASE-001", EventType.CASE_OPENED, "system", "Opened")
        data = e.to_dict()
        assert data["case_number"] == "CASE-001"
        assert data["event_type"] == "case_opened"

    def test_case_event_count(self):
        from src.kortana.services.procedural_timeline import EventType
        t = self._make()
        t.record_event("CASE-001", EventType.CASE_OPENED, "system", "A")
        t.record_event("CASE-001", EventType.STANDING_CHECKED, "alice", "B")
        t.record_event("CASE-002", EventType.CASE_OPENED, "system", "C")
        assert t.case_event_count("CASE-001") == 2

    def test_summary(self):
        from src.kortana.services.procedural_timeline import EventType
        t = self._make()
        t.record_event("CASE-001", EventType.CASE_OPENED, "system", "A")
        t.record_event("CASE-002", EventType.CASE_OPENED, "system", "B")
        summary = t.get_summary()
        assert summary["total_events"] == 2
        assert summary["distinct_cases"] == 2

    def test_module_singleton(self):
        from src.kortana.services.procedural_timeline import get_procedural_timeline
        t1 = get_procedural_timeline()
        t2 = get_procedural_timeline()
        assert t1 is t2


# ═══════════════════════════════════════════════════════════════════════════════
# V25C: Notice Service Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestNoticeService:
    """Tests for formal notice delivery and tracking."""

    def _make(self):
        from src.kortana.services.notice_service import NoticeService
        return NoticeService()

    def test_send_notice(self):
        from src.kortana.services.notice_service import DeliveryStatus, NoticeType
        svc = self._make()
        n = svc.send_notice("CASE-001", NoticeType.CASE_OPENED, "alice",
                            "Case opened", "You are a party")
        assert n.recipient == "alice"
        assert n.delivery_status == DeliveryStatus.PENDING
        assert svc.notice_count == 1

    def test_notify_parties(self):
        from src.kortana.services.notice_service import NoticeType
        svc = self._make()
        notices = svc.notify_parties("CASE-001", NoticeType.CASE_OPENED,
                                     ["alice", "bob", "charlie"],
                                     "Case opened", "You are all parties")
        assert len(notices) == 3
        assert svc.notice_count == 3

    def test_mark_delivered(self):
        from src.kortana.services.notice_service import DeliveryStatus, NoticeType
        svc = self._make()
        n = svc.send_notice("CASE-001", NoticeType.CASE_OPENED, "alice",
                            "Subj", "Body")
        assert svc.mark_delivered(n.notice_id) is True
        assert n.delivery_status == DeliveryStatus.DELIVERED
        assert n.delivered_at != ""

    def test_mark_acknowledged(self):
        from src.kortana.services.notice_service import DeliveryStatus, NoticeType
        svc = self._make()
        n = svc.send_notice("CASE-001", NoticeType.DECISION_RENDERED, "bob",
                            "Decision", "Upheld")
        svc.mark_delivered(n.notice_id)
        assert svc.mark_acknowledged(n.notice_id) is True
        assert n.delivery_status == DeliveryStatus.ACKNOWLEDGED
        assert n.acknowledged_at != ""

    def test_mark_acknowledged_from_pending(self):
        from src.kortana.services.notice_service import DeliveryStatus, NoticeType
        svc = self._make()
        n = svc.send_notice("CASE-001", NoticeType.CASE_OPENED, "alice",
                            "Subj", "Body")
        # Acknowledge directly from pending — should work and auto-set delivered
        assert svc.mark_acknowledged(n.notice_id) is True
        assert n.delivery_status == DeliveryStatus.ACKNOWLEDGED

    def test_mark_failed(self):
        from src.kortana.services.notice_service import DeliveryStatus, NoticeType
        svc = self._make()
        n = svc.send_notice("CASE-001", NoticeType.CASE_OPENED, "alice",
                            "Subj", "Body")
        assert svc.mark_failed(n.notice_id) is True
        assert n.delivery_status == DeliveryStatus.FAILED

    def test_get_notices_by_case(self):
        from src.kortana.services.notice_service import NoticeType
        svc = self._make()
        svc.send_notice("CASE-001", NoticeType.CASE_OPENED, "alice", "S", "B")
        svc.send_notice("CASE-002", NoticeType.CASE_OPENED, "bob", "S", "B")
        results = svc.get_notices(case_number="CASE-001")
        assert len(results) == 1

    def test_get_notices_by_recipient(self):
        from src.kortana.services.notice_service import NoticeType
        svc = self._make()
        svc.send_notice("CASE-001", NoticeType.CASE_OPENED, "alice", "S", "B")
        svc.send_notice("CASE-001", NoticeType.DECISION_RENDERED, "alice", "S", "B")
        svc.send_notice("CASE-001", NoticeType.CASE_OPENED, "bob", "S", "B")
        results = svc.get_notices(recipient="alice")
        assert len(results) == 2

    def test_get_unacknowledged(self):
        from src.kortana.services.notice_service import NoticeType
        svc = self._make()
        n1 = svc.send_notice("CASE-001", NoticeType.CASE_OPENED, "alice", "S", "B")
        svc.send_notice("CASE-001", NoticeType.CASE_OPENED, "bob", "S", "B")
        svc.mark_acknowledged(n1.notice_id)
        unack = svc.get_unacknowledged()
        assert len(unack) == 1
        assert unack[0].recipient == "bob"

    def test_get_unacknowledged_by_recipient(self):
        from src.kortana.services.notice_service import NoticeType
        svc = self._make()
        svc.send_notice("CASE-001", NoticeType.CASE_OPENED, "alice", "S", "B")
        svc.send_notice("CASE-001", NoticeType.CASE_OPENED, "bob", "S", "B")
        unack = svc.get_unacknowledged(recipient="alice")
        assert len(unack) == 1

    def test_notice_hash(self):
        from src.kortana.services.notice_service import NoticeType
        svc = self._make()
        n = svc.send_notice("CASE-001", NoticeType.CASE_OPENED, "alice", "S", "B")
        assert len(n.notice_hash) == 16

    def test_to_dict(self):
        from src.kortana.services.notice_service import NoticeType
        svc = self._make()
        n = svc.send_notice("CASE-001", NoticeType.CASE_OPENED, "alice",
                            "Subject", "Body text")
        data = n.to_dict()
        assert data["recipient"] == "alice"
        assert data["notice_type"] == "case_opened"
        assert data["delivery_status"] == "pending"

    def test_pending_count(self):
        from src.kortana.services.notice_service import NoticeType
        svc = self._make()
        n1 = svc.send_notice("CASE-001", NoticeType.CASE_OPENED, "alice", "S", "B")
        svc.send_notice("CASE-001", NoticeType.CASE_OPENED, "bob", "S", "B")
        svc.mark_delivered(n1.notice_id)
        assert svc.pending_count == 1

    def test_summary(self):
        from src.kortana.services.notice_service import NoticeType
        svc = self._make()
        svc.send_notice("CASE-001", NoticeType.CASE_OPENED, "alice", "S", "B")
        svc.send_notice("CASE-001", NoticeType.DECISION_RENDERED, "bob", "S", "B")
        summary = svc.get_summary()
        assert summary["total_notices"] == 2
        assert summary["pending"] == 2

    def test_module_singleton(self):
        from src.kortana.services.notice_service import get_notice_service
        s1 = get_notice_service()
        s2 = get_notice_service()
        assert s1 is s2


# ═══════════════════════════════════════════════════════════════════════════════
# V25D: Decision Registry Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestDecisionRegistry:
    """Tests for the searchable decision registry."""

    def _make(self):
        from src.kortana.services.decision_registry import DecisionRegistry
        return DecisionRegistry()

    def test_record_decision(self):
        from src.kortana.services.decision_registry import DecisionOutcome
        reg = self._make()
        d = reg.record_decision("CASE-001", "appeal", DecisionOutcome.UPHELD,
                                "Appeal upheld — policy was misapplied")
        assert d.case_number == "CASE-001"
        assert d.outcome == DecisionOutcome.UPHELD
        assert reg.decision_count == 1

    def test_get_decision(self):
        from src.kortana.services.decision_registry import DecisionOutcome
        reg = self._make()
        d = reg.record_decision("CASE-001", "appeal", DecisionOutcome.DENIED,
                                "No error found")
        found = reg.get_decision(d.decision_id)
        assert found is not None
        assert found.summary == "No error found"

    def test_get_by_case(self):
        from src.kortana.services.decision_registry import DecisionOutcome
        reg = self._make()
        reg.record_decision("CASE-001", "appeal", DecisionOutcome.UPHELD, "Upheld")
        reg.record_decision("CASE-001", "waiver", DecisionOutcome.GRANTED, "Granted")
        reg.record_decision("CASE-002", "appeal", DecisionOutcome.DENIED, "Denied")
        results = reg.get_by_case("CASE-001")
        assert len(results) == 2

    def test_search_by_type(self):
        from src.kortana.services.decision_registry import DecisionOutcome
        reg = self._make()
        reg.record_decision("C1", "appeal", DecisionOutcome.UPHELD, "S1")
        reg.record_decision("C2", "waiver", DecisionOutcome.GRANTED, "S2")
        results = reg.search(decision_type="appeal")
        assert len(results) == 1

    def test_search_by_outcome(self):
        from src.kortana.services.decision_registry import DecisionOutcome
        reg = self._make()
        reg.record_decision("C1", "appeal", DecisionOutcome.UPHELD, "S1")
        reg.record_decision("C2", "appeal", DecisionOutcome.DENIED, "S2")
        results = reg.search(outcome=DecisionOutcome.UPHELD)
        assert len(results) == 1

    def test_search_by_policy_area(self):
        from src.kortana.services.decision_registry import DecisionOutcome
        reg = self._make()
        reg.record_decision("C1", "appeal", DecisionOutcome.UPHELD, "S1",
                            policy_area="security")
        reg.record_decision("C2", "appeal", DecisionOutcome.DENIED, "S2",
                            policy_area="runtime")
        results = reg.search(policy_area="security")
        assert len(results) == 1

    def test_search_by_party(self):
        from src.kortana.services.decision_registry import DecisionOutcome
        reg = self._make()
        reg.record_decision("C1", "appeal", DecisionOutcome.UPHELD, "S1",
                            parties=["alice", "bob"])
        reg.record_decision("C2", "appeal", DecisionOutcome.DENIED, "S2",
                            parties=["charlie"])
        results = reg.search(party="alice")
        assert len(results) == 1

    def test_search_by_tag(self):
        from src.kortana.services.decision_registry import DecisionOutcome
        reg = self._make()
        reg.record_decision("C1", "appeal", DecisionOutcome.UPHELD, "S1",
                            tags=["landmark", "security"])
        reg.record_decision("C2", "appeal", DecisionOutcome.DENIED, "S2",
                            tags=["routine"])
        results = reg.search(tag="landmark")
        assert len(results) == 1

    def test_full_text_search(self):
        from src.kortana.services.decision_registry import DecisionOutcome
        reg = self._make()
        reg.record_decision("C1", "appeal", DecisionOutcome.UPHELD,
                            "Security policy was misapplied to runtime agent")
        reg.record_decision("C2", "waiver", DecisionOutcome.GRANTED,
                            "Temporary waiver for deployment window")
        results = reg.search(query="security")
        assert len(results) == 1

    def test_decision_hash(self):
        from src.kortana.services.decision_registry import DecisionOutcome
        reg = self._make()
        d = reg.record_decision("C1", "appeal", DecisionOutcome.UPHELD, "S")
        assert len(d.decision_hash) == 16

    def test_to_dict(self):
        from src.kortana.services.decision_registry import DecisionOutcome
        reg = self._make()
        d = reg.record_decision("C1", "appeal", DecisionOutcome.UPHELD, "Summary",
                                decided_by="judge-1", tags=["important"])
        data = d.to_dict()
        assert data["outcome"] == "upheld"
        assert data["decided_by"] == "judge-1"
        assert "important" in data["tags"]

    def test_summary(self):
        from src.kortana.services.decision_registry import DecisionOutcome
        reg = self._make()
        reg.record_decision("C1", "appeal", DecisionOutcome.UPHELD, "S1",
                            policy_area="security")
        reg.record_decision("C2", "waiver", DecisionOutcome.GRANTED, "S2",
                            policy_area="runtime")
        summary = reg.get_summary()
        assert summary["total_decisions"] == 2
        assert summary["by_type"]["appeal"] == 1
        assert summary["by_outcome"]["upheld"] == 1

    def test_module_singleton(self):
        from src.kortana.services.decision_registry import get_decision_registry
        r1 = get_decision_registry()
        r2 = get_decision_registry()
        assert r1 is r2


# ═══════════════════════════════════════════════════════════════════════════════
# V25 Pipeline: Cross-Component Integration
# ═══════════════════════════════════════════════════════════════════════════════


class TestV25Pipeline:
    """Integration tests for the constitutional transparency pipeline."""

    def test_full_transparency_pipeline(self):
        """End-to-end: open case → timeline events → notices → decision → close."""
        from src.kortana.services.decision_registry import (
            DecisionOutcome,
            DecisionRegistry,
        )
        from src.kortana.services.notice_service import NoticeService, NoticeType
        from src.kortana.services.procedural_timeline import (
            EventType,
            ProceduralTimeline,
        )
        from src.kortana.services.public_docket import (
            CaseStatus,
            CaseType,
            PublicDocket,
        )

        docket = PublicDocket()
        timeline = ProceduralTimeline()
        notices = NoticeService()
        decisions = DecisionRegistry()

        # Step 1: Open case on public docket
        case = docket.open_case(
            CaseType.APPEAL, "Policy classification appeal",
            ["appellant-alice", "respondent-system"],
            policy_area="security",
            reference_id="appeal-789",
        )

        # Step 2: Record case opening in timeline
        timeline.record_event(case.case_number, EventType.CASE_OPENED,
                              "system", "Case docketed")

        # Step 3: Notify all parties
        sent = notices.notify_parties(
            case.case_number, NoticeType.CASE_OPENED,
            case.parties, "Case Opened", f"Case {case.case_number} has been opened",
        )
        assert len(sent) == 2

        # Step 4: Standing check recorded
        timeline.record_event(case.case_number, EventType.STANDING_CHECKED,
                              "appellant-alice", "Standing confirmed for appeal")

        # Step 5: Update status to in-progress
        docket.update_status(case.case_number, CaseStatus.IN_PROGRESS)
        timeline.record_event(case.case_number, EventType.STATUS_CHANGED,
                              "system", "Status → in_progress")

        # Step 6: Decision rendered
        decisions.record_decision(
            case.case_number, "appeal", DecisionOutcome.UPHELD,
            "The security classification was found to be incorrect",
            policy_area="security",
            parties=case.parties,
            decided_by="constitutional-authority",
            tags=["security", "classification"],
        )
        timeline.record_event(case.case_number, EventType.DECISION_RENDERED,
                              "constitutional-authority", "Appeal upheld")

        # Step 7: Notify of decision
        notices.notify_parties(
            case.case_number, NoticeType.DECISION_RENDERED,
            case.parties, "Decision Rendered",
            f"Case {case.case_number}: appeal upheld",
        )

        # Step 8: Close case
        docket.close_case(case.case_number, "Appeal upheld")
        timeline.record_event(case.case_number, EventType.CASE_CLOSED,
                              "system", "Case closed")

        # Verify complete record
        assert case.status == CaseStatus.CLOSED
        full_timeline = timeline.get_timeline(case.case_number)
        assert len(full_timeline) == 5  # opened, standing, status, decision, closed
        assert notices.notice_count == 4  # 2 opening + 2 decision
        assert decisions.decision_count == 1
        case_decisions = decisions.get_by_case(case.case_number)
        assert len(case_decisions) == 1
        assert case_decisions[0].outcome == DecisionOutcome.UPHELD

    def test_docket_searchable_after_close(self):
        """Closed cases should still be searchable in the docket."""
        from src.kortana.services.public_docket import (
            CaseStatus,
            CaseType,
            PublicDocket,
        )

        docket = PublicDocket()
        e = docket.open_case(CaseType.WAIVER, "Waiver for deploy", ["ops-team"],
                             policy_area="deployment")
        docket.close_case(e.case_number, "Waiver granted")

        # Should still find it
        results = docket.search(case_type=CaseType.WAIVER)
        assert len(results) == 1
        results = docket.search(status=CaseStatus.CLOSED)
        assert len(results) == 1
        results = docket.search(query="deploy")
        assert len(results) == 1

    def test_timeline_reconstructs_procedure(self):
        """Timeline should reconstruct the full procedural history."""
        from src.kortana.services.procedural_timeline import (
            EventType,
            ProceduralTimeline,
        )

        timeline = ProceduralTimeline()
        cn = "TEST-CASE-001"

        # Simulate a full procedure
        events = [
            (EventType.CASE_OPENED, "system", "Opened"),
            (EventType.STANDING_CHECKED, "alice", "Standing OK"),
            (EventType.DEADLINE_CREATED, "system", "48h deadline"),
            (EventType.REVIEW_STARTED, "judge", "Review begun"),
            (EventType.DECISION_RENDERED, "judge", "Decided"),
            (EventType.REASONING_PUBLISHED, "judge", "Reasoning filed"),
            (EventType.NOTICE_SENT, "system", "All parties notified"),
            (EventType.CASE_CLOSED, "system", "Closed"),
        ]

        for et, actor, desc in events:
            timeline.record_event(cn, et, actor, desc)

        full = timeline.get_timeline(cn)
        assert len(full) == 8
        assert full[0].event_type == EventType.CASE_OPENED
        assert full[-1].event_type == EventType.CASE_CLOSED

    def test_notice_tracking_completeness(self):
        """All notices should be trackable from send to acknowledge."""
        from src.kortana.services.notice_service import NoticeService, NoticeType

        svc = NoticeService()
        parties = ["alice", "bob", "charlie"]

        notices = svc.notify_parties("CASE-X", NoticeType.CASE_OPENED,
                                     parties, "Case Filed", "Review required")

        # All pending initially
        assert svc.pending_count == 3

        # Deliver to alice and bob
        svc.mark_delivered(notices[0].notice_id)
        svc.mark_delivered(notices[1].notice_id)
        assert svc.pending_count == 1

        # Alice acknowledges
        svc.mark_acknowledged(notices[0].notice_id)
        assert svc.acknowledged_count == 1

        # Charlie's delivery fails
        svc.mark_failed(notices[2].notice_id)

        # Check unacknowledged
        unack = svc.get_unacknowledged()
        # bob (delivered but not acknowledged) + charlie (failed)
        assert len(unack) == 2

    def test_decision_registry_full_text(self):
        """Decisions should be searchable by summary text and tags."""
        from src.kortana.services.decision_registry import (
            DecisionOutcome,
            DecisionRegistry,
        )

        reg = DecisionRegistry()
        reg.record_decision("C1", "appeal", DecisionOutcome.UPHELD,
                            "Security policy improperly applied to runtime agent",
                            policy_area="security",
                            cited_articles=["article-2", "article-5"],
                            tags=["landmark", "security-policy"])
        reg.record_decision("C2", "waiver", DecisionOutcome.GRANTED,
                            "Emergency deployment window exception",
                            policy_area="deployment",
                            tags=["routine"])

        # Search by text
        assert len(reg.search(query="runtime")) == 1
        assert len(reg.search(query="deployment")) == 1
        # Search by tag
        assert len(reg.search(tag="landmark")) == 1
        # Search by area
        assert len(reg.search(policy_area="security")) == 1
