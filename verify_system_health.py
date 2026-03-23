#!/usr/bin/env python3
"""
KOR'TANA System Health Verification Script
===============================================

Autonomous system health check that validates:
- Phase 1-2 Volitional Self-Correction Engine operational status
- All core implementation files present and compilable
- Dynamic classification working correctly
- System autonomy level and readiness

Usage:
    python verify_system_health.py

Exit Codes:
    0 = System healthy, all checks passed
    1 = One or more health checks failed
"""

import subprocess
import sys
from enum import Enum
from pathlib import Path


class HealthStatus(Enum):
    """System health status levels"""

    HEALTHY = "✅ HEALTHY"
    WARNING = "⚠️ WARNING"
    CRITICAL = "🔴 CRITICAL"


def check_file_exists(filepath: str) -> tuple[bool, str]:
    """Check if file exists and is readable"""
    path = Path(filepath)
    if path.exists() and path.is_file():
        return True, f"✅ Found: {filepath}"
    return False, f"❌ Missing: {filepath}"


def check_python_syntax(filepath: str) -> tuple[bool, str]:
    """Check if Python file has valid syntax"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", filepath],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return True, f"✅ Syntax valid: {filepath}"
        return False, f"❌ Syntax error in {filepath}: {result.stderr}"
    except Exception as e:
        return False, f"❌ Error checking {filepath}: {str(e)}"


def check_imports(import_statement: str) -> tuple[bool, str]:
    """Check if Python imports work"""
    try:
        result = subprocess.run(
            [sys.executable, "-c", import_statement],
            capture_output=True,
            text=True,
            timeout=10,
            cwd="c:\\KOR-TANA\\kortana\\backend",
        )
        if result.returncode == 0:
            return True, f"✅ Imports work: {import_statement}"
        return False, f"❌ Import failed: {import_statement}"
    except Exception as e:
        return False, f"❌ Error checking imports: {str(e)}"


def check_dynamic_classification() -> tuple[bool, str]:
    """Test Phase 1 dynamic classification"""
    test_code = """
from src.kortana.human_only_protocol import HumanOnlyProtocol, TaskClassification
hop = HumanOnlyProtocol()
result = hop.classify_task('fix_test_failure', {'branch': 'evolution/fix'})
assert result == TaskClassification.SELF_CORRECTION, f"Expected SELF_CORRECTION, got {result}"
print("CLASSIFICATION_WORKS")
"""
    try:
        result = subprocess.run(
            [sys.executable, "-c", test_code],
            capture_output=True,
            text=True,
            timeout=10,
            cwd="c:\\KOR-TANA\\kortana\\backend",
        )
        if "CLASSIFICATION_WORKS" in result.stdout:
            return True, "✅ Dynamic classification: SELF_CORRECTION tier working"
        return False, f"❌ Classification test failed: {result.stderr}"
    except Exception as e:
        return False, f"❌ Error testing classification: {str(e)}"


def check_custom_tests() -> tuple[bool, str]:
    """Run custom Phase 1-2 validation tests"""
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "test_volitional_self_correction.py",
                "test_phase2_integration.py",
                "-q",
                "--tb=no",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            cwd="c:\\KOR-TANA\\kortana\\backend",
        )
        if result.returncode == 0 and "2 passed" in result.stdout:
            return True, "✅ Custom tests: 2/2 PASSED"
        return False, "❌ Custom tests failed or incomplete"
    except Exception as e:
        return False, f"❌ Error running tests: {str(e)}"


def check_files_exist() -> list[tuple[bool, str]]:
    """Check all critical implementation files"""
    files = [
        "backend/src/kortana/human_only_protocol.py",
        "backend/src/kortana/schemas.py",
        "backend/src/kortana/routers/task_queue.py",
        "SYSTEM_OPERATIONAL_STATUS_2026-03-22.md",
        "PHASE_3_GITHUB_PR_AUTOMATION_PLAN.md",
    ]
    return [check_file_exists(f) for f in files]


def main():
    """Run all health checks"""
    print("\n" + "=" * 70)
    print("KOR'TANA SYSTEM HEALTH VERIFICATION")
    print("=" * 70 + "\n")

    all_passed = True
    check_results = []

    # File existence checks
    print("📁 FILE INTEGRITY CHECKS")
    print("-" * 70)
    for passed, message in check_files_exist():
        print(message)
        if not passed:
            all_passed = False
        check_results.append(passed)

    # Syntax checks
    print("\n🔍 SYNTAX VALIDATION")
    print("-" * 70)
    for filepath in [
        "backend/src/kortana/human_only_protocol.py",
        "backend/src/kortana/schemas.py",
        "backend/src/kortana/routers/task_queue.py",
    ]:
        passed, message = check_python_syntax(filepath)
        print(message)
        if not passed:
            all_passed = False
        check_results.append(passed)

    # Import checks
    print("\n📦 IMPORT VALIDATION")
    print("-" * 70)
    imports = [
        "from src.kortana.human_only_protocol import HumanOnlyProtocol, TaskClassification",
        "from src.kortana.schemas import TaskClassification as SchemaTC",
        "from src.kortana.routers.task_queue import router",
    ]
    for imp in imports:
        passed, message = check_imports(imp)
        print(message)
        if not passed:
            all_passed = False
        check_results.append(passed)

    # Phase 1 dynamic classification
    print("\n⚙️ PHASE 1 DYNAMIC CLASSIFICATION")
    print("-" * 70)
    passed, message = check_dynamic_classification()
    print(message)
    if not passed:
        all_passed = False
    check_results.append(passed)

    # Custom tests
    print("\n✅ PHASE 1-2 VALIDATION TESTS")
    print("-" * 70)
    passed, message = check_custom_tests()
    print(message)
    if not passed:
        all_passed = False
    check_results.append(passed)

    # Summary
    print("\n" + "=" * 70)
    total_checks = len(check_results)
    passed_checks = sum(check_results)

    if all_passed:
        status = HealthStatus.HEALTHY
        autonomy = "60% (Phase 1-2 Complete)"
    else:
        status = (
            HealthStatus.CRITICAL
            if passed_checks < total_checks // 2
            else HealthStatus.WARNING
        )
        autonomy = "UNKNOWN"

    print(f"SYSTEM STATUS: {status.value}")
    print(f"CHECKS PASSED: {passed_checks}/{total_checks}")
    print(f"AUTONOMY LEVEL: {autonomy}")
    print(f"READINESS: {'✅ PRODUCTION READY' if all_passed else '⚠️ NEEDS ATTENTION'}")
    print("=" * 70 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
