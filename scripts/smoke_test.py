#!/usr/bin/env python
"""
Smoke test for Project Kor'tana.

This script verifies that the basic imports and functionality
work correctly after the repository restructuring.
"""

import importlib
import os
import subprocess
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


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


def check_import(module_name):
    """Try to import a module and return success status."""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError as e:
        color_print(f"Failed to import {module_name}: {str(e)}", "red")
        return False


def run_cli_help(command):
    """Run the CLI command with --help flag."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", command, "--help"],
            capture_output=True,
            text=True,
            env=dict(os.environ, PYTHONPATH=str(Path(__file__).parent.parent)),
        )
        if result.returncode != 0:
            color_print(f"CLI command {command} --help failed:", "red")
            print(result.stderr)
            return False
        else:
            return True
    except Exception as e:
        color_print(f"Error running {command} --help: {str(e)}", "red")
        return False


def test_editable_install():
    """Test pip install -e . works."""
    project_root = Path(__file__).parent.parent
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", "."],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            color_print("Failed to install package in editable mode:", "red")
            print(result.stderr)
            return False
        else:
            color_print("✅ Package installed in editable mode", "green")
            return True
    except Exception as e:
        color_print(f"Error installing package: {str(e)}", "red")
        return False


def main():
    """Run the smoke tests."""
    color_print("🔥 Running Kor'tana Smoke Tests 🔥", "blue")
    print("=====================================")

    # Test basic imports
    color_print("\nTesting basic imports:", "blue")
    imports = [
        "config",
        "kortana",
        "kortana.core",
        "kortana.memory",
        "kortana.agents",
        "kortana.cli",
    ]

    import_results = []
    for module in imports:
        if check_import(module):
            color_print(f"✅ Successfully imported {module}", "green")
            import_results.append(True)
        else:
            import_results.append(False)

    # Test CLI modules
    color_print("\nTesting CLI modules:", "blue")
    cli_modules = [
        "kortana.cli.api",
        "kortana.cli.dashboard",
        "kortana.cli.autonomous",
    ]

    cli_results = []
    for module in cli_modules:
        if run_cli_help(module):
            color_print(f"✅ Successfully ran {module} --help", "green")
            cli_results.append(True)
        else:
            cli_results.append(False)

    # Test editable install (if not already done)
    color_print("\nTesting editable install:", "blue")
    install_result = test_editable_install()

    # Summary
    print("\n=====================================")
    import_success = all(import_results)
    cli_success = all(cli_results)

    if import_success and cli_success and install_result:
        color_print("✅ All smoke tests passed!", "green")
        return 0
    else:
        color_print("❌ Some smoke tests failed!", "red")
        return 1


if __name__ == "__main__":
    sys.exit(main())
