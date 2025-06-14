"""
Module: ade_tools.py
Tools and utilities for Autonomous Development Engine (ADE) operations.
"""

import os
import subprocess
from typing import Any


def read_file(file_path: str) -> str:
    """
    Read the contents of a file and return as a string.
    Args:
        file_path: Path to the file to read.
    Returns:
        The file contents as a string.
    """
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def write_file(file_path: str, content: str) -> str:
    """
    Write content to a file, overwriting if it exists.
    Args:
        file_path: Path to the file to write.
        content: The content to write to the file.
    Returns:
        Success or error message.
    """
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing to {file_path}: {e}"


def list_directory(path: str) -> list[str]:
    """
    List all files and directories at the given path.
    Args:
        path: Directory path to list.
    Returns:
        List of file and directory names.
    """
    return os.listdir(path)


def execute_python_script(
    script_path: str, args: list[str] | None = None
) -> dict[str, Any]:
    """
    Execute a Python script and capture its output and errors.
    Args:
        script_path: Path to the Python script.
        args: List of arguments to pass to the script.
    Returns:
        Dictionary with 'stdout', 'stderr', and 'returncode'.
    """
    if args is None:
        args = []
    result = subprocess.run(
        ["python", script_path, *args], capture_output=True, text=True
    )
    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
    }


def run_pytest(target: str = ".") -> dict[str, Any]:
    """
    Run pytest on the given target and return structured results.
    Args:
        target: Directory or file to test (default: current directory).
    Returns:
        Dictionary with 'success', 'output', and 'errors'.
    """
    result = subprocess.run(
        ["pytest", target, "--maxfail=1", "--disable-warnings", "-q"],
        capture_output=True,
        text=True,
    )
    return {
        "success": result.returncode == 0,
        "output": result.stdout,
        "errors": result.stderr,
    }
