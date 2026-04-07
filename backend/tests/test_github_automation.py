"""
Unit tests for GitHub automation engine
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.kortana.github_automation import (
    GitHubAutomationEngine,
    GitHubIssue,
    IssueAnalysis,
    ExecutionPlan,
)


@pytest.fixture
def github_engine():
    """Fixture for GitHub automation engine"""
    with patch.dict('os.environ', {
        'GITHUB_TOKEN': 'test_token',
        'GITHUB_OWNER': 'test-owner',
        'GITHUB_REPO': 'test-repo',
        'GEMINI_API_KEY': 'test_key',
    }):
        engine = GitHubAutomationEngine()
        engine.gh = Mock()
        return engine


@pytest.fixture
def sample_issue():
    """Fixture for sample GitHub issue"""
    return GitHubIssue(
        number=123,
        title="Add feature X",
        body="This is a feature request for X",
        author="testuser",
        labels=["enhancement", "backend"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        html_url="https://github.com/test/repo/issues/123",
    )


@pytest.mark.asyncio
async def test_issue_analysis(github_engine, sample_issue):
    """Test issue analysis with LLM"""
    with patch.object(github_engine.llm, 'generate', return_value=Mock(
        content='{"priority": "high", "complexity": "simple", "estimated_effort": "1 day", "skill_required": ["Python"], "suggested_approach": "Test", "potential_risks": [], "success_criteria": ["Done"]}'
    )):
        analysis = await github_engine.analyze_issue(sample_issue)
        assert isinstance(analysis, IssueAnalysis)
        assert analysis.priority == "high"
        assert analysis.complexity == "simple"


@pytest.mark.asyncio
async def test_execution_plan_creation(github_engine, sample_issue):
    """Test execution plan creation"""
    analysis = IssueAnalysis(
        priority="high",
        complexity="simple",
        estimated_effort="1 day",
        skill_required=["Python"],
        suggested_approach="Implement the feature",
        potential_risks=[],
        success_criteria=["Feature works"],
    )

    with patch.object(github_engine.llm, 'generate', return_value=Mock(
        content='{"steps": ["Step 1", "Step 2"], "file_changes": ["file.py"], "tests_required": ["test"], "estimated_duration": "1 day", "rollback_strategy": "Revert"}'
    )):
        plan = await github_engine.create_execution_plan(sample_issue, analysis)
        assert isinstance(plan, ExecutionPlan)
        assert len(plan.steps) > 0


@pytest.mark.asyncio
async def test_process_issue_webhook(github_engine, sample_issue):
    """Test GitHub webhook processing"""
    payload = {
        "action": "opened",
        "issue": {
            "number": 123,
            "title": "Test issue",
            "body": "Test body",
            "user": {"login": "testuser"},
            "labels": [{"name": "enhancement"}],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "html_url": "https://github.com/test/repo/issues/123",
        },
    }

    with patch.object(github_engine, 'analyze_issue', return_value=IssueAnalysis(
        priority="high",
        complexity="simple",
        estimated_effort="1 day",
        skill_required=["Python"],
        suggested_approach="Test",
        potential_risks=[],
        success_criteria=[],
    )):
        with patch.object(github_engine, 'create_execution_plan', return_value=ExecutionPlan(
            steps=["Step 1"],
            file_changes=[],
            tests_required=[],
            estimated_duration="1 day",
            rollback_strategy="Revert",
        )):
            result = await github_engine.process_issue_webhook(payload)
            assert result["status"] in ["analyzed", "skipped"]


@pytest.mark.asyncio
async def test_webhook_skip_excluded_labels(github_engine):
    """Test webhook skips issues with excluded labels"""
    payload = {
        "action": "opened",
        "issue": {
            "number": 123,
            "title": "Test issue",
            "body": "Test body",
            "user": {"login": "testuser"},
            "labels": [{"name": "wontfix"}],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "html_url": "https://github.com/test/repo/issues/123",
        },
    }

    result = await github_engine.process_issue_webhook(payload)
    assert result["status"] == "skipped"
    assert "excluded_label" in result.get("reason", "")
