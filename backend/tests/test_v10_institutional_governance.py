"""V10 — Institutional-grade governance tests.

Tests for operator identity, auth context, deploy gate, and policy engine.
"""

from datetime import datetime

import pytest


# ---------------------------------------------------------------------------
# V10A — Operator identity tests
# ---------------------------------------------------------------------------

class TestOperatorRole:
    """OperatorRole enum tests."""

    def test_roles_defined(self):
        from src.kortana.services.operator_identity import OperatorRole
        assert OperatorRole.ADMIN == "admin"
        assert OperatorRole.OPERATOR == "operator"
        assert OperatorRole.REVIEWER == "reviewer"
        assert OperatorRole.VIEWER == "viewer"
        assert OperatorRole.ONCALL == "oncall"

    def test_invalid_role_raises(self):
        from src.kortana.services.operator_identity import OperatorRole
        with pytest.raises(ValueError):
            OperatorRole("nonexistent")


class TestPermissionMatrix:
    """ROLE_PERMISSIONS mapping tests."""

    def test_admin_has_all_permissions(self):
        from src.kortana.services.operator_identity import (
            ROLE_PERMISSIONS,
            OperatorRole,
            Permission,
        )
        admin_perms = ROLE_PERMISSIONS[OperatorRole.ADMIN]
        for p in Permission:
            assert p in admin_perms, f"ADMIN missing {p}"

    def test_viewer_has_only_view(self):
        from src.kortana.services.operator_identity import (
            ROLE_PERMISSIONS,
            OperatorRole,
            Permission,
        )
        viewer_perms = ROLE_PERMISSIONS[OperatorRole.VIEWER]
        assert Permission.CONTROL_ROOM_VIEW in viewer_perms
        assert len(viewer_perms) == 1

    def test_oncall_no_policy_manage(self):
        from src.kortana.services.operator_identity import (
            ROLE_PERMISSIONS,
            OperatorRole,
            Permission,
        )
        oncall_perms = ROLE_PERMISSIONS[OperatorRole.ONCALL]
        assert Permission.POLICY_MANAGE not in oncall_perms


class TestOperatorIdentity:
    """OperatorIdentity dataclass tests."""

    def test_create_identity(self):
        from src.kortana.services.operator_identity import OperatorIdentity, OperatorRole
        ident = OperatorIdentity(
            operator_id="test-op",
            display_name="Test",
            role=OperatorRole.OPERATOR,
        )
        assert ident.operator_id == "test-op"
        assert ident.active is True
        assert ident.identity_hash
        assert len(ident.identity_hash) == 64

    def test_identity_hash_deterministic(self):
        from src.kortana.services.operator_identity import OperatorIdentity, OperatorRole
        now = datetime.utcnow()
        a = OperatorIdentity("x", "X", OperatorRole.ADMIN, created_at=now)
        b = OperatorIdentity("x", "X", OperatorRole.ADMIN, created_at=now)
        assert a.identity_hash == b.identity_hash

    def test_has_permission(self):
        from src.kortana.services.operator_identity import (
            OperatorIdentity,
            OperatorRole,
            Permission,
        )
        admin = OperatorIdentity("a", "A", OperatorRole.ADMIN)
        assert admin.has_permission(Permission.DEPLOY_APPROVE)

    def test_to_dict_contains_keys(self):
        from src.kortana.services.operator_identity import OperatorIdentity, OperatorRole
        d = OperatorIdentity("op1", "Op One", OperatorRole.REVIEWER).to_dict()
        assert "operator_id" in d
        assert "role" in d
        assert "permissions" in d


class TestOperatorRegistry:
    """OperatorRegistry tests."""

    def test_register_and_get(self):
        from src.kortana.services.operator_identity import OperatorRegistry, OperatorRole
        reg = OperatorRegistry()
        reg.register("r1", "R1", OperatorRole.OPERATOR)
        op = reg.get("r1")
        assert op is not None
        assert op.display_name == "R1"

    def test_register_duplicate_raises(self):
        from src.kortana.services.operator_identity import OperatorRegistry, OperatorRole
        reg = OperatorRegistry()
        reg.register("dup", "D", OperatorRole.VIEWER)
        with pytest.raises(ValueError, match="already registered"):
            reg.register("dup", "D2", OperatorRole.VIEWER)

    def test_deactivate_and_activate(self):
        from src.kortana.services.operator_identity import OperatorRegistry, OperatorRole
        reg = OperatorRegistry()
        reg.register("da", "DA", OperatorRole.OPERATOR)
        assert reg.deactivate("da") is True
        assert reg.get("da").active is False
        assert reg.activate("da") is True
        assert reg.get("da").active is True

    def test_update_role(self):
        from src.kortana.services.operator_identity import OperatorRegistry, OperatorRole
        reg = OperatorRegistry()
        reg.register("ur", "UR", OperatorRole.VIEWER)
        assert reg.update_role("ur", OperatorRole.ADMIN) is True
        assert reg.get("ur").role == OperatorRole.ADMIN

    def test_check_permission(self):
        from src.kortana.services.operator_identity import (
            OperatorRegistry,
            OperatorRole,
            Permission,
        )
        reg = OperatorRegistry()
        reg.register("cp", "CP", OperatorRole.OPERATOR)
        result = reg.check("cp", Permission.DRILL_RUN)
        assert result.allowed is True

    def test_check_missing_operator(self):
        from src.kortana.services.operator_identity import (
            OperatorRegistry,
            Permission,
        )
        reg = OperatorRegistry()
        result = reg.check("no-one", Permission.DEPLOY_GATE)
        assert result.allowed is False

    def test_default_registry_has_matt(self):
        from src.kortana.services.operator_identity import get_operator_registry
        reg = get_operator_registry()
        matt = reg.get("matt")
        assert matt is not None
        assert matt.role.value == "admin"


# ---------------------------------------------------------------------------
# V10B — Auth context tests
# ---------------------------------------------------------------------------


class TestAuthContext:
    """AuthContext dataclass tests."""

    def test_from_operator(self):
        from src.kortana.services.operator_identity import OperatorIdentity, OperatorRole
        from src.kortana.services.auth_context import AuthContext
        ident = OperatorIdentity("ac", "AC", OperatorRole.ADMIN)
        ctx = AuthContext.from_operator(ident)
        assert ctx.operator_id == "ac"
        assert ctx.identity_hash == ident.identity_hash

    def test_sign_action(self):
        from src.kortana.services.operator_identity import OperatorIdentity, OperatorRole
        from src.kortana.services.auth_context import AuthContext
        ident = OperatorIdentity("sa", "SA", OperatorRole.OPERATOR)
        ctx = AuthContext.from_operator(ident)
        signed = ctx.sign_action("deploy", "canary-1")
        assert signed.action == "deploy"
        assert signed.resource == "canary-1"
        assert len(signed.action_signature) == 64


class TestSignedAction:
    """SignedAction verification tests."""

    def test_signature_changes_with_action(self):
        from src.kortana.services.operator_identity import OperatorIdentity, OperatorRole
        from src.kortana.services.auth_context import AuthContext
        ident = OperatorIdentity("sv", "SV", OperatorRole.ADMIN)
        ctx = AuthContext.from_operator(ident)
        a = ctx.sign_action("deploy", "r1")
        b = ctx.sign_action("rollback", "r1")
        assert a.action_signature != b.action_signature


class TestGovernanceActionLog:
    """GovernanceActionLog tests."""

    def test_record_and_retrieve(self):
        from src.kortana.services.auth_context import GovernanceActionLog
        from src.kortana.services.operator_identity import OperatorIdentity, OperatorRole
        from src.kortana.services.auth_context import AuthContext

        log = GovernanceActionLog()
        ident = OperatorIdentity("gl", "GL", OperatorRole.OPERATOR)
        ctx = AuthContext.from_operator(ident)
        signed = ctx.sign_action("override", "mode-auto")
        log.record(signed)
        assert log.count == 1
        assert len(log.actions_by_operator("gl")) == 1
        assert len(log.actions_by_resource("mode-auto")) == 1

    def test_empty_log(self):
        from src.kortana.services.auth_context import GovernanceActionLog
        log = GovernanceActionLog()
        assert log.count == 0
        assert log.all_actions == []


class TestResolveAuthContext:
    """resolve_auth_context integration tests."""

    def test_resolve_known_operator(self):
        from src.kortana.services.auth_context import resolve_auth_context
        ctx, err = resolve_auth_context("matt")
        assert ctx is not None
        assert err is None
        assert ctx.operator_id == "matt"

    def test_resolve_unknown_operator(self):
        from src.kortana.services.auth_context import resolve_auth_context
        ctx, err = resolve_auth_context("ghost")
        assert ctx is None
        assert err is not None

    def test_resolve_with_permission_check(self):
        from src.kortana.services.auth_context import resolve_auth_context
        from src.kortana.services.operator_identity import Permission
        ctx, err = resolve_auth_context("matt", Permission.DEPLOY_APPROVE)
        assert ctx is not None
        assert err is None


# ---------------------------------------------------------------------------
# V10C — Deploy gate tests
# ---------------------------------------------------------------------------


class TestDeployGateBasic:
    """Basic deploy gate tests."""

    def test_gate_passes_for_admin(self):
        from src.kortana.services.deploy_gate import evaluate_deploy_gate
        result = evaluate_deploy_gate(
            operator_id="matt",
            target_mode=None,
            current_mode="manual",
        )
        assert result.allowed is True
        assert len(result.blocking_failures) == 0
        assert result.gate_hash
        assert len(result.gate_hash) == 64

    def test_gate_fails_unknown_operator(self):
        from src.kortana.services.deploy_gate import evaluate_deploy_gate
        result = evaluate_deploy_gate(
            operator_id="unknown-person",
            target_mode=None,
            current_mode="manual",
        )
        assert result.allowed is False
        assert any(c.name == "operator_identity" for c in result.checks)


class TestDeployGateChecks:
    """Deploy gate individual check tests."""

    def test_override_conflict_check(self):
        from src.kortana.services.deploy_gate import evaluate_deploy_gate
        result = evaluate_deploy_gate(
            operator_id="matt",
            target_mode="auto",
            current_mode="manual",
            active_override_mode="manual",
        )
        check = next(c for c in result.checks if c.name == "override_conflict")
        assert check.passed is False

    def test_slo_violation_blocks(self):
        from src.kortana.services.deploy_gate import evaluate_deploy_gate
        result = evaluate_deploy_gate(
            operator_id="matt",
            target_mode=None,
            current_mode="manual",
            drill_slo_results=[{"met": False, "name": "uptime"}],
        )
        check = next(c for c in result.checks if c.name == "drill_slo_health")
        assert check.passed is False

    def test_gate_result_to_dict(self):
        from src.kortana.services.deploy_gate import evaluate_deploy_gate
        result = evaluate_deploy_gate(
            operator_id="matt",
            target_mode=None,
            current_mode="manual",
        )
        d = result.to_dict()
        assert "allowed" in d
        assert "checks" in d
        assert "gate_hash" in d


# ---------------------------------------------------------------------------
# V10D — Policy engine tests
# ---------------------------------------------------------------------------


class TestPolicyRule:
    """PolicyRule evaluation tests."""

    def test_simple_match(self):
        from src.kortana.services.policy_engine import PolicyRule, RuleAction, RulePriority
        rule = PolicyRule(
            rule_id="test-1",
            name="test",
            description="test rule",
            conditions={"x": 1},
            action=RuleAction.ALLOW,
            priority=RulePriority.DEFAULT,
        )
        assert rule.evaluate({"x": 1}) is True
        assert rule.evaluate({"x": 2}) is False

    def test_operator_conditions(self):
        from src.kortana.services.policy_engine import PolicyRule, RuleAction, RulePriority
        rule = PolicyRule(
            rule_id="test-gt",
            name="gt test",
            description="greater than",
            conditions={"score": {"op": "gt", "value": 50}},
            action=RuleAction.ALLOW,
            priority=RulePriority.DEFAULT,
        )
        assert rule.evaluate({"score": 80}) is True
        assert rule.evaluate({"score": 30}) is False

    def test_in_operator(self):
        from src.kortana.services.policy_engine import PolicyRule, RuleAction, RulePriority
        rule = PolicyRule(
            rule_id="test-in",
            name="in test",
            description="in list",
            conditions={"mode": {"op": "in", "value": ["auto", "semi"]}},
            action=RuleAction.ALLOW,
            priority=RulePriority.DEFAULT,
        )
        assert rule.evaluate({"mode": "auto"}) is True
        assert rule.evaluate({"mode": "manual"}) is False

    def test_is_true_operator(self):
        from src.kortana.services.policy_engine import PolicyRule, RuleAction, RulePriority
        rule = PolicyRule(
            rule_id="test-bool",
            name="bool test",
            description="is_true",
            conditions={"active": {"op": "is_true", "value": True}},
            action=RuleAction.DENY,
            priority=RulePriority.HIGH,
        )
        assert rule.evaluate({"active": True}) is True
        assert rule.evaluate({"active": False}) is False

    def test_to_dict(self):
        from src.kortana.services.policy_engine import PolicyRule, RuleAction, RulePriority
        rule = PolicyRule("r1", "R1", "desc", {}, RuleAction.HOLD, RulePriority.MEDIUM)
        d = rule.to_dict()
        assert d["rule_id"] == "r1"
        assert d["action"] == "hold"


class TestPolicyEngine:
    """PolicyEngine evaluation tests."""

    def test_add_and_evaluate(self):
        from src.kortana.services.policy_engine import (
            PolicyEngine,
            PolicyRule,
            RuleAction,
            RulePriority,
        )
        engine = PolicyEngine()
        engine.add_rule(PolicyRule(
            "e1", "E1", "test", {"x": True}, RuleAction.DENY, RulePriority.HIGH,
        ))
        engine.add_rule(PolicyRule(
            "e2", "E2", "fallback", {}, RuleAction.ALLOW, RulePriority.DEFAULT,
        ))
        decision = engine.evaluate({"x": True})
        assert decision.action == "deny"

    def test_priority_ordering(self):
        from src.kortana.services.policy_engine import (
            PolicyEngine,
            PolicyRule,
            RuleAction,
            RulePriority,
        )
        engine = PolicyEngine()
        engine.add_rule(PolicyRule(
            "lo", "Lo", "low", {"a": 1}, RuleAction.ALLOW, RulePriority.LOW,
        ))
        engine.add_rule(PolicyRule(
            "hi", "Hi", "high", {"a": 1}, RuleAction.DENY, RulePriority.CRITICAL,
        ))
        decision = engine.evaluate({"a": 1})
        assert decision.action == "deny"

    def test_no_match_defaults_hold(self):
        from src.kortana.services.policy_engine import PolicyEngine
        engine = PolicyEngine()
        decision = engine.evaluate({"nothing": True})
        assert decision.action == "hold"

    def test_remove_rule(self):
        from src.kortana.services.policy_engine import (
            PolicyEngine,
            PolicyRule,
            RuleAction,
            RulePriority,
        )
        engine = PolicyEngine()
        engine.add_rule(PolicyRule("rm1", "RM", "x", {}, RuleAction.DENY, RulePriority.HIGH))
        assert engine.count == 1
        assert engine.remove_rule("rm1") is True
        assert engine.count == 0

    def test_count(self):
        from src.kortana.services.policy_engine import PolicyEngine
        engine = PolicyEngine()
        assert engine.count == 0


class TestDefaultEngine:
    """Default governance engine tests."""

    def test_default_engine_has_rules(self):
        from src.kortana.services.policy_engine import create_default_engine
        engine = create_default_engine()
        assert engine.count == 6

    def test_override_blocks_deploy(self):
        from src.kortana.services.policy_engine import create_default_engine
        engine = create_default_engine()
        decision = engine.evaluate({
            "override_active": True,
            "deploy_requested": True,
            "in_cooldown": False,
            "drill_slos_met": True,
            "rate_limited": False,
            "quorum_pending": 0,
        })
        assert decision.action == "deny"

    def test_clean_state_allows(self):
        from src.kortana.services.policy_engine import create_default_engine
        engine = create_default_engine()
        decision = engine.evaluate({
            "override_active": False,
            "deploy_requested": False,
            "in_cooldown": False,
            "drill_slos_met": True,
            "rate_limited": False,
            "quorum_pending": 0,
        })
        assert decision.action == "allow"


class TestPolicyDecision:
    """PolicyDecision output tests."""

    def test_decision_hash_present(self):
        from src.kortana.services.policy_engine import PolicyEngine
        engine = PolicyEngine()
        decision = engine.evaluate({})
        assert len(decision.decision_hash) == 64

    def test_to_dict_keys(self):
        from src.kortana.services.policy_engine import PolicyEngine
        engine = PolicyEngine()
        d = engine.evaluate({}).to_dict()
        assert "action" in d
        assert "reason" in d
        assert "decision_hash" in d
        assert "matched_rules" in d
