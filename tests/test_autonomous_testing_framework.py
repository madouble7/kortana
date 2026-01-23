"""
Tests for the Autonomous Testing Framework

Tests all five core modules:
1. Self-testing mechanisms
2. Autonomous debugging capabilities
3. Feature self-expansion
4. Performance monitoring and improvement
5. Ethical compliance self-audit
"""


import pytest

from kortana.core.autonomous_testing_config import DEFAULT_CONFIG, FrameworkConfig
from kortana.core.autonomous_testing_framework import (
    AutonomousDebuggingModule,
    AutonomousTestingFramework,
    DebugStatus,
    EthicalComplianceModule,
    FeatureSelfExpansionModule,
    PerformanceMonitoringModule,
    SelfTestingModule,
    TestStatus,
)


class TestSelfTestingModule:
    """Tests for self-testing mechanisms"""

    @pytest.mark.asyncio
    async def test_generate_test(self):
        """Test that we can generate a test case"""
        module = SelfTestingModule()
        test_case = await module.generate_test("sample_function", "unit")

        assert test_case is not None
        assert test_case.test_type == "unit"
        assert "sample_function" in test_case.name
        assert test_case.status == TestStatus.PENDING
        assert test_case.test_id in module.test_cases

    @pytest.mark.asyncio
    async def test_execute_test(self):
        """Test that we can execute a test case"""
        module = SelfTestingModule()
        test_case = await module.generate_test("sample_function", "unit")

        result = await module.execute_test(test_case.test_id)

        assert result["success"] is True
        assert module.test_cases[test_case.test_id].status == TestStatus.PASSED
        assert len(module.test_history) == 1

    @pytest.mark.asyncio
    async def test_execute_nonexistent_test(self):
        """Test executing a test that doesn't exist"""
        module = SelfTestingModule()
        result = await module.execute_test("nonexistent_test_id")

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_analyze_test_results(self):
        """Test analyzing test results"""
        module = SelfTestingModule()
        test_case = await module.generate_test("sample_function", "unit")
        await module.execute_test(test_case.test_id)

        analysis = await module.analyze_test_results(test_case.test_id)

        assert analysis is not None
        assert analysis["test_id"] == test_case.test_id
        assert analysis["status"] == TestStatus.PASSED.value
        assert "insights" in analysis


class TestAutonomousDebuggingModule:
    """Tests for autonomous debugging capabilities"""

    @pytest.mark.asyncio
    async def test_scan_for_issues(self):
        """Test scanning for issues"""
        module = AutonomousDebuggingModule()
        issues = await module.scan_for_issues("test/path")

        assert isinstance(issues, list)
        assert len(issues) > 0
        assert issues[0].issue_id in module.issues

    @pytest.mark.asyncio
    async def test_analyze_issue(self):
        """Test analyzing an issue"""
        module = AutonomousDebuggingModule()
        issues = await module.scan_for_issues()
        issue_id = issues[0].issue_id

        analysis = await module.analyze_issue(issue_id)

        assert "issue_id" in analysis
        assert analysis["issue_id"] == issue_id
        assert "root_cause" in analysis
        assert module.issues[issue_id].status == DebugStatus.ANALYZING

    @pytest.mark.asyncio
    async def test_attempt_fix(self):
        """Test attempting to fix an issue"""
        module = AutonomousDebuggingModule()
        issues = await module.scan_for_issues()
        issue_id = issues[0].issue_id

        # Set issue to low severity so it can be auto-fixed
        module.issues[issue_id].severity = "low"

        fix_result = await module.attempt_fix(issue_id)

        assert "success" in fix_result
        assert len(module.issues[issue_id].fix_attempts) == 1
        assert len(module.fix_history) == 1


class TestFeatureSelfExpansionModule:
    """Tests for feature self-expansion"""

    @pytest.mark.asyncio
    async def test_set_guidelines(self):
        """Test setting guidelines"""
        module = FeatureSelfExpansionModule()
        guidelines = {"quality": {"min_score": 0.8}}

        module.set_guidelines(guidelines)

        assert "quality" in module.guidelines

    @pytest.mark.asyncio
    async def test_analyze_codebase(self):
        """Test codebase analysis"""
        module = FeatureSelfExpansionModule()
        opportunities = await module.analyze_codebase()

        assert isinstance(opportunities, list)
        assert len(opportunities) > 0

    @pytest.mark.asyncio
    async def test_suggest_improvement(self):
        """Test suggesting improvements"""
        module = FeatureSelfExpansionModule()
        suggestion = await module.suggest_improvement("performance")

        assert suggestion is not None
        assert suggestion.suggestion_id in module.suggestions
        assert "performance" in suggestion.title.lower()
        assert suggestion.approved is False

    @pytest.mark.asyncio
    async def test_implement_suggestion_not_approved(self):
        """Test that unapproved suggestions cannot be implemented"""
        module = FeatureSelfExpansionModule()
        suggestion = await module.suggest_improvement("performance")

        result = await module.implement_suggestion(suggestion.suggestion_id)

        assert "error" in result
        assert "not approved" in result["error"]

    @pytest.mark.asyncio
    async def test_implement_suggestion_approved(self):
        """Test implementing an approved suggestion"""
        module = FeatureSelfExpansionModule()
        suggestion = await module.suggest_improvement("performance")

        # Approve the suggestion
        module.suggestions[suggestion.suggestion_id].approved = True

        result = await module.implement_suggestion(suggestion.suggestion_id)

        assert result["success"] is True
        assert module.suggestions[suggestion.suggestion_id].implemented is True


class TestPerformanceMonitoringModule:
    """Tests for performance monitoring and improvement"""

    @pytest.mark.asyncio
    async def test_set_threshold(self):
        """Test setting a performance threshold"""
        module = PerformanceMonitoringModule()
        module.set_threshold("response_time", 100.0)

        assert "response_time" in module.thresholds
        assert module.thresholds["response_time"] == 100.0

    @pytest.mark.asyncio
    async def test_record_metric(self):
        """Test recording a performance metric"""
        module = PerformanceMonitoringModule()
        metric = await module.record_metric("response_time", 50.0, "ms")

        assert metric is not None
        assert metric.name == "response_time"
        assert metric.value == 50.0
        assert metric.status == "normal"
        assert "response_time" in module.metrics

    @pytest.mark.asyncio
    async def test_record_metric_exceeds_threshold(self):
        """Test recording a metric that exceeds threshold"""
        module = PerformanceMonitoringModule()
        module.set_threshold("response_time", 100.0)

        metric = await module.record_metric("response_time", 150.0, "ms")

        assert metric.status == "warning"

    @pytest.mark.asyncio
    async def test_analyze_trends(self):
        """Test analyzing performance trends"""
        module = PerformanceMonitoringModule()

        # Record multiple metrics
        await module.record_metric("response_time", 50.0, "ms")
        await module.record_metric("response_time", 60.0, "ms")
        await module.record_metric("response_time", 55.0, "ms")

        analysis = await module.analyze_trends("response_time")

        assert analysis is not None
        assert analysis["metric_name"] == "response_time"
        assert analysis["count"] == 3
        assert analysis["average"] == pytest.approx(55.0)
        assert analysis["min"] == 50.0
        assert analysis["max"] == 60.0

    @pytest.mark.asyncio
    async def test_suggest_optimizations(self):
        """Test suggesting optimizations"""
        module = PerformanceMonitoringModule()
        module.set_threshold("response_time", 100.0)

        # Record metrics near threshold
        for _ in range(10):
            await module.record_metric("response_time", 85.0, "ms")

        optimizations = await module.suggest_optimizations()

        assert isinstance(optimizations, list)
        assert len(optimizations) > 0
        assert optimizations[0]["metric"] == "response_time"


class TestEthicalComplianceModule:
    """Tests for ethical compliance self-audit"""

    @pytest.mark.asyncio
    async def test_default_guidelines(self):
        """Test that default guidelines are loaded"""
        module = EthicalComplianceModule()

        assert len(module.guidelines) > 0
        assert "transparency" in module.guidelines
        assert "no_harm" in module.guidelines
        assert "helpfulness" in module.guidelines

    @pytest.mark.asyncio
    async def test_update_guidelines(self):
        """Test updating guidelines"""
        module = EthicalComplianceModule()
        new_guidelines = {"custom_rule": {"description": "Test rule"}}

        module.update_guidelines(new_guidelines)

        assert "custom_rule" in module.guidelines

    @pytest.mark.asyncio
    async def test_audit_action_compliant(self):
        """Test auditing a compliant action"""
        module = EthicalComplianceModule()

        result = await module.audit_action(
            "read_file", {"logged": True, "user_approved": True}
        )

        assert result["compliant"] is True
        assert len(result["violations"]) == 0
        assert result["compliance_score"] >= 0.8

    @pytest.mark.asyncio
    async def test_audit_action_not_logged(self):
        """Test auditing an action that's not logged"""
        module = EthicalComplianceModule()

        result = await module.audit_action("read_file", {"logged": False})

        assert result["compliant"] is False
        assert len(result["violations"]) > 0

    @pytest.mark.asyncio
    async def test_audit_action_destructive_without_approval(self):
        """Test auditing a destructive action without approval"""
        module = EthicalComplianceModule()

        result = await module.audit_action(
            "delete_file", {"logged": True, "user_approved": False}
        )

        assert result["compliant"] is False
        assert any(v["guideline"] == "user_consent" for v in result["violations"])

    @pytest.mark.asyncio
    async def test_perform_self_audit(self):
        """Test performing a self-audit"""
        module = EthicalComplianceModule()

        audit_result = await module.perform_self_audit()

        assert audit_result is not None
        assert len(audit_result.guidelines_checked) > 0
        assert audit_result.compliance_score >= 0.0
        assert audit_result.compliance_score <= 1.0
        assert len(module.audit_history) == 1


class TestAutonomousTestingFramework:
    """Tests for the main framework orchestrator"""

    @pytest.mark.asyncio
    async def test_framework_initialization(self):
        """Test framework initialization"""
        framework = AutonomousTestingFramework()

        assert framework is not None
        assert framework.self_testing is not None
        assert framework.debugging is not None
        assert framework.feature_expansion is not None
        assert framework.performance_monitoring is not None
        assert framework.ethical_compliance is not None
        assert framework.active is False

    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test starting and stopping the framework"""
        framework = AutonomousTestingFramework()

        await framework.start()
        assert framework.active is True

        await framework.stop()
        assert framework.active is False

    @pytest.mark.asyncio
    async def test_run_cycle(self):
        """Test running a complete autonomous cycle"""
        framework = AutonomousTestingFramework()
        await framework.start()

        results = await framework.run_cycle()

        assert results is not None
        assert results["cycle_number"] == 1
        assert "modules" in results
        assert "ethical_audit" in results["modules"]
        assert "performance" in results["modules"]
        assert "testing" in results["modules"]
        assert "debugging" in results["modules"]
        assert "feature_expansion" in results["modules"]

    @pytest.mark.asyncio
    async def test_run_cycle_not_active(self):
        """Test that cycle fails when framework is not active"""
        framework = AutonomousTestingFramework()

        results = await framework.run_cycle()

        assert "error" in results

    @pytest.mark.asyncio
    async def test_get_status(self):
        """Test getting framework status"""
        framework = AutonomousTestingFramework()
        await framework.start()
        await framework.run_cycle()

        status = await framework.get_status()

        assert status is not None
        assert status["active"] is True
        assert status["cycles_completed"] == 1
        assert "modules" in status
        assert "self_testing" in status["modules"]


class TestFrameworkConfig:
    """Tests for framework configuration"""

    def test_default_config(self):
        """Test default configuration"""
        config = FrameworkConfig()

        assert config.enabled is True
        assert config.self_testing.enabled is True
        assert config.debugging.enabled is True
        assert config.feature_expansion.enabled is True
        assert config.performance.enabled is True
        assert config.ethical_compliance.enabled is True

    def test_config_from_dict(self):
        """Test creating config from dictionary"""
        config_dict = {
            "enabled": True,
            "cycle_interval_minutes": 30,
            "self_testing": {"enabled": True, "auto_generate_tests": False},
        }

        config = FrameworkConfig.from_dict(config_dict)

        assert config.enabled is True
        assert config.cycle_interval_minutes == 30
        assert config.self_testing.auto_generate_tests is False

    def test_config_to_dict(self):
        """Test converting config to dictionary"""
        config = FrameworkConfig()
        config_dict = config.to_dict()

        assert "enabled" in config_dict
        assert "self_testing" in config_dict
        assert "debugging" in config_dict
        assert "feature_expansion" in config_dict
        assert "performance" in config_dict
        assert "ethical_compliance" in config_dict

    def test_default_config_instance(self):
        """Test DEFAULT_CONFIG instance"""
        assert DEFAULT_CONFIG is not None
        assert DEFAULT_CONFIG.enabled is True
