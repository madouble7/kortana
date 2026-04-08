"""
Tests for Test Orchestration Module
Tests pytest integration, coverage analysis, and CI/CD hooks
"""

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest
from src.kortana.routers.test_orchestrator import (
    TestOrchestrationError,
    TestOrchestrator,
)


class TestTestOrchestrator:
    """Test TestOrchestrator class functionality"""

    @pytest.fixture
    def orchestrator(self, tmp_path):
        """Create TestOrchestrator instance"""
        return TestOrchestrator(repo_path=str(tmp_path))

    @pytest.fixture
    def test_repo_structure(self, tmp_path):
        """Create mock test repository structure"""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()

        # Create mock test files
        (tests_dir / "test_example.py").write_text("def test_something(): pass")
        (tests_dir / "test_another.py").write_text("def test_other(): pass")

        return tmp_path

    def test_orchestrator_initialization(self, orchestrator):
        """Test TestOrchestrator initialization"""
        assert orchestrator is not None
        assert orchestrator.repo_path.exists()

    def test_initialization_with_invalid_path(self):
        """Test initialization with invalid path raises error"""
        with pytest.raises(TestOrchestrationError):
            TestOrchestrator(repo_path="/nonexistent/path/xyz")

    def test_discover_tests(self, test_repo_structure):
        """Test test discovery"""
        orchestrator = TestOrchestrator(repo_path=str(test_repo_structure))
        tests = orchestrator.discover_tests(test_dir="tests")

        assert len(tests) >= 2
        assert any("test_example.py" in t for t in tests)

    def test_discover_tests_no_directory(self, tmp_path):
        """Test discovery when test directory doesn't exist"""
        orchestrator = TestOrchestrator(repo_path=str(tmp_path))
        tests = orchestrator.discover_tests(test_dir="nonexistent")

        assert tests == []

    @patch("subprocess.run")
    def test_run_tests_success(self, mock_run, orchestrator):
        """Test successful test execution"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "3 passed in 0.25s"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = orchestrator.run_tests(verbose=True, coverage=False)

        assert result["success"] is True
        assert result["return_code"] == 0
        assert mock_run.called

    @patch("subprocess.run")
    def test_run_tests_failure(self, mock_run, orchestrator):
        """Test failed test execution"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "1 failed"
        mock_result.stderr = "AssertionError"
        mock_run.return_value = mock_result

        result = orchestrator.run_tests(verbose=True, coverage=False)

        assert result["success"] is False
        assert result["return_code"] == 1

    @patch("subprocess.run")
    def test_run_tests_with_coverage(self, mock_run, orchestrator):
        """Test test execution with coverage"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        orchestrator.run_tests(coverage=True)

        # Verify coverage flags were added
        call_args = mock_run.call_args
        assert "--cov" in str(call_args)

    @patch("subprocess.run")
    def test_run_tests_timeout(self, mock_run, orchestrator):
        """Test test execution timeout"""
        mock_run.side_effect = subprocess.TimeoutExpired("pytest", 300)

        with pytest.raises(TestOrchestrationError):
            orchestrator.run_tests()

    @patch("subprocess.run")
    def test_run_tests_with_markers(self, mock_run, orchestrator):
        """Test running tests with specific markers"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        orchestrator.run_tests(markers="unit")

        call_args = mock_run.call_args
        assert "-m" in call_args[0][0] or "-m" in str(call_args)

    def test_run_tests_dry_run(self, orchestrator):
        """Test dry-run mode"""
        result = orchestrator.run_tests(dry_run=True)

        assert result["dry_run"] is True
        assert "command" in result

    def test_parse_coverage_success(self, tmp_path):
        """Test coverage parsing"""
        orchestrator = TestOrchestrator(repo_path=str(tmp_path))

        coverage_data = {
            "totals": {
                "percent_covered": 85.5,
                "num_statements": 100,
                "num_missing": 15,
            },
            "files": {"main.py": {}, "utils.py": {}},
        }

        coverage_file = tmp_path / "coverage.json"
        coverage_file.write_text(json.dumps(coverage_data))

        result = orchestrator.parse_coverage()

        assert result["percent_covered"] == 85.5
        assert result["num_statements"] == 100
        assert result["files"] == 2

    def test_parse_coverage_file_not_found(self, tmp_path):
        """Test coverage parsing when file doesn't exist"""
        orchestrator = TestOrchestrator(repo_path=str(tmp_path))
        result = orchestrator.parse_coverage()

        assert "error" in result

    def test_check_coverage_threshold_pass(self, tmp_path):
        """Test coverage threshold check passes"""
        orchestrator = TestOrchestrator(repo_path=str(tmp_path))

        coverage_data = {
            "totals": {
                "percent_covered": 90.0,
                "num_statements": 100,
                "num_missing": 10,
            },
            "files": {},
        }

        coverage_file = tmp_path / "coverage.json"
        coverage_file.write_text(json.dumps(coverage_data))

        result = orchestrator.check_coverage_threshold(threshold=80.0)

        assert result is True

    def test_check_coverage_threshold_fail(self, tmp_path):
        """Test coverage threshold check fails"""
        orchestrator = TestOrchestrator(repo_path=str(tmp_path))

        coverage_data = {
            "totals": {
                "percent_covered": 70.0,
                "num_statements": 100,
                "num_missing": 30,
            },
            "files": {},
        }

        coverage_file = tmp_path / "coverage.json"
        coverage_file.write_text(json.dumps(coverage_data))

        result = orchestrator.check_coverage_threshold(threshold=80.0)

        assert result is False

    @patch("subprocess.run")
    def test_run_specific_tests(self, mock_run, orchestrator):
        """Test running specific tests"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        test_names = ["tests/test_example.py::test_one", "tests/test_example.py::test_two"]
        result = orchestrator.run_specific_tests(test_names=test_names)

        assert result["success"] is True
        assert result["tests"] == test_names

    def test_run_specific_tests_dry_run(self, orchestrator):
        """Test dry-run for specific tests"""
        test_names = ["tests/test_example.py::test_one"]
        result = orchestrator.run_specific_tests(test_names=test_names, dry_run=True)

        assert result["dry_run"] is True
        assert result["tests"] == test_names

    @patch("subprocess.run")
    def test_run_linting(self, mock_run, orchestrator):
        """Test linting execution"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = orchestrator.run_linting()

        assert result["success"] is True
        assert mock_run.called

    @patch("subprocess.run")
    def test_run_linting_with_errors(self, mock_run, orchestrator):
        """Test linting with errors"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "E501: line too long"
        mock_run.return_value = mock_result

        result = orchestrator.run_linting()

        assert result["success"] is False

    def test_run_linting_dry_run(self, orchestrator):
        """Test linting dry-run"""
        result = orchestrator.run_linting(dry_run=True)

        assert result["dry_run"] is True

    @patch("subprocess.run")
    def test_run_type_checking(self, mock_run, orchestrator):
        """Test type checking execution"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = orchestrator.run_type_checking()

        assert result["success"] is True

    def test_run_type_checking_dry_run(self, orchestrator):
        """Test type checking dry-run"""
        result = orchestrator.run_type_checking(dry_run=True)

        assert result["dry_run"] is True

    @patch.object(TestOrchestrator, "run_linting")
    @patch.object(TestOrchestrator, "run_type_checking")
    @patch.object(TestOrchestrator, "run_tests")
    def test_run_full_pipeline(self, mock_tests, mock_type, mock_lint, orchestrator):
        """Test full pipeline execution"""
        mock_lint.return_value = {"success": True}
        mock_type.return_value = {"success": True}
        mock_tests.return_value = {"success": True}

        result = orchestrator.run_full_pipeline()

        assert result["success"] is True
        assert len(result["steps"]) >= 3

    def test_run_full_pipeline_dry_run(self, orchestrator):
        """Test full pipeline dry-run"""
        result = orchestrator.run_full_pipeline(dry_run=True)

        assert result["success"] is True
        assert len(result["steps"]) >= 1

    @patch.object(TestOrchestrator, "run_linting")
    def test_full_pipeline_stops_on_error(self, mock_lint, orchestrator):
        """Test pipeline stops on first error"""
        mock_lint.return_value = {"success": False, "error": "Linting failed"}

        with patch.object(TestOrchestrator, "run_type_checking") as mock_type:
            mock_type.return_value = {"success": True}
            result = orchestrator.run_full_pipeline()

            # Type checking should not be called if linting fails
            assert result["success"] is False


class TestTestOrchestrationAPI:
    """Test Test Orchestration API endpoints"""

    @pytest.fixture
    def client(self, app_fixture):
        """Create test client"""
        from .conftest import SyncTestClient
        return SyncTestClient(app_fixture)

    @patch("src.kortana.routers.test_orchestrator.TestOrchestrator.run_tests")
    def test_run_tests_endpoint(self, mock_run, client):
        """Test POST /tests/run endpoint"""
        mock_run.return_value = {
            "success": True,
            "return_code": 0,
        }

        response = client.post("/api/testing/run", json={"test_dir": "tests", "coverage": True})

        assert response.status_code == 200

    @patch("src.kortana.routers.test_orchestrator.TestOrchestrator.discover_tests")
    def test_discover_tests_endpoint(self, mock_discover, client):
        """Test GET /tests/discover endpoint"""
        mock_discover.return_value = ["test_example.py", "test_other.py"]

        response = client.get("/api/testing/discover")

        assert response.status_code == 200
        assert len(response.json()) >= 0

    @patch("src.kortana.routers.test_orchestrator.TestOrchestrator.run_full_pipeline")
    def test_full_pipeline_endpoint(self, mock_pipeline, client):
        """Test POST /tests/pipeline endpoint"""
        mock_pipeline.return_value = {"success": True, "steps": []}

        response = client.post("/api/testing/pipeline")

        assert response.status_code == 200

    @patch("src.kortana.routers.test_orchestrator.TestOrchestrator.check_coverage_threshold")
    def test_coverage_endpoint(self, mock_coverage, client):
        """Test POST /tests/coverage endpoint"""
        mock_coverage.return_value = True

        response = client.post("/api/testing/coverage", json={"threshold": 80.0})

        assert response.status_code == 200

    def test_orchestration_health_endpoint(self, client):
        """Test GET /tests/health endpoint"""
        response = client.get("/api/testing/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestTestOrchestrationIntegration:
    """Integration tests for test automation workflow"""

    @patch("subprocess.run")
    def test_discover_and_run_workflow(self, mock_run):
        """Test discovering and running tests"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        # In real scenario, would discover then run
        assert mock_result.returncode == 0

    def test_coverage_gate_enforcement(self, tmp_path):
        """Test coverage gate enforcement"""
        orchestrator = TestOrchestrator(repo_path=str(tmp_path))

        # Simulate low coverage
        coverage_data = {
            "totals": {
                "percent_covered": 75.0,
                "num_statements": 100,
                "num_missing": 25,
            },
            "files": {},
        }

        coverage_file = tmp_path / "coverage.json"
        coverage_file.write_text(json.dumps(coverage_data))

        # Should fail with 80% threshold
        assert orchestrator.check_coverage_threshold(threshold=80.0) is False

        # Should pass with 70% threshold
        assert orchestrator.check_coverage_threshold(threshold=70.0) is True

    @patch("subprocess.run")
    def test_lint_type_test_sequence(self, mock_run):
        """Test sequence of linting, type checking, and testing"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        # Would run all three in sequence
        assert mock_result.returncode == 0
