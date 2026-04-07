"""
Unit and integration tests for GitHub autonomy system
"""

import json
import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import httpx
import pytest

# Import the app and models
from src.kortana.models import GitHubTask
from src.kortana.services.ai_consensus import ConsensusMode


@pytest.fixture
def mock_db():
    """Mock database session"""
    db = MagicMock()

    default_result = MagicMock()
    default_result.all.return_value = []
    default_result.scalar_one_or_none.return_value = None
    default_result.scalars.return_value.all.return_value = []
    default_result.scalar_one.return_value = 0

    db.execute = AsyncMock(return_value=default_result)
    db.commit = AsyncMock(return_value=None)
    db.rollback = AsyncMock(return_value=None)
    db.add = MagicMock()
    db.close = MagicMock()

    return db


class TestGitHubRouter:
    """Tests for GitHub API integration"""

    def test_get_issues_missing_token(self, client):
        """Test fetching issues without GitHub token configured"""
        with patch.dict("os.environ", {"GITHUB_TOKEN": ""}):
            response = client.get("/api/github/repos/test/repo/issues")
            assert response.status_code == 500
            assert "GitHub token not configured" in response.json()["message"]

    def test_get_issues_pagination(self, client):
        """Test issue fetching with pagination"""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {"number": 1, "title": "Test issue", "body": "Test body"}
            ]
            mock_response.raise_for_status = MagicMock()

            # Make it awaitable for AsyncClient
            async def mock_awaitable(*args, **kwargs):
                return mock_response

            mock_get.side_effect = mock_awaitable

            with patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}):
                response = client.get(
                    "/api/github/repos/test/repo/issues?page=1&per_page=10"
                )
                assert response.status_code == 200
                assert "pagination" in response.json()

    def test_get_issues_invalid_pagination(self, client):
        """Test issue fetching with invalid pagination params"""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_response.raise_for_status = MagicMock()

            async def mock_awaitable(*args, **kwargs):
                return mock_response

            mock_get.side_effect = mock_awaitable

            with patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}):
                # per_page should be capped at 100
                response = client.get("/api/github/repos/test/repo/issues?per_page=500")
                assert response.status_code == 200

    def test_get_pulls_success(self, client):
        """Test fetching pull requests"""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {"number": 1, "title": "Test PR", "body": "Test body"}
            ]
            mock_response.raise_for_status = MagicMock()

            async def mock_awaitable(*args, **kwargs):
                return mock_response

            mock_get.side_effect = mock_awaitable

            with patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}):
                response = client.get("/api/github/repos/test/repo/pulls")
                assert response.status_code == 200
                data = response.json()
                assert "pull_requests" in data

    def test_analyze_github_issue_success(self, client):
        """Test analyzing a GitHub issue with Gemini"""
        with (
            patch("google.generativeai.GenerativeModel") as mock_model,
            patch(
                "src.kortana.routers.github.get_preferred_model_name",
                return_value="gemini-2.0-flash",
            ),
        ):
            mock_response = Mock()
            mock_response.text = '{"summary": "Test", "priority": "high", "analysis": "Analysis", "suggested_actions": ["Act1"], "estimated_effort": "1 day"}'
            mock_instance = Mock()
            mock_instance.generate_content.return_value = mock_response
            mock_model.return_value = mock_instance

            payload = {
                "title": "Test Issue",
                "body": "Test description",
                "issue_number": 1,
                "type": "issue",
                "author": "test",
                "created_at": "2026-01-17",
            }

            with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
                response = client.post("/api/github/analyze", json=payload)
                assert response.status_code == 200
                data = response.json()
                assert data["issue_number"] == 1
                assert data["priority"] in ["high", "medium", "low"]
                mock_model.assert_called_once_with("gemini-2.0-flash")

    def test_analyze_github_issue_no_api_key(self, client):
        """Test analyzing without Gemini API key"""
        with patch.dict("os.environ", {"GEMINI_API_KEY": ""}):
            payload = {
                "title": "Test Issue",
                "body": "Test description",
                "issue_number": 1,
                "type": "issue",
            }

            response = client.post("/api/github/analyze", json=payload)
            assert response.status_code == 500


class TestAutonomyRouter:
    """Tests for autonomy task management"""

    def test_queue_github_tasks_success(self, client):
        """Test queueing tasks from GitHub issues"""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {"number": 1, "title": "Test Issue", "body": "Test body", "labels": []}
            ]
            mock_response.raise_for_status = MagicMock()

            async def mock_awaitable(*args, **kwargs):
                return mock_response

            mock_get.side_effect = mock_awaitable

            with patch("src.kortana.database.SessionLocal"):
                with patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}):
                    response = client.post("/api/autonomy/task-queue")
                    assert response.status_code == 200
                    data = response.json()
                    assert "count" in data
                    assert "tasks" in data

    def test_get_task_queue_status(self, client, app_fixture):
        """Test getting task queue status"""
        from src.kortana.database import get_db

        mock_db = AsyncMock()
        mock_result_1 = MagicMock()
        mock_result_1.all.return_value = []
        mock_result_2 = MagicMock()
        mock_result_2.scalars.return_value.all.return_value = []
        mock_db.execute.side_effect = [mock_result_1, mock_result_2]
        app_fixture.dependency_overrides[get_db] = lambda: mock_db

        response = client.get("/api/autonomy/status")
        assert response.status_code == 200
        data = response.json()
        assert "total_tasks" in data
        assert "stats" in data
        assert "completion_rate" in data

    def test_health_check(self, client):
        """Test autonomy health check"""
        response = client.get("/api/autonomy/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "autonomy"


class TestCodeGenerator:
    """Tests for code generation"""

    def test_parse_plan_json_format(self):
        """Test parsing Gemini plan in JSON format"""
        from src.kortana.services.code_generator import CodeGenerator

        gen = CodeGenerator()
        plan_text = """
```json
{
  "files": [
    {
      "path": "test.py",
      "action": "create",
      "content": "print('test')"
    }
  ]
}
```
"""
        parsed = gen.parse_plan(plan_text)
        assert "files" in parsed
        assert len(parsed["files"]) > 0

    def test_parse_plan_raw_json_file_changes_format(self):
        """Test parsing raw JSON plans stored directly in the task record."""
        from src.kortana.services.code_generator import CodeGenerator

        gen = CodeGenerator()
        plan_text = """
{
  "action": "create-files",
  "description": "Create a test file",
  "FILE_CHANGES": [
    {
      "path": "test_pipeline_execution.py",
      "action": "create",
      "content": "print('success')"
    }
  ]
}
"""
        parsed = gen.parse_plan(plan_text)
        assert parsed["files"] == [
            {
                "path": "test_pipeline_execution.py",
                "action": "create",
                "dependencies": [],
                "priority": 0,
                "content": "print('success')",
            }
        ]

    def test_parse_plan_yaml_files_block(self):
        """Test parsing YAML fenced plans with a files list."""
        from src.kortana.services.code_generator import CodeGenerator

        gen = CodeGenerator()
        plan_text = """
### FILE_CHANGES

```yaml
files:
  - path: docs/autonomy-smoke-note.md
    action: create
    content: |
      # Autonomy Smoke Note
      This file was created by the autonomous GitHub pipeline.
```
"""
        parsed = gen.parse_plan(plan_text)
        assert len(parsed["files"]) == 1
        assert parsed["files"][0]["path"] == "docs/autonomy-smoke-note.md"
        assert parsed["files"][0]["action"] == "create"
        assert (
            parsed["files"][0]["content"]
            == "# Autonomy Smoke Note\nThis file was created by the autonomous GitHub pipeline."
        )

    def test_parse_plan_markdown_file_changes_with_file_blocks(self):
        """Test parsing markdown FILE_CHANGES bullets plus detailed FILE blocks."""
        from src.kortana.services.code_generator import CodeGenerator

        gen = CodeGenerator()
        plan_text = """
**FILE_CHANGES**
*   **NEW:** `tests/e2e/utils/git.ts`
*   **MOD:** `.env.test`

**FILE: `tests/e2e/utils/git.ts`**
```typescript
export const x = 1;
```

**FILE: `.env.test`**
```dotenv
GITHUB_TOKEN=test
```
"""
        parsed = gen.parse_plan(plan_text)
        assert parsed["files"] == [
            {
                "path": "tests/e2e/utils/git.ts",
                "action": "create",
                "dependencies": [],
                "priority": 0,
                "content": "export const x = 1;",
            },
            {
                "path": ".env.test",
                "action": "modify",
                "dependencies": [],
                "priority": 0,
                "content": "GITHUB_TOKEN=test",
            },
        ]

    def test_validate_plan_structure(self):
        """Test plan validation"""
        from src.kortana.services.code_generator import CodeGenerator

        gen = CodeGenerator()
        valid_plan = {
            "files": [{"path": "test.py", "action": "create", "content": "test"}]
        }
        assert gen.validate_plan(valid_plan)

    def test_validate_plan_invalid_action(self):
        """Test plan validation with invalid action"""
        from src.kortana.services.code_generator import CodeGenerator

        gen = CodeGenerator()
        invalid_plan = {
            "files": [{"path": "test.py", "action": "invalid", "content": "test"}]
        }
        assert not gen.validate_plan(invalid_plan)

    def test_path_traversal_protection(self):
        """Test protection against path traversal attacks"""
        from src.kortana.services.code_generator import (
            CodeGenerationError,
            CodeGenerator,
        )

        gen = CodeGenerator()
        malicious_plan = {
            "files": [
                {"path": "../../../etc/passwd", "action": "create", "content": "test"}
            ]
        }
        with pytest.raises(CodeGenerationError):
            gen.validate_plan(malicious_plan)

    def test_format_python_code(self):
        """Test Python code formatting"""
        from src.kortana.services.code_generator import CodeGenerator

        gen = CodeGenerator()
        code = "def test( ):\n\n\n    pass"
        formatted = gen.format_code(code, "py")
        # Should remove extra blank lines
        assert formatted.count("\n\n") <= 1


class TestGitHubAutonomyService:
    """Tests for GitHubAutonomyService"""

    @pytest.fixture
    def service(self, mock_db):
        """Create GitHubAutonomyService instance"""
        from src.kortana.services.github_autonomy_service import GitHubAutonomyService

        return GitHubAutonomyService(db_session=mock_db)

    @pytest.mark.asyncio
    async def test_validate_token_success(self, service):
        """Test token validation with valid token"""
        with patch("os.getenv", return_value="test_token"):
            service._validate_token()  # Should not raise

    @pytest.mark.asyncio
    async def test_validate_token_failure(self, service):
        """Test token validation with missing token"""
        with (
            patch("os.getenv", return_value=None),
            patch(
                "src.kortana.services.github_autonomy_service.get_settings"
            ) as mock_settings,
        ):
            mock_settings.return_value.GITHUB_TOKEN = None
            with pytest.raises(ValueError, match="GitHub token not configured"):
                service._validate_token()

    @pytest.mark.asyncio
    async def test_fetch_and_queue_issues_success(self, service, mock_db):
        """Test fetching and queuing issues"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"number": 1, "title": "Test Issue", "body": "Description", "labels": []}
        ]
        mock_response.raise_for_status = MagicMock()

        # Mock the resilient http_client directly on the service
        service.http_client = AsyncMock()
        service.http_client.get = AsyncMock(return_value=mock_response)

        with patch("os.getenv", return_value="test_token"):
            # Mock existing issues check
            mock_result = MagicMock()
            mock_result.all.return_value = []
            mock_db.execute.return_value = mock_result

            tasks = await service.fetch_and_queue_issues("test/repo")
            assert len(tasks) == 1
            assert tasks[0].github_issue_number == 1
            assert tasks[0].title == "Test Issue"

    @pytest.mark.asyncio
    async def test_fetch_and_queue_issues_existing_task(self, service, mock_db):
        """Test fetching issues when task already exists"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"number": 1, "title": "Test Issue", "body": "Description", "labels": []}
        ]
        mock_response.raise_for_status = MagicMock()

        with (
            patch("httpx.AsyncClient.get") as mock_get,
            patch("os.getenv", return_value="test_token"),
        ):
            mock_get.return_value = mock_response

            # Mock existing task
            mock_result = MagicMock()
            mock_result.all.return_value = [(1,)]  # Existing issue number
            mock_db.execute.return_value = mock_result

            tasks = await service.fetch_and_queue_issues("test/repo")
            assert len(tasks) == 0  # No new tasks should be created

    def test_determine_priority_high(self, service):
        """Test priority determination for high priority labels"""
        issue = {"labels": [{"name": "critical"}, {"name": "bug"}]}
        priority = service._determine_priority(issue)
        assert priority == "high"

    def test_determine_priority_low(self, service):
        """Test priority determination for low priority labels"""
        issue = {"labels": [{"name": "chore"}, {"name": "p2"}]}
        priority = service._determine_priority(issue)
        assert priority == "low"

    def test_determine_priority_medium(self, service):
        """Test priority determination for medium priority (default)"""
        issue = {"labels": [{"name": "enhancement"}]}
        priority = service._determine_priority(issue)
        assert priority == "medium"

    def test_generate_branch_name(self, service):
        """Test branch name generation"""
        branch_name = service._generate_branch_name(123, "Test Issue Title")
        assert branch_name.startswith("auto-fix/123-")
        assert "test-issue-title" in branch_name
        assert len(branch_name) <= 50 + len("auto-fix/123-")

    @pytest.mark.asyncio
    async def test_analyze_task_success(self, service, mock_db):
        """Test task analysis"""
        task = GitHubTask(
            github_issue_number=1,
            github_repo="test/repo",
            title="Test Task",
            description="Test description",
            status="pending",
        )

        with patch(
            "src.kortana.services.github_autonomy_service.gemini_service.analyze_text"
        ) as mock_analyze:
            mock_analyze.return_value = "Analysis result"
            mock_db.commit = MagicMock()

            result = await service.analyze_task(task)
            assert result.status == "analyzed"
            assert result.analysis == "Analysis result"
            assert result.analyzed_at is not None

    @pytest.mark.asyncio
    async def test_analyze_task_falls_back_when_gemini_quota_is_exhausted(
        self, service, mock_db
    ):
        """Analysis should use another provider instead of deferring on Gemini quota."""
        task = GitHubTask(
            github_issue_number=1,
            github_repo="test/repo",
            title="Test Task",
            description="Test description",
            status="pending",
        )

        fallback_engine = MagicMock()
        fallback_engine.query = AsyncMock(
            return_value=MagicMock(
                answer="Fallback analysis",
                provider_used="openrouter",
            )
        )
        service._provider_backoff_until.clear()

        with (
            patch(
                "src.kortana.services.github_autonomy_service.gemini_service.analyze_text"
            ) as mock_analyze,
            patch(
                "src.kortana.services.github_autonomy_service.get_consensus_engine",
                return_value=fallback_engine,
            ),
        ):
            mock_analyze.return_value = (
                "The generative model is temporarily unavailable. "
                "The system continues without Gemini."
            )
            mock_db.commit = MagicMock()

            result = await service.analyze_task(task)

            assert result.status == "analyzed"
            assert result.analysis == "Fallback analysis"
            fallback_engine.query.assert_awaited_once()
            assert (
                fallback_engine.query.await_args.kwargs["mode"] == ConsensusMode.FASTEST
            )
        service._provider_backoff_until.clear()

    @pytest.mark.asyncio
    async def test_analyze_task_by_id(self, service, mock_db):
        """Test task analysis by ID"""
        task = GitHubTask(
            id="test-id",
            github_issue_number=1,
            github_repo="test/repo",
            title="Test Task",
            description="Test description",
            status="pending",
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = task
        mock_db.execute.return_value = mock_result

        with patch(
            "src.kortana.services.github_autonomy_service.gemini_service.analyze_text"
        ) as mock_analyze:
            mock_analyze.return_value = "Analysis result"
            mock_db.commit = MagicMock()

            result = await service.analyze_task("test-id")
            assert result.status == "analyzed"

    @pytest.mark.asyncio
    async def test_plan_task_success(self, service, mock_db):
        """Test task planning"""
        task = GitHubTask(
            github_issue_number=1,
            github_repo="test/repo",
            title="Test Task",
            description="Test description",
            analysis="Test analysis",
            status="analyzed",
        )

        with patch(
            "src.kortana.services.github_autonomy_service.gemini_service.analyze_text"
        ) as mock_analyze:
            mock_analyze.return_value = "Planning result"
            mock_db.commit = MagicMock()

            result = await service.plan_task(task)
            assert result.status == "planning_complete"
            assert result.plan == "Planning result"

    @pytest.mark.asyncio
    async def test_plan_task_falls_back_when_gemini_quota_is_exhausted(
        self, service, mock_db
    ):
        """Planning should use another provider instead of deferring on Gemini quota."""
        task = GitHubTask(
            github_issue_number=1,
            github_repo="test/repo",
            title="Test Task",
            description="Test description",
            analysis="Test analysis",
            status="analyzed",
        )

        fallback_plan = json.dumps(
            {
                "FILE_CHANGES": [
                    {
                        "file": "backend/src/kortana/services/fallback_task.py",
                        "action": "create",
                        "content": "def ok():\n    return True\n",
                    }
                ]
            }
        )
        fallback_engine = MagicMock()
        fallback_engine.query = AsyncMock(
            return_value=MagicMock(
                answer=fallback_plan,
                provider_used="openai",
            )
        )
        service._provider_backoff_until.clear()

        with (
            patch(
                "src.kortana.services.github_autonomy_service.gemini_service.analyze_text"
            ) as mock_analyze,
            patch(
                "src.kortana.services.github_autonomy_service.get_consensus_engine",
                return_value=fallback_engine,
            ),
        ):
            mock_analyze.return_value = (
                "The generative model is temporarily unavailable. "
                "The system continues without Gemini."
            )
            mock_db.commit = MagicMock()

            result = await service.plan_task(task)

            assert result.status == "planning_complete"
            assert "backend/src/kortana/services/fallback_task.py" in result.plan
            fallback_engine.query.assert_awaited_once()
            assert fallback_engine.query.await_args.kwargs["mode"] == ConsensusMode.BEST
        service._provider_backoff_until.clear()

    @pytest.mark.asyncio
    async def test_analyze_task_skips_gemini_during_quota_backoff(
        self, service, mock_db
    ):
        """After a quota fallback, subsequent analysis should skip Gemini temporarily."""
        first_task = GitHubTask(
            github_issue_number=1,
            github_repo="test/repo",
            title="First Task",
            description="Test description",
            status="pending",
        )
        second_task = GitHubTask(
            github_issue_number=2,
            github_repo="test/repo",
            title="Second Task",
            description="Test description",
            status="pending",
        )

        fallback_engine = MagicMock()
        fallback_engine.query = AsyncMock(
            return_value=MagicMock(
                answer="Fallback analysis",
                provider_used="openrouter",
            )
        )
        service._provider_backoff_until.clear()

        with (
            patch(
                "src.kortana.services.github_autonomy_service.gemini_service.analyze_text"
            ) as mock_analyze,
            patch(
                "src.kortana.services.github_autonomy_service.get_consensus_engine",
                return_value=fallback_engine,
            ),
        ):
            mock_analyze.return_value = (
                "The generative model is temporarily unavailable. "
                "The system continues without Gemini."
            )
            mock_db.commit = MagicMock()

            first_result = await service.analyze_task(first_task)
            second_result = await service.analyze_task(second_task)

            assert first_result.status == "analyzed"
            assert second_result.status == "analyzed"
            assert mock_analyze.call_count == 1
            assert fallback_engine.query.await_count == 2
        service._provider_backoff_until.clear()

    def test_sanitize_plan_for_repo_removes_hallucinated_paths(self, service, tmp_path):
        """Repo-grounded planning should drop file changes outside the observed repo shape."""
        (tmp_path / "backend" / "src" / "kortana" / "services").mkdir(parents=True)
        (tmp_path / "frontend" / "src").mkdir(parents=True)
        (tmp_path / "backend" / "src" / "kortana" / "main.py").write_text(
            "print('ok')\n",
            encoding="utf-8",
        )
        (tmp_path / "frontend" / "src" / "main.tsx").write_text(
            "export {};\n",
            encoding="utf-8",
        )

        service.repo_root = tmp_path
        service._repo_inventory_cache = None
        service._repo_shape_cache = None

        raw_plan = json.dumps(
            {
                "FILE_CHANGES": [
                    {
                        "file": "backend/src/kortana/services/deploy_guard.py",
                        "action": "create",
                        "content": "def guard():\n    return True\n",
                    },
                    {
                        "file": "core/boot.go",
                        "action": "create",
                        "content": "package main\n",
                    },
                ]
            }
        )

        sanitized = service._sanitize_plan_for_repo(raw_plan)
        payload = json.loads(sanitized)

        assert payload["FILE_CHANGES"] == [
            {
                "path": "backend/src/kortana/services/deploy_guard.py",
                "action": "create",
                "content": "def guard():\n    return True\n",
                "dependencies": [],
                "priority": 0,
            }
        ]
        assert payload["VALIDATION_NOTES"] == [
            "core/boot.go: top-level root is not present in the repository"
        ]

    def test_service_prefers_configured_workspace_root_when_it_looks_like_repo(
        self, mock_db, tmp_path, monkeypatch
    ):
        """The autonomy service should use a mounted workspace when available."""
        (tmp_path / ".git").mkdir()
        monkeypatch.setenv("KORTANA_WORKSPACE_ROOT", str(tmp_path))

        from src.kortana.services.github_autonomy_service import GitHubAutonomyService

        service = GitHubAutonomyService(db_session=mock_db)

        assert service.repo_root == tmp_path.resolve()

    @pytest.mark.asyncio
    async def test_execute_task_success(self, service, mock_db):
        """Test task execution"""
        task = GitHubTask(
            github_issue_number=1,
            github_repo="test/repo",
            title="Test Task",
            description="Test description",
            plan="Test plan",
            status="planning_complete",
            branch_name="test-branch",
        )

        mock_codegen = MagicMock()
        mock_codegen.generate_from_gemini_plan.return_value = {
            "errors": None,
            "created": ["test.py"],
            "modified": [],
            "deleted": [],
        }
        fake_workspace = Path("/tmp/fake-workspace")

        with (
            patch.object(service, "_create_branch", return_value=True),
            patch.object(service, "code_gen", mock_codegen),
            patch.object(
                service,
                "_prepare_execution_workspace",
                AsyncMock(return_value=fake_workspace),
            ),
            patch.object(service, "_cleanup_execution_workspace", AsyncMock()),
            patch.object(service, "_normalize_changed_files", return_value=["test.py"]),
            patch.object(
                service, "_commit_workspace_changes", AsyncMock(return_value="abc123")
            ) as mock_commit,
            patch.object(
                service, "_push_workspace_branch", AsyncMock(return_value=True)
            ) as mock_push,
            patch.object(
                service, "_create_pull_request_for_branch", AsyncMock(return_value=42)
            ) as mock_pr,
        ):
            mock_db.commit = MagicMock()

            result = await service.execute_task(task)
            assert result.status == "executed"
            assert result.executed_at is not None
            assert result.code_changes == ["test.py"]
            assert result.commit_sha == "abc123"
            assert result.github_pr_number == 42
            mock_commit.assert_awaited_once_with(task, ["test.py"], fake_workspace)
            mock_push.assert_awaited_once_with(task, fake_workspace)
            mock_pr.assert_awaited_once_with(task)
            assert mock_codegen.generate_from_gemini_plan.call_args.kwargs[
                "repo_path"
            ] == str(fake_workspace)

    @pytest.mark.asyncio
    async def test_execute_task_branch_creation_failure(self, service, mock_db):
        """Test task execution when branch creation fails"""
        task = GitHubTask(
            github_issue_number=1,
            github_repo="test/repo",
            title="Test Task",
            description="Test description",
            plan="Test plan",
            status="planning_complete",
            branch_name="test-branch",
        )

        task.error_message = "Branch creation failed with status 403: forbidden"

        with patch.object(service, "_create_branch", return_value=False):
            mock_db.commit = MagicMock()

            with pytest.raises(
                Exception, match="Branch creation failed with status 403: forbidden"
            ):
                await service.execute_task(task)

    @pytest.mark.asyncio
    async def test_create_branch_success(self, service):
        """Test branch creation success"""
        task = GitHubTask(branch_name="test-branch", github_repo="owner/repo")

        mock_ref_response = MagicMock()
        mock_ref_response.status_code = 200
        mock_ref_response.json.return_value = {"object": {"sha": "abc123"}}

        mock_create_response = MagicMock()
        mock_create_response.status_code = 201

        # Mock the resilient http_client directly on the service
        service.http_client = AsyncMock()
        service.http_client.get = AsyncMock(return_value=mock_ref_response)
        service.http_client.post = AsyncMock(return_value=mock_create_response)

        with patch("os.getenv", return_value="test_token"):
            result = await service._create_branch(task)
            assert result is True

    @pytest.mark.asyncio
    async def test_create_branch_master_fallback(self, service):
        """Test branch creation with master branch fallback"""
        task = GitHubTask(branch_name="test-branch", github_repo="owner/repo")

        # Main branch fails, master succeeds
        main_response = MagicMock()
        main_response.status_code = 404

        master_response = MagicMock()
        master_response.status_code = 200
        master_response.json.return_value = {"object": {"sha": "abc123"}}

        create_response = MagicMock()
        create_response.status_code = 201

        # Mock http_client: first get (main) raises exception, second get (master) succeeds
        service.http_client = AsyncMock()
        service.http_client.get = AsyncMock(
            side_effect=[Exception("Not found"), master_response]
        )
        service.http_client.post = AsyncMock(return_value=create_response)

        with patch("os.getenv", return_value="test_token"):
            result = await service._create_branch(task)
            assert result is True

    @pytest.mark.asyncio
    async def test_create_branch_idempotent_on_422(self, service):
        """Test branch creation is idempotent when branch already exists (422 response)"""
        task = GitHubTask(branch_name="test-branch", github_repo="owner/repo")

        mock_ref_response = MagicMock()
        mock_ref_response.status_code = 200
        mock_ref_response.json.return_value = {"object": {"sha": "abc123"}}

        # 422 = conflict (branch already exists)
        mock_create_response = MagicMock()
        mock_create_response.status_code = 422
        mock_create_response.text = "Branch already exists"

        service.http_client = AsyncMock()
        service.http_client.get = AsyncMock(return_value=mock_ref_response)
        service.http_client.post = AsyncMock(return_value=mock_create_response)

        with patch("os.getenv", return_value="test_token"):
            result = await service._create_branch(task)
            assert result is True  # Should succeed (idempotent)

    @pytest.mark.asyncio
    async def test_create_branch_logs_http_status_error_details(self, service):
        """Test branch creation logs useful details when httpx raises before returning."""
        task = GitHubTask(branch_name="test-branch", github_repo="owner/repo")

        mock_ref_response = MagicMock()
        mock_ref_response.status_code = 200
        mock_ref_response.json.return_value = {"object": {"sha": "abc123"}}

        request = httpx.Request(
            "POST", "https://api.github.com/repos/owner/repo/git/refs"
        )
        response = httpx.Response(
            403,
            request=request,
            json={"message": "Resource not accessible by integration"},
        )

        service.http_client = AsyncMock()
        service.http_client.get = AsyncMock(return_value=mock_ref_response)
        service.http_client.post = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "403 Client Error", request=request, response=response
            )
        )

        with patch(
            "src.kortana.services.github_autonomy_service.logger"
        ) as mock_logger:
            result = await service._create_branch(task)

        assert result is False
        mock_logger.error.assert_any_call(
            "Branch creation failed with status 403: Resource not accessible by integration"
        )

    @pytest.mark.asyncio
    async def test_commit_branch_changes_isolated(self, service):
        """Test that _commit_branch_changes delegates to the workspace-based implementation"""
        task = GitHubTask(
            github_issue_number=123, branch_name="autonomy/test-123", title="Test Task"
        )
        files_changed = ["test.py", "test2.py"]
        service.repo_root = Path("C:/repo-root")

        with patch("subprocess.run") as mock_run:
            # git add test.py, git add test2.py, git commit, git rev-parse HEAD
            mock_results = [
                MagicMock(returncode=0, stdout=""),  # add 1
                MagicMock(returncode=0, stdout=""),  # add 2
                MagicMock(returncode=0, stdout=""),  # commit
                MagicMock(returncode=0, stdout="abc123def456\n"),  # rev-parse
            ]
            mock_run.side_effect = mock_results

            commit_sha = await service._commit_branch_changes(task, files_changed)

            assert mock_run.call_count >= 4
            # First call is git add test.py
            add_call = mock_run.call_args_list[0]
            assert "add" in str(add_call)
            assert "test.py" in str(add_call)
            assert add_call.kwargs["cwd"] == service.repo_root
            # Third call is git commit --no-verify
            commit_call = mock_run.call_args_list[2]
            assert "--no-verify" in str(commit_call)
            assert commit_call.kwargs["cwd"] == service.repo_root

            assert commit_sha == "abc123def456"

    @pytest.mark.asyncio
    async def test_commit_branch_changes_bootstraps_local_branch(self, service):
        """Test that _commit_branch_changes returns None if git add fails."""
        task = GitHubTask(
            github_issue_number=123, branch_name="autonomy/test-123", title="Test Task"
        )
        files_changed = ["test.py"]

        add_error = subprocess.CalledProcessError(
            1, ["git", "add", "test.py"], stderr="pathspec not found"
        )

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [add_error]

            commit_sha = await service._commit_branch_changes(task, files_changed)

            assert commit_sha is None
            assert mock_run.call_count >= 1
            add_call = mock_run.call_args_list[0]
            assert "add" in str(add_call)
            assert "test.py" in str(add_call)

    @pytest.mark.asyncio
    async def test_push_branch_isolated_with_recovery(self, service):
        """Test that _push_branch delegates to _push_workspace_branch"""
        task = GitHubTask(
            github_issue_number=123,
            branch_name="autonomy/test-123",
            github_repo="owner/repo",
        )

        with patch("subprocess.run") as mock_run:
            mock_results = [
                MagicMock(returncode=0, stdout=""),  # git push
            ]
            mock_run.side_effect = mock_results

            with patch("os.getenv", return_value="test_token"):
                result = await service._push_branch(task)

            assert result is True
            assert mock_run.call_count >= 1

            # Verify push uses explicit branch:branch ref
            push_call = mock_run.call_args_list[0]
            assert "push" in str(push_call)
            assert "autonomy/test-123:autonomy/test-123" in str(push_call)


class TestHOPAutonomyService:
    """Tests for HOPAutonomyService"""

    @pytest.fixture
    def service(self, mock_db):
        """Create HOPAutonomyService instance"""
        from src.kortana.services.hop_autonomy_service import HOPAutonomyService

        return HOPAutonomyService(db_session=mock_db)

    @pytest.fixture
    def mock_task(self):
        """Create mock task"""
        from src.kortana.models import Task

        return Task(
            id="test-id",
            title="Test Task",
            description="Test description",
            status="pending",
            classification=None,
        )

    @pytest.mark.asyncio
    async def test_run_hop_cycle_success(self, service):
        """Test running HOP cycle"""
        with patch(
            "src.kortana.services.hop_autonomy_service.run_autonomy_cycle.delay"
        ) as mock_delay:
            mock_task = MagicMock()
            mock_task.id = "celery-task-id"
            mock_delay.return_value = mock_task

            result = await service.run_hop_cycle()
            assert result["status"] == "cycle_started"
            assert result["celery_task_id"] == "celery-task-id"

    @pytest.mark.asyncio
    async def test_classify_hop_task_auto(self, service, mock_task, mock_db):
        """Test task classification as auto"""
        with patch(
            "src.kortana.services.hop_autonomy_service.gemini_service.analyze_text"
        ) as mock_analyze:
            mock_analyze.return_value = "auto"
            mock_db.commit = MagicMock()

            result = await service.classify_hop_task(mock_task)
            assert result == "auto"
            assert mock_task.classification == "auto"

    @pytest.mark.asyncio
    async def test_classify_hop_task_invalid_response(
        self, service, mock_task, mock_db
    ):
        """Test task classification with invalid response defaults to ho"""
        with patch(
            "src.kortana.services.hop_autonomy_service.gemini_service.analyze_text"
        ) as mock_analyze:
            mock_analyze.return_value = "invalid"
            mock_db.commit = MagicMock()

            result = await service.classify_hop_task(mock_task)
            assert result == "ho"
            assert mock_task.classification == "ho"

    @pytest.mark.asyncio
    async def test_get_autonomy_status(self, service, mock_db):
        """Test getting autonomy status"""
        # Mock the count queries
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 5

        mock_recent_result = MagicMock()
        mock_recent_result.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [mock_count_result] * 6 + [mock_recent_result]

        result = await service.get_autonomy_status()
        assert result["status"] == "active"
        assert result["statistics"]["total_tasks"] == 5
        assert "by_status" in result["statistics"]
        assert "by_classification" in result["statistics"]

    @pytest.mark.asyncio
    async def test_trigger_task(self, service):
        """Test triggering a task action"""
        result = await service.trigger_task("autonomous_merge", "task-123")
        assert result["status"] == "triggered"
        assert result["action"] == "autonomous_merge"
        assert result["task_id"] == "task-123"

    @pytest.mark.asyncio
    async def test_should_require_human_not_classified(self, service, mock_task):
        """Test human requirement check for unclassified task"""
        with patch.object(
            service, "classify_hop_task", return_value="ho"
        ) as mock_classify:
            result = await service.should_require_human(mock_task)
            assert result is True
            mock_classify.assert_called_once_with(mock_task)

    @pytest.mark.asyncio
    async def test_should_require_human_already_classified(self, service, mock_task):
        """Test human requirement check for already classified task"""
        mock_task.classification = "approval"
        result = await service.should_require_human(mock_task)
        assert result is True

    @pytest.mark.asyncio
    async def test_generate_ho_scaffold(self, service, mock_task, mock_db):
        """Test generating HO scaffold"""
        with patch(
            "src.kortana.services.hop_autonomy_service.gemini_service.analyze_text"
        ) as mock_analyze:
            mock_analyze.return_value = "Scaffold content"
            mock_db.commit = MagicMock()

            result = await service.generate_ho_scaffold(mock_task)
            assert result == "Scaffold content"
            assert mock_task.ho_scaffold == "Scaffold content"

    @pytest.mark.asyncio
    async def test_approve_task_success(self, service, mock_db):
        """Test task approval"""
        mock_task = MagicMock()
        mock_task.status = "waiting_for_ho"
        mock_task.metadata_json = None

        mock_result = MagicMock()
        mock_result.scalar_one.return_value = mock_task
        mock_db.execute.return_value = mock_result
        mock_db.commit = MagicMock()

        result = await service.approve_task("task-123", True, "Approved")
        assert result.status == "pending"
        assert result.classification == "auto"

    @pytest.mark.asyncio
    async def test_approve_task_reject(self, service, mock_db):
        """Test task rejection"""
        mock_task = MagicMock()
        mock_task.status = "waiting_for_ho"
        mock_task.metadata_json = None

        mock_result = MagicMock()
        mock_result.scalar_one.return_value = mock_task
        mock_db.execute.return_value = mock_result
        mock_db.commit = MagicMock()

        result = await service.approve_task("task-123", False, "Rejected")
        assert result.status == "cancelled"

    @pytest.mark.asyncio
    async def test_approve_task_not_waiting(self, service, mock_db):
        """Test approval of task not waiting for approval"""
        mock_task = MagicMock()
        mock_task.status = "completed"

        mock_result = MagicMock()
        mock_result.scalar_one.return_value = mock_task
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="not awaiting approval"):
            await service.approve_task("task-123", True)


class TestGitHubTaskModel:
    """Tests for GitHubTask database model"""

    def test_github_task_creation(self):
        """Test creating a GitHubTask model instance"""
        task = GitHubTask(
            github_issue_number=1,
            github_repo="test/repo",
            title="Test Task",
            description="Test description",
            status="pending",
            branch_name="feature/1-test",
        )
        assert task.github_issue_number == 1
        assert task.github_repo == "test/repo"
        assert task.title == "Test Task"


class TestRateLimiting:
    """Tests for rate limiting"""

    def test_rate_limit_check_within_limit(self, client):
        """Test rate limit check within acceptable range"""
        from src.kortana.routers.github import rate_limit_check

        # Should pass for first 60 requests
        for i in range(60):
            assert rate_limit_check("test_endpoint")

    def test_rate_limit_check_exceeded(self, client):
        """Test rate limit check when exceeded"""
        from src.kortana.routers.github import rate_limit_check

        endpoint = "test_endpoint_limit"
        for i in range(61):
            result = rate_limit_check(endpoint)
            if i == 60:
                assert not result  # 61st request should fail


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
