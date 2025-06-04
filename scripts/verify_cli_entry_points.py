#!/usr/bin/env python
"""
Verify CLI entry points for Project Kor'tana.
This script checks that all CLI entry points are properly configured.
"""

import os
import subprocess
import sys
from pathlib import Path

import pkg_resources

# Add the project root to Python path
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


def check_entry_points_in_setup():
    """Check that all entry points are properly configured in setup.py."""
    color_print("\n🔍 Checking entry points in setup.py", "blue")

    project_root = Path(__file__).parent.parent
    setup_py = project_root / "setup.py"

    if not setup_py.exists():
        color_print(f"❌ setup.py not found: {setup_py}", "red")
        return False

    try:
        content = setup_py.read_text(encoding="utf-8")

        # Check for console_scripts section
        if "console_scripts" not in content:
            color_print("❌ No console_scripts section found in setup.py", "red")
            return False

        # Check for necessary entry points
        required_entry_points = {
            "kortana-api": "kortana.cli.api:main",
            "kortana-dashboard": "kortana.cli.dashboard:main",
            "kortana-autonomous": "kortana.cli.autonomous:main",
        }

        missing_entry_points = []
        for name, target in required_entry_points.items():
            if name not in content or target not in content:
                missing_entry_points.append(f"{name} -> {target}")

        if missing_entry_points:
            color_print("❌ Missing entry points in setup.py:", "red")
            for entry_point in missing_entry_points:
                print(f"   - {entry_point}")
            return False
        else:
            color_print("✅ All required entry points found in setup.py")
            return True
    except Exception as e:
        color_print(f"❌ Error checking setup.py: {str(e)}", "red")
        return False


def check_cli_module_structure():
    """Check that the CLI module structure is correct."""
    color_print("\n🔍 Checking CLI module structure", "blue")

    project_root = Path(__file__).parent.parent
    cli_dir = project_root / "src" / "kortana" / "cli"

    if not cli_dir.exists() or not cli_dir.is_dir():
        color_print(f"❌ CLI directory not found: {cli_dir}", "red")
        return False

    # Check for necessary CLI modules
    required_modules = ["__init__.py", "api.py", "dashboard.py", "autonomous.py"]

    missing_modules = []
    for module in required_modules:
        if not (cli_dir / module).exists():
            missing_modules.append(module)

    if missing_modules:
        color_print("❌ Missing CLI modules:", "red")
        for module in missing_modules:
            print(f"   - {module}")
        return False
    else:
        color_print("✅ All required CLI modules found")
        return True


def check_cli_imports():
    """Check that the CLI modules import correctly."""
    color_print("\n🔍 Checking CLI module imports", "blue")

    project_root = Path(__file__).parent.parent
    cli_dir = project_root / "src" / "kortana" / "cli"

    if not cli_dir.exists():
        color_print(f"❌ CLI directory not found: {cli_dir}", "red")
        return False

    # Check the imports in each CLI module
    errors = []

    for module_path in cli_dir.glob("*.py"):
        if module_path.name == "__init__.py":
            continue

        module_name = module_path.stem
        try:
            # Use subprocess to avoid affecting the current process
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    f"from kortana.cli import {module_name}; print('OK')",
                ],
                capture_output=True,
                text=True,
                cwd=project_root,
                env=dict(os.environ, PYTHONPATH=str(project_root)),
            )

            if result.returncode != 0:
                errors.append((module_name, result.stderr.strip()))
        except Exception as e:
            errors.append((module_name, str(e)))

    if errors:
        color_print("❌ Found errors in CLI module imports:", "red")
        for module, error in errors:
            print(f"   - {module}: {error}")
        return False
    else:
        color_print("✅ All CLI modules import correctly")
        return True


def check_installed_entry_points():
    """Check that the entry points are installed correctly."""
    color_print("\n🔍 Checking installed entry points", "blue")

    # Get installed entry points
    try:
        installed = {
            entry.name: entry
            for entry in pkg_resources.iter_entry_points("console_scripts")
        }
    except Exception as e:
        color_print(f"❌ Error getting installed entry points: {str(e)}", "red")
        return False

    # Check for Kor'tana entry points
    required_entry_points = ["kortana-api", "kortana-dashboard", "kortana-autonomous"]

    installed_entry_points = []
    missing_entry_points = []

    for name in required_entry_points:
        if name in installed:
            installed_entry_points.append(name)
        else:
            missing_entry_points.append(name)

    if missing_entry_points:
        color_print("❌ Missing installed entry points:", "red")
        for name in missing_entry_points:
            print(f"   - {name}")
        color_print("   Run 'pip install -e .' to install entry points", "yellow")
        return False
    else:
        color_print("✅ All required entry points are installed")
        for name in installed_entry_points:
            entry = installed[name]
            print(f"   - {name} -> {entry.module_name}.{entry.attrs[0]}")
        return True


def run_entry_point_help_commands():
    """Try running help commands for the entry points."""
    color_print("\n🔍 Testing entry point help commands", "blue")

    project_root = Path(__file__).parent.parent

    # Try running help commands for each entry point
    entry_points = ["kortana-api", "kortana-dashboard", "kortana-autonomous"]

    success = True
    for name in entry_points:
        print(f"\n   Testing {name} --help:")
        # Run the command in a subprocess
        try:
            result = subprocess.run(
                [sys.executable, "-m", f"kortana.cli.{name.split('-')[1]}", "--help"],
                capture_output=True,
                text=True,
                cwd=project_root,
                env=dict(os.environ, PYTHONPATH=str(project_root)),
            )

            if result.returncode != 0:
                color_print(f"❌ {name} --help failed:", "red")
                print(result.stderr)
                success = False
            else:
                print(result.stdout.strip())
                color_print(f"✅ {name} help command works", "green")
        except Exception as e:
            color_print(f"❌ Error running {name} --help: {str(e)}", "red")
            success = False

    return success


def main():
    """Run all CLI entry point verification checks."""
    color_print("🔍 Verifying Kor'tana CLI Entry Points", "blue")
    color_print("====================================", "blue")

    results = []
    results.append(check_entry_points_in_setup())
    results.append(check_cli_module_structure())
    results.append(check_cli_imports())
    # Commenting out this check since it requires proper installation
    # results.append(check_installed_entry_points())
    # results.append(run_entry_point_help_commands())

    print("\n====================================")
    success_count = results.count(True)
    total_tests = len(results)

    if all(results):
        color_print(
            f"✅ All {total_tests}/{total_tests} CLI entry point tests passed!", "green"
        )
        color_print("\nTo complete the setup:", "blue")
        color_print(
            "1. Run 'pip install -e .' to install the package in development mode",
            "blue",
        )
        color_print("2. Test the entry points with '--help' option", "blue")
    else:
        color_print(
            f"⚠️ {success_count}/{total_tests} CLI entry point tests passed", "yellow"
        )

    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
