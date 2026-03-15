#!/usr/bin/env python3
"""
Quick validation test for Batch 10 Proactive Engineering System
"""

import os
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


def test_scanner_directly():
    """Test the code scanner functionality directly."""
    print("🔍 Testing Code Scanner...")

    try:
        from kortana.core.execution_engine import ExecutionEngine

        # Create execution engine
        engine = ExecutionEngine(
            allowed_dirs=["c:/project-kortana"], blocked_commands=[]
        )

        # Test scan with a simple directory
        test_dir = "src/kortana/api/routers"
        if os.path.exists(test_dir):
            result = engine.scan_codebase_for_issues(
                directory_to_scan=test_dir,
                rules=["missing_docstring"],
                file_patterns=["*.py"],
            )

            if result and result.success:
                findings = result.data or []
                print(
                    f"✅ Scanner works! Found {len(findings)} functions missing docstrings"
                )

                # Show first few findings
                for finding in findings[:3]:
                    file_path = finding.get(
                        "relative_path", finding.get("file_path", "unknown")
                    )
                    func_name = finding.get("function_name", "unknown")
                    line_num = finding.get("line_number", "unknown")
                    print(f"  📄 {file_path} -> {func_name}() at line {line_num}")

                return True
            else:
                print(
                    f"❌ Scanner returned error: {result.error if result else 'No result'}"
                )
                return False
        else:
            print(f"❌ Test directory not found: {test_dir}")
            return False

    except Exception as e:
        print(f"❌ Scanner test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_database_connection():
    """Test database connection and look for existing goals."""
    print("\n💾 Testing Database Connection...")

    try:
        from sqlalchemy import desc

        from kortana.database.db_setup import SessionLocal
        from kortana.models.goal import Goal

        db = SessionLocal()

        # Get recent goals
        recent_goals = db.query(Goal).order_by(desc(Goal.created_at)).limit(5).all()

        print(f"✅ Database connected! Found {len(recent_goals)} recent goals")

        proactive_count = 0
        for goal in recent_goals:
            metadata_str = str(goal.metadata) if goal.metadata else ""
            if "proactive" in metadata_str.lower():
                proactive_count += 1
                print(f"  🚀 PROACTIVE: {goal.title} (ID: {goal.id})")
            else:
                print(f"  📝 Regular: {goal.title} (ID: {goal.id})")

        print(f"🎯 Found {proactive_count} proactive goals")

        db.close()
        return True

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


def main():
    """Main validation function."""
    print("🚀 BATCH 10 PROACTIVE ENGINEER - QUICK VALIDATION")
    print("=" * 60)

    success_count = 0
    total_tests = 2

    # Test 1: Code Scanner
    if test_scanner_directly():
        success_count += 1

    # Test 2: Database Connection
    if test_database_connection():
        success_count += 1

    print("\n" + "=" * 60)
    print(f"📊 VALIDATION SUMMARY: {success_count}/{total_tests} tests passed")

    if success_count == total_tests:
        print("🎉 Core components working! Scanner and database operational.")
    else:
        print("❌ Issues found. Need investigation.")

    return success_count == total_tests


if __name__ == "__main__":
    main()
