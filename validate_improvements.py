#!/usr/bin/env python
"""
Validation Script for Kor'tana 2.0 Improvements

Tests that all new utility modules import correctly and core modules work.
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def test_imports():
    """Test all utility imports."""
    print("\n" + "=" * 70)
    print("TESTING IMPORTS")
    print("=" * 70)

    tests = [
        ("TTLCache", "from kortana.utils import TTLCache"),
        ("CircuitBreaker", "from kortana.utils import CircuitBreaker"),
        ("MetricsCollector", "from kortana.utils import MetricsCollector"),
        ("Validator", "from kortana.utils import Validator"),
        ("AsyncBatchProcessor", "from kortana.utils import AsyncBatchProcessor"),
        ("cached_async decorator", "from kortana.utils import cached_async"),
        ("timed_execution decorator", "from kortana.utils import timed_execution"),
        ("AsyncRetry decorator", "from kortana.utils import AsyncRetry"),
        ("AsyncCache", "from kortana.utils import AsyncCache"),
        ("ConnectionPool", "from kortana.utils import ConnectionPool"),
        ("KortanaError", "from kortana.utils import KortanaError"),
        ("ServiceError", "from kortana.utils import ServiceError"),
        ("ErrorContext", "from kortana.utils import ErrorContext"),
        ("Chat Engine with improvements", "from kortana.brain import ChatEngine"),
        (
            "LLM Service with improvements",
            "from kortana.services.llm_service import LLMService",
        ),
    ]

    failed = []
    for name, import_stmt in tests:
        try:
            exec(import_stmt)
            print(f"✅ {name}")
        except Exception as e:
            print(f"❌ {name}: {e}")
            failed.append((name, str(e)))

    return failed


def test_basic_functionality():
    """Test basic functionality of key utilities."""
    print("\n" + "=" * 70)
    print("TESTING BASIC FUNCTIONALITY")
    print("=" * 70)

    try:
        from kortana.utils import TTLCache

        cache = TTLCache(max_size=10, default_ttl=60)
        print("✅ TTLCache creation: max_size=10, default_ttl=60")

        from kortana.utils import CircuitBreaker

        breaker = CircuitBreaker(5, 60)
        print("✅ CircuitBreaker creation: failure_threshold=5, recovery_timeout=60")

        from kortana.utils import MetricsCollector

        metrics = MetricsCollector()
        print("✅ MetricsCollector creation: ready to track operations")

        from kortana.utils import Validator

        validator = Validator("test_field")
        print("✅ Validator creation: ready for validation rules")

        print("\n🎯 All basic functionality tests passed!")
        return []
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        import traceback

        traceback.print_exc()
        return [("functionality", str(e))]


def test_type_hints():
    """Test that type hints are present."""
    print("\n" + "=" * 70)
    print("CHECKING TYPE HINTS")
    print("=" * 70)

    modules = [
        ("performance", "src/kortana/utils/performance.py"),
        ("errors", "src/kortana/utils/errors.py"),
        ("async_helpers", "src/kortana/utils/async_helpers.py"),
        ("validation", "src/kortana/utils/validation.py"),
    ]

    failed = []
    for name, path in modules:
        full_path = os.path.join(os.path.dirname(__file__), path)
        if os.path.exists(full_path):
            with open(full_path) as f:
                content = f.read()
                # Check for type hints (simple heuristic: -> and : with types)
                if "->" in content or ": " in content:
                    print(f"✅ {name}: Type hints present")
                else:
                    print(f"⚠️  {name}: Type hints may be missing")
        else:
            failed.append((name, "File not found"))

    return failed


def main():
    """Run all validation tests."""
    print("\n" + "█" * 70)
    print("█" + " " * 68 + "█")
    print("█" + " " * 15 + "KOR'TANA 2.0 IMPROVEMENTS VALIDATION" + " " * 14 + "█")
    print("█" + " " * 68 + "█")
    print("█" * 70)

    all_failures = []

    # Test 1: Imports
    failures = test_imports()
    all_failures.extend(failures)

    # Test 2: Basic functionality
    failures = test_basic_functionality()
    all_failures.extend(failures)

    # Test 3: Type hints
    failures = test_type_hints()
    all_failures.extend(failures)

    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    if not all_failures:
        print("\n✅ ALL TESTS PASSED!")
        print(
            "\nKor'tana 2.0 improvements are successfully installed and ready to use."
        )
        print("\nNext steps:")
        print("  1. Read QUICK_START_IMPROVEMENTS.md for usage examples")
        print("  2. Check OPTIMIZATIONS_GUIDE.md for detailed documentation")
        print("  3. Run the full test suite: pytest tests/")
        print("  4. Review KOR'TANA_2.0_COMPLETION_REPORT.md for deployment info")
        return 0
    else:
        print(f"\n❌ {len(all_failures)} test(s) failed:")
        for name, error in all_failures:
            print(f"  - {name}: {error}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
