#!/usr/bin/env python
"""
Check for sensitive files tracked in git.

This script checks for sensitive files like .env, database files,
cache directories, etc. that might be tracked in git.
"""

import subprocess
import sys


def color_print(message, color="green"):
    """Print colored messages to the console."""
    colors = {
        "reset": "\033[0m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "blue": "\033[94m",
    }
    print(f"{colors.get(color, '')}{message}{colors['reset']}")


def get_tracked_files():
    """Get a list of files tracked in git."""
    try:
        result = subprocess.run(
            ["git", "ls-files"], capture_output=True, text=True, check=True
        )
        return result.stdout.splitlines()
    except subprocess.CalledProcessError as e:
        color_print(f"Error running git ls-files: {str(e)}", "red")
        return []
    except FileNotFoundError:
        color_print("Git command not found. Is git installed?", "red")
        return []


def check_sensitive_files(tracked_files):
    """Check for sensitive files in the tracked files list."""
    # Patterns to look for
    patterns = {
        "Environment files": [".env"],
        "Database files": [".db", ".sqlite", ".sqlite3"],
        "Cache directories": [
            "__pycache__",
            ".ruff_cache",
            ".mypy_cache",
            ".pytest_cache",
        ],
        "Virtual environment": ["venv", ".venv", "venv311"],
        "Logs": [".log", "logs/"],
        "Lock files (acceptable)": ["poetry.lock", "package-lock.json", "yarn.lock"],
    }

    # Allowed patterns
    allowed = [".env.example", ".env.template"]

    # Check each tracked file against the patterns
    findings = {}
    for category, patterns_list in patterns.items():
        for pattern in patterns_list:
            matched_files = [file for file in tracked_files if pattern in file.lower()]

            # Filter out allowed files
            if not category.endswith("(acceptable)"):
                matched_files = [
                    file
                    for file in matched_files
                    if not any(allowed_pattern in file for allowed_pattern in allowed)
                ]

            if matched_files:
                if category not in findings:
                    findings[category] = []
                findings[category].extend(matched_files)

    return findings


def main():
    """Run the check for sensitive tracked files."""
    color_print("🔍 Checking for Sensitive Files Tracked in Git", "blue")
    print("===========================================")

    # Get tracked files
    tracked_files = get_tracked_files()
    if not tracked_files:
        color_print("No tracked files found or error running git command", "yellow")
        return 1

    # Check for sensitive files
    findings = check_sensitive_files(tracked_files)

    # Print results
    if not findings:
        color_print("✅ No sensitive files found in git tracking!", "green")
        return 0

    # Print findings
    color_print("⚠️ Found potentially sensitive files tracked in git:", "yellow")

    has_critical = False
    for category, files in findings.items():
        is_critical = not category.endswith("(acceptable)")

        if is_critical:
            has_critical = True
            color_print(f"\n{category}:", "red")
        else:
            color_print(f"\n{category}:", "yellow")

        for file in sorted(files):
            if is_critical:
                print(f"  ❌ {file}")
            else:
                print(f"  ⚠️ {file}")

    if has_critical:
        color_print("\n❌ Critical issues found! Use this to remove them:", "red")
        print("\ngit rm --cached <file>  # To remove from tracking but keep locally")
        return 1
    else:
        color_print(
            "\n⚠️ Only non-critical files found. These are typically acceptable.",
            "yellow",
        )
        return 0


if __name__ == "__main__":
    sys.exit(main())
