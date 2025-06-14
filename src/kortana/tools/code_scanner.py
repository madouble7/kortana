"""
Code Scanner Tool for Kor'tana: Detects Python functions missing docstrings.
"""

import ast
import os


def scan_python_file_for_missing_docstrings(
    filepath: str,
) -> list[tuple[str, str, int]]:
    """
    Scans a Python file for functions missing docstrings.
    Returns a list of (function_name, filepath, line_number).
    """
    results = []
    with open(filepath, encoding="utf-8") as f:
        source = f.read()
    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError:
        return results  # skip files with syntax errors
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if ast.get_docstring(node) is None:
                results.append((node.name, filepath, node.lineno))
    return results


def scan_codebase_for_missing_docstrings(root_dir: str) -> list[tuple[str, str, int]]:
    """
    Recursively scans all .py files in root_dir for functions missing docstrings.
    Returns a list of (function_name, filepath, line_number).
    """
    missing = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(".py"):
                filepath = os.path.join(dirpath, filename)
                missing.extend(scan_python_file_for_missing_docstrings(filepath))
    return missing
