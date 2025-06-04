#!/usr/bin/env python
"""
Clean up all cached files and directories in the project.
"""

import shutil
import sys
from pathlib import Path


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


def cleanup_cached_files():
    """Clean up cached files and directories."""
    project_root = Path(__file__).parent.parent

    # Directories to remove
    cache_dirs = [
        "**/__pycache__",
        "**/.pytest_cache",
        "**/.mypy_cache",
        "**/.ruff_cache",
        "**/.qodo",
        "**/.cacheme",
        "build",
        "dist",
        "**/*.egg-info",
        "coverage_html",
        "htmlcov",
        "test_outputs",
        "test-results",
    ]

    # Files to remove
    cache_files = [
        "**/*.pyc",
        "**/*.pyo",
        "**/*.pyd",
        "**/*.so",
        "**/*.coverage",
        "coverage.xml",
        ".coverage*",
    ]

    dirs_removed = 0
    files_removed = 0

    # Remove directories
    color_print("Removing cached directories:", "blue")
    for pattern in cache_dirs:
        for path in project_root.glob(pattern):
            if path.is_dir():
                rel_path = path.relative_to(project_root)
                try:
                    shutil.rmtree(path)
                    print(f"  - Removed: {rel_path}")
                    dirs_removed += 1
                except Exception as e:
                    print(f"  - Failed to remove {rel_path}: {str(e)}")

    # Remove files
    color_print("\nRemoving cached files:", "blue")
    for pattern in cache_files:
        for path in project_root.glob(pattern):
            if path.is_file():
                rel_path = path.relative_to(project_root)
                try:
                    path.unlink()
                    print(f"  - Removed: {rel_path}")
                    files_removed += 1
                except Exception as e:
                    print(f"  - Failed to remove {rel_path}: {str(e)}")

    color_print(
        f"\nCleanup complete! Removed {dirs_removed} directories and {files_removed} files.",
        "green",
    )


def main():
    """Run the cleanup script."""
    color_print("🧹 Cleaning up cached files and directories...", "blue")

    # Confirm before proceeding
    confirm = input(
        "This will remove all cached files and directories. Continue? (y/n): "
    )
    if confirm.lower() != "y":
        color_print("Cleanup cancelled.", "yellow")
        return 1

    cleanup_cached_files()
    return 0


if __name__ == "__main__":
    sys.exit(main())
