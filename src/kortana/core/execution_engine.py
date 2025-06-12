"""
Kor'tana's Execution Engine
Provides safe, controlled interaction with the file system and shell commands.
This is the bridge between Kor'tana's intelligence and the real world.
"""

import logging
import os
import subprocess
import json
from dataclasses import dataclass
from typing import List, Dict, Optional, Any, Union
from pathlib import Path
import asyncio
import time

logger = logging.getLogger(__name__)

@dataclass 
class OperationResult:
    """Result of an execution engine operation"""
    success: bool
    data: Optional[Any] = None 
    error: Optional[str] = None
    duration: float = 0
    operation_type: str = ""

class ExecutionEngine:
    """
    Safe execution engine with built-in security controls.
    Enables Kor'tana to interact with her environment while maintaining safety.
    """

    def __init__(self, allowed_dirs: List[str], blocked_commands: List[str]):
        """Initialize the execution engine with safety controls

        Args:
            allowed_dirs: List of directory paths that the engine can access
            blocked_commands: List of shell commands that are forbidden
        """
        self.allowed_dirs = [os.path.abspath(d) for d in allowed_dirs]
        self.blocked_commands = blocked_commands
        self._command_history: List[Dict] = []
        self._start_time = time.time()

    def _validate_path_access(self, filepath: Union[str, Path]) -> bool:
        """Check if a file path is within allowed directories"""
        abs_path = os.path.abspath(str(filepath))
        return any(abs_path.startswith(d) for d in self.allowed_dirs)

    def _validate_command(self, command: str) -> bool:
        """Check if a shell command is allowed"""
        cmd = command.strip().split()[0].lower()
        return not any(blocked in cmd for blocked in self.blocked_commands)

    def _log_operation(self, operation: str, details: Dict) -> None:
        """Log an operation to history"""
        timestamp = time.time()
        self._command_history.append({
            "operation": operation,
            "timestamp": timestamp,
            "runtime": timestamp - self._start_time,
            **details
        })

    async def read_file(self, filepath: str) -> OperationResult:
        """Safely read a file from allowed directories."""
        start = time.time()
        try:
            if not self._validate_path_access(filepath):
                return OperationResult(
                    success=False,
                    error="Access denied: outside allowed directories.",
                    duration=time.time() - start,
                    operation_type="read_file"
                )

            async with asyncio.Lock():
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

            self._log_operation("read_file", {
                "file": filepath,
                "size": len(content)
            })

            return OperationResult(
                success=True,
                data=content,
                duration=time.time() - start,
                operation_type="read_file"
            )

        except Exception as e:
            logger.error(f"Error reading file {filepath}: {str(e)}")
            return OperationResult(
                success=False,
                error=str(e),
                duration=time.time() - start,
                operation_type="read_file"
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
                    operation_type="write_file"
                )

            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            async with asyncio.Lock():
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)

            self._log_operation("write_file", {
                "file": filepath,
                "size": len(content)
            })

            return OperationResult(
                success=True,
                duration=time.time() - start,
                operation_type="write_file"
            )

        except Exception as e:
            logger.error(f"Error writing to file {filepath}: {str(e)}")
            return OperationResult(
                success=False,
                error=str(e),
                duration=time.time() - start,
                operation_type="write_file"
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
                    operation_type="shell_command"
                )

            if working_dir and not self._validate_path_access(working_dir):
                return OperationResult(
                    success=False, 
                    error=f"Working directory '{working_dir}' is outside allowed paths.",
                    duration=time.time() - start,
                    operation_type="shell_command"
                )

            work_dir = working_dir if working_dir else os.getcwd()
            
            # Run command with timeout
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=work_dir
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                try:
                    process.kill()
                except:
                    pass
                return OperationResult(
                    success=False,
                    error=f"Command timed out after {timeout} seconds",
                    duration=time.time() - start,
                    operation_type="shell_command"
                )

            self._log_operation("shell_command", {
                "command": command,
                "working_dir": work_dir,
                "return_code": process.returncode
            })

            if process.returncode != 0:
                return OperationResult(
                    success=False,
                    error=f"Command failed: {stderr.decode()}",
                    data={
                        "stdout": stdout.decode(),
                        "stderr": stderr.decode(),
                        "return_code": process.returncode
                    },
                    duration=time.time() - start,
                    operation_type="shell_command"
                )

            return OperationResult(
                success=True,
                data={
                    "stdout": stdout.decode(),
                    "stderr": stderr.decode(),
                    "return_code": process.returncode
                },
                duration=time.time() - start,
                operation_type="shell_command"
            )

        except Exception as e:
            logger.error(f"Error executing command '{command}': {str(e)}")
            return OperationResult(
                success=False,
                error=str(e),
                duration=time.time() - start,
                operation_type="shell_command"
            )

    def get_operation_history(self) -> List[Dict]:
        """Get the complete operation history"""
        return self._command_history

    def clear_history(self) -> None:
        """Clear the operation history"""
        self._command_history = []
        self._start_time = time.time()

    def export_metrics(self) -> Dict[str, Any]:
        """Export execution engine metrics"""
        total_operations = len(self._command_history)
        operation_types = {}
        errors = 0
        total_duration = 0

        for op in self._command_history:
            op_type = op["operation"]
            operation_types[op_type] = operation_types.get(op_type, 0) + 1
            if "error" in op:
                errors += 1
            if "duration" in op:
                total_duration += op["duration"]

        return {
            "total_operations": total_operations,
            "operation_types": operation_types, 
            "error_count": errors,
            "total_runtime": time.time() - self._start_time,
            "total_operation_time": total_duration,
            "success_rate": (total_operations - errors) / total_operations if total_operations > 0 else 0
        }
