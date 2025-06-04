#!/usr/bin/env python
"""
Verify the repository is ready for release.

This script runs all the verification checks to ensure the repository
is ready for release or audit.
"""

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


def run_script(script_name, description=None):
    """Run a Python script from the scripts directory."""
    script_path = Path(__file__).parent / f"{script_name}.py"
    if not script_path.exists():
        color_print(f"❌ Script not found: {script_name}.py", "red")
        return False

    if description:
        color_print(f"\n🔍 {description}", "blue")
        print("=" * (len(description) + 4))

    project_root = Path(__file__).parent.parent
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=project_root,
        env=dict(os.environ, PYTHONPATH=str(project_root)),
    )

    return result.returncode == 0


def check_git_status():
    """Check if there are uncommitted changes."""
    color_print("\n🔍 Checking git status", "blue")
    print("====================")

    try:
        result = subprocess.run(
            ["git", "status", "--short"], capture_output=True, text=True
        )

        if result.stdout.strip():
            color_print("⚠️ You have uncommitted changes:", "yellow")
            print(result.stdout)
            return False
        else:
            color_print("✅ Working directory clean", "green")
            return True
    except Exception as e:
        color_print(f"❌ Error checking git status: {str(e)}", "red")
        return False


def verify_env_files():
    """Verify that only .env.example and .env.template are tracked."""
    color_print("\n🔍 Verifying environment files", "blue")
    print("============================")

    try:
        # Check if .env exists but is not tracked
        result = subprocess.run(
            ["git", "ls-files", ".env"], capture_output=True, text=True
        )

        if result.stdout.strip():
            color_print("❌ .env file should not be tracked in git!", "red")
            return False

        # Check if .env.example and .env.template exist
        project_root = Path(__file__).parent.parent
        env_example = project_root / ".env.example"
        env_template = project_root / ".env.template"

        if not env_example.exists() and not env_template.exists():
            color_print("❌ Neither .env.example nor .env.template found!", "red")
            return False

        # Check if they are tracked
        result = subprocess.run(
            ["git", "ls-files", ".env.example", ".env.template"],
            capture_output=True,
            text=True,
        )

        tracked = result.stdout.strip().split("\n")
        if not tracked or tracked == [""]:
            color_print("❌ .env.example or .env.template should be tracked!", "red")
            return False

        color_print("✅ Environment file configuration is correct", "green")
        return True
    except Exception as e:
        color_print(f"❌ Error verifying environment files: {str(e)}", "red")
        return False


def check_readme_completeness():
    """Check that README.md contains required sections."""
    color_print("\n🔍 Checking README.md completeness", "blue")
    print("==============================")

    project_root = Path(__file__).parent.parent
    readme_path = project_root / "README.md"

    if not readme_path.exists():
        color_print("❌ README.md not found!", "red")
        return False

    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read().lower()

        required_sections = [
            "setup",
            "environment",
            "configuration",
            "development",
            "test",
        ]

        missing = []
        for section in required_sections:
            if section not in content:
                missing.append(section)

        if missing:
            color_print(
                f"❌ README.md is missing these sections: {', '.join(missing)}", "red"
            )
            return False

        color_print("✅ README.md contains all required sections", "green")
        return True
    except Exception as e:
        color_print(f"❌ Error checking README.md: {str(e)}", "red")
        return False


def verify_cli_entry_points():
    """Verify CLI entry points are correctly defined in setup.py."""
    color_print("\n🔍 Verifying CLI entry points", "blue")
    print("=========================")

    project_root = Path(__file__).parent.parent
    setup_py = project_root / "setup.py"

    if not setup_py.exists():
        color_print("❌ setup.py not found!", "red")
        return False

    try:
        with open(setup_py, "r", encoding="utf-8") as f:
            content = f.read()

        entry_points = ["kortana-api", "kortana-dashboard", "kortana-autonomous"]
        missing = []

        for entry in entry_points:
            if entry not in content:
                missing.append(entry)

        if missing:
            color_print(
                f"❌ Missing CLI entry points in setup.py: {', '.join(missing)}", "red"
            )
            return False

        color_print("✅ CLI entry points correctly defined in setup.py", "green")
        return True
    except Exception as e:
        color_print(f"❌ Error checking setup.py: {str(e)}", "red")
        return False


def main():
    """Run all repository verification checks."""
    color_print("🔍 Verifying Kor'tana Repository for Release", "blue")
    print("=========================================")

    results = []

    # Check for tracked sensitive files
    results.append(
        run_script("check_tracked_files", "Checking for tracked sensitive files")
    )

    # Check git status
    results.append(check_git_status())

    # Verify environment files
    results.append(verify_env_files())

    # Smoke test to verify imports and functionality
    results.append(run_script("smoke_test", "Running smoke tests"))

    # Run configuration verification
    results.append(
        run_script("verify_config_pipeline", "Verifying configuration pipeline")
    )

    # Verify CLI entry points
    results.append(verify_cli_entry_points())

    # Check README.md completeness
    results.append(check_readme_completeness())

    # Print summary
    color_print("\n=========================================", "blue")
    color_print("Repository Verification Summary:", "blue")

    success_count = results.count(True)
    total_checks = len(results)

    if all(results):
        color_print(f"✅ All {success_count}/{total_checks} checks passed!", "green")
        color_print("\nYour repository is ready for release!", "green")
        color_print("\nNext steps:", "blue")
        color_print("1. Commit any remaining changes", "blue")
        color_print("2. Push to main branch", "blue")
        color_print("3. Tag the release: python scripts/tag_release.py --push", "blue")
        return 0
    else:
        color_print(
            f"❌ {total_checks - success_count} of {total_checks} checks failed", "red"
        )
        color_print("\nPlease fix the issues before release.", "red")
        return 1


if __name__ == "__main__":
    sys.exit(main())
