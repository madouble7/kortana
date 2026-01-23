"""
Unit and integration tests for GitHub autonomy system
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

# Import the app and models
from src.kortana.models import GitHubTask


@pytest.fixture
def mock_db():
    """Mock database session"""
    db = MagicMock()
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
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {"number": 1, "title": "Test issue", "body": "Test body"}
            ]
            mock_get.return_value = mock_response

            response = client.get(
                "/api/github/repos/test/repo/issues?page=1&per_page=10"
            )
            assert response.status_code == 200
            assert "pagination" in response.json()

    def test_get_issues_invalid_pagination(self, client):
        """Test issue fetching with invalid pagination params"""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_get.return_value = mock_response

            # per_page should be capped at 100
            response = client.get("/api/github/repos/test/repo/issues?per_page=500")
            assert response.status_code == 200

    def test_get_pulls_success(self, client):
        """Test fetching pull requests"""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {"number": 1, "title": "Test PR", "body": "Test body"}
            ]
            mock_get.return_value = mock_response

            response = client.get("/api/github/repos/test/repo/pulls")
            assert response.status_code == 200
            data = response.json()
            assert "pull_requests" in data

    def test_analyze_github_issue_success(self, client):
        """Test analyzing a GitHub issue with Gemini"""
        with patch("google.generativeai.GenerativeModel") as mock_model:
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
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {"number": 1, "title": "Test Issue", "body": "Test body", "labels": []}
            ]
            mock_get.return_value = mock_response

            with patch("src.kortana.database.SessionLocal"):
                response = client.post("/api/autonomy/task-queue")
                assert response.status_code == 200
                data = response.json()
                assert "count" in data
                assert "tasks" in data

    def test_get_task_queue_status(self, client):
        """Test getting task queue status"""
        with patch("src.kortana.database.SessionLocal"):
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
        assert task.status == "pending"

    def test_github_task_status_transitions(self):
        """Test valid status transitions"""
        task = GitHubTask(
            github_issue_number=1,
            github_repo="test/repo",
            title="Test",
            description="Test",
            branch_name="feature/1",
        )

        valid_statuses = [
            "pending",
            "analyzing",
            "planning",
            "ready_to_execute",
            "executing",
            "completed",
            "failed",
        ]

        for status in valid_statuses:
            task.status = status
            assert task.status == status

    def test_github_task_error_tracking(self):
        """Test error tracking on tasks"""
        task = GitHubTask(
            github_issue_number=1,
            github_repo="test/repo",
            title="Test",
            description="Test",
            branch_name="feature/1",
            error_count=0,
            max_retries=3,
        )

        assert task.error_count == 0
        task.error_count += 1
        assert task.error_count == 1


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
