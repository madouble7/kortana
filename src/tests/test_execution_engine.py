"""
Unit tests for Kor'tana's ExecutionEngine
"""

import asyncio
import os
from pathlib import Path

import pytest

from kortana.core.execution_engine import ExecutionEngine

TEST_DIR = Path(__file__).parent / "test_data"
ALLOWED_DIRS = [str(TEST_DIR)]
BLOCKED_COMMANDS = ["rm", "del", "rmdir", "format"]


@pytest.fixture
def engine():
    """Create a test execution engine instance"""
    os.makedirs(TEST_DIR, exist_ok=True)
    engine = ExecutionEngine(ALLOWED_DIRS, BLOCKED_COMMANDS)
    yield engine
    # Cleanup test directory after test
    if TEST_DIR.exists():
        for f in TEST_DIR.glob("*"):
            try:
                f.unlink()
            except:
                pass
        TEST_DIR.rmdir()


@pytest.mark.asyncio
async def test_read_file(engine):
    """Test reading a file within allowed directory"""
    test_file = TEST_DIR / "test.txt"
    test_content = "Hello Kor'tana!"

    with open(test_file, "w") as f:
        f.write(test_content)

    result = await engine.read_file(str(test_file))
    assert result.success
    assert result.data == test_content
    assert result.operation_type == "read_file"
    assert result.duration > 0
    assert result.error is None


@pytest.mark.asyncio
async def test_read_file_outside_allowed(engine):
    """Test reading a file outside allowed directories fails"""
    result = await engine.read_file("/etc/passwd")
    assert not result.success
    assert "Access denied" in result.error
    assert result.operation_type == "read_file"


@pytest.mark.asyncio
async def test_write_file(engine):
    """Test writing a file within allowed directory"""
    test_file = TEST_DIR / "write_test.txt"
    test_content = "Test write content"

    result = await engine.write_to_file(str(test_file), test_content)
    assert result.success
    assert result.operation_type == "write_file"
    assert result.duration > 0

    # Verify content was written
    with open(test_file) as f:
        assert f.read() == test_content


@pytest.mark.asyncio
async def test_write_file_outside_allowed(engine):
    """Test writing a file outside allowed directories fails"""
    result = await engine.write_to_file("/tmp/test.txt", "test")
    assert not result.success
    assert "Access denied" in result.error
    assert result.operation_type == "write_file"


@pytest.mark.asyncio
async def test_execute_command(engine):
    """Test executing an allowed command"""
    result = await engine.execute_shell_command(
        "echo 'test'", working_dir=str(TEST_DIR)
    )
    assert result.success
    assert "test" in result.data["stdout"]
    assert result.operation_type == "shell_command"
    assert result.duration > 0


@pytest.mark.asyncio
async def test_blocked_command(engine):
    """Test that blocked commands are prevented"""
    result = await engine.execute_shell_command("rm -rf /", working_dir=str(TEST_DIR))
    assert not result.success
    assert "blocked for security" in result.error
    assert result.operation_type == "shell_command"


@pytest.mark.asyncio
async def test_command_timeout(engine):
    """Test command timeout works"""
    result = await engine.execute_shell_command(
        "sleep 2", timeout=1, working_dir=str(TEST_DIR)
    )
    assert not result.success
    assert "timed out" in result.error
    assert result.operation_type == "shell_command"


def test_metrics(engine):
    """Test metrics collection"""

    # Run some operations
    async def run_ops():
        await engine.read_file(str(TEST_DIR / "nonexistent.txt"))  # Error
        test_file = TEST_DIR / "metrics_test.txt"
        await engine.write_to_file(str(test_file), "test")  # Success
        await engine.execute_shell_command("echo test")  # Success

    asyncio.run(run_ops())

    metrics = engine.export_metrics()

    assert metrics["total_operations"] == 3
    assert metrics["error_count"] == 1
    assert metrics["success_rate"] == 2 / 3
    assert "read_file" in metrics["operation_types"]
    assert "write_file" in metrics["operation_types"]
    assert "shell_command" in metrics["operation_types"]
    assert metrics["total_runtime"] > 0
    assert metrics["total_operation_time"] > 0


def test_history_clear(engine):
    """Test history clearing works"""

    # Run an operation
    async def run_op():
        await engine.write_to_file(str(TEST_DIR / "test.txt"), "test")

    asyncio.run(run_op())
    assert len(engine.get_operation_history()) == 1

    engine.clear_history()
    assert len(engine.get_operation_history()) == 0
