"""
Tests for Code Review Module
Tests security scanning, code quality analysis, and Gemini integration
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.kortana.routers.code_reviewer import CodeReviewer


class TestCodeReviewer:
    """Test CodeReviewer class functionality"""

    @pytest.fixture
    def code_reviewer(self):
        """Create CodeReviewer instance"""
        return CodeReviewer()

    @pytest.fixture
    def sample_code(self):
        """Sample code for review"""
        return """
def authenticate_user(username, password):
    # Vulnerable: SQL injection
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    db.execute(query)

    # Vulnerable: Hardcoded credentials
    api_token = "sk_test_123456789abcdef"

    # Code quality issue: long line
    result = do_something_with_many_parameters(param1, param2, param3, param4, param5, param6, param7, param8, param9, param10)

    return result
"""

    @pytest.fixture
    def clean_code(self):
        """Clean, secure code"""
        return """
def add_numbers(a, b):
    '''Add two numbers and return result'''
    # Good: parameterized queries
    result = a + b
    # Good: environment variables for secrets
    return result
"""

    def test_scan_for_sql_injection(self, code_reviewer, sample_code):
        """Test SQL injection vulnerability detection"""
        issues = code_reviewer.scan_for_security_issues(sample_code)

        assert len(issues) > 0
        assert any("sql" in issue.lower() for issue in issues)

    def test_scan_for_hardcoded_credentials(self, code_reviewer, sample_code):
        """Test hardcoded credentials detection"""
        issues = code_reviewer.scan_for_security_issues(sample_code)

        assert any(
            "credential" in issue.lower() or "secret" in issue.lower()
            for issue in issues
        )

    def test_scan_for_unsafe_eval(self, code_reviewer):
        """Test unsafe eval detection"""
        code = "result = eval(user_input)"
        issues = code_reviewer.scan_for_security_issues(code)

        assert len(issues) > 0
        assert any("eval" in issue.lower() for issue in issues)

    def test_scan_for_insecure_deserialization(self, code_reviewer):
        """Test insecure deserialization detection"""
        code = "data = pickle.loads(user_data)"
        issues = code_reviewer.scan_for_security_issues(code)

        assert len(issues) > 0

    def test_clean_code_passes_scan(self, code_reviewer, clean_code):
        """Test clean code has minimal issues"""
        issues = code_reviewer.scan_for_security_issues(clean_code)

        # Clean code should have no or minimal issues
        assert len(issues) <= 2

    def test_check_code_quality_long_lines(self, code_reviewer):
        """Test code quality check detects long lines"""
        code = "x = " + "a" * 150  # Very long line
        quality = code_reviewer.check_code_quality(code)

        assert quality["long_lines"] > 0

    def test_check_code_quality_comment_ratio(self, code_reviewer):
        """Test code quality check comment ratio"""
        code = """
# Comment 1
# Comment 2
x = 1
"""
        quality = code_reviewer.check_code_quality(code)

        assert "comment_ratio" in quality
        assert quality["comment_ratio"] >= 0

    def test_check_code_quality_metrics(self, code_reviewer, sample_code):
        """Test code quality metrics calculation"""
        quality = code_reviewer.check_code_quality(sample_code)

        assert "line_count" in quality
        assert "empty_lines" in quality
        assert "avg_line_length" in quality
        assert "long_lines" in quality

    @pytest.mark.asyncio
    async def test_generate_review_with_gemini(self, code_reviewer):
        """Test review generation with Gemini API"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps(
                                    {
                                        "score": 7,
                                        "summary": "Good code",
                                        "strengths": ["readable"],
                                        "improvements": ["add type hints"],
                                        "recommendation": "approve",
                                    }
                                )
                            }
                        ]
                    }
                }
            ]
        }
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch.dict("os.environ", {"GEMINI_API_KEY": "test_key"}), patch(
            "src.kortana.routers.code_reviewer.httpx.AsyncClient",
            return_value=mock_client,
        ):
            review = await code_reviewer.generate_review(
                code="def hello(): pass", plan="Add hello function"
            )

            assert "score" in review
            assert review["score"] >= 0

    def test_should_auto_approve_high_quality(self, code_reviewer):
        """Test auto-approval for high quality code"""
        review = {"score": 9, "recommendation": "approve", "summary": "Excellent code"}

        assert code_reviewer.should_auto_approve(review) is True

    def test_should_not_auto_approve_low_quality(self, code_reviewer):
        """Test no auto-approval for low quality code"""
        review = {
            "score": 5,
            "recommendation": "review",
            "summary": "Needs improvement",
        }

        assert code_reviewer.should_auto_approve(review) is False

    def test_should_not_auto_approve_rejections(self, code_reviewer):
        """Test no auto-approval for rejected reviews"""
        review = {
            "score": 8,
            "recommendation": "reject",
            "summary": "Security issues found",
        }

        assert code_reviewer.should_auto_approve(review) is False

    def test_create_review_comment_format(self, code_reviewer):
        """Test review comment formatting"""
        review = {
            "score": 8,
            "summary": "Good code",
            "strengths": ["readable", "efficient"],
            "improvements": ["add docstrings"],
            "recommendation": "approve",
        }

        comment = code_reviewer.create_review_comment(review)

        assert "Score:" in comment or "score:" in comment.lower()
        assert "Good code" in comment or "good code" in comment.lower()
        assert comment.startswith("#") or comment.startswith(">")  # Markdown format

    @pytest.mark.asyncio
    async def test_post_review_to_github(self, code_reviewer):
        """Test posting review to GitHub PR"""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 123}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        review = {
            "score": 8,
            "summary": "Good code",
            "strengths": ["readable"],
            "improvements": [],
            "recommendation": "approve",
        }

        with patch.dict("os.environ", {"GITHUB_TOKEN": "test_token"}), patch(
            "src.kortana.routers.code_reviewer.httpx.AsyncClient",
            return_value=mock_client,
        ):
            result = await code_reviewer.post_review(
                owner="testuser",
                repo="testrepo",
                pr_number=123,
                review=review,
                token="test_token",
            )

        assert result["success"] is True or result.get("comment_id") is not None

    @pytest.mark.asyncio
    async def test_post_review_dry_run(self, code_reviewer):
        """Test posting review in dry-run mode"""
        review = {
            "score": 8,
            "summary": "Good code",
            "strengths": ["readable"],
            "improvements": [],
            "recommendation": "approve",
        }

        result = await code_reviewer.post_review(
            owner="testuser",
            repo="testrepo",
            pr_number=123,
            review=review,
            token="test_token",
            dry_run=True,
        )

        assert result["dry_run"] is True

    def test_code_reviewer_initialization(self, code_reviewer):
        """Test CodeReviewer initialization"""
        assert code_reviewer is not None
        assert hasattr(code_reviewer, "scan_for_security_issues")
        assert hasattr(code_reviewer, "check_code_quality")
        assert hasattr(code_reviewer, "generate_review")
        assert hasattr(code_reviewer, "should_auto_approve")

    def test_security_patterns_defined(self, code_reviewer):
        """Test that security patterns are properly defined"""
        # Verify security scanning works
        test_codes = {
            "SQL": "SELECT * FROM users WHERE id = '" + "test" + "'",
            "eval": "eval('code')",
            "pickle": "pickle.loads(data)",
        }

        for name, code in test_codes.items():
            issues = code_reviewer.scan_for_security_issues(code)
            assert len(issues) > 0, f"Should detect {name} vulnerability"


class TestCodeReviewAPI:
    """Test Code Review API endpoints"""

    @pytest.fixture
    def client(self, app_fixture):
        """Create test client"""
        from .conftest import SyncTestClient

        return SyncTestClient(app_fixture)

    @patch("src.kortana.routers.code_reviewer.CodeReviewer.scan_for_security_issues")
    def test_scan_security_endpoint(self, mock_scan, client):
        """Test POST /scan-security endpoint"""
        mock_scan.return_value = ["SQL injection detected"]

        response = client.post(
            "/api/code-review/scan-security",
            json={"code": "SELECT * FROM users WHERE id = 'test'"},
        )

        assert response.status_code == 200
        assert len(response.json()["issues"]) > 0

    @patch("src.kortana.routers.code_reviewer.CodeReviewer.check_code_quality")
    def test_check_quality_endpoint(self, mock_quality, client):
        """Test POST /check-quality endpoint"""
        mock_quality.return_value = {
            "line_count": 10,
            "avg_line_length": 40,
        }

        response = client.post(
            "/api/code-review/check-quality", json={"code": "def hello(): pass"}
        )

        assert response.status_code == 200
        assert "line_count" in response.json()

    @patch("src.kortana.routers.code_reviewer.CodeReviewer.generate_review")
    def test_generate_review_endpoint(self, mock_generate, client):
        """Test POST /generate-review endpoint"""
        mock_generate.return_value = {
            "score": 8,
            "summary": "Good code",
            "recommendation": "approve",
        }

        response = client.post(
            "/api/code-review/generate-review",
            json={"code": "def hello(): pass", "plan": "Add hello function"},
        )

        assert response.status_code == 200
        assert response.json()["score"] >= 0

    @patch("src.kortana.routers.code_reviewer.CodeReviewer.post_review")
    def test_post_review_endpoint(self, mock_post, client):
        """Test POST /post-review endpoint"""
        mock_post.return_value = {"success": True}

        response = client.post(
            "/api/code-review/post-review",
            json={
                "owner": "testuser",
                "repo": "testrepo",
                "pr_number": 123,
                "review": {
                    "score": 8,
                    "summary": "Good code",
                    "recommendation": "approve",
                },
            },
        )

        assert response.status_code == 200

    @patch("src.kortana.routers.code_reviewer.CodeReviewer.should_auto_approve")
    def test_auto_approve_endpoint(self, mock_approve, client):
        """Test POST /auto-approve endpoint"""
        mock_approve.return_value = True

        response = client.post(
            "/api/code-review/auto-approve",
            json={"score": 9, "recommendation": "approve"},
        )

        assert response.status_code == 200
        assert response.json()["should_approve"] is True

    def test_review_health_endpoint(self, client):
        """Test GET /review/health endpoint"""
        response = client.get("/api/code-review/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestCodeReviewIntegration:
    """Integration tests for code review workflow"""

    @patch("requests.post")
    def test_security_scan_and_review(self, mock_post):
        """Test complete security scan and review workflow"""
        reviewer = CodeReviewer()

        code = """
        def unsafe_query(user_input):
            query = f"SELECT * FROM users WHERE id = '{user_input}'"
            return db.execute(query)
        """

        # Scan for security issues
        issues = reviewer.scan_for_security_issues(code)
        assert len(issues) > 0

        # Check code quality
        quality = reviewer.check_code_quality(code)
        assert "line_count" in quality

    def test_quality_gate_workflow(self):
        """Test complete quality gate workflow"""
        reviewer = CodeReviewer()

        code = "def hello():\n    pass"

        # Scan security
        security = reviewer.scan_for_security_issues(code)

        # Check quality
        quality = reviewer.check_code_quality(code)

        # Both should complete without error
        assert isinstance(security, list)
        assert isinstance(quality, dict)

    def test_review_decision_logic(self):
        """Test review decision logic"""
        reviewer = CodeReviewer()

        # High quality review
        good_review = {"score": 9, "recommendation": "approve"}
        assert reviewer.should_auto_approve(good_review) is True

        # Low quality review
        bad_review = {"score": 4, "recommendation": "review"}
        assert reviewer.should_auto_approve(bad_review) is False
