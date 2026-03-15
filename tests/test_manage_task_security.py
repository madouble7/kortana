"""
Tests for security fixes in manage_task.py

These tests verify that the security vulnerabilities have been properly fixed:
1. Module whitelist validation
2. Function name validation
3. Environment variable name validation
4. Command injection prevention
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from src.kortana.manage_task import (
    execute_task,
    load_task_config,
    save_task_result,
    validate_command_args,
    validate_module_name,
)


class TestModuleValidation:
    """Test module name validation security."""

    def test_validate_allowed_module(self):
        """Test that allowed modules pass validation."""
        assert validate_module_name("kortana.agents.test_agent")
        assert validate_module_name("kortana.core.brain")
        assert validate_module_name("kortana.tools.helper")
        assert validate_module_name("kortana.utils.formatter")

    def test_validate_disallowed_module(self):
        """Test that disallowed modules fail validation."""
        assert not validate_module_name("os.system")
        assert not validate_module_name("subprocess.run")
        assert not validate_module_name("malicious_module")
        assert not validate_module_name("__import__")


class TestCommandValidation:
    """Test command validation security."""

    def test_validate_safe_commands(self):
        """Test that safe commands pass validation."""
        assert validate_command_args("echo hello")
        assert validate_command_args("ls -la")
        assert validate_command_args("python --version")

    def test_validate_dangerous_commands(self):
        """Test that dangerous commands fail validation."""
        # Shell metacharacters
        assert not validate_command_args("echo hello; rm -rf /")
        assert not validate_command_args("echo hello && rm -rf /")
        assert not validate_command_args("echo hello | cat /etc/passwd")
        assert not validate_command_args("echo hello `whoami`")
        assert not validate_command_args("echo hello $(whoami)")
        
        # Variable expansion
        assert not validate_command_args("echo ${PATH}")
        
        # Redirections
        assert not validate_command_args("cat file > &2")
        assert not validate_command_args("cat file < &0")


class TestTaskExecution:
    """Test task execution with security validations."""

    def setup_method(self):
        """Set up test environment."""
        self.task_dir = Path("tasks")
        self.task_dir.mkdir(exist_ok=True)
        
        self.result_dir = Path("task_results")
        self.result_dir.mkdir(exist_ok=True)

    def teardown_method(self):
        """Clean up test files."""
        # Clean up task configs
        if self.task_dir.exists():
            for file in self.task_dir.glob("test_*.json"):
                file.unlink()
        
        # Clean up results
        if self.result_dir.exists():
            for file in self.result_dir.glob("test_*.json"):
                file.unlink()

    def test_invalid_module_rejected(self):
        """Test that tasks with invalid modules are rejected."""
        task_config = {
            "module": "os.system",
            "function": "execute",
            "args": {}
        }
        
        task_file = self.task_dir / "test_invalid_module.json"
        with open(task_file, "w") as f:
            json.dump(task_config, f)
        
        result = execute_task("test_invalid_module")
        
        assert result["success"] is False
        assert "not allowed" in result["error"]

    def test_invalid_function_name_rejected(self):
        """Test that tasks with invalid function names are rejected."""
        task_config = {
            "module": "kortana.core.brain",
            "function": "__import__",
            "args": {}
        }
        
        task_file = self.task_dir / "test_invalid_function.json"
        with open(task_file, "w") as f:
            json.dump(task_config, f)
        
        result = execute_task("test_invalid_function")
        
        assert result["success"] is False
        assert "Invalid function name" in result["error"]

    def test_invalid_env_var_rejected(self):
        """Test that tasks with invalid environment variables are rejected."""
        task_config = {
            "env_vars": {
                "INVALID-VAR": "value",  # Hyphen not allowed
            },
            "command": "echo test"
        }
        
        task_file = self.task_dir / "test_invalid_env.json"
        with open(task_file, "w") as f:
            json.dump(task_config, f)
        
        result = execute_task("test_invalid_env")
        
        assert result["success"] is False
        assert "Invalid environment variable" in result["error"]

    def test_dangerous_command_rejected(self):
        """Test that dangerous commands are rejected."""
        task_config = {
            "command": "echo hello; rm -rf /"
        }
        
        task_file = self.task_dir / "test_dangerous_cmd.json"
        with open(task_file, "w") as f:
            json.dump(task_config, f)
        
        result = execute_task("test_dangerous_cmd")
        
        assert result["success"] is False
        assert "validation failed" in result["error"]

    def test_safe_command_accepted(self):
        """Test that safe commands are accepted (may fail if command doesn't exist, but should pass validation)."""
        task_config = {
            "command": "echo hello"
        }
        
        task_file = self.task_dir / "test_safe_cmd.json"
        with open(task_file, "w") as f:
            json.dump(task_config, f)
        
        result = execute_task("test_safe_cmd")
        
        # Command should pass validation (success depends on whether 'echo' exists)
        # We're mainly testing it doesn't fail with "validation failed"
        if not result["success"]:
            assert "validation failed" not in result.get("error", "")


class TestLoadSaveOperations:
    """Test load and save operations."""

    def setup_method(self):
        """Set up test environment."""
        self.task_dir = Path("tasks")
        self.task_dir.mkdir(exist_ok=True)
        
        self.result_dir = Path("task_results")
        self.result_dir.mkdir(exist_ok=True)

    def test_load_nonexistent_task(self):
        """Test loading a task that doesn't exist."""
        result = load_task_config("nonexistent_task")
        assert result is None

    def test_load_valid_task(self):
        """Test loading a valid task configuration."""
        task_config = {"command": "echo test"}
        task_file = self.task_dir / "test_valid.json"
        
        with open(task_file, "w") as f:
            json.dump(task_config, f)
        
        loaded = load_task_config("test_valid")
        assert loaded is not None
        assert loaded["command"] == "echo test"
        
        # Clean up
        task_file.unlink()

    def test_save_task_result(self):
        """Test saving a task result."""
        result = {
            "success": True,
            "task_id": "test_save",
            "result": "test result"
        }
        
        save_task_result("test_save", result)
        
        # Check that a result file was created
        result_files = list(self.result_dir.glob("test_save-*.json"))
        assert len(result_files) > 0
        
        # Clean up
        for file in result_files:
            file.unlink()
