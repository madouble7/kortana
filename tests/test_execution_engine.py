import os
from unittest.mock import MagicMock, mock_open, patch

import pytest

from kortana.core.execution_engine import ExecutionEngine

# Define allowed directories and blocked commands for testing
ALLOWED_DIRS = [
    os.path.abspath("c:\\project-kortana\\src"),
    os.path.abspath("c:\\project-kortana\\tests"),
]
BLOCKED_COMMANDS = ["rm", "sudo"]


@pytest.fixture
def execution_engine():
    """Fixture to create an ExecutionEngine instance with test configurations."""
    return ExecutionEngine(allowed_dirs=ALLOWED_DIRS, blocked_commands=BLOCKED_COMMANDS)


@patch("builtins.open", new_callable=mock_open)
@patch(
    "os.path.abspath", side_effect=lambda x: x
)  # Mock abspath to simplify testing paths
def test_edit_file_success(mock_abspath, mock_file, execution_engine):
    """Test successful file editing within allowed directory."""
    file_path = os.path.join(ALLOWED_DIRS[0], "test_file.txt")
    initial_content = "This is some old text."
    edits = [{"target": "old text", "replacement": "new text"}]
    expected_content = "This is some new text."

    mock_file.return_value.read.return_value = initial_content

    result = execution_engine.edit_file(file_path, edits)

    assert result["success"] is True
    assert result["message"] == f"Successfully edited {file_path}"
    mock_file.assert_called_with(file_path, "w", encoding="utf-8")
    mock_file.return_value.write.assert_called_once_with(expected_content)


@patch("os.path.abspath", side_effect=lambda x: x)
def test_edit_file_outside_allowed_dirs(mock_abspath, execution_engine):
    """Test file editing failure outside allowed directories."""
    file_path = os.path.abspath("c:\\outside\\sensitive_file.txt")
    edits = [{"target": "old_text", "replacement": "new_text"}]

    result = execution_engine.edit_file(file_path, edits)

    assert result["success"] is False
    assert "outside of allowed directories" in result["error"]


@patch("subprocess.run")
@patch("os.path.abspath", side_effect=lambda x: x)
def test_run_tests_success(mock_subprocess_run, mock_abspath, execution_engine):
    """Test successful test execution."""
    test_command = "pytest tests/some_test.py"
    mock_subprocess_run.return_value = MagicMock(
        returncode=0, stdout="Tests passed", stderr=""
    )

    result = execution_engine.run_tests(test_command)

    assert result["success"] is True
    assert result["return_code"] == 0
    assert result["stdout"] == "Tests passed"
    mock_subprocess_run.assert_called_once()


@patch("subprocess.run")
@patch("os.path.abspath", side_effect=lambda x: x)
def test_run_tests_failure(mock_subprocess_run, mock_abspath, execution_engine):
    """Test test execution failure."""
    test_command = "pytest tests/some_test.py"
    mock_subprocess_run.return_value = MagicMock(
        returncode=1, stdout="", stderr="Tests failed"
    )

    result = execution_engine.run_tests(test_command)

    assert result["success"] is False
    assert result["return_code"] == 1
    assert result["stderr"] == "Tests failed"
    mock_subprocess_run.assert_called_once()


@patch("subprocess.run")
@patch("os.path.abspath", side_effect=lambda x: x)
def test_execute_shell_command_blocked(
    mock_subprocess_run, mock_abspath, execution_engine
):
    """
    Test blocking of a dangerous shell command.
    """
    blocked_command = "sudo rm -rf /"

    result = execution_engine.execute_shell_command(blocked_command)

    assert result["success"] is False
    assert "is blocked for security reasons" in result["error"]
    mock_subprocess_run.assert_not_called()


@patch("subprocess.run")
@patch("os.path.abspath", side_effect=lambda x: x)
def test_deploy_success(mock_subprocess_run, mock_abspath, execution_engine):
    """Test successful deployment."""
    deploy_command = "sh deploy.sh"
    mock_subprocess_run.return_value = MagicMock(
        returncode=0, stdout="Deployment successful", stderr=""
    )

    result = execution_engine.deploy(deploy_command)

    assert result["success"] is True
    assert result["return_code"] == 0
    assert result["stdout"] == "Deployment successful"
    mock_subprocess_run.assert_called_once()
