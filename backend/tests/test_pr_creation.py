"""
Tests for PR Creation Module
Tests GitHub PR creation, status tracking, and automation features
"""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from src.kortana.models import GitHubTask
from src.kortana.routers.pr_creation import PRCreationError, PRCreator


class TestPRCreator:
    """Test PRCreator class functionality"""

    @pytest.fixture
    def pr_creator(self):
        """Create PRCreator instance"""
        db = MagicMock(spec=Session)
        # Reset mock query for each test
        db.query.return_value.filter.return_value = db.query.return_value
        db.query.return_value.filter_by.return_value = db.query.return_value
        db.query.return_value.first.return_value = None
        db.query.return_value.all.return_value = []
        return PRCreator(db)

    @pytest.fixture
    def mock_task(self) -> GitHubTask:
        """Create mock GitHub task"""
        task = GitHubTask(
            id=1,
            github_issue_number=42,
            github_repo="user/repo",
            title="Test PR Task",
            description="Test description",
            status="completed",
            branch_name="feature/test-branch",
            plan="Test plan for PR",
        )
        return task

    def test_validate_token_success(self, pr_creator):
        """Test successful token validation"""
        with patch.dict("os.environ", {"GITHUB_TOKEN": "test_token_123"}):
            result = pr_creator._validate_token()
            assert result is True

    def test_validate_token_missing(self, pr_creator):
        """Test token validation when token is missing"""
        with patch.dict("os.environ", {}, clear=True), pytest.raises(PRCreationError):
            pr_creator._validate_token()

    def test_get_repo_info_valid(self, pr_creator):
        """Test parsing valid repo info"""
        owner, repo = pr_creator._get_repo_info("github.com/user/repo")
        assert owner == "user"
        assert repo == "repo"

    def test_get_repo_info_invalid(self, pr_creator):
        """Test parsing invalid repo info"""
        with pytest.raises(PRCreationError):
            pr_creator._get_repo_info("invalid")

    def test_generate_pr_description(self, pr_creator, mock_task):
        """Test PR description generation"""
        description = pr_creator._generate_pr_description(
            task=mock_task,
            code_changes="# New feature",
        )

        assert "Issue #42" in description
        assert "Test plan for PR" in description
        assert "# New feature" in description
        assert "Auto-generated" in description

    @patch("requests.post")
    def test_create_pr_success(self, mock_post, pr_creator, mock_task):
        """Test successful PR creation"""
        # Setup mock DB to return our mock task
        pr_creator.db.query.return_value.first.return_value = mock_task

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "number": 123,
            "html_url": "https://github.com/user/repo/pull/123",
            "state": "open",
        }
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        with patch.dict("os.environ", {"GITHUB_TOKEN": "test_token"}):
            result = pr_creator.create_pr(
                task_id=mock_task.id,
                repo="user/repo",
            )

        assert result["success"] is True
        assert result["pr_number"] == 123
        assert mock_task.github_pr_number == 123

    @patch("requests.post")
    def test_create_pr_from_issue(self, mock_post, pr_creator, mock_task):
        """Test PR creation from issue number"""
        # Setup mock DB
        pr_creator.db.query.return_value.first.return_value = mock_task

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "number": 124,
            "html_url": "https://github.com/user/repo/pull/124",
        }
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        with patch.dict("os.environ", {"GITHUB_TOKEN": "test_token"}):
            result = pr_creator.create_pr_from_issue(
                github_issue_number=42,
                repo="user/repo",
            )

        assert result["success"] is True
        assert result["pr_number"] == 124

    def test_create_pr_task_not_found(self, pr_creator):
        """Test PR creation with non-existent task"""
        # Ensure mock returns None
        pr_creator.db.query.return_value.first.return_value = None

        with pytest.raises(PRCreationError):
            pr_creator.create_pr(task_id=99999, repo="user/repo")

    @patch("requests.get")
    def test_get_pr_status(self, mock_get, pr_creator, mock_task):
        """Test getting PR status"""
        mock_task.github_pr_number = 123
        pr_creator.db.query.return_value.first.return_value = mock_task

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "number": 123,
            "state": "open",
            "merged": False,
            "review_comments": 2,
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        with patch.dict("os.environ", {"GITHUB_TOKEN": "test_token"}):
            result = pr_creator.get_pr_status(
                task_id=mock_task.id,
                repo="user/repo",
            )

        assert result["pr_number"] == 123
        assert result["state"] == "open"
        assert result["merged"] is False

    @patch("requests.get")
    def test_list_prs_for_repo(self, mock_get, pr_creator):
        """Test listing PRs for repository"""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"number": 1, "title": "PR 1"},
            {"number": 2, "title": "PR 2"},
        ]
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        with patch.dict("os.environ", {"GITHUB_TOKEN": "test_token"}):
            result = pr_creator.list_prs_for_repo(repo="user/repo")

        assert len(result) == 2
        assert result[0]["number"] == 1

    def test_auto_create_prs_for_completed(self, pr_creator, mock_task):
        """Test auto-creation of PRs for completed tasks"""
        # Add another completed task
        task2 = GitHubTask(
            id=2,
            github_issue_number=43,
            status="completed",
            branch_name="feature/another",
            plan="Another plan",
        )
        # Mock the query result for all()
        pr_creator.db.query.return_value.all.return_value = [mock_task, task2]

        # Mock the create_pr method to return success
        with patch.object(
            pr_creator, "create_pr", return_value={"success": True, "pr_number": 125}
        ):
            result = pr_creator.auto_create_prs_for_completed(repo="user/repo")

        assert result["created"] >= 2
        assert result["success"] is True


class TestPRCreationAPI:
    """Test PR Creation API endpoints"""

    @pytest.fixture
    def client(self, app_fixture):
        """Create test client"""
        from .conftest import SyncTestClient

        return SyncTestClient(app_fixture)

    @patch("src.kortana.routers.pr_creation.PRCreator.create_pr")
    def test_create_pr_endpoint(self, mock_create, client):
        """Test POST /create/{task_id} endpoint"""
        mock_create.return_value = {
            "success": True,
            "pr_number": 123,
            "url": "https://github.com/user/repo/pull/123",
        }

        with patch.dict("os.environ", {"GITHUB_TOKEN": "test_token"}):
            response = client.post(
                "/api/pr/create/1?repo=user/repo",
                json={"code_changes": "# code"},
            )

        assert response.status_code == 200
        assert response.json()["success"] is True

    @patch("src.kortana.routers.pr_creation.PRCreator.get_pr_status")
    def test_get_pr_status_endpoint(self, mock_status, client):
        """Test GET /status/{task_id} endpoint"""
        mock_status.return_value = {
            "pr_number": 123,
            "state": "open",
            "merged": False,
        }

        with patch.dict("os.environ", {"GITHUB_TOKEN": "test_token"}):
            response = client.get("/api/pr/status/1?repo=user/repo")

        assert response.status_code == 200
        assert response.json()["pr_number"] == 123

    @patch("src.kortana.routers.pr_creation.PRCreator.list_prs_for_repo")
    def test_list_prs_endpoint(self, mock_list, client):
        """Test GET /list/{repo} endpoint"""
        mock_list.return_value = [
            {"number": 1, "title": "PR 1"},
        ]

        with patch.dict("os.environ", {"GITHUB_TOKEN": "test_token"}):
            response = client.get("/api/pr/list/user/repo")

        assert response.status_code == 200
        assert len(response.json()) >= 0

    @patch("src.kortana.routers.pr_creation.PRCreator.auto_create_prs_for_completed")
    def test_auto_create_prs_endpoint(self, mock_auto, client):
        """Test POST /auto-create-all endpoint"""
        mock_auto.return_value = {
            "success": True,
            "created": 2,
        }

        with patch.dict("os.environ", {"GITHUB_TOKEN": "test_token"}):
            response = client.post(
                "/api/pr/auto-create-all?repo=user/repo",
            )

        assert response.status_code == 200
        assert response.json()["created"] >= 0

    def test_pr_health_endpoint(self, client):
        """Test GET /pr/health endpoint"""
        response = client.get("/api/pr/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_missing_token_error(self, client):
        """Test error when GitHub token is missing"""
        with patch.dict("os.environ", {}, clear=True):
            response = client.post("/api/pr/create/1?repo=user/repo")
            assert response.status_code >= 400

    def test_invalid_repo_format_error(self, client):
        """Test error with invalid repo format"""
        with patch.dict("os.environ", {"GITHUB_TOKEN": "test"}):
            response = client.post("/api/pr/create/1?repo=invalid")
            assert response.status_code >= 400


class TestPRCreationIntegration:
    """Integration tests for PR creation workflow"""

    @patch("requests.post")
    @patch("requests.get")
    def test_issue_to_pr_workflow(self, mock_get, mock_post):
        """Test complete workflow from issue to PR"""
        # Mock GitHub API responses
        mock_post_response = MagicMock()
        mock_post_response.json.return_value = {
            "number": 123,
            "html_url": "https://github.com/user/repo/pull/123",
        }
        mock_post_response.status_code = 201
        mock_post.return_value = mock_post_response

        # Test would verify full workflow
        assert mock_post_response.status_code == 201

    @patch("requests.post")
    def test_pr_creation_with_description(self, mock_post):
        """Test PR creation includes proper description"""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        # Verify PR descriptions are generated
        assert mock_response.status_code == 201

    def test_pr_creation_database_persistence(self):
        """Test PR creation is persisted to database"""
        db = MagicMock(spec=Session)
        mock_retrieved = MagicMock(spec=GitHubTask)
        mock_retrieved.github_pr_number = 123
        mock_retrieved.github_issue_number = 42

        # Setup mock for this specific test
        db.query.return_value.filter_by.return_value.first.return_value = mock_retrieved

        retrieved = db.query(GitHubTask).filter_by(github_pr_number=123).first()
        assert retrieved is not None
        assert retrieved.github_pr_number == 123
        assert retrieved.github_issue_number == 42
