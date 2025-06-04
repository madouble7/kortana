#!/usr/bin/env python
"""
Run all test suites for Project Kor'tana.

This script runs all test suites (unit, integration, e2e) and reports the results.
"""

import os
import subprocess
import sys
import time
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


def run_pytest(test_path, options=None):
    """Run pytest with the given options."""
    project_root = Path(__file__).parent.parent

    if options is None:
        options = []

    cmd = [sys.executable, "-m", "pytest"] + options + [test_path]

    color_print(f"Running: {' '.join(cmd)}", "blue")

    start_time = time.time()
    result = subprocess.run(
        cmd, cwd=project_root, env=dict(os.environ, PYTHONPATH=str(project_root))
    )
    elapsed = time.time() - start_time

    return result.returncode == 0, elapsed


def run_frontend_tests():
    """Run frontend tests if applicable."""
    project_root = Path(__file__).parent.parent
    frontend_dir = project_root / "frontend"

    # Skip if no frontend directory
    if not frontend_dir.exists():
        color_print("No frontend directory found, skipping frontend tests", "yellow")
        return True, 0

    # Check if package.json exists
    package_json = frontend_dir / "package.json"
    if not package_json.exists():
        color_print(
            "No package.json found in frontend directory, skipping frontend tests",
            "yellow",
        )
        return True, 0

    # Check for test script in package.json
    try:
        import json

        with open(package_json, "r") as f:
            data = json.load(f)

        if "scripts" not in data or "test" not in data["scripts"]:
            color_print(
                "No test script found in package.json, skipping frontend tests",
                "yellow",
            )
            return True, 0

        # Run frontend tests
        color_print("Running frontend tests...", "blue")
        start_time = time.time()
        result = subprocess.run(["npm", "test"], cwd=frontend_dir)
        elapsed = time.time() - start_time

        return result.returncode == 0, elapsed
    except Exception as e:
        color_print(f"Error checking/running frontend tests: {str(e)}", "red")
        return False, 0


def run_e2e_tests():
    """Run end-to-end tests if applicable."""
    project_root = Path(__file__).parent.parent
    e2e_dir = project_root / "tests" / "e2e"

    # Skip if no e2e directory
    if not e2e_dir.exists():
        color_print("No e2e test directory found, skipping e2e tests", "yellow")
        return True, 0

    # Check for e2e test framework
    if (e2e_dir / "playwright.config.js").exists() or (
        e2e_dir / "playwright.config.ts"
    ).exists():
        # Run Playwright tests
        color_print("Running Playwright e2e tests...", "blue")
        start_time = time.time()
        result = subprocess.run(
            ["npx", "playwright", "test"],
            cwd=e2e_dir if e2e_dir.exists() else project_root,
        )
        elapsed = time.time() - start_time

        return result.returncode == 0, elapsed
    elif (e2e_dir / "cypress.json").exists() or (
        e2e_dir / "cypress.config.js"
    ).exists():
        # Run Cypress tests
        color_print("Running Cypress e2e tests...", "blue")
        start_time = time.time()
        result = subprocess.run(
            ["npx", "cypress", "run"], cwd=e2e_dir if e2e_dir.exists() else project_root
        )
        elapsed = time.time() - start_time

        return result.returncode == 0, elapsed
    else:
        # Check for Python e2e tests
        if list(e2e_dir.glob("**/test_*.py")):
            return run_pytest("tests/e2e", ["--e2e"])

        color_print("No e2e test framework detected, skipping e2e tests", "yellow")
        return True, 0


def main():
    """Run all test suites and report results."""
    color_print("🧪 Running All Test Suites for Kor'tana 🧪", "blue")
    print("===========================================")

    results = []

    # Run unit tests
    color_print("\n📋 Running Unit Tests", "blue")
    unit_success, unit_time = run_pytest(
        "tests/unit", ["--cov=src", "--cov-report=term-missing"]
    )
    results.append(("Unit Tests", unit_success, unit_time))

    # Run integration tests
    color_print("\n📋 Running Integration Tests", "blue")
    integration_success, integration_time = run_pytest("tests/integration")
    results.append(("Integration Tests", integration_success, integration_time))

    # Run e2e tests
    color_print("\n📋 Running End-to-End Tests", "blue")
    e2e_success, e2e_time = run_e2e_tests()
    results.append(("E2E Tests", e2e_success, e2e_time))

    # Run frontend tests
    color_print("\n📋 Running Frontend Tests", "blue")
    frontend_success, frontend_time = run_frontend_tests()
    results.append(("Frontend Tests", frontend_success, frontend_time))

    # Print summary
    color_print("\n===========================================", "blue")
    color_print("Test Results Summary:", "blue")

    all_success = True
    for name, success, elapsed in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        status_color = "green" if success else "red"

        if elapsed > 0:
            color_print(f"{name}: {status} ({elapsed:.2f}s)", status_color)
        else:
            color_print(f"{name}: {status}", status_color)

        all_success = all_success and success

    print("\n===========================================")
    if all_success:
        color_print("✅ All tests passed!", "green")
    else:
        color_print("❌ Some tests failed!", "red")

    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())
