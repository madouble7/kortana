#!/usr/bin/env python3
"""
Infrastructure Validation Script
Verifies that the locked database infrastructure is working correctly.
"""

import os
import subprocess
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def run_command(command, description):
    """Run a command and return success status."""
    print(f"\n[CHECKING] {description}")
    print(f"Command: {command}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd="c:\\project-kortana",
        )
        if result.returncode == 0:
            print("[SUCCESS]")
            if result.stdout.strip():
                print(f"Output: {result.stdout.strip()}")
            return True
        else:
            print("[FAILED]")
            print(f"Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"[EXCEPTION]: {e}")
        return False


def validate_imports():
    """Validate key package imports."""
    print("\n[CHECKING] Validating Package Imports")
    try:
        import fastapi
        import sqlalchemy

        import alembic

        print("[SUCCESS] All critical imports successful")
        print(f"   SQLAlchemy: {sqlalchemy.__version__}")
        print(f"   Alembic: {alembic.__version__}")
        print(f"   FastAPI: {fastapi.__version__}")
        return True
    except Exception as e:
        print(f"[FAILED] Import failed: {e}")
        return False


def validate_database():
    """Validate database functionality."""
    print("\n[CHECKING] Validating Database Operations")
    try:
        from kortana.modules.memory_core.services import MemoryCoreService
        from kortana.services.database import SyncSessionLocal

        # Test database connection
        session = SyncSessionLocal()

        # Test memory service
        memory_service = MemoryCoreService(session)

        # Test store and retrieve
        memory = memory_service.store_memory(
            title="Infrastructure Test",
            content="This is an automated infrastructure validation test.",
        )

        retrieved = memory_service.retrieve_memory_by_id(memory.id)

        session.close()

        if retrieved and retrieved.title == "Infrastructure Test":
            print("[SUCCESS] Database operations successful")
            print(f"   Test memory ID: {memory.id}")
            return True
        else:
            print("[FAILED] Database operations failed")
            return False

    except Exception as e:
        print(f"[FAILED] Database validation failed: {e}")
        return False


def main():
    """Run complete infrastructure validation."""
    print("=" * 60)
    print("KORTANA INFRASTRUCTURE VALIDATION")
    print("=" * 60)

    checks = []

    # Check Alembic status
    checks.append(
        run_command(
            "C:\\project-kortana\\venv311\\Scripts\\alembic.exe current",
            "Checking Alembic Migration Status",
        )
    )

    # Check Alembic history
    checks.append(
        run_command(
            "C:\\project-kortana\\venv311\\Scripts\\alembic.exe history",
            "Checking Migration History",
        )
    )

    # Validate imports
    checks.append(validate_imports())

    # Validate database operations
    checks.append(validate_database())

    # Test FastAPI app import
    checks.append(
        run_command(
            "C:\\project-kortana\\venv311\\Scripts\\python.exe test_app_import.py",
            "Testing FastAPI Application Import",
        )
    )  # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    passed = sum(checks)
    total = len(checks)

    print(f"Checks Passed: {passed}/{total}")

    if passed == total:
        print("[SUCCESS] ALL INFRASTRUCTURE CHECKS PASSED!")
        print("[READY] System is ready for feature development")
        return True
    else:
        print("[FAILED] Some infrastructure checks failed")
        print("[ACTION] Please review and fix issues before proceeding")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
