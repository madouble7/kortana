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
    data: Any | None = None
    error: str | None = None
    duration: float = 0
    operation_type: str = ""


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
            )

        except Exception as e:
            logger.error(f"Error reading file {filepath}: {str(e)}")
            return OperationResult(
                success=False,
                error=str(e),
                duration=time.time() - start,
                operation_type="read_file",
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
                )

            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            async with asyncio.Lock():
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)

            self._log_operation("write_file", {"file": filepath, "size": len(content)})

            return OperationResult(
                success=True, duration=time.time() - start, operation_type="write_file"
            )

        except Exception as e:
            logger.error(f"Error writing to file {filepath}: {str(e)}")
            return OperationResult(
                success=False,
                error=str(e),
                duration=time.time() - start,
                operation_type="write_file",
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
                )

            if working_dir and not self._validate_path_access(working_dir):
                return OperationResult(
                    success=False,
                    error=f"Working directory '{working_dir}' is outside allowed paths.",
                    duration=time.time() - start,
                    operation_type="shell_command",
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
                )

            self._log_operation(
                "shell_command",
                {
                    "command": command,
                    "working_dir": work_dir,
                    "return_code": process.returncode,
                },
            )

            if process.returncode != 0:
                return OperationResult(
                    success=False,
                    error=f"Command failed: {stderr.decode()}",
                    data={
                        "stdout": stdout.decode(),
                        "stderr": stderr.decode(),
                        "return_code": process.returncode,
                    },
                    duration=time.time() - start,
                    operation_type="shell_command",
                )

            return OperationResult(
                success=True,
                data={
                    "stdout": stdout.decode(),
                    "stderr": stderr.decode(),
                    "return_code": process.returncode,
                },
                duration=time.time() - start,
                operation_type="shell_command",
            )

        except Exception as e:
            logger.error(f"Error executing command '{command}': {str(e)}")
            return OperationResult(
                success=False,
                error=str(e),
                duration=time.time() - start,
                operation_type="shell_command",
            )

    # ========== GENESIS PROTOCOL: ADVANCED DEVELOPMENT TOOLS ==========
    async def search_codebase(
        self, query: str, file_patterns: list[str] | None = None, max_results: int = 50
    ) -> OperationResult:
        """
        SEARCH_CODEBASE: Find relevant code snippets or files using semantic and pattern search.

        Args:
            query: Search query (can be function names, patterns, or semantic descriptions)
            file_patterns: List of file patterns to search (e.g., ['*.py', '*.md'])
            max_results: Maximum number of results to return

        Returns:
            OperationResult with search results
        """
        start = time.time()
        try:
            search_results = []

            # Default patterns if none provided
            if file_patterns is None:
                file_patterns = ["*.py", "*.md", "*.yaml", "*.json"]

            # Search through allowed directories
            for allowed_dir in self.allowed_dirs:
                for pattern in file_patterns:
                    for filepath in Path(allowed_dir).rglob(pattern):
                        if not self._validate_path_access(filepath):
                            continue

                        try:
                            with open(filepath, encoding="utf-8") as f:
                                content = f.read()

                            # Simple text search (can be enhanced with semantic search later)
                            if query.lower() in content.lower():
                                # Find relevant lines with context
                                lines = content.split("\n")
                                for i, line in enumerate(lines):
                                    if query.lower() in line.lower():
                                        # Get context (3 lines before and after)
                                        start_line = max(0, i - 3)
                                        end_line = min(len(lines), i + 4)
                                        context = "\n".join(lines[start_line:end_line])

                                        search_results.append(
                                            {
                                                "file": str(filepath),
                                                "line_number": i + 1,
                                                "matched_line": line.strip(),
                                                "context": context,
                                                "relative_path": str(
                                                    filepath.relative_to(allowed_dir)
                                                ),
                                            }
                                        )

                                        if len(search_results) >= max_results:
                                            break

                        except (UnicodeDecodeError, PermissionError):
                            # Skip files that can't be read
                            continue

                        if len(search_results) >= max_results:
                            break
                    if len(search_results) >= max_results:
                        break
                if len(search_results) >= max_results:
                    break

            self._log_operation(
                "search_codebase",
                {
                    "query": query,
                    "results_found": len(search_results),
                    "patterns": file_patterns,
                },
            )

            return OperationResult(
                success=True,
                data={
                    "query": query,
                    "results": search_results,
                    "total_found": len(search_results),
                },
                duration=time.time() - start,
                operation_type="search_codebase",
            )

        except Exception as e:
            logger.error(f"Error searching codebase: {str(e)}")
            return OperationResult(
                success=False,
                error=str(e),
                duration=time.time() - start,
                operation_type="search_codebase",
            )

    async def scan_codebase_for_issues(
        self,
        directory_to_scan: str,
        rules: list[str],
        file_patterns: list[str] | None = None,
    ) -> OperationResult:
        start_time = time.time()
        issues_found: list[dict] = []

        if not self._validate_path_access(directory_to_scan):
            return OperationResult(
                success=False,
                error=f"Access denied: Directory '{directory_to_scan}' is outside allowed paths.",
                duration=time.time() - start_time,
                operation_type="scan_codebase_for_issues",
            )

        if file_patterns is None:
            file_patterns = ["*.py"]

        # Ensure directory_to_scan is absolute for Path operations
        # and that self.allowed_dirs[0] is a safe base for relative_to
        # This assumes self.allowed_dirs[0] is the project root or a relevant base.
        # A more robust solution might involve finding the common parent path.
        try:
            project_base_path = (
                Path(self.allowed_dirs[0]) if self.allowed_dirs else Path(os.getcwd())
            )
            absolute_scan_dir = Path(os.path.abspath(directory_to_scan))
            if not absolute_scan_dir.is_dir():
                return OperationResult(
                    success=False,
                    error=f"Scan directory '{directory_to_scan}' does not exist or is not a directory.",
                    duration=time.time() - start_time,
                    operation_type="scan_codebase_for_issues",
                )
        except IndexError:
            return OperationResult(
                success=False,
                error="ExecutionEngine has no allowed_dirs configured, cannot determine base path for relative paths.",
                duration=time.time() - start_time,
                operation_type="scan_codebase_for_issues",
            )

        for pattern in file_patterns:
            for filepath_obj in absolute_scan_dir.rglob(pattern):
                filepath_str = str(filepath_obj)
                if not filepath_obj.is_file() or not self._validate_path_access(
                    filepath_str
                ):
                    continue

                try:
                    with open(filepath_obj, encoding="utf-8") as file:
                        content = file.read()

                    if "missing_docstring" in rules:
                        try:
                            tree = ast.parse(content, filename=filepath_str)
                            for node in ast.walk(tree):
                                if isinstance(node, ast.FunctionDef):
                                    # ast.get_docstring is preferred for robustness (Python 3.8+)
                                    docstring = ast.get_docstring(node, clean=False)
                                    if docstring is None:
                                        issues_found.append(
                                            {
                                                "file_path": filepath_str,
                                                "relative_path": str(
                                                    filepath_obj.relative_to(
                                                        project_base_path
                                                    )
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
                                    "relative_path": str(
                                        filepath_obj.relative_to(project_base_path)
                                    ),
                                    "function_name": None,  # No function context if syntax error at file level
                                    "line_number": e.lineno,
                                    "issue_type": "syntax_error",
                                    "message": f"Syntax error: {e.msg}",
                                }
                            )
                        except Exception as e:  # Catch other AST processing errors
                            logger.error(
                                f"Error processing {filepath_str} for missing docstrings: {e}"
                            )
                except (UnicodeDecodeError, PermissionError, OSError) as e:
                    logger.warning(
                        f"Could not read or process file {filepath_str}: {e}"
                    )
                    continue

        self._log_operation(
            "scan_codebase_for_issues",
            {
                "directory": directory_to_scan,
                "rules": rules,
                "issues_found_count": len(issues_found),
            },
        )

        return OperationResult(
            success=True,
            data=issues_found,
            duration=time.time() - start_time,
            operation_type="scan_codebase_for_issues",
        )

    async def apply_patch(
        self, filepath: str, patch_content: str, target_commit: str = "HEAD"
    ) -> OperationResult:
        """Apply a patch to a file and commit the change.

        Args:
            filepath: The path to the file to patch
            patch_content: The content of the patch to apply
            target_commit: The commit hash or reference to amend (default: HEAD)

        Returns:
            OperationResult indicating success or failure
        """
        start = time.time()
        try:
            if not self._validate_path_access(filepath):
                return OperationResult(
                    success=False,
                    error="Access denied: outside allowed directories.",
                    duration=time.time() - start,
                    operation_type="apply_patch",
                )

            # Write the patch to a temporary file
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(patch_content)

            # Commit the change
            commit_message = f"Apply patch to {os.path.basename(filepath)}"
            result = await self.execute_shell_command(
                f"git add {filepath} && git commit -m '{commit_message}'",
                working_dir=os.path.dirname(filepath),
            )

            if not result.success:
                return OperationResult(
                    success=False,
                    error=f"Git commit failed: {result.error}",
                    duration=time.time() - start,
                    operation_type="apply_patch",
                )

            self._log_operation(
                "apply_patch",
                {"file": filepath, "patch_size": len(patch_content)},
            )

            return OperationResult(
                success=True,
                duration=time.time() - start,
                operation_type="apply_patch",
            )

        except Exception as e:
            logger.error(f"Error applying patch to file {filepath}: {str(e)}")
            return OperationResult(
                success=False,
                error=str(e),
                duration=time.time() - start,
                operation_type="apply_patch",
            )

    async def run_tests(  # Corrected default argument and added missing parameters
        self,
        file_paths: list[str] | None = None,
        specific_test: str | None = None,
        verbose: bool = False,
    ) -> OperationResult:
        """Run tests using the specified test command.

        Args:
            test_command: The command to run tests (e.g., 'pytest', 'unittest')

        Returns:
            OperationResult with test results or error
        """
        start = time.time()
        try:
            cmd_parts = ["pytest"]  # Default to pytest

            if file_paths:
                cmd_parts.extend(file_paths)  # Corrected variable name

            if specific_test:
                cmd_parts.append(specific_test)  # Corrected variable name

            if verbose:
                cmd_parts.append("--verbose")

            result = await self.execute_shell_command(
                " ".join(cmd_parts)
            )  # Log test results
            self._log_operation(
                "run_tests",
                {
                    "command": " ".join(cmd_parts),
                    "return_code": result.returncode,
                },
            )

            return OperationResult(
                success=result.success,
                data=result.data,
                error=result.error,
                duration=time.time() - start,
                operation_type="run_tests",
            )

        except Exception as e:
            logger.error(f"Error running tests: {str(e)}")
            return OperationResult(
                success=False,
                error=str(e),
                duration=time.time() - start,
                operation_type="run_tests",
            )

    # ========== END GENESIS PROTOCOL: ADVANCED DEVELOPMENT TOOLS ==========

    async def _scan_file_for_issues(
        self, filepath: Path, issue_type: str, findings: list[dict]
    ) -> None:
        """Scan a single Python file for specific issues."""
        try:
            content = await self.read_file(str(filepath))
            if not content.success:
                findings.append(
                    {
                        "file": str(filepath),
                        "error": f"Could not read file: {content.error}",
                        "issue_type": "read_error",
                    }
                )
                return

            tree = ast.parse(content.data)

            if issue_type == "missing_docstrings":
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                        # Skip private functions (start with _)
                        if node.name.startswith("_"):
                            continue

                        if not ast.get_docstring(node):
                            # Calculate relative path for cleaner reporting
                            try:
                                relative_path = filepath.relative_to(
                                    self.allowed_dirs[0]
                                )
                            except (ValueError, IndexError):
                                relative_path = filepath

                            findings.append(
                                {
                                    "file": str(filepath),
                                    "relative_path": str(relative_path),
                                    "function_name": node.name,
                                    "line_number": node.lineno,
                                    "issue_type": "missing_docstring",
                                    "severity": "medium",
                                    "description": f"Function '{node.name}' at line {node.lineno} is missing a docstring",
                                    "suggested_fix": f"Add a comprehensive docstring to the '{node.name}' function explaining its purpose, parameters, and return value",
                                }
                            )

        except SyntaxError as e:
            findings.append(
                {
                    "file": str(filepath),
                    "error": f"Syntax error: {e.msg}",
                    "line_number": e.lineno if e.lineno else 0,
                    "issue_type": "syntax_error",
                }
            )
        except Exception as e:
            findings.append(
                {
                    "file": str(filepath),
                    "error": f"Error parsing file: {str(e)}",
                    "issue_type": "parse_error",
                }
            )
            logger.error(f"Error scanning file {filepath}: {str(e)}")

    def get_operation_stats(self) -> dict:
        """Get statistics about operations performed by this execution engine."""
        total_operations = len(self._command_history)
        if total_operations == 0:
            return {"total_operations": 0}

        operation_types = {}
        errors = 0
        total_duration = 0

        for op in self._command_history:
            op_type = op.get("operation", "unknown")
            operation_types[op_type] = operation_types.get(op_type, 0) + 1

            if op.get("error"):
                errors += 1
            total_duration += op.get("duration", 0)

        return {
            "total_operations": total_operations,
            "operation_types": operation_types,
            "error_count": errors,
            "total_runtime": time.time() - self._start_time,
            "total_operation_time": total_duration,
            "success_rate": (total_operations - errors) / total_operations
            if total_operations > 0
            else 0,
        }

    async def execute_action(self, action_type: str, parameters: dict):
        """Execute an action based on the Genesis protocol.

        Args:
            action_type: The type of action to execute
            parameters: A dictionary of parameters for the action

        Returns:
            OperationResult of the executed action
        """
        if action_type == "SEARCH_CODEBASE":
            query = parameters.get("query", "")
            file_patterns = parameters.get("file_patterns", None)
            max_results = parameters.get("max_results", 50)
            return await self.search_codebase(query, file_patterns, max_results)
        elif action_type == "SCAN_CODEBASE_FOR_ISSUES":
            directory = parameters.get("directory", ".")
            rules = parameters.get("rules", [])
            file_patterns = parameters.get("file_patterns", None)
            return await self.scan_codebase_for_issues(directory, rules, file_patterns)
        elif action_type == "APPLY_PATCH":
            filepath = parameters.get("filepath", "")
            patch_content = parameters.get("patch_content", "")
            target_commit = parameters.get("target_commit", "HEAD")
            return await self.apply_patch(filepath, patch_content, target_commit)
        elif action_type == "RUN_TESTS":
            file_paths = parameters.get("file_paths", None)
            specific_test = parameters.get("specific_test", None)
            verbose = parameters.get("verbose", False)
            return await self.run_tests(file_paths, specific_test, verbose)
        else:
            return OperationResult(
                success=False,
                error=f"Unknown action type: {action_type}",
                operation_type="unknown_action",
            )
