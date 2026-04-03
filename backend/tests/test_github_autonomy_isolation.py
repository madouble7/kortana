import json
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
    task.validation_report = None

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
    assert task.validation_report["stage"] == "executed"
    assert task.validation_report["changed_files"] == ["backend/src/kortana/demo.py"]
    assert task.validation_report["publish_target"] == "github"
    assert service.code_gen.generate_from_gemini_plan.call_args.kwargs[
        "repo_path"
    ] == str(workspace)
    service._commit_workspace_changes.assert_awaited_once_with(
        task, ["backend/src/kortana/demo.py"], workspace
    )
    service._push_workspace_branch.assert_awaited_once_with(task, workspace)
    service._cleanup_execution_workspace.assert_awaited_once_with(workspace)


@pytest.mark.asyncio
async def test_execute_task_persists_task_scoped_validation_result(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setenv("KORTANA_GITHUB_MODE", "deferred")

    service = GitHubAutonomyService(db_session=MagicMock())
    service._db_commit = AsyncMock()
    service._db_rollback = AsyncMock()

    task = GitHubTask(
        id="task-validation-pass",
        github_issue_number=52,
        github_repo="local/kortana",
        title="Validation pass",
        description="desc",
        branch_name="auto/local/52-validation-pass",
        plan=json.dumps(
            {
                "FILE_CHANGES": [
                    {
                        "file": "backend/src/kortana/demo.py",
                        "action": "create",
                        "content": "print(3)\n",
                    }
                ],
                "TESTS": [
                    "python -m pytest backend/tests/test_github_autonomy_isolation.py -q"
                ],
            }
        ),
        status="planning_complete",
        error_count=0,
    )

    workspace = tmp_path / "task-worktree"
    generated = workspace / "backend" / "src" / "kortana" / "demo.py"
    generated.parent.mkdir(parents=True)
    generated.write_text("print(3)\n", encoding="utf-8")

    service._prepare_execution_workspace = AsyncMock(return_value=workspace)
    service._commit_workspace_changes = AsyncMock(return_value="bead1234")
    service._cleanup_execution_workspace = AsyncMock()
    service._execute_validation_command = MagicMock(
        return_value={
            "command": "python -m pytest backend/tests/test_github_autonomy_isolation.py -q",
            "status": "passed",
            "exit_code": 0,
            "stdout": "ok",
            "stderr": "",
            "duration_ms": 12,
        }
    )
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
    assert task.validation_report["validation_result"]["status"] == "passed"
    assert task.validation_report["validation_result"]["executed_count"] == 1
    assert any(
        item["name"] == "task_scoped_validation" and item["status"] == "passed"
        for item in task.validation_report["validations"]
    )
    service._commit_workspace_changes.assert_awaited_once()


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
    task.validation_report = None

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
    assert task.validation_report["publish_target"] == "local"
    service._create_branch.assert_not_awaited()
    service._push_workspace_branch.assert_not_awaited()
    service._create_pull_request_for_branch.assert_not_awaited()


def test_sanitize_plan_blocks_protected_paths(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    service = GitHubAutonomyService(db_session=MagicMock())

    sanitized = service._sanitize_plan_for_repo(
        json.dumps(
            {
                "FILE_CHANGES": [
                    {
                        "file": ".env",
                        "action": "modify",
                        "content": "OPENAI_API_KEY=badidea\n",
                    },
                    {
                        "file": "backend/src/kortana/demo.py",
                        "action": "create",
                        "content": "print(1)\n",
                    },
                ],
                "TESTS": ["python -m pytest backend/tests/test_demo.py -q"],
            }
        )
    )

    payload = json.loads(sanitized)

    assert payload["FILE_CHANGES"] == [
        {
            "path": "backend/src/kortana/demo.py",
            "action": "create",
            "content": "print(1)\n",
            "dependencies": [],
            "priority": 0,
        }
    ]
    assert any("protected pattern .env" in note for note in payload["VALIDATION_NOTES"])


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
async def test_execute_task_rejects_protected_paths(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setenv("KORTANA_GITHUB_MODE", "deferred")

    service = GitHubAutonomyService(db_session=MagicMock())
    service._db_commit = AsyncMock()
    service._db_rollback = AsyncMock()

    task = GitHubTask(
        id="task-protected",
        github_issue_number=88,
        github_repo="madouble7/kortana",
        title="Protected path",
        description="desc",
        branch_name="auto/local/88-protected-path",
        plan='{"FILE_CHANGES":[{"file":".env","action":"modify","content":"SECRET=1\\n"}]}',
        status="planning_complete",
        error_count=0,
    )

    workspace = tmp_path / "task-worktree"
    secret_file = workspace / ".env"
    secret_file.parent.mkdir(parents=True, exist_ok=True)
    secret_file.write_text("SECRET=1\n", encoding="utf-8")

    service._prepare_execution_workspace = AsyncMock(return_value=workspace)
    service._commit_workspace_changes = AsyncMock()
    service._cleanup_execution_workspace = AsyncMock()
    service.code_gen.generate_from_gemini_plan = MagicMock(
        return_value={
            "created": [str(secret_file)],
            "modified": [],
            "deleted": [],
            "errors": [],
        }
    )

    with pytest.raises(Exception, match="protected paths"):
        await service.execute_task(task)

    assert task.status == "planning_complete"
    assert "protected paths" in str(task.error_message)
    assert task.validation_report["stage"] == "execution_failed"
    assert ".env" in str(task.validation_report["error"])
    service._commit_workspace_changes.assert_not_awaited()
    service._cleanup_execution_workspace.assert_awaited_once_with(workspace)


@pytest.mark.asyncio
async def test_execute_task_fails_when_task_scoped_validation_fails(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setenv("KORTANA_GITHUB_MODE", "deferred")

    service = GitHubAutonomyService(db_session=MagicMock())
    service._db_commit = AsyncMock()
    service._db_rollback = AsyncMock()

    task = GitHubTask(
        id="task-validation-fail",
        github_issue_number=89,
        github_repo="local/kortana",
        title="Validation fail",
        description="desc",
        branch_name="auto/local/89-validation-fail",
        plan=json.dumps(
            {
                "FILE_CHANGES": [
                    {
                        "file": "backend/src/kortana/demo.py",
                        "action": "create",
                        "content": "print(4)\n",
                    }
                ],
                "TESTS": [
                    "python -m pytest backend/tests/test_github_autonomy_isolation.py -q"
                ],
            }
        ),
        status="planning_complete",
        error_count=0,
    )

    workspace = tmp_path / "task-worktree"
    generated = workspace / "backend" / "src" / "kortana" / "demo.py"
    generated.parent.mkdir(parents=True)
    generated.write_text("print(4)\n", encoding="utf-8")

    service._prepare_execution_workspace = AsyncMock(return_value=workspace)
    service._commit_workspace_changes = AsyncMock()
    service._cleanup_execution_workspace = AsyncMock()
    service._execute_validation_command = MagicMock(
        return_value={
            "command": "python -m pytest backend/tests/test_github_autonomy_isolation.py -q",
            "status": "failed",
            "exit_code": 1,
            "stdout": "",
            "stderr": "failed",
            "duration_ms": 15,
        }
    )
    service.code_gen.generate_from_gemini_plan = MagicMock(
        return_value={
            "created": [str(generated)],
            "modified": [],
            "deleted": [],
            "errors": [],
        }
    )

    with pytest.raises(Exception, match="Task-scoped validation failed"):
        await service.execute_task(task)

    assert task.status == "planning_complete"
    assert task.validation_report["validation_result"]["status"] == "failed"
    assert task.validation_report["validation_result"]["failed_count"] == 1
    assert "Task-scoped validation failed" in str(task.error_message)
    service._commit_workspace_changes.assert_not_awaited()
    service._cleanup_execution_workspace.assert_awaited_once_with(workspace)


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


# ---------------------------------------------------------------------------
# PatchValidator gateway tests
# ---------------------------------------------------------------------------


def _make_service(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setenv("KORTANA_GITHUB_MODE", "deferred")
    service = GitHubAutonomyService(db_session=MagicMock())
    service._db_commit = AsyncMock()
    service._db_rollback = AsyncMock()
    return service


def _base_task(plan: str | None = None) -> MagicMock:
    task = MagicMock(spec=GitHubTask)
    task.github_issue_number = 100
    task.github_repo = "local/kortana"
    task.title = "Gateway test"
    task.branch_name = "auto/local/100-gateway-test"
    task.plan = (
        plan
        or '{"FILE_CHANGES":[{"file":"backend/src/kortana/demo.py","action":"create","content":"pass\\n"}]}'
    )
    task.status = "planning_complete"
    task.error_count = 0
    task.commit_sha = None
    task.github_pr_number = None
    task.validation_report = None
    return task


@pytest.mark.asyncio
async def test_gateway_allows_safe_additive_patch(tmp_path, monkeypatch):
    """A small additive diff must pass the validator and reach _commit_workspace_changes."""
    from unittest.mock import patch as mock_patch

    service = _make_service(monkeypatch)
    task = _base_task()

    workspace = tmp_path / "wt"
    generated = workspace / "backend" / "src" / "kortana" / "demo.py"
    generated.parent.mkdir(parents=True)
    generated.write_text("pass\n", encoding="utf-8")

    service._prepare_execution_workspace = AsyncMock(return_value=workspace)
    service._commit_workspace_changes = AsyncMock(return_value="safe123")
    service._cleanup_execution_workspace = AsyncMock()
    service.code_gen.generate_from_gemini_plan = MagicMock(
        return_value={
            "created": [str(generated)],
            "modified": [],
            "deleted": [],
            "errors": [],
        }
    )

    # Simulate _get_pending_diff returning a small additive diff
    small_diff = (
        "--- /dev/null\n+++ b/backend/src/kortana/demo.py\n@@ -0,0 +1 @@\n+pass\n"
    )
    with mock_patch.object(service, "_get_pending_diff", return_value=small_diff):
        result = await service.execute_task(task)

    assert result is task
    assert task.status == "executed"
    service._commit_workspace_changes.assert_awaited_once()


@pytest.mark.asyncio
async def test_gateway_blocks_destructive_rewrite(tmp_path, monkeypatch):
    """A diff with LDR > 0.40 must be blocked: status stays pending, commit not called."""
    from unittest.mock import patch as mock_patch

    service = _make_service(monkeypatch)
    task = _base_task()

    workspace = tmp_path / "wt"
    # Large target file so LDR calculation has real content to compare against
    target = workspace / "backend" / "src" / "kortana" / "autonomy_daemon.py"
    target.parent.mkdir(parents=True)
    original_lines = 600
    target.write_text(
        "".join(f"line {i}\n" for i in range(original_lines)), encoding="utf-8"
    )

    generated = workspace / "backend" / "src" / "kortana" / "demo.py"
    generated.parent.mkdir(parents=True, exist_ok=True)
    generated.write_text("pass\n", encoding="utf-8")

    service._prepare_execution_workspace = AsyncMock(return_value=workspace)
    service._commit_workspace_changes = AsyncMock()
    service._cleanup_execution_workspace = AsyncMock()
    service.code_gen.generate_from_gemini_plan = MagicMock(
        return_value={
            "created": [str(generated)],
            "modified": [],
            "deleted": [],
            "errors": [],
        }
    )

    # Build a destructive diff: 560 deletions out of 600 lines → LDR ≈ 0.93
    deletions = "\n".join(f"-line {i}" for i in range(560))
    destructive_diff = (
        f"--- a/backend/src/kortana/autonomy_daemon.py\n"
        f"+++ b/backend/src/kortana/autonomy_daemon.py\n"
        f"@@ -1,600 +1,40 @@\n"
        f"{deletions}\n"
    )

    with mock_patch.object(service, "_get_pending_diff", return_value=destructive_diff):
        result = await service.execute_task(task)

    assert result is task
    assert task.status == "failed"
    assert task.error_message is not None
    assert (
        "guardrail" in task.error_message.lower() or "ldr" in task.error_message.lower()
    )
    service._commit_workspace_changes.assert_not_awaited()


@pytest.mark.asyncio
async def test_gateway_skips_validation_when_no_diff(tmp_path, monkeypatch):
    """If _get_pending_diff returns empty string, validation is skipped and commit proceeds."""
    from unittest.mock import patch as mock_patch

    service = _make_service(monkeypatch)
    task = _base_task()

    workspace = tmp_path / "wt"
    generated = workspace / "backend" / "src" / "kortana" / "demo.py"
    generated.parent.mkdir(parents=True)
    generated.write_text("pass\n", encoding="utf-8")

    service._prepare_execution_workspace = AsyncMock(return_value=workspace)
    service._commit_workspace_changes = AsyncMock(return_value="empty123")
    service._cleanup_execution_workspace = AsyncMock()
    service.code_gen.generate_from_gemini_plan = MagicMock(
        return_value={
            "created": [str(generated)],
            "modified": [],
            "deleted": [],
            "errors": [],
        }
    )

    with mock_patch.object(service, "_get_pending_diff", return_value=""):
        result = await service.execute_task(task)

    assert result is task
    assert task.status == "executed"
    service._commit_workspace_changes.assert_awaited_once()


@pytest.mark.asyncio
async def test_gateway_resets_git_index_on_block(tmp_path, monkeypatch):
    """When the validator blocks, git reset HEAD must be called to undo staged state."""
    from unittest.mock import patch as mock_patch

    service = _make_service(monkeypatch)
    task = _base_task()

    workspace = tmp_path / "wt"
    generated = workspace / "backend" / "src" / "kortana" / "demo.py"
    generated.parent.mkdir(parents=True)
    generated.write_text("pass\n", encoding="utf-8")

    service._prepare_execution_workspace = AsyncMock(return_value=workspace)
    service._commit_workspace_changes = AsyncMock()
    service._cleanup_execution_workspace = AsyncMock()
    service.code_gen.generate_from_gemini_plan = MagicMock(
        return_value={
            "created": [str(generated)],
            "modified": [],
            "deleted": [],
            "errors": [],
        }
    )

    deletions = "\n".join(f"-line {i}" for i in range(560))
    destructive_diff = (
        f"--- a/backend/src/kortana/autonomy_daemon.py\n"
        f"+++ b/backend/src/kortana/autonomy_daemon.py\n"
        f"@@ -1,600 +1,40 @@\n"
        f"{deletions}\n"
    )

    reset_calls: list = []

    def fake_run_git(cmd, **kwargs):
        if cmd == ["git", "reset", "HEAD"]:
            reset_calls.append(kwargs.get("cwd"))
        return MagicMock(stdout="")

    with mock_patch.object(service, "_get_pending_diff", return_value=destructive_diff):
        with mock_patch.object(service, "_run_git", side_effect=fake_run_git):
            # PatchValidator itself does not call _run_git; the reset is called by
            # the gateway block branch inside execute_task.
            # We patch _get_pending_diff to bypass the internal git add/diff calls.
            result = await service.execute_task(task)

    assert task.status == "failed"
    # git reset HEAD should have been called with the workspace as cwd
    assert any(str(workspace) in str(p) for p in reset_calls), (
        f"Expected git reset HEAD call with cwd={workspace}, got: {reset_calls}"
    )
    service._commit_workspace_changes.assert_not_awaited()
