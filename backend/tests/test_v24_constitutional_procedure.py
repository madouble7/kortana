"""V24 — constitutional procedure tests.

Tests for standing rules, deadline clock, recusal manager, and reasoning templates.
"""

from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════════
# V24A: Standing Rules Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestStandingRules:
    """Tests for standing rules — who may take procedural actions."""

    def _make(self):
        from src.kortana.services.standing_rules import StandingRules
        return StandingRules(load_defaults=True)

    def test_default_rules_loaded(self):
        s = self._make()
        assert s.rule_count == 5

    def test_register_actor(self):
        from src.kortana.services.standing_rules import ActorRole
        s = self._make()
        s.register_actor("alice", ActorRole.CONSTITUTIONAL_AUTHORITY)
        assert s.get_actor_role("alice") == ActorRole.CONSTITUTIONAL_AUTHORITY
        assert s.actor_count == 1

    def test_unregistered_actor_defaults_to_observer(self):
        from src.kortana.services.standing_rules import ActorRole
        s = self._make()
        assert s.get_actor_role("unknown") == ActorRole.OBSERVER

    def test_constitutional_authority_full_standing(self):
        from src.kortana.services.standing_rules import ActionType, ActorRole
        s = self._make()
        s.register_actor("matt", ActorRole.CONSTITUTIONAL_AUTHORITY)
        for action in ActionType:
            result = s.check_standing("matt", action)
            assert result.allowed is True, f"CA should have standing for {action.value}"

    def test_operator_limited_standing(self):
        from src.kortana.services.standing_rules import ActionType, ActorRole
        s = self._make()
        s.register_actor("bob", ActorRole.OPERATOR)
        # Operators can file appeals and cast votes
        r1 = s.check_standing("bob", ActionType.FILE_APPEAL)
        assert r1.allowed is True
        r2 = s.check_standing("bob", ActionType.CAST_VOTE)
        assert r2.allowed is True
        # But cannot declare emergencies
        r3 = s.check_standing("bob", ActionType.DECLARE_EMERGENCY)
        assert r3.allowed is False

    def test_observer_no_standing(self):
        from src.kortana.services.standing_rules import ActionType, ActorRole
        s = self._make()
        s.register_actor("viewer", ActorRole.OBSERVER)
        for action in ActionType:
            result = s.check_standing("viewer", action)
            assert result.allowed is False, f"Observer should not have standing for {action.value}"

    def test_senior_operator_standing(self):
        from src.kortana.services.standing_rules import ActionType, ActorRole
        s = self._make()
        s.register_actor("senior", ActorRole.SENIOR_OPERATOR)
        assert s.check_standing("senior", ActionType.FILE_APPEAL).allowed is True
        assert s.check_standing("senior", ActionType.REQUEST_WAIVER).allowed is True
        assert s.check_standing("senior", ActionType.CAST_VOTE).allowed is True
        assert s.check_standing("senior", ActionType.REVIEW_DECISION).allowed is True
        # Cannot grant waivers or declare emergencies
        assert s.check_standing("senior", ActionType.GRANT_WAIVER).allowed is False
        assert s.check_standing("senior", ActionType.DECLARE_EMERGENCY).allowed is False

    def test_system_role_standing(self):
        from src.kortana.services.standing_rules import ActionType, ActorRole
        s = self._make()
        s.register_actor("system-agent", ActorRole.SYSTEM)
        assert s.check_standing("system-agent", ActionType.DECLARE_EMERGENCY).allowed is True
        assert s.check_standing("system-agent", ActionType.RECORD_PRECEDENT).allowed is True
        assert s.check_standing("system-agent", ActionType.FILE_APPEAL).allowed is False

    def test_check_history_tracked(self):
        from src.kortana.services.standing_rules import ActionType, ActorRole
        s = self._make()
        s.register_actor("alice", ActorRole.OPERATOR)
        s.check_standing("alice", ActionType.FILE_APPEAL)
        s.check_standing("alice", ActionType.DECLARE_EMERGENCY)
        assert s.check_count == 2
        checks = s.get_checks("alice")
        assert len(checks) == 2

    def test_standing_rule_hash(self):
        from src.kortana.services.standing_rules import (
            ActionType,
            ActorRole,
            StandingRule,
        )
        rule = StandingRule(
            rule_id="test-rule",
            role=ActorRole.OPERATOR,
            allowed_actions=[ActionType.FILE_APPEAL],
        )
        assert len(rule.rule_hash) == 16

    def test_standing_result_to_dict(self):
        from src.kortana.services.standing_rules import ActionType, ActorRole
        s = self._make()
        s.register_actor("alice", ActorRole.OPERATOR)
        result = s.check_standing("alice", ActionType.FILE_APPEAL)
        d = result.to_dict()
        assert d["allowed"] is True
        assert d["actor"] == "alice"
        assert d["role"] == "operator"
        assert d["action"] == "file_appeal"

    def test_summary(self):
        from src.kortana.services.standing_rules import ActionType, ActorRole
        s = self._make()
        s.register_actor("a", ActorRole.OPERATOR)
        s.register_actor("b", ActorRole.OBSERVER)
        s.check_standing("a", ActionType.FILE_APPEAL)
        s.check_standing("b", ActionType.FILE_APPEAL)
        summary = s.get_summary()
        assert summary["total_rules"] == 5
        assert summary["registered_actors"] == 2
        assert summary["total_checks"] == 2
        assert summary["allowed_checks"] == 1
        assert summary["denied_checks"] == 1

    def test_add_custom_rule(self):
        from src.kortana.services.standing_rules import (
            ActionType,
            ActorRole,
            StandingRule,
        )
        s = self._make()
        custom = StandingRule(
            rule_id="custom",
            role=ActorRole.OBSERVER,
            allowed_actions=[ActionType.FILE_APPEAL],
            description="Custom observer rule",
        )
        s.add_rule(custom)
        s.register_actor("viewer", ActorRole.OBSERVER)
        result = s.check_standing("viewer", ActionType.FILE_APPEAL)
        assert result.allowed is True

    def test_area_restricted_rule(self):
        from src.kortana.services.standing_rules import (
            ActionType,
            ActorRole,
            StandingRule,
        )
        s = self._make()
        restricted = StandingRule(
            rule_id="restricted",
            role=ActorRole.OPERATOR,
            allowed_actions=[ActionType.FILE_APPEAL],
            restricted_areas=["security"],
        )
        s.add_rule(restricted)
        s.register_actor("bob", ActorRole.OPERATOR)
        # Has standing in restricted area
        r1 = s.check_standing("bob", ActionType.FILE_APPEAL, policy_area="security")
        assert r1.allowed is True
        # No standing outside restricted area
        r2 = s.check_standing("bob", ActionType.FILE_APPEAL, policy_area="finance")
        assert r2.allowed is False

    def test_module_singleton(self):
        from src.kortana.services.standing_rules import get_standing_rules
        s1 = get_standing_rules()
        s2 = get_standing_rules()
        assert s1 is s2


# ═══════════════════════════════════════════════════════════════════════════════
# V24B: Deadline Clock Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestDeadlineClock:
    """Tests for procedural deadline management."""

    def _make(self):
        from src.kortana.services.deadline_clock import DeadlineClock
        return DeadlineClock()

    def test_create_deadline(self):
        from src.kortana.services.deadline_clock import DeadlineStatus, DeadlineType
        clock = self._make()
        d = clock.create_deadline("ref-1", DeadlineType.APPEAL_FILING)
        assert d.deadline_type == DeadlineType.APPEAL_FILING
        assert d.status == DeadlineStatus.PENDING
        assert d.reference_id == "ref-1"
        assert d.extensions == 0
        assert clock.deadline_count == 1

    def test_meet_deadline(self):
        from src.kortana.services.deadline_clock import DeadlineStatus, DeadlineType
        clock = self._make()
        d = clock.create_deadline("ref-1", DeadlineType.WAIVER_REVIEW)
        assert clock.meet_deadline(d.deadline_id) is True
        assert d.status == DeadlineStatus.MET
        assert d.met_at != ""

    def test_meet_nonexistent_deadline(self):
        clock = self._make()
        assert clock.meet_deadline("nonexistent") is False

    def test_extend_deadline(self):
        from src.kortana.services.deadline_clock import DeadlineType
        clock = self._make()
        d = clock.create_deadline("ref-1", DeadlineType.APPEAL_FILING)
        original_due = d.due_at
        assert clock.extend_deadline(d.deadline_id, 24) is True
        assert d.extensions == 1
        assert d.due_at != original_due

    def test_max_extensions(self):
        from src.kortana.services.deadline_clock import DeadlineType
        clock = self._make()
        d = clock.create_deadline("ref-1", DeadlineType.APPEAL_FILING)
        assert clock.extend_deadline(d.deadline_id, 24) is True
        assert clock.extend_deadline(d.deadline_id, 24) is True
        # Third extension should fail
        assert clock.extend_deadline(d.deadline_id, 24) is False
        assert d.extensions == 2

    def test_cancel_deadline(self):
        from src.kortana.services.deadline_clock import DeadlineStatus, DeadlineType
        clock = self._make()
        d = clock.create_deadline("ref-1", DeadlineType.EMERGENCY_REVIEW)
        assert clock.cancel_deadline(d.deadline_id) is True
        assert d.status == DeadlineStatus.CANCELLED

    def test_custom_hours(self):
        from src.kortana.services.deadline_clock import DeadlineType
        clock = self._make()
        d = clock.create_deadline("ref-1", DeadlineType.APPEAL_FILING, hours=12)
        # Should be 12 hours from now, not default 48
        due = datetime.fromisoformat(d.due_at)
        created = datetime.fromisoformat(d.created_at)
        delta_hours = (due - created).total_seconds() / 3600
        assert abs(delta_hours - 12) < 0.1

    def test_deadline_hash(self):
        from src.kortana.services.deadline_clock import DeadlineType
        clock = self._make()
        d = clock.create_deadline("ref-1", DeadlineType.APPEAL_FILING)
        assert len(d.deadline_hash) == 16

    def test_get_deadlines_filtered(self):
        from src.kortana.services.deadline_clock import DeadlineType
        clock = self._make()
        clock.create_deadline("ref-1", DeadlineType.APPEAL_FILING)
        clock.create_deadline("ref-1", DeadlineType.WAIVER_REVIEW)
        clock.create_deadline("ref-2", DeadlineType.APPEAL_FILING)

        # Filter by reference_id
        r1 = clock.get_deadlines(reference_id="ref-1")
        assert len(r1) == 2

        # Filter by type
        r2 = clock.get_deadlines(deadline_type=DeadlineType.APPEAL_FILING)
        assert len(r2) == 2

    def test_deadline_to_dict(self):
        from src.kortana.services.deadline_clock import DeadlineType
        clock = self._make()
        d = clock.create_deadline("ref-1", DeadlineType.APPEAL_FILING)
        data = d.to_dict()
        assert data["reference_id"] == "ref-1"
        assert data["deadline_type"] == "appeal_filing"
        assert data["status"] == "pending"
        assert "deadline_hash" in data

    def test_summary(self):
        from src.kortana.services.deadline_clock import DeadlineType
        clock = self._make()
        clock.create_deadline("ref-1", DeadlineType.APPEAL_FILING)
        clock.create_deadline("ref-2", DeadlineType.WAIVER_REVIEW)
        summary = clock.get_summary()
        assert summary["total_deadlines"] == 2
        assert summary["pending"] == 2
        assert summary["missed"] == 0

    def test_pending_count(self):
        from src.kortana.services.deadline_clock import DeadlineType
        clock = self._make()
        d1 = clock.create_deadline("ref-1", DeadlineType.APPEAL_FILING)
        clock.create_deadline("ref-2", DeadlineType.WAIVER_REVIEW)
        clock.meet_deadline(d1.deadline_id)
        assert clock.pending_count == 1

    def test_module_singleton(self):
        from src.kortana.services.deadline_clock import get_deadline_clock
        c1 = get_deadline_clock()
        c2 = get_deadline_clock()
        assert c1 is c2


# ═══════════════════════════════════════════════════════════════════════════════
# V24C: Recusal Manager Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestRecusalManager:
    """Tests for conflict-of-interest and recusal management."""

    def _make(self):
        from src.kortana.services.recusal_manager import RecusalManager
        return RecusalManager()

    def test_declare_interest(self):
        mgr = self._make()
        decl = mgr.declare_interest("alice", ["security", "auth"])
        assert decl.actor == "alice"
        assert "security" in decl.policy_areas
        assert mgr.interest_count == 1

    def test_check_proposer_conflict(self):
        from src.kortana.services.recusal_manager import ConflictType
        mgr = self._make()
        conflicts = mgr.check_conflicts("alice", "prop-1", "security", proposer_id="alice")
        assert ConflictType.PROPOSER in conflicts

    def test_check_area_interest_conflict(self):
        from src.kortana.services.recusal_manager import ConflictType
        mgr = self._make()
        mgr.declare_interest("bob", ["security"])
        conflicts = mgr.check_conflicts("bob", "prop-1", "security")
        assert ConflictType.AREA_INTEREST in conflicts

    def test_no_conflict_different_area(self):
        mgr = self._make()
        mgr.declare_interest("bob", ["security"])
        conflicts = mgr.check_conflicts("bob", "prop-1", "finance")
        # No area interest conflict for different area
        assert len([c for c in conflicts if c.value == "area_interest"]) == 0

    def test_recuse_actor(self):
        from src.kortana.services.recusal_manager import ConflictType
        mgr = self._make()
        rec = mgr.recuse("alice", "prop-1", ConflictType.PROPOSER, "Self-proposer conflict")
        assert rec.actor == "alice"
        assert rec.mandatory is False
        assert mgr.recusal_count == 1

    def test_mandatory_recusal(self):
        from src.kortana.services.recusal_manager import ConflictType
        mgr = self._make()
        rec = mgr.recuse("alice", "prop-1", ConflictType.PROPOSER, "Required", mandatory=True)
        assert rec.mandatory is True

    def test_is_recused(self):
        from src.kortana.services.recusal_manager import ConflictType
        mgr = self._make()
        mgr.recuse("alice", "prop-1", ConflictType.AREA_INTEREST, "Conflict")
        assert mgr.is_recused("alice", "prop-1") is True
        assert mgr.is_recused("alice", "prop-2") is False
        assert mgr.is_recused("bob", "prop-1") is False

    def test_get_recusals_filtered(self):
        from src.kortana.services.recusal_manager import ConflictType
        mgr = self._make()
        mgr.recuse("alice", "prop-1", ConflictType.PROPOSER, "r1")
        mgr.recuse("alice", "prop-2", ConflictType.AREA_INTEREST, "r2")
        mgr.recuse("bob", "prop-1", ConflictType.PERSONAL, "r3")

        by_actor = mgr.get_recusals(actor="alice")
        assert len(by_actor) == 2
        by_ref = mgr.get_recusals(reference_id="prop-1")
        assert len(by_ref) == 2

    def test_interest_declaration_to_dict(self):
        mgr = self._make()
        decl = mgr.declare_interest("alice", ["security"], "Test reason")
        d = decl.to_dict()
        assert d["actor"] == "alice"
        assert "security" in d["policy_areas"]

    def test_recusal_hash(self):
        from src.kortana.services.recusal_manager import ConflictType
        mgr = self._make()
        rec = mgr.recuse("alice", "prop-1", ConflictType.PROPOSER, "test")
        assert len(rec.recusal_hash) == 16

    def test_recusal_to_dict(self):
        from src.kortana.services.recusal_manager import ConflictType
        mgr = self._make()
        rec = mgr.recuse("alice", "prop-1", ConflictType.PROPOSER, "test")
        d = rec.to_dict()
        assert d["actor"] == "alice"
        assert d["conflict_type"] == "proposer"

    def test_summary(self):
        from src.kortana.services.recusal_manager import ConflictType
        mgr = self._make()
        mgr.declare_interest("alice", ["security"])
        mgr.recuse("alice", "prop-1", ConflictType.PROPOSER, "r1", mandatory=True)
        mgr.recuse("bob", "prop-2", ConflictType.PERSONAL, "r2")
        summary = mgr.get_summary()
        assert summary["total_interests"] == 1
        assert summary["total_recusals"] == 2
        assert summary["mandatory_recusals"] == 1
        assert summary["voluntary_recusals"] == 1

    def test_prior_involvement_detected(self):
        from src.kortana.services.recusal_manager import ConflictType
        mgr = self._make()
        # Bob was recused from a prior proceeding
        mgr.recuse("bob", "prop-1", ConflictType.AREA_INTEREST, "prior")
        # Check bob for a new proceeding — should flag prior involvement
        conflicts = mgr.check_conflicts("bob", "prop-2", "security")
        assert ConflictType.PRIOR_INVOLVEMENT in conflicts

    def test_module_singleton(self):
        from src.kortana.services.recusal_manager import get_recusal_manager
        m1 = get_recusal_manager()
        m2 = get_recusal_manager()
        assert m1 is m2


# ═══════════════════════════════════════════════════════════════════════════════
# V24D: Reasoning Templates Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestReasoningTemplates:
    """Tests for published reasoning and template validation."""

    def _make(self):
        from src.kortana.services.reasoning_templates import ReasoningRegistry
        return ReasoningRegistry(load_defaults=True)

    def test_default_templates_loaded(self):
        reg = self._make()
        assert reg.template_count == 3

    def test_get_template(self):
        reg = self._make()
        t = reg.get_template("appeal_decision")
        assert t is not None
        assert t.decision_type == "appeal_decision"
        assert len(t.required_sections) == 4

    def test_publish_reasoning(self):
        reg = self._make()
        r = reg.publish(
            reference_id="appeal-1",
            decision_type="appeal_decision",
            sections={
                "findings_of_fact": "The policy was misapplied.",
                "legal_basis": "Article 3: proportionality.",
                "analysis": "The harm outweighs the benefit.",
                "conclusion": "Appeal upheld.",
            },
            cited_articles=["article-3"],
            author="judge-1",
        )
        assert r.decision_type == "appeal_decision"
        assert reg.published_count == 1

    def test_validate_complete_reasoning(self):
        from src.kortana.services.reasoning_templates import PublishedReasoning
        reg = self._make()
        reasoning = PublishedReasoning(
            reasoning_id="test",
            reference_id="appeal-1",
            decision_type="appeal_decision",
            sections={
                "findings_of_fact": "Facts.",
                "legal_basis": "Law.",
                "analysis": "Review.",
                "conclusion": "Upheld.",
            },
            cited_articles=["article-1"],
            author="judge-1",
        )
        result = reg.validate(reasoning)
        assert result.valid is True
        assert len(result.missing_sections) == 0

    def test_validate_missing_sections(self):
        from src.kortana.services.reasoning_templates import PublishedReasoning
        reg = self._make()
        reasoning = PublishedReasoning(
            reasoning_id="test",
            reference_id="appeal-1",
            decision_type="appeal_decision",
            sections={
                "findings_of_fact": "Facts.",
                # Missing: legal_basis, analysis, conclusion
            },
            author="judge-1",
        )
        result = reg.validate(reasoning)
        assert result.valid is False
        assert "legal_basis" in result.missing_sections
        assert "analysis" in result.missing_sections
        assert "conclusion" in result.missing_sections

    def test_validate_empty_section_counts_as_missing(self):
        from src.kortana.services.reasoning_templates import PublishedReasoning
        reg = self._make()
        reasoning = PublishedReasoning(
            reasoning_id="test",
            reference_id="appeal-1",
            decision_type="appeal_decision",
            sections={
                "findings_of_fact": "Facts.",
                "legal_basis": "",
                "analysis": "Review.",
                "conclusion": "Done.",
            },
            author="judge-1",
        )
        result = reg.validate(reasoning)
        assert result.valid is False
        assert "legal_basis" in result.missing_sections

    def test_validate_warns_no_citations(self):
        from src.kortana.services.reasoning_templates import PublishedReasoning
        reg = self._make()
        reasoning = PublishedReasoning(
            reasoning_id="test",
            reference_id="appeal-1",
            decision_type="appeal_decision",
            sections={
                "findings_of_fact": "Facts.",
                "legal_basis": "Law.",
                "analysis": "Review.",
                "conclusion": "Done.",
            },
            # No cited_articles or author
        )
        result = reg.validate(reasoning)
        assert result.valid is True
        assert any("articles" in w.lower() for w in result.warnings)

    def test_validate_unknown_type_passes(self):
        from src.kortana.services.reasoning_templates import PublishedReasoning
        reg = self._make()
        reasoning = PublishedReasoning(
            reasoning_id="test",
            reference_id="x",
            decision_type="custom_type",
            sections={"summary": "ok"},
        )
        result = reg.validate(reasoning)
        assert result.valid is True
        assert len(result.warnings) > 0

    def test_waiver_decision_template(self):
        from src.kortana.services.reasoning_templates import PublishedReasoning
        reg = self._make()
        reasoning = PublishedReasoning(
            reasoning_id="test",
            reference_id="waiver-1",
            decision_type="waiver_decision",
            sections={
                "findings_of_fact": "Good reasons.",
                "analysis": "Reviewed.",
                "conclusion": "Granted.",
                "conditions": "Must not exceed 48h.",
            },
            cited_articles=["article-5"],
            author="reviewer-1",
        )
        result = reg.validate(reasoning)
        assert result.valid is True

    def test_add_custom_template(self):
        from src.kortana.services.reasoning_templates import (
            ReasoningSection,
            ReasoningTemplate,
        )
        reg = self._make()
        custom = ReasoningTemplate(
            template_id="custom-1",
            decision_type="boundary_review",
            required_sections=[ReasoningSection.ANALYSIS, ReasoningSection.CONCLUSION],
            description="Custom boundary review template",
        )
        reg.add_template(custom)
        t = reg.get_template("boundary_review")
        assert t is not None
        assert len(t.required_sections) == 2

    def test_get_published_filtered(self):
        reg = self._make()
        reg.publish("ref-1", "appeal_decision", {"s": "v"}, author="judge-1")
        reg.publish("ref-2", "waiver_decision", {"s": "v"}, author="judge-2")
        reg.publish("ref-1", "waiver_decision", {"s": "v"}, author="judge-1")

        by_ref = reg.get_published(reference_id="ref-1")
        assert len(by_ref) == 2
        by_type = reg.get_published(decision_type="waiver_decision")
        assert len(by_type) == 2
        by_author = reg.get_published(author="judge-1")
        assert len(by_author) == 2

    def test_reasoning_hash(self):
        reg = self._make()
        r = reg.publish("ref-1", "appeal_decision", {"s": "v"}, author="j")
        assert len(r.reasoning_hash) == 16

    def test_reasoning_to_dict(self):
        reg = self._make()
        r = reg.publish("ref-1", "appeal_decision", {"s": "v"}, author="j")
        d = r.to_dict()
        assert d["reference_id"] == "ref-1"
        assert d["decision_type"] == "appeal_decision"

    def test_template_to_dict(self):
        reg = self._make()
        t = reg.get_template("appeal_decision")
        assert t is not None
        d = t.to_dict()
        assert d["decision_type"] == "appeal_decision"
        assert len(d["required_sections"]) == 4

    def test_validation_result_to_dict(self):
        from src.kortana.services.reasoning_templates import PublishedReasoning
        reg = self._make()
        reasoning = PublishedReasoning(
            reasoning_id="test",
            reference_id="x",
            decision_type="appeal_decision",
            sections={"findings_of_fact": "f", "legal_basis": "l", "analysis": "a", "conclusion": "c"},
            cited_articles=["a1"],
            author="j",
        )
        result = reg.validate(reasoning)
        d = result.to_dict()
        assert d["valid"] is True
        assert "checked_at" in d

    def test_summary(self):
        reg = self._make()
        reg.publish("ref-1", "appeal_decision", {"s": "v"})
        reg.publish("ref-2", "appeal_decision", {"s": "v"})
        summary = reg.get_summary()
        assert summary["total_templates"] == 3
        assert summary["total_published"] == 2
        assert summary["by_decision_type"]["appeal_decision"] == 2

    def test_module_singleton(self):
        from src.kortana.services.reasoning_templates import get_reasoning_registry
        r1 = get_reasoning_registry()
        r2 = get_reasoning_registry()
        assert r1 is r2


# ═══════════════════════════════════════════════════════════════════════════════
# V24 Pipeline: Cross-Component Integration
# ═══════════════════════════════════════════════════════════════════════════════


class TestV24Pipeline:
    """Integration tests for constitutional procedure pipeline."""

    def test_standing_before_appeal(self):
        """Standing must be checked before filing an appeal."""
        from src.kortana.services.deadline_clock import DeadlineClock, DeadlineType
        from src.kortana.services.standing_rules import (
            ActionType,
            ActorRole,
            StandingRules,
        )

        standing = StandingRules(load_defaults=True)
        clock = DeadlineClock()

        # Register an operator
        standing.register_actor("alice", ActorRole.OPERATOR)

        # Check standing → allowed
        result = standing.check_standing("alice", ActionType.FILE_APPEAL)
        assert result.allowed is True

        # Create filing deadline
        deadline = clock.create_deadline("appeal-123", DeadlineType.APPEAL_FILING)
        assert deadline.status.value == "pending"

    def test_recusal_blocks_participation(self):
        """Recused actors should not participate in proceedings."""
        from src.kortana.services.recusal_manager import ConflictType, RecusalManager

        mgr = RecusalManager()
        mgr.declare_interest("bob", ["security"])

        # Check conflicts
        conflicts = mgr.check_conflicts("bob", "prop-1", "security")
        assert ConflictType.AREA_INTEREST in conflicts

        # Recuse
        mgr.recuse("bob", "prop-1", ConflictType.AREA_INTEREST, "Declared interest in security", mandatory=True)
        assert mgr.is_recused("bob", "prop-1") is True

    def test_reasoning_required_for_decisions(self):
        """Every decision must have published reasoning that passes validation."""
        from src.kortana.services.reasoning_templates import ReasoningRegistry

        reg = ReasoningRegistry(load_defaults=True)

        # Publish appeal decision reasoning
        reasoning = reg.publish(
            reference_id="appeal-123",
            decision_type="appeal_decision",
            sections={
                "findings_of_fact": "The agent miscategorized the policy.",
                "legal_basis": "Article 2: fair classification.",
                "analysis": "Analysis shows the classification was incorrect.",
                "conclusion": "Appeal is upheld. Policy reclassified.",
            },
            cited_articles=["article-2"],
            author="constitutional-authority",
        )

        # Validate
        result = reg.validate(reasoning)
        assert result.valid is True

    def test_full_procedure_pipeline(self):
        """End-to-end: standing → deadline → recusal check → reasoning."""
        from src.kortana.services.deadline_clock import DeadlineClock, DeadlineType
        from src.kortana.services.reasoning_templates import ReasoningRegistry
        from src.kortana.services.recusal_manager import RecusalManager
        from src.kortana.services.standing_rules import (
            ActionType,
            ActorRole,
            StandingRules,
        )

        standing = StandingRules(load_defaults=True)
        clock = DeadlineClock()
        recusal = RecusalManager()
        reasoning = ReasoningRegistry(load_defaults=True)

        # Step 1: Register actors
        standing.register_actor("judge", ActorRole.CONSTITUTIONAL_AUTHORITY)
        standing.register_actor("appellant", ActorRole.OPERATOR)

        # Step 2: Appellant files appeal (check standing)
        s = standing.check_standing("appellant", ActionType.FILE_APPEAL)
        assert s.allowed is True

        # Step 3: Create filing deadline
        dl = clock.create_deadline("appeal-456", DeadlineType.APPEAL_FILING)
        assert dl.status.value == "pending"

        # Step 4: Meet filing deadline
        clock.meet_deadline(dl.deadline_id)
        assert dl.status.value == "met"

        # Step 5: Check judge for conflicts
        conflicts = recusal.check_conflicts("judge", "appeal-456", "runtime")
        assert len(conflicts) == 0  # No conflicts

        # Step 6: Create review deadline
        review_dl = clock.create_deadline("appeal-456", DeadlineType.APPEAL_REVIEW)
        assert review_dl.status.value == "pending"

        # Step 7: Judge publishes reasoning
        r = reasoning.publish(
            reference_id="appeal-456",
            decision_type="appeal_decision",
            sections={
                "findings_of_fact": "The policy was correctly applied.",
                "legal_basis": "Article 1: rule of law.",
                "analysis": "No error found.",
                "conclusion": "Appeal denied.",
            },
            cited_articles=["article-1"],
            author="judge",
        )

        # Step 8: Validate reasoning
        validation = reasoning.validate(r)
        assert validation.valid is True

        # Step 9: Meet review deadline
        clock.meet_deadline(review_dl.deadline_id)
        assert review_dl.status.value == "met"

        # Verify aggregate state
        assert standing.check_count == 1
        assert clock.deadline_count == 2
        assert clock.pending_count == 0
        assert reasoning.published_count == 1

    def test_observer_cannot_participate(self):
        """Observers should have no standing for any procedural action."""
        from src.kortana.services.standing_rules import (
            ActionType,
            ActorRole,
            StandingRules,
        )

        standing = StandingRules(load_defaults=True)
        standing.register_actor("viewer", ActorRole.OBSERVER)

        for action in ActionType:
            r = standing.check_standing("viewer", action)
            assert r.allowed is False

    def test_proposer_must_recuse(self):
        """A proposer should be flagged for conflict and recuse."""
        from src.kortana.services.recusal_manager import ConflictType, RecusalManager
        from src.kortana.services.standing_rules import (
            ActionType,
            ActorRole,
            StandingRules,
        )

        standing = StandingRules(load_defaults=True)
        recusal = RecusalManager()

        standing.register_actor("alice", ActorRole.SENIOR_OPERATOR)

        # Alice has standing to review decisions
        r = standing.check_standing("alice", ActionType.REVIEW_DECISION)
        assert r.allowed is True

        # But she proposed the thing being reviewed
        conflicts = recusal.check_conflicts("alice", "prop-789", "deployment", proposer_id="alice")
        assert ConflictType.PROPOSER in conflicts

        # She recuses
        recusal.recuse("alice", "prop-789", ConflictType.PROPOSER, "I proposed this", mandatory=True)
        assert recusal.is_recused("alice", "prop-789") is True
