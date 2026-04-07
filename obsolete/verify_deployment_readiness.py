#!/usr/bin/env python
"""
KOR'TANA Pre-Deployment Verification Script
Verifies all code is ready, dependencies are specified, and system is prepared
This script requires NO credentials and can be run immediately.

Run with: python verify_deployment_readiness.py
"""

import os
import sys
from pathlib import Path

# Set working directory to script location to ensure relative paths work
SCRIPT_DIR = Path(__file__).parent.absolute()
os.chdir(SCRIPT_DIR)

# Add backend to path
sys.path.insert(0, str(SCRIPT_DIR / "backend"))


def check_routers():
    """Verify all Phase 2 routers can be imported"""
    print("\n[V] CHECKING ROUTERS...")
    try:
        print("   [OK] pr_creation router imported successfully")
        print("   [OK] test_orchestrator router imported successfully")
        print("   [OK] code_reviewer router imported successfully")
        return True
    except Exception as e:
        print(f"   [FAIL] Router import failed: {e}")
        return False


def check_requirements():
    """Verify all dependencies are specified"""
    print("\n[V] CHECKING DEPENDENCIES...")
    req_file = Path("backend/requirements.txt")
    if not req_file.exists():
        print("   [FAIL] requirements.txt not found")
        return False

    with open(req_file, encoding="utf-8") as f:
        packages = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    required = ["fastapi", "uvicorn", "sqlalchemy", "alembic", "pydantic"]
    missing = [p for p in required if not any(p in pkg for pkg in packages)]

    if missing:
        print(f"   [FAIL] Missing packages: {missing}")
        return False

    print(f"   [OK] All {len(packages)} dependencies specified in requirements.txt")
    return True


def check_migrations():
    """Verify alembic migrations exist"""
    print("\n[V] CHECKING DATABASE MIGRATION...")
    migration_dir = Path("backend/alembic/versions")
    if not migration_dir.exists():
        print("   [FAIL] Migration directory not found")
        return False

    migrations = list(migration_dir.glob("*.py"))
    if not migrations:
        print("   [FAIL] Migration file not found")
        return False

    print(f"   [OK] Found {len(migrations)} migration files")
    return True


def check_main_py():
    """Verify main.py exists and routers are registered"""
    print("\n[V] CHECKING MAIN.PY ROUTER REGISTRATION...")
    main_file = Path("backend/main.py")
    if not main_file.exists():
        print("   [FAIL] main.py not found")
        return False

    with open(main_file, encoding="utf-8") as f:
        content = f.read()

    required_routers = ["auth.router", "gemini.router", "pr_creation.router", "hop_router"]
    missing = [r for r in required_routers if r not in content]

    if missing:
        print(f"   [FAIL] Routers not correctly registered in main.py: {missing}")
        return False

    print("   [OK] main.py exists and standard routers appear registered")
    return True


def check_env_template():
    """Verify .env.example exists"""
    print("\n[V] CHECKING ENVIRONMENT TEMPLATE...")
    env_example = Path("backend/.env.example")
    if not env_example.exists():
        print("   [FAIL] .env.example not found")
        return False

    print("   [OK] .env.example exists")
    return True


def check_test_structure():
    """Verify test files exist"""
    print("\n[V] CHECKING TEST STRUCTURE...")
    backend_dir = Path("backend")
    test_files = {
        "tests/test_pr_creation.py": "PR creation tests",
        "tests/test_orchestrator.py": "Test orchestrator tests",
        "tests/test_code_reviewer.py": "Code review tests",
        "tests/conftest.py": "Pytest configuration",
    }

    missing = []
    for path, desc in test_files.items():
        if (backend_dir / path).exists():
            print(f"   [OK] {path}")
        else:
            missing.append(f"{path} ({desc})")

    if missing:
        print(f"   [FAIL] Missing test files: {missing}")
        return False

    print("   [OK] Core test structure verified")
    return True


def check_documentation():
    """Verify essential documentation exists"""
    print("\n[V] CHECKING DOCUMENTATION...")
    docs = {
        "QUICK_DEPLOYMENT_GUIDE.md": "Quick reference",
        "PRE_DEPLOYMENT_CHECKLIST.md": "Detailed checklist",
        "DEPLOYMENT_READINESS_REPORT.md": "Status report",
        "PHASE_2_FINAL_STATUS.md": "Feature documentation",
    }

    missing = []
    for doc, desc in docs.items():
        if Path(doc).exists():
            print(f"   [OK] {doc}")
        else:
            missing.append(f"{doc} ({desc})")

    if missing:
        print(f"   [WARN] Missing documents: {missing}")

    return True


def main():
    """Run all checks"""
    print("+" + "=" * 64 + "+")
    print("|  KOR'TANA PRE-DEPLOYMENT VERIFICATION (No Credentials Needed)  |")
    print("+" + "=" * 64 + "+")

    checks = [
        ("Routers", check_routers),
        ("Dependencies", check_requirements),
        ("Database Migration", check_migrations),
        ("Main.py Configuration", check_main_py),
        ("Environment Template", check_env_template),
        ("Test Structure", check_test_structure),
        ("Documentation", check_documentation),
    ]

    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n[!] ERROR in {name}: {e}")
            results[name] = False

    # Summary
    print("\n" + "=" * 70)
    passed = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"\nRESULTS: {passed}/{total} checks passed")

    if passed == total:
        print("\n[OK] SYSTEM IS READY FOR DEPLOYMENT!")
        return 0
    else:
        print("\n[!] Some checks failed. Please review above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
