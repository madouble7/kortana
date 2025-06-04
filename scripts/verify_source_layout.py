#!/usr/bin/env python
"""
Verify the source layout for Project Kor'tana.
This ensures all code modules are properly under src/kortana/.
"""

import importlib.util
import os
import re
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


def check_package_structure():
    """Verify that all code modules are under src/kortana/."""
    color_print("\n📦 Checking package structure", "blue")

    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src"
    kortana_dir = src_dir / "kortana"

    # Check that src/kortana exists
    if not kortana_dir.exists() or not kortana_dir.is_dir():
        color_print(f"❌ src/kortana directory not found: {kortana_dir}", "red")
        return False

    color_print("✅ src/kortana directory exists")

    # Check for __init__.py files in directories
    missing_inits = []
    for root, dirs, files in os.walk(kortana_dir):
        root_path = Path(root)
        for dirname in dirs:
            # Skip __pycache__ and similar directories
            if dirname.startswith("__") or dirname.startswith("."):
                continue

            init_path = root_path / dirname / "__init__.py"
            if not init_path.exists():
                missing_inits.append(str(init_path.relative_to(project_root)))

    if missing_inits:
        color_print(
            f"❌ Found {len(missing_inits)} directories without __init__.py:", "red"
        )
        for init in missing_inits:
            print(f"   - {init}")
        return False
    else:
        color_print("✅ All packages have __init__.py files")

    return True


def check_for_misplaced_modules():
    """Check that no Python modules are misplaced."""
    color_print("\n📍 Checking for misplaced modules", "blue")

    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src"

    # Find Python files directly under src/ that should be in src/kortana/
    misplaced_files = []

    # Check for Python files directly under src/
    for item in src_dir.iterdir():
        if item.is_file() and item.suffix == ".py" and item.name != "__init__.py":
            misplaced_files.append(str(item.relative_to(project_root)))

    # Check for directories directly under src/ that should be under kortana/
    for item in src_dir.iterdir():
        if item.is_dir() and item.name not in ["kortana", "__pycache__", "tests"]:
            misplaced_files.append(str(item.relative_to(project_root)))

    if misplaced_files:
        color_print(
            f"❌ Found {len(misplaced_files)} misplaced modules/packages:", "red"
        )
        for file in misplaced_files:
            print(f"   - {file}")
        return False
    else:
        color_print("✅ No misplaced modules found")

    return True


def check_import_statements():
    """Check for problematic import statements that use old paths."""
    color_print("\n🔍 Checking import statements", "blue")

    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src"
    kortana_dir = src_dir / "kortana"

    old_import_pattern = re.compile(r"from\s+src\.(?!kortana)")
    problematic_files = []

    for root, dirs, files in os.walk(kortana_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                try:
                    content = file_path.read_text(encoding="utf-8")
                    if old_import_pattern.search(content):
                        problematic_files.append(
                            str(file_path.relative_to(project_root))
                        )
                except UnicodeDecodeError:
                    print(f"   Could not decode file: {file_path}")

    if problematic_files:
        color_print(
            f"❌ Found {len(problematic_files)} files with old import patterns:", "red"
        )
        for file in problematic_files:
            print(f"   - {file}")
        return False
    else:
        color_print("✅ No problematic import patterns found")

    return True


def check_editable_install():
    """Test editable installation."""
    color_print("\n🔄 Testing editable installation", "blue")

    try:
        # Check if kortana is importable
        if importlib.util.find_spec("kortana") is not None:
            color_print("✅ 'kortana' package is importable")
            return True
        else:
            color_print("❌ 'kortana' package is not importable.", "red")
            color_print(
                "   Run 'pip install -e .' to install in editable mode", "yellow"
            )
            return False
    except Exception as e:
        color_print(f"❌ Error testing package import: {str(e)}", "red")
        return False


def main():
    """Run all source layout verification checks."""
    color_print("🔍 Verifying Kor'tana Source Layout", "blue")
    color_print("==================================", "blue")

    results = []
    results.append(check_package_structure())
    results.append(check_for_misplaced_modules())
    results.append(check_import_statements())
    results.append(check_editable_install())

    print("\n==================================")
    success_count = results.count(True)
    total_tests = len(results)

    if all(results):
        color_print(
            f"✅ All {total_tests}/{total_tests} source layout tests passed!", "green"
        )
    else:
        color_print(
            f"⚠️ {success_count}/{total_tests} source layout tests passed", "yellow"
        )

    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
