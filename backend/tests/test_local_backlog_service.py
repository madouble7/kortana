from unittest.mock import AsyncMock, MagicMock

import pytest
from src.kortana.models import GitHubTask
from src.kortana.services.local_backlog_service import LocalBacklogService
from src.kortana.services.operator_directive_service import DirectiveSummary


@pytest.mark.asyncio
async def test_discover_workspace_tasks_creates_local_task(monkeypatch) -> None:
    monkeypatch.setenv("KORTANA_LOCAL_BACKLOG_ENABLED", "true")

    session = AsyncMock()
    session.add = MagicMock()
    active_result = MagicMock()
    active_result.scalar_one_or_none.return_value = None
    existing_result = MagicMock()
    existing_result.scalar_one_or_none.return_value = None
    next_issue_result = MagicMock()
    next_issue_result.scalar_one_or_none.return_value = None
    # Extra result for PromptAssemblyService.load_profile identity query
    profile_result = MagicMock()
    mock_profile = MagicMock()
    mock_profile.name = "kor'tana"
    mock_profile.mission = "test mission"
    profile_result.scalars.return_value.first.return_value = mock_profile
    session.execute.side_effect = [
        active_result,
        existing_result,
        profile_result,
        next_issue_result,
    ]

    service = LocalBacklogService(session)
    tasks = await service.discover_workspace_tasks(
        workspace_status={
            "branch": "main",
            "dirty": True,
            "changed_count": 3,
            "changed_files": [
                "backend/src/kortana/services/autonomy_daemon.py",
                "backend/tests/test_autonomy_daemon.py",
            ],
        },
        guidance=DirectiveSummary(focus_topics=["autonomy", "tests"]),
    )

    assert len(tasks) == 1
    task = tasks[0]
    assert task.github_repo == "local/workspace"
    assert task.github_issue_number == -1
    assert task.classification == "local"
    assert task.branch_name.startswith("auto/local/1-")
    assert "[LOCAL-TASK-ANCHOR]" in task.description
    session.add.assert_called_once_with(task)
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_manifest_self_repair_creates_local_backlog_task(monkeypatch) -> None:
    monkeypatch.setenv("KORTANA_LOCAL_BACKLOG_ENABLED", "true")

    session = AsyncMock()
    session.add = MagicMock()
    existing_result = MagicMock()
    existing_result.scalar_one_or_none.return_value = None
    next_issue_result = MagicMock()
    next_issue_result.scalar_one_or_none.return_value = -4
    # Extra result for PromptAssemblyService.load_profile identity query
    profile_result = MagicMock()
    mock_profile = MagicMock()
    mock_profile.name = "kor'tana"
    mock_profile.mission = "test mission"
    profile_result.scalars.return_value.first.return_value = mock_profile
    session.execute.side_effect = [existing_result, profile_result, next_issue_result]

    failed_task = GitHubTask(
        id="task-fail",
        github_issue_number=110,
        github_repo="madouble7/kortana",
        title="Broken pipeline",
        description="desc",
        status="failed",
        error_message="planner crashed",
    )

    service = LocalBacklogService(session)
    task = await service.manifest_self_repair(
        failed_task=failed_task,
        repair_anchor="[SELF-REPAIR-ANCHOR] task:task-fail",
    )

    assert task is not None
    assert task.github_repo == "local/self-heal"
    assert task.github_issue_number == -5
    assert task.classification == "self_repair"
    assert task.branch_name.startswith("auto/self-repair/5-")
    assert "planner crashed" in task.description
    session.add.assert_called_once_with(task)
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_discover_workspace_tasks_no_reseed_after_execution(monkeypatch) -> None:
    """Regression: same anchor must not re-seed after a task reaches executed/failed."""
    monkeypatch.setenv("KORTANA_LOCAL_BACKLOG_ENABLED", "true")

    session = AsyncMock()
    session.add = MagicMock()

    # Simulate: no active task in-flight (active query returns None)
    active_result = MagicMock()
    active_result.scalar_one_or_none.return_value = None

    # Simulate: a previously executed task that carries the same anchor is found
    executed_task = GitHubTask(
        id="task-executed",
        github_issue_number=-10,
        github_repo="local/workspace",
        title="Reconcile local workspace changes",
        description="[LOCAL-TASK-ANCHOR] workspace:abc123def456",
        status="executed",
    )
    existing_result = MagicMock()
    existing_result.scalar_one_or_none.return_value = executed_task

    session.execute.side_effect = [active_result, existing_result]

    service = LocalBacklogService(session)

    # Monkeypatch the anchor method to return a known value matching the executed task
    monkeypatch.setattr(
        LocalBacklogService,
        "_workspace_anchor",
        staticmethod(
            lambda *_args, **_kwargs: "[LOCAL-TASK-ANCHOR] workspace:abc123def456"
        ),
    )

    tasks = await service.discover_workspace_tasks(
        workspace_status={
            "branch": "main",
            "dirty": True,
            "changed_count": 2,
            "changed_files": ["backend/src/kortana/services/autonomy_daemon.py"],
        },
        guidance=DirectiveSummary(),
    )

    assert tasks == [], (
        "Should not re-seed when the same anchor was previously executed"
    )
    session.add.assert_not_called()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_discover_workspace_tasks_no_reseed_after_failure(monkeypatch) -> None:
    """Regression: same anchor must not re-seed after a task reaches failed state."""
    monkeypatch.setenv("KORTANA_LOCAL_BACKLOG_ENABLED", "true")

    session = AsyncMock()
    session.add = MagicMock()

    active_result = MagicMock()
    active_result.scalar_one_or_none.return_value = None

    failed_task = GitHubTask(
        id="task-failed",
        github_issue_number=-11,
        github_repo="local/workspace",
        title="Reconcile local workspace changes",
        description="[LOCAL-TASK-ANCHOR] workspace:deadbeef1234",
        status="failed",
    )
    existing_result = MagicMock()
    existing_result.scalar_one_or_none.return_value = failed_task

    session.execute.side_effect = [active_result, existing_result]

    service = LocalBacklogService(session)

    monkeypatch.setattr(
        LocalBacklogService,
        "_workspace_anchor",
        staticmethod(
            lambda *_args, **_kwargs: "[LOCAL-TASK-ANCHOR] workspace:deadbeef1234"
        ),
    )

    tasks = await service.discover_workspace_tasks(
        workspace_status={
            "branch": "main",
            "dirty": True,
            "changed_count": 1,
            "changed_files": ["backend/src/kortana/services/autonomy_daemon.py"],
        },
        guidance=DirectiveSummary(),
    )

    assert tasks == [], "Should not re-seed when the same anchor previously failed"
    session.add.assert_not_called()
    session.commit.assert_not_awaited()
