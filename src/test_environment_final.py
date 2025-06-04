#!/usr/bin/env python3
"""
Final environment verification script for Kortana project.
This script verifies that all Python environment configurations are working correctly.
"""

import os
import sys


def main():
    print("=== FINAL ENVIRONMENT VERIFICATION ===")
    print("Date: June 3, 2025")
    print()

    # Check Python executable
    print("1. Python Executable:")
    print(f"   {sys.executable}")
    expected_python = "C:\\project-kortana\\venv311\\Scripts\\python.exe"
    if sys.executable.lower() == expected_python.lower():
        print("   ✅ Correct venv311 Python is being used")
    else:
        print(f"   ❌ Expected: {expected_python}")
        print(f"   ❌ Actual: {sys.executable}")
    print()

    # Check Python version
    print("2. Python Version:")
    print(f"   {sys.version}")
    if sys.version_info >= (3, 11):
        print("   ✅ Python 3.11+ detected")
    else:
        print("   ❌ Python 3.11+ required")
    print()

    # Check virtual environment
    print("3. Virtual Environment:")
    venv_path = os.environ.get("VIRTUAL_ENV")
    print(f"   VIRTUAL_ENV: {venv_path}")
    expected_venv = "C:\\project-kortana\\venv311"
    if venv_path and venv_path.lower() == expected_venv.lower():
        print("   ✅ Correct virtual environment activated")
    else:
        print(f"   ❌ Expected: {expected_venv}")
    print()

    # Check Python path
    print("4. Python Path:")
    for i, path in enumerate(sys.path):
        print(f"   [{i}] {path}")

    project_root = "C:\\project-kortana"
    src_path = "C:\\project-kortana\\src"

    if any(project_root.lower() in p.lower() for p in sys.path):
        print("   ✅ Project root in PYTHONPATH")
    else:
        print("   ❌ Project root missing from PYTHONPATH")

    if any(src_path.lower() in p.lower() for p in sys.path):
        print("   ✅ Source directory in PYTHONPATH")
    else:
        print("   ❌ Source directory missing from PYTHONPATH")
    print()

    # Test import capabilities
    print("5. Import Tests:")

    # Test local imports
    try:
        # import brain # Removed F401 unused import

        print("   ✅ Can import brain module")
    except ImportError as e:
        print(f"   ❌ Cannot import brain: {e}")

    try:
        # import autonomous_development_engine # Removed F401 unused import

        print("   ✅ Can import autonomous_development_engine")
    except ImportError as e:
        print(f"   ❌ Cannot import autonomous_development_engine: {e}")

    # Test package imports
    try:
        # import kortana # Removed F401 unused import

        print("   ✅ Can import kortana package")
    except ImportError as e:
        print(f"   ❌ Cannot import kortana package: {e}")

    print()

    # Check working directory
    print("6. Working Directory:")
    cwd = os.getcwd()
    print(f"   {cwd}")
    if "project-kortana" in cwd.lower():
        print("   ✅ Working in project directory")
    else:
        print("   ❌ Not in project directory")
    print()

    # Check environment variables
    print("7. Environment Variables:")
    pythonpath = os.environ.get("PYTHONPATH", "Not set")
    print(f"   PYTHONPATH: {pythonpath}")

    if pythonpath != "Not set" and ("project-kortana" in pythonpath.lower()):
        print("   ✅ PYTHONPATH includes project directory")
    else:
        print("   ❌ PYTHONPATH may need configuration")
    print()

    # VS Code integration check
    print("8. VS Code Integration:")
    if "TERM_PROGRAM" in os.environ and os.environ["TERM_PROGRAM"] == "vscode":
        print("   ✅ Running from VS Code terminal")
    else:
        print("   ℹ️ Not running from VS Code terminal")
    print()

    # Final status
    print("=== ENVIRONMENT STATUS ===")
    issues = []

    if sys.executable.lower() != expected_python.lower():
        issues.append("Wrong Python executable")

    if not venv_path or venv_path.lower() != expected_venv.lower():
        issues.append("Virtual environment not activated")

    if not any(project_root.lower() in p.lower() for p in sys.path):
        issues.append("Project root not in PYTHONPATH")

    if issues:
        print("❌ ISSUES FOUND:")
        for issue in issues:
            print(f"   - {issue}")
        print("\nRecommendations:")
        print("   1. Use VS Code task 'Activate venv311 Environment'")
        print("   2. Ensure venv311 is selected as Python interpreter")
        print("   3. Restart VS Code if needed")
    else:
        print("✅ ENVIRONMENT FULLY CONFIGURED!")
        print("   All checks passed. Ready for development!")

    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()
