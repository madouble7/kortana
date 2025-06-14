"""
Kor'tana's Execution Engine
Provides safe, controlled interaction with the file system and shell commands.
This is the bridge between Kor'tana's intelligence and the real world.
"""

import ast
import asyncio
import logging
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class OperationResult:
    """Result of an execution engine operation"""

    success: bool
    data: str | dict[str, Any] | list[dict[str, Any]] | None = None
    error: str | None = None
    duration: float = 0
    operation_type: str = ""
    returncode: int | None = None  # Return code from shell commands


class ExecutionEngine:
    """
    Safe execution engine with built-in security controls.
    Enables Kor'tana to interact with her environment while maintaining safety.
    """

    def __init__(self, allowed_dirs: list[str], blocked_commands: list[str]):
        """Initialize the execution engine with safety controls

        Args:
            allowed_dirs: List of directory paths that the engine can access
            blocked_commands: List of shell commands that are forbidden
        """
        self.allowed_dirs = [os.path.abspath(d) for d in allowed_dirs]
        self.blocked_commands = blocked_commands
        self._command_history: list[dict] = []
        self._start_time = time.time()

    def _validate_path_access(self, filepath: str | Path) -> bool:
        """Check if a file path is within allowed directories"""
        abs_path = os.path.abspath(str(filepath))
        return any(abs_path.startswith(d) for d in self.allowed_dirs)

    def _validate_command(self, command: str) -> bool:
        """Check if a shell command is allowed"""
        cmd = command.strip().split()[0].lower()
        return not any(blocked in cmd for blocked in self.blocked_commands)

    def _log_operation(self, operation: str, details: dict) -> None:
        """Log an operation to history"""
        timestamp = time.time()
        self._command_history.append(
            {
                "operation": operation,
                "timestamp": timestamp,
                "runtime": timestamp - self._start_time,
                **details,
            }
        )

    async def read_file(self, filepath: str) -> OperationResult:
        """Safely read a file from allowed directories."""
        start = time.time()
        try:
            if not self._validate_path_access(filepath):
                return OperationResult(
                    success=False,
                    error="Access denied: outside allowed directories.",
                    duration=time.time() - start,
                    operation_type="read_file",
                    returncode=1,
                )

            async with asyncio.Lock():
                with open(filepath, encoding="utf-8") as f:
                    content = f.read()

            self._log_operation("read_file", {"file": filepath, "size": len(content)})

            return OperationResult(
                success=True,
                data=content,
                duration=time.time() - start,
                operation_type="read_file",
                returncode=0,
            )

        except Exception as e:
            logger.error(f"Error reading file {filepath}: {str(e)}")
            return OperationResult(
                success=False,
                error=str(e),
                duration=time.time() - start,
                operation_type="read_file",
                returncode=1,
            )

    async def write_to_file(self, filepath: str, content: str) -> OperationResult:
        """Safely write content to a file in allowed directories."""
        start = time.time()
        try:
            if not self._validate_path_access(filepath):
                return OperationResult(
                    success=False,
                    error="Access denied: outside allowed directories.",
                    duration=time.time() - start,
                    operation_type="write_file",
                    returncode=1,
                )

            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            async with asyncio.Lock():
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)

            self._log_operation("write_file", {"file": filepath, "size": len(content)})

            return OperationResult(
                success=True,
                duration=time.time() - start,
                operation_type="write_file",
                returncode=0,
            )

        except Exception as e:
            logger.error(f"Error writing to file {filepath}: {str(e)}")
            return OperationResult(
                success=False,
                error=str(e),
                duration=time.time() - start,
                operation_type="write_file",
                returncode=1,
            )

    async def execute_shell_command(
        self, command: str, working_dir: str = "", timeout: int = 300
    ) -> OperationResult:
        """Safely execute a shell command, blocking dangerous commands.

        Args:
            command: The shell command to execute
            working_dir: Optional working directory
            timeout: Maximum execution time in seconds

        Returns:
            OperationResult containing command output or error
        """
        start = time.time()
        try:
            if not self._validate_command(command):
                return OperationResult(
                    success=False,
                    error=f"Command '{command}' is blocked for security.",
                    duration=time.time() - start,
                    operation_type="shell_command",
                    returncode=1,
                )

            if working_dir and not self._validate_path_access(working_dir):
                return OperationResult(
                    success=False,
                    error=f"Working directory '{working_dir}' is outside allowed paths.",
                    duration=time.time() - start,
                    operation_type="shell_command",
                    returncode=1,
                )

            work_dir = working_dir if working_dir else os.getcwd()

            # Run command with timeout
            process = await asyncio.create_subprocess_shell(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=work_dir
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
            except TimeoutError:
                try:
                    process.kill()
                except Exception:
                    pass

                return OperationResult(
                    success=False,
                    error=f"Command timed out after {timeout} seconds",
                    duration=time.time() - start,
                    operation_type="shell_command",
                    returncode=1,
                )

            return_code = process.returncode or 1
            self._log_operation(
                "shell_command",
                {
                    "command": command,
                    "working_dir": work_dir,
                    "return_code": return_code,
                },
            )

            if return_code != 0:
                return OperationResult(
                    success=False,
                    error=f"Command failed: {stderr.decode()}",
                    data={
                        "stdout": stdout.decode(),
                        "stderr": stderr.decode(),
                        "return_code": return_code,
                    },
                    duration=time.time() - start,
                    operation_type="shell_command",
                    returncode=return_code,
                )

            return OperationResult(
                success=True,
                data={
                    "stdout": stdout.decode(),
                    "stderr": stderr.decode(),
                    "return_code": return_code,
                },
                duration=time.time() - start,
                operation_type="shell_command",
                returncode=return_code,
            )

        except Exception as e:
            logger.error(f"Error executing command '{command}': {str(e)}")
            return OperationResult(
                success=False,
                error=str(e),
                duration=time.time() - start,
                operation_type="shell_command",
                returncode=1,
            )

    async def analyze_codebase(
        self,
        project_base_path: str | Path,
        rules: list[str] | None = None,
        file_patterns: list[str] | None = None,
    ) -> OperationResult:
        """Analyze codebase for code quality issues.

        Args:
            project_base_path: Base path of the project to analyze
            rules: List of analysis rules to apply
            file_patterns: File patterns to analyze

        Returns:
            OperationResult with analysis results
        """
        start_time = time.time()
        issues_found: list[dict[str, Any]] = []

        try:
            # Validate project path
            if not self._validate_path_access(project_base_path):
                return OperationResult(
                    success=False,
                    error="Project path is outside allowed directories",
                    duration=time.time() - start_time,
                    operation_type="analyze_code",
                    returncode=1,
                )

            # Set default patterns and rules
            patterns = file_patterns if file_patterns is not None else ["*.py"]
            rules_to_apply = rules if rules is not None else ["missing_docstring"]

            # Process each matching file
            base_path = Path(project_base_path)
            for pattern in patterns:
                for filepath_obj in base_path.rglob(pattern):
                    filepath_str = str(filepath_obj)

                    # Skip files outside allowed paths
                    if not self._validate_path_access(filepath_str):
                        continue

                    # Process each file
                    try:
                        with open(filepath_obj, encoding="utf-8") as f:
                            content = f.read()

                            # Run docstring analysis if requested
                            if "missing_docstring" in rules_to_apply:
                                self._analyze_docstrings(
                                    content,
                                    filepath_obj,
                                    filepath_str,
                                    project_base_path,
                                    issues_found,
                                )

                    except (UnicodeDecodeError, PermissionError, OSError) as e:
                        logger.warning(f"Could not analyze {filepath_str}: {e}")

            # Log operation completion
            self._log_operation(
                "analyze_code",
                {
                    "base_path": str(project_base_path),
                    "rules": rules_to_apply,
                    "issues_count": len(issues_found),
                },
            )

            return OperationResult(
                success=True,
                data={"issues": issues_found},
                duration=time.time() - start_time,
                operation_type="analyze_code",
                returncode=0,
            )

        except Exception as e:
            logger.error(f"Error analyzing codebase: {e}")
            return OperationResult(
                success=False,
                error=str(e),
                duration=time.time() - start_time,
                operation_type="analyze_code",
                returncode=1,
            )

    def _analyze_docstrings(
        self,
        content: str,
        filepath_obj: Path,
        filepath_str: str,
        project_base_path: str | Path,
        issues_found: list[dict[str, Any]],
    ) -> None:
        """Analyze Python code for missing docstrings.

        Args:
            content: The Python source code to analyze
            filepath_obj: Path object for the file
            filepath_str: String representation of the file path
            project_base_path: Base path of the project for relative paths
            issues_found: List to append issues to
        """
        try:
            if not isinstance(content, str) or not content:
                logger.warning(f"Invalid content for {filepath_str}")
                return

            tree = ast.parse(content, filename=filepath_str)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                    docstring = ast.get_docstring(node, clean=False)
                    if docstring is None:
                        issues_found.append(
                            {
                                "file_path": filepath_str,
                                "relative_path": str(
                                    filepath_obj.relative_to(project_base_path)
                                ),
                                "function_name": node.name,
                                "line_number": node.lineno,
                                "issue_type": "missing_docstring",
                                "message": f"Function '{node.name}' is missing a docstring.",
                            }
                        )

        except SyntaxError as e:
            logger.warning(f"SyntaxError parsing {filepath_str}: {e}")
            issues_found.append(
                {
                    "file_path": filepath_str,
                    "relative_path": str(filepath_obj.relative_to(project_base_path)),
                    "function_name": None,  # No function context for file-level errors
                    "line_number": e.lineno,
                    "issue_type": "syntax_error",
                    "message": f"Syntax error: {e.msg}",
                }
            )

        except Exception as e:
            logger.error(f"Error analyzing docstrings in {filepath_str}: {e}")
