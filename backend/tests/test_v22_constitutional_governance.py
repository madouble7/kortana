"""V22 — constitutional governance tests."""

from __future__ import annotations

import sys
sys.path.insert(0, "src")

from src.kortana.services.constitution import (
    Constitution,
    ConstitutionalArticle,
    PolicyClassification,
    Sensitivity,
    ViolationSeverity,
    get_constitution,
)
from src.kortana.services.quorum_policy import (
    QuorumPolicy,
    QuorumType,
    QuorumRequirement,
    get_quorum_policy,
)
from src.kortana.services.boundary_enforcer import (
    BoundaryEnforcer,
    get_boundary_enforcer,
)
from src.kortana.services.constitutional_audit import (
    ConstitutionalAudit,
    get_constitutional_audit,
)
from src.kortana.services.policy_feedback_loop import PolicyArea
from src.kortana.services.proposal_registry import PolicyProposal


def _make_proposal(
    area: PolicyArea = PolicyArea.ROLLOUT,
    confidence: float = 0.8,
    proposal_id: str = "prop-test-001",
) -> PolicyProposal:
    """Helper to create a test proposal."""
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


# ═══ V22A: Constitution ═══


class TestConstitution:
    """Tests for constitutional articles and policy classification."""

    def test_default_articles_loaded(self) -> None:
        const = Constitution()
        assert const.article_count == 6

    def test_governance_is_immutable(self) -> None:
        const = Constitution()
        assert const.is_immutable(PolicyArea.GOVERNANCE)
        assert const.get_classification(PolicyArea.GOVERNANCE) == PolicyClassification.IMMUTABLE

    def test_autonomy_is_restricted(self) -> None:
        const = Constitution()
        assert const.is_restricted(PolicyArea.AUTONOMY)
        assert const.get_classification(PolicyArea.AUTONOMY) == PolicyClassification.RESTRICTED

    def test_escalation_is_restricted(self) -> None:
        const = Constitution()
        assert const.is_restricted(PolicyArea.ESCALATION)

    def test_rollout_is_amendable(self) -> None:
        const = Constitution()
        assert const.is_amendable(PolicyArea.ROLLOUT)
        assert const.get_classification(PolicyArea.ROLLOUT) == PolicyClassification.AMENDABLE

    def test_retry_is_amendable(self) -> None:
        const = Constitution()
        assert const.is_amendable(PolicyArea.RETRY)

    def test_priority_is_amendable(self) -> None:
        const = Constitution()
        assert const.is_amendable(PolicyArea.PRIORITY)

    def test_governance_is_critical_sensitivity(self) -> None:
        const = Constitution()
        assert const.get_sensitivity(PolicyArea.GOVERNANCE) == Sensitivity.CRITICAL

    def test_autonomy_is_high_sensitivity(self) -> None:
        const = Constitution()
        assert const.get_sensitivity(PolicyArea.AUTONOMY) == Sensitivity.HIGH

    def test_rollout_is_standard_sensitivity(self) -> None:
        const = Constitution()
        assert const.get_sensitivity(PolicyArea.ROLLOUT) == Sensitivity.STANDARD

    def test_retry_is_low_sensitivity(self) -> None:
        const = Constitution()
        assert const.get_sensitivity(PolicyArea.RETRY) == Sensitivity.LOW

    def test_get_article_by_id(self) -> None:
        const = Constitution()
        art = const.get_article("art-001")
        assert art is not None
        assert art.classification == PolicyClassification.IMMUTABLE

    def test_get_articles_for_area(self) -> None:
        const = Constitution()
        arts = const.get_articles_for_area(PolicyArea.GOVERNANCE)
        assert len(arts) >= 1

    def test_add_custom_article(self) -> None:
        const = Constitution(load_defaults=False)
        art = ConstitutionalArticle(
            article_id="art-custom",
            title="Custom rule",
            policy_area=PolicyArea.ROLLOUT,
            classification=PolicyClassification.RESTRICTED,
            sensitivity=Sensitivity.HIGH,
            boundary_rule="custom boundary",
            violation_severity=ViolationSeverity.MAJOR,
            rationale="custom rationale",
        )
        const.add_article(art)
        assert const.article_count == 1
        assert const.get_article("art-custom") is not None

    def test_article_hash(self) -> None:
        const = Constitution()
        art = const.get_article("art-001")
        assert len(art.article_hash) == 16

    def test_article_to_dict(self) -> None:
        const = Constitution()
        art = const.get_article("art-001")
        d = art.to_dict()
        assert "article_id" in d
        assert "classification" in d

    def test_summary(self) -> None:
        const = Constitution()
        s = const.get_summary()
        assert s["total_articles"] == 6
        assert "by_classification" in s
        assert "by_sensitivity" in s

    def test_module_singleton(self) -> None:
        c1 = get_constitution()
        c2 = get_constitution()
        assert c1 is c2

    def test_empty_constitution(self) -> None:
        const = Constitution(load_defaults=False)
        assert const.article_count == 0
        assert const.is_amendable(PolicyArea.ROLLOUT)
        assert const.get_sensitivity(PolicyArea.ROLLOUT) == Sensitivity.STANDARD


# ═══ V22B: Quorum Policy ═══


class TestQuorumPolicy:
    """Tests for quorum requirements and voting."""

    def test_critical_requires_unanimous(self) -> None:
        qp = QuorumPolicy()
        req = qp.get_requirement(Sensitivity.CRITICAL)
        assert req.quorum_type == QuorumType.UNANIMOUS
        assert req.min_approvers == 3
        assert req.require_identity_verification

    def test_high_requires_supermajority(self) -> None:
        qp = QuorumPolicy()
        req = qp.get_requirement(Sensitivity.HIGH)
        assert req.quorum_type == QuorumType.SUPERMAJORITY
        assert req.min_approvers == 2

    def test_standard_requires_simple_majority(self) -> None:
        qp = QuorumPolicy()
        req = qp.get_requirement(Sensitivity.STANDARD)
        assert req.quorum_type == QuorumType.SIMPLE_MAJORITY
        assert req.min_approvers == 1

    def test_low_is_auto(self) -> None:
        qp = QuorumPolicy()
        req = qp.get_requirement(Sensitivity.LOW)
        assert req.quorum_type == QuorumType.AUTO

    def test_auto_quorum_always_passes(self) -> None:
        qp = QuorumPolicy()
        result = qp.check_quorum("prop-1", Sensitivity.LOW)
        assert result.quorum_met

    def test_unanimous_passes_with_3_approvers(self) -> None:
        qp = QuorumPolicy()
        for voter in ["alice", "bob", "charlie"]:
            qp.cast_vote("prop-1", voter, approved=True, identity_verified=True)
        result = qp.check_quorum("prop-1", Sensitivity.CRITICAL)
        assert result.quorum_met
        assert result.identity_check_passed

    def test_unanimous_fails_with_rejection(self) -> None:
        qp = QuorumPolicy()
        qp.cast_vote("prop-1", "alice", approved=True, identity_verified=True)
        qp.cast_vote("prop-1", "bob", approved=True, identity_verified=True)
        qp.cast_vote("prop-1", "charlie", approved=False, identity_verified=True)
        result = qp.check_quorum("prop-1", Sensitivity.CRITICAL)
        assert not result.quorum_met

    def test_unanimous_fails_without_identity(self) -> None:
        qp = QuorumPolicy()
        for voter in ["alice", "bob", "charlie"]:
            qp.cast_vote("prop-1", voter, approved=True, identity_verified=False)
        result = qp.check_quorum("prop-1", Sensitivity.CRITICAL)
        assert not result.quorum_met
        assert not result.identity_check_passed

    def test_supermajority_passes(self) -> None:
        qp = QuorumPolicy()
        qp.cast_vote("prop-1", "alice", approved=True, identity_verified=True)
        qp.cast_vote("prop-1", "bob", approved=True, identity_verified=True)
        qp.cast_vote("prop-1", "charlie", approved=False, identity_verified=True)
        result = qp.check_quorum("prop-1", Sensitivity.HIGH)
        assert result.quorum_met

    def test_simple_majority_passes(self) -> None:
        qp = QuorumPolicy()
        qp.cast_vote("prop-1", "alice", approved=True)
        result = qp.check_quorum("prop-1", Sensitivity.STANDARD)
        assert result.quorum_met

    def test_simple_majority_fails_with_more_rejections(self) -> None:
        qp = QuorumPolicy()
        qp.cast_vote("prop-1", "alice", approved=False)
        qp.cast_vote("prop-1", "bob", approved=False)
        result = qp.check_quorum("prop-1", Sensitivity.STANDARD)
        assert not result.quorum_met

    def test_vote_replacement(self) -> None:
        qp = QuorumPolicy()
        qp.cast_vote("prop-1", "alice", approved=True)
        qp.cast_vote("prop-1", "alice", approved=False)
        votes = qp.get_votes("prop-1")
        assert len(votes) == 1
        assert not votes[0].approved

    def test_vote_hash(self) -> None:
        qp = QuorumPolicy()
        vote = qp.cast_vote("prop-1", "alice", approved=True)
        assert len(vote.vote_hash) == 16

    def test_result_to_dict(self) -> None:
        qp = QuorumPolicy()
        result = qp.check_quorum("prop-1", Sensitivity.LOW)
        d = result.to_dict()
        assert "quorum_met" in d
        assert "quorum_type" in d

    def test_module_singleton(self) -> None:
        q1 = get_quorum_policy()
        q2 = get_quorum_policy()
        assert q1 is q2

    def test_custom_requirement(self) -> None:
        qp = QuorumPolicy()
        custom = QuorumRequirement(
            sensitivity=Sensitivity.STANDARD,
            quorum_type=QuorumType.SINGLE_APPROVER,
            min_approvers=1,
            require_identity_verification=True,
            cooldown_hours=12,
        )
        qp.set_requirement(custom)
        req = qp.get_requirement(Sensitivity.STANDARD)
        assert req.quorum_type == QuorumType.SINGLE_APPROVER


# ═══ V22C: Boundary Enforcer ═══


class TestBoundaryEnforcer:
    """Tests for constitutional boundary enforcement."""

    def test_amendable_proposal_passes(self) -> None:
        const = Constitution()
        enforcer = BoundaryEnforcer(const)
        proposal = _make_proposal(area=PolicyArea.ROLLOUT)
        check = enforcer.check_proposal(proposal)
        assert check.passed
        assert len(check.violations) == 0

    def test_immutable_proposal_blocked(self) -> None:
        const = Constitution()
        enforcer = BoundaryEnforcer(const)
        proposal = _make_proposal(area=PolicyArea.GOVERNANCE)
        check = enforcer.check_proposal(proposal)
        assert not check.passed
        assert len(check.violations) > 0
        assert check.violations[0].severity == ViolationSeverity.FATAL

    def test_restricted_proposal_warns(self) -> None:
        const = Constitution()
        enforcer = BoundaryEnforcer(const)
        proposal = _make_proposal(area=PolicyArea.AUTONOMY)
        check = enforcer.check_proposal(proposal)
        assert check.passed  # Restricted generates warnings, not violations
        assert len(check.warnings) > 0

    def test_low_confidence_high_sensitivity_warns(self) -> None:
        const = Constitution()
        enforcer = BoundaryEnforcer(const)
        proposal = _make_proposal(area=PolicyArea.AUTONOMY, confidence=0.3)
        check = enforcer.check_proposal(proposal)
        # Should have warnings about both restricted and low confidence
        assert len(check.warnings) >= 2

    def test_validate_evolution_batch(self) -> None:
        const = Constitution()
        enforcer = BoundaryEnforcer(const)
        proposals = [
            _make_proposal(area=PolicyArea.ROLLOUT, proposal_id="prop-1"),
            _make_proposal(area=PolicyArea.GOVERNANCE, proposal_id="prop-2"),
            _make_proposal(area=PolicyArea.RETRY, proposal_id="prop-3"),
        ]
        result = enforcer.validate_evolution_batch(proposals)
        assert not result["all_passed"]
        assert result["passed_count"] == 2
        assert result["blocked_count"] == 1

    def test_check_classification_field(self) -> None:
        const = Constitution()
        enforcer = BoundaryEnforcer(const)
        proposal = _make_proposal(area=PolicyArea.ROLLOUT)
        check = enforcer.check_proposal(proposal)
        assert check.classification == "amendable"
        assert check.sensitivity == "standard"

    def test_check_hash(self) -> None:
        const = Constitution()
        enforcer = BoundaryEnforcer(const)
        proposal = _make_proposal()
        check = enforcer.check_proposal(proposal)
        assert len(check.check_hash) == 16

    def test_check_to_dict(self) -> None:
        const = Constitution()
        enforcer = BoundaryEnforcer(const)
        proposal = _make_proposal()
        check = enforcer.check_proposal(proposal)
        d = check.to_dict()
        assert "passed" in d
        assert "violations" in d
        assert "warnings" in d

    def test_get_checks(self) -> None:
        const = Constitution()
        enforcer = BoundaryEnforcer(const)
        enforcer.check_proposal(_make_proposal(proposal_id="prop-1"))
        enforcer.check_proposal(_make_proposal(proposal_id="prop-2"))
        assert enforcer.check_count == 2
        assert len(enforcer.get_checks("prop-1")) == 1

    def test_violation_summary(self) -> None:
        const = Constitution()
        enforcer = BoundaryEnforcer(const)
        enforcer.check_proposal(_make_proposal(area=PolicyArea.GOVERNANCE))
        summary = enforcer.get_violation_summary()
        assert summary["total_violations"] > 0
        assert "fatal" in summary["by_severity"]

    def test_module_singleton(self) -> None:
        e1 = get_boundary_enforcer()
        e2 = get_boundary_enforcer()
        assert e1 is e2


# ═══ V22D: Constitutional Audit ═══


class TestConstitutionalAudit:
    """Tests for compliance proofs and violation tracking."""

    def test_record_passing_check(self) -> None:
        audit = ConstitutionalAudit()
        const = Constitution()
        enforcer = BoundaryEnforcer(const)
        check = enforcer.check_proposal(_make_proposal(area=PolicyArea.ROLLOUT))
        proof = audit.record_check(check)
        assert proof.all_checks_passed
        assert proof.violations_found == 0
        assert audit.proof_count == 1

    def test_record_failing_check(self) -> None:
        audit = ConstitutionalAudit()
        const = Constitution()
        enforcer = BoundaryEnforcer(const)
        check = enforcer.check_proposal(_make_proposal(area=PolicyArea.GOVERNANCE))
        proof = audit.record_check(check)
        assert not proof.all_checks_passed
        assert proof.violations_found > 0
        assert audit.violation_count > 0

    def test_resolve_violation(self) -> None:
        audit = ConstitutionalAudit()
        const = Constitution()
        enforcer = BoundaryEnforcer(const)
        check = enforcer.check_proposal(_make_proposal(area=PolicyArea.GOVERNANCE))
        audit.record_check(check)
        violations = audit.get_violations()
        assert len(violations) > 0
        ok = audit.resolve_violation(violations[0].violation_id, "accepted risk")
        assert ok
        assert violations[0].resolved

    def test_get_violations_filtered(self) -> None:
        audit = ConstitutionalAudit()
        const = Constitution()
        enforcer = BoundaryEnforcer(const)
        audit.record_check(enforcer.check_proposal(_make_proposal(area=PolicyArea.GOVERNANCE, proposal_id="prop-1")))
        audit.record_check(enforcer.check_proposal(_make_proposal(area=PolicyArea.ROLLOUT, proposal_id="prop-2")))
        assert len(audit.get_violations(proposal_id="prop-1")) > 0
        assert len(audit.get_violations(proposal_id="prop-2")) == 0

    def test_get_violations_unresolved_only(self) -> None:
        audit = ConstitutionalAudit()
        const = Constitution()
        enforcer = BoundaryEnforcer(const)
        audit.record_check(enforcer.check_proposal(_make_proposal(area=PolicyArea.GOVERNANCE)))
        violations = audit.get_violations()
        audit.resolve_violation(violations[0].violation_id)
        unresolved = audit.get_violations(unresolved_only=True)
        assert len(unresolved) == 0

    def test_compliance_report(self) -> None:
        audit = ConstitutionalAudit()
        const = Constitution()
        enforcer = BoundaryEnforcer(const)
        audit.record_check(enforcer.check_proposal(_make_proposal(area=PolicyArea.ROLLOUT, proposal_id="prop-1")))
        audit.record_check(enforcer.check_proposal(_make_proposal(area=PolicyArea.GOVERNANCE, proposal_id="prop-2")))
        report = audit.get_compliance_report()
        assert report["total_proofs"] == 2
        assert report["proofs_passed"] == 1
        assert report["proofs_failed"] == 1
        assert report["compliance_rate"] == 0.5
        assert report["constitutional_health"] == "attention_needed"

    def test_healthy_report(self) -> None:
        audit = ConstitutionalAudit()
        const = Constitution()
        enforcer = BoundaryEnforcer(const)
        audit.record_check(enforcer.check_proposal(_make_proposal(area=PolicyArea.ROLLOUT)))
        report = audit.get_compliance_report()
        assert report["constitutional_health"] == "healthy"

    def test_proof_hash(self) -> None:
        audit = ConstitutionalAudit()
        const = Constitution()
        enforcer = BoundaryEnforcer(const)
        check = enforcer.check_proposal(_make_proposal())
        proof = audit.record_check(check)
        assert len(proof.proof_hash) == 16

    def test_proof_to_dict(self) -> None:
        audit = ConstitutionalAudit()
        const = Constitution()
        enforcer = BoundaryEnforcer(const)
        check = enforcer.check_proposal(_make_proposal())
        proof = audit.record_check(check)
        d = proof.to_dict()
        assert "proof_id" in d
        assert "all_checks_passed" in d

    def test_resolve_nonexistent(self) -> None:
        audit = ConstitutionalAudit()
        assert not audit.resolve_violation("fake-id")

    def test_module_singleton(self) -> None:
        a1 = get_constitutional_audit()
        a2 = get_constitutional_audit()
        assert a1 is a2


# ═══ Integration: Full V22 Pipeline ═══


class TestV22Pipeline:
    """Integration: constitution → quorum → boundary → audit."""

    def test_full_constitutional_governance_pipeline(self) -> None:
        """Amendable proposal passes all constitutional checks."""
        const = Constitution()
        qp = QuorumPolicy()
        enforcer = BoundaryEnforcer(const)
        audit = ConstitutionalAudit()

        # 1. Create amendable proposal
        proposal = _make_proposal(area=PolicyArea.ROLLOUT, confidence=0.85)

        # 2. Check classification
        assert const.is_amendable(PolicyArea.ROLLOUT)
        sensitivity = const.get_sensitivity(PolicyArea.ROLLOUT)
        assert sensitivity == Sensitivity.STANDARD

        # 3. Check quorum (standard = simple majority)
        qp.cast_vote(proposal.proposal_id, "matt", approved=True)
        result = qp.check_quorum(proposal.proposal_id, sensitivity)
        assert result.quorum_met

        # 4. Check boundaries
        check = enforcer.check_proposal(proposal)
        assert check.passed

        # 5. Record in audit
        proof = audit.record_check(check)
        assert proof.all_checks_passed
        assert audit.violation_count == 0

        # 6. Report
        report = audit.get_compliance_report()
        assert report["constitutional_health"] == "healthy"

    def test_immutable_proposal_blocked_pipeline(self) -> None:
        """Immutable governance proposal is blocked at boundary check."""
        const = Constitution()
        qp = QuorumPolicy()
        enforcer = BoundaryEnforcer(const)
        audit = ConstitutionalAudit()

        # 1. Try to change governance policy
        proposal = _make_proposal(area=PolicyArea.GOVERNANCE)

        # 2. Even with unanimous quorum, boundary should block
        for voter in ["alice", "bob", "charlie"]:
            qp.cast_vote(proposal.proposal_id, voter, approved=True, identity_verified=True)
        quorum = qp.check_quorum(proposal.proposal_id, Sensitivity.CRITICAL)
        assert quorum.quorum_met

        # 3. But boundary enforcer blocks it
        check = enforcer.check_proposal(proposal)
        assert not check.passed
        assert check.violations[0].severity == ViolationSeverity.FATAL

        # 4. Record violation in audit
        proof = audit.record_check(check)
        assert not proof.all_checks_passed
        assert audit.violation_count > 0
        assert audit.get_compliance_report()["constitutional_health"] == "attention_needed"

    def test_restricted_with_quorum_pipeline(self) -> None:
        """Restricted autonomy proposal passes with quorum but gets warnings."""
        const = Constitution()
        qp = QuorumPolicy()
        enforcer = BoundaryEnforcer(const)
        audit = ConstitutionalAudit()

        # 1. Autonomy change (restricted, high sensitivity)
        proposal = _make_proposal(area=PolicyArea.AUTONOMY, confidence=0.9)

        # 2. Need supermajority
        qp.cast_vote(proposal.proposal_id, "alice", approved=True, identity_verified=True)
        qp.cast_vote(proposal.proposal_id, "bob", approved=True, identity_verified=True)
        quorum = qp.check_quorum(proposal.proposal_id, Sensitivity.HIGH)
        assert quorum.quorum_met

        # 3. Boundary warns but passes
        check = enforcer.check_proposal(proposal)
        assert check.passed
        assert len(check.warnings) > 0

        # 4. Record proof
        proof = audit.record_check(check)
        assert proof.all_checks_passed
