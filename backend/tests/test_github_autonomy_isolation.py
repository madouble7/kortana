from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.kortana.models import GitHubTask
from src.kortana.services.github_autonomy_service import GitHubAutonomyService


@pytest.mark.asyncio
async def test_execute_task_uses_isolated_workspace(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")

    service = GitHubAutonomyService(db_session=MagicMock())
    service._db_commit = AsyncMock()
    service._db_rollback = AsyncMock()

    task = MagicMock(spec=GitHubTask)
    task.github_issue_number = 42
    task.github_repo = "madouble7/kortana"
    task.title = "Isolated execution"
    task.branch_name = "auto-fix/42-isolated-execution"
    task.plan = (
        '{"FILE_CHANGES":[{"file":"backend/src/kortana/demo.py",'
        '"action":"create","content":"print(1)\\n"}]}'
    )
    task.status = "planning_complete"
    task.error_count = 0
    task.commit_sha = None
    task.github_pr_number = None

    workspace = tmp_path / "task-worktree"
    generated = workspace / "backend" / "src" / "kortana" / "demo.py"
    generated.parent.mkdir(parents=True)
    generated.write_text("print(1)\n", encoding="utf-8")

    service._create_branch = AsyncMock(return_value=True)
    service._prepare_execution_workspace = AsyncMock(return_value=workspace)
    service._commit_workspace_changes = AsyncMock(return_value="abc123def")
    service._push_workspace_branch = AsyncMock(return_value=True)
    service._create_pull_request_for_branch = AsyncMock(return_value=99)
    service._cleanup_execution_workspace = AsyncMock()
    service.code_gen.generate_from_gemini_plan = MagicMock(
        return_value={
            "created": [str(generated)],
            "modified": [],
            "deleted": [],
            "errors": [],
        }
    )

    result = await service.execute_task(task)

    assert result is task
    assert task.status == "executed"
    assert task.commit_sha == "abc123def"
    assert task.github_pr_number == 99
    assert task.code_changes == ["backend/src/kortana/demo.py"]
    assert service.code_gen.generate_from_gemini_plan.call_args.kwargs[
        "repo_path"
    ] == str(workspace)
    service._commit_workspace_changes.assert_awaited_once_with(
        task, ["backend/src/kortana/demo.py"], workspace
    )
    service._push_workspace_branch.assert_awaited_once_with(task, workspace)
    service._cleanup_execution_workspace.assert_awaited_once_with(workspace)


@pytest.mark.asyncio
async def test_execute_task_skips_github_publish_when_mode_deferred(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setenv("KORTANA_GITHUB_MODE", "deferred")

    service = GitHubAutonomyService(db_session=MagicMock())
    service._db_commit = AsyncMock()
    service._db_rollback = AsyncMock()

    task = MagicMock(spec=GitHubTask)
    task.github_issue_number = 77
    task.github_repo = "madouble7/kortana"
    task.title = "Deferred publish"
    task.branch_name = "auto-fix/77-deferred-publish"
    task.plan = (
        '{"FILE_CHANGES":[{"file":"backend/src/kortana/demo.py",'
        '"action":"create","content":"print(2)\\n"}]}'
    )
    task.status = "planning_complete"
    task.error_count = 0
    task.commit_sha = None
    task.github_pr_number = None

    workspace = tmp_path / "task-worktree"
    generated = workspace / "backend" / "src" / "kortana" / "demo.py"
    generated.parent.mkdir(parents=True)
    generated.write_text("print(2)\n", encoding="utf-8")

    service._create_branch = AsyncMock(return_value=True)
    service._prepare_execution_workspace = AsyncMock(return_value=workspace)
    service._commit_workspace_changes = AsyncMock(return_value="feedface1234")
    service._push_workspace_branch = AsyncMock(return_value=True)
    service._create_pull_request_for_branch = AsyncMock(return_value=101)
    service._cleanup_execution_workspace = AsyncMock()
    service.code_gen.generate_from_gemini_plan = MagicMock(
        return_value={
            "created": [str(generated)],
            "modified": [],
            "deleted": [],
            "errors": [],
        }
    )

    result = await service.execute_task(task)

    assert result is task
    assert task.status == "executed"
    assert task.commit_sha == "feedface1234"
    assert task.github_pr_number is None
    service._create_branch.assert_not_awaited()
    service._push_workspace_branch.assert_not_awaited()
    service._create_pull_request_for_branch.assert_not_awaited()


def test_normalize_changed_files_relativizes_workspace_paths(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    service = GitHubAutonomyService(db_session=MagicMock())

    workspace = tmp_path / "wt"
    nested = workspace / "backend" / "src" / "kortana" / "demo.py"
    nested.parent.mkdir(parents=True)
    nested.write_text("print(1)\n", encoding="utf-8")

    normalized = service._normalize_changed_files([str(nested)], workspace)

    assert normalized == ["backend/src/kortana/demo.py"]


@pytest.mark.asyncio
async def test_commit_workspace_changes_uses_passed_workspace(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    service = GitHubAutonomyService(db_session=MagicMock())

    task = MagicMock(spec=GitHubTask)
    task.github_issue_number = 42
    task.title = "Isolated execution"
    task.branch_name = "auto-fix/42-isolated-execution"

    workspace = tmp_path / "task-worktree"
    workspace.mkdir()

    rev_parse = MagicMock(stdout="deadbeef12345678\n")
    service._run_git = MagicMock(side_effect=[None, None, rev_parse])

    commit_sha = await service._commit_workspace_changes(
        task,
        ["backend/src/kortana/demo.py"],
        workspace,
    )

    assert commit_sha == "deadbeef12345678"
    assert service._run_git.call_args_list[0].kwargs["cwd"] == workspace
    assert service._run_git.call_args_list[1].kwargs["cwd"] == workspace
    assert service._run_git.call_args_list[2].kwargs["cwd"] == workspace


@pytest.mark.asyncio
async def test_fetch_and_queue_issues_skips_when_github_mode_deferred(
    monkeypatch,
) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setenv("KORTANA_GITHUB_MODE", "deferred")

    service = GitHubAutonomyService(db_session=MagicMock())
    service.http_client.get = AsyncMock()

    tasks = await service.fetch_and_queue_issues()

    assert tasks == []
    service.http_client.get.assert_not_awaited()
