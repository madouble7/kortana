from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.kortana.models import GitHubTask
from src.kortana.services.task_approval_service import TaskApprovalService


@pytest.mark.asyncio
async def test_self_aware_approval_holds_high_risk_task(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("KORTANA_SELF_AWARE_APPROVAL", "true")
    session = AsyncMock()
    service = TaskApprovalService(session)
    task = GitHubTask(
        id="task-risky",
        github_issue_number=101,
        github_repo="madouble7/kortana",
        title="Refactor models and database",
        description="high risk",
        priority="high",
        classification="approval",
        plan=(
            '{"FILE_CHANGES":['
            '{"file":"backend/src/kortana/models.py","action":"modify"},'
            '{"file":"backend/src/kortana/database.py","action":"modify"}'
            "]}"
        ),
    )

    decision = await service.evaluate_task(
        task,
        approval_mode="self-aware",
        system_state="degraded",
        runtime_profile={"execution_confidence": 0.61},
        workspace_status={"changed_count": 120},
    )

    assert decision is not None
    assert decision.approved is False
    assert decision.review_required is True
    assert decision.reason_code == "self_approval_hold"
    assert decision.risk_level in {"medium", "high"}


@pytest.mark.asyncio
async def test_self_aware_approval_auto_approves_low_risk_task(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("KORTANA_SELF_AWARE_APPROVAL", "true")
    session = AsyncMock()
    service = TaskApprovalService(session)
    task = GitHubTask(
        id="task-safe",
        github_issue_number=102,
        github_repo="madouble7/kortana",
        title="Tighten flaky test assertion",
        description="low risk",
        priority="low",
        classification="auto",
        plan='{"FILE_CHANGES":[{"file":"backend/tests/test_autonomy_daemon.py","action":"modify"}]}',
    )

    decision = await service.evaluate_task(
        task,
        approval_mode="self-aware",
        system_state="nominal",
        runtime_profile={"execution_confidence": 0.92},
        workspace_status={"changed_count": 4},
    )

    assert decision is not None
    assert decision.approved is True
    assert decision.review_required is False
    assert decision.reason_code == "self_approved"
    assert decision.risk_level == "low"


@pytest.mark.asyncio
async def test_self_aware_approval_holds_when_validation_blocks_protected_paths(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("KORTANA_SELF_AWARE_APPROVAL", "true")
    session = AsyncMock()
    service = TaskApprovalService(session)
    task = GitHubTask(
        id="task-guarded",
        github_issue_number=150,
        github_repo="madouble7/kortana",
        title="Touch protected config",
        description="guardrail check",
        priority="medium",
        classification="auto",
        plan='{"FILE_CHANGES":[{"file":"backend/src/kortana/demo.py","action":"modify"}]}',
        validation_report={
            "stage": "planning_complete",
            "blocked_paths": [".env"],
            "planned_tests": [],
            "validation_notes": [".env: path matches protected pattern .env"],
            "validations": [
                {"name": "repo_grounding", "status": "adjusted"},
                {"name": "protected_path_guard", "status": "blocked"},
            ],
        },
    )

    decision = await service.evaluate_task(
        task,
        approval_mode="self-aware",
        system_state="nominal",
        runtime_profile={"execution_confidence": 0.91},
        workspace_status={"changed_count": 3},
    )

    assert decision is not None
    assert decision.approved is False
    assert decision.review_required is True
    assert "validation:blocked_paths" in decision.factors
    assert decision.validation_summary["blocked_paths"] == [".env"]
    assert decision.validation_summary["failed_validations"] == ["protected_path_guard"]


@pytest.mark.asyncio
async def test_auto_approval_bypasses_risk_holds(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("KORTANA_DEFAULT_APPROVAL_MODE", "auto")
    session = AsyncMock()
    service = TaskApprovalService(session)
    task = GitHubTask(
        id="task-full-send",
        github_issue_number=111,
        github_repo="madouble7/kortana",
        title="Rewrite critical runtime",
        description="high risk but auto-approved",
        priority="high",
        classification="approval",
        plan=(
            '{"FILE_CHANGES":['
            '{"file":"backend/src/kortana/models.py","action":"modify"},'
            '{"file":"backend/src/kortana/database.py","action":"modify"}'
            "]}"
        ),
    )

    decision = await service.evaluate_task(
        task,
        approval_mode=None,
        system_state="critical",
        runtime_profile={"execution_confidence": 0.1},
        workspace_status={"changed_count": 999},
    )

    assert decision is not None
    assert decision.mode == "auto"
    assert decision.approved is True
    assert decision.review_required is False
    assert decision.reason_code == "auto_approved"


@pytest.mark.asyncio
async def test_record_decision_moves_task_into_approval_queue():
    session = AsyncMock()
    session.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
    )
    session.flush = AsyncMock()
    session.add = MagicMock()
    service = TaskApprovalService(session)

    task = GitHubTask(
        id="task-queue",
        github_issue_number=103,
        github_repo="madouble7/kortana",
        title="Queue me",
        description="desc",
        status="planning_complete",
    )

    decision = await service.evaluate_task(
        task,
        approval_mode="manual",
        system_state="nominal",
        runtime_profile={"execution_confidence": 0.9},
        workspace_status={"changed_count": 1},
    )

    assert decision is not None
    approval = await service.record_decision(task, decision)

    assert task.status == "waiting_for_approval"
    assert approval.status == "pending"
    assert approval.decision_factors["validation_summary"]["report_present"] is False
    session.add.assert_called_once()


@pytest.mark.asyncio
async def test_record_decision_marks_auto_mode_as_autonomous():
    session = AsyncMock()
    session.execute = AsyncMock(
        side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
        ]
    )
    session.flush = AsyncMock()
    session.add = MagicMock()
    service = TaskApprovalService(session)

    task = GitHubTask(
        id="task-auto",
        github_issue_number=112,
        github_repo="madouble7/kortana",
        title="Auto all the way",
        description="desc",
        status="planning_complete",
    )

    decision = await service.evaluate_task(
        task,
        approval_mode="auto",
        system_state="critical",
        runtime_profile={"execution_confidence": 0.01},
        workspace_status={"changed_count": 999},
    )

    assert decision is not None
    approval = await service.record_decision(task, decision)

    assert approval.status == "auto_approved"
    assert approval.reviewer == "autonomous"


@pytest.mark.asyncio
async def test_record_decision_persists_validation_summary():
    session = AsyncMock()
    session.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
    )
    session.flush = AsyncMock()
    session.add = MagicMock()
    service = TaskApprovalService(session)

    task = GitHubTask(
        id="task-validation",
        github_issue_number=151,
        github_repo="madouble7/kortana",
        title="Approval payload",
        description="desc",
        status="planning_complete",
        priority="medium",
        validation_report={
            "stage": "planning_complete",
            "blocked_paths": [".env"],
            "planned_tests": [
                "python -m pytest backend/tests/test_task_approval_service.py -q"
            ],
            "validations": [
                {"name": "protected_path_guard", "status": "blocked"},
            ],
        },
    )

    decision = await service.evaluate_task(
        task,
        approval_mode="manual",
        system_state="nominal",
        runtime_profile={"execution_confidence": 0.9},
        workspace_status={"changed_count": 2},
    )

    assert decision is not None
    approval = await service.record_decision(task, decision)

    assert approval.decision_factors["validation_summary"]["blocked_paths"] == [".env"]
    assert approval.decision_factors["validation_summary"]["report_present"] is True


@pytest.mark.asyncio
async def test_approve_task_reactivates_planning_complete():
    session = AsyncMock()
    task = GitHubTask(
        id="task-review",
        github_issue_number=104,
        github_repo="madouble7/kortana",
        title="Review me",
        description="desc",
        status="waiting_for_approval",
        classification="approval",
    )
    approval_row = MagicMock(
        status="pending",
        review_required=True,
        created_at=None,
        updated_at=None,
    )
    session.execute = AsyncMock(
        side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=task)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=approval_row)),
        ]
    )
    session.flush = AsyncMock()
    session.add = MagicMock()
    service = TaskApprovalService(session)

    result = await service.approve_task(
        "task-review",
        approved=True,
        reviewer="operator",
        notes="ship it",
    )

    assert result.status == "planning_complete"
    assert result.classification == "auto"
    assert approval_row.status == "approved"
