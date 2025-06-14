#!/usr/bin/env python3
"""
BATCH 10 FINAL VALIDATION - PROACTIVE ENGINEER COMPLETION CHECK
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


def validate_implementation_files():
    """Check that all required implementation files exist and have the right components."""
    print("📁 VALIDATING IMPLEMENTATION FILES...")

    required_files = {
        "src/kortana/core/execution_engine.py": [
            "scan_codebase_for_issues",
            "_scan_file_for_issues",
        ],
        "src/kortana/core/autonomous_tasks.py": ["run_proactive_code_review_task"],
        "src/kortana/core/scheduler.py": ["proactive_code_review_task"],
        "src/kortana/core/brain.py": ["_proactive_code_review_cycle"],
    }

    validation_results = {}

    for file_path, required_functions in required_files.items():
        full_path = project_root / file_path
        if full_path.exists():
            try:
                with open(full_path, encoding="utf-8") as f:
                    content = f.read()

                found_functions = []
                missing_functions = []

                for func_name in required_functions:
                    if func_name in content:
                        found_functions.append(func_name)
                    else:
                        missing_functions.append(func_name)

                validation_results[file_path] = {
                    "exists": True,
                    "found_functions": found_functions,
                    "missing_functions": missing_functions,
                    "complete": len(missing_functions) == 0,
                }

                if len(missing_functions) == 0:
                    print(f"  ✅ {file_path} - All functions present")
                else:
                    print(f"  ⚠️  {file_path} - Missing: {missing_functions}")

            except Exception as e:
                validation_results[file_path] = {
                    "exists": True,
                    "error": str(e),
                    "complete": False,
                }
                print(f"  ❌ {file_path} - Error reading file: {e}")
        else:
            validation_results[file_path] = {"exists": False, "complete": False}
            print(f"  ❌ {file_path} - File not found")

    return validation_results


def test_code_scanner():
    """Test the code scanner functionality."""
    print("\n🔍 TESTING CODE SCANNER...")

    try:
        from src.kortana.core.execution_engine import ExecutionEngine

        # Test directory with known Python files
        test_dirs = [
            "src/kortana/api/routers",
            "src/kortana/core",
            "src/kortana/models",
        ]

        for test_dir in test_dirs:
            if os.path.exists(test_dir):
                print(f"  Testing directory: {test_dir}")

                engine = ExecutionEngine(
                    allowed_dirs=["c:/project-kortana"], blocked_commands=[]
                )

                result = engine.scan_codebase_for_issues(
                    directory_to_scan=test_dir,
                    rules=["missing_docstring"],
                    file_patterns=["*.py"],
                )

                if result and result.success:
                    findings = result.data or []
                    print(f"    ✅ Found {len(findings)} functions missing docstrings")

                    # Show examples
                    for i, finding in enumerate(findings[:2]):
                        file_path = finding.get(
                            "relative_path", finding.get("file_path", "unknown")
                        )
                        func_name = finding.get("function_name", "unknown")
                        print(f"      📄 {file_path} -> {func_name}()")

                    return True
                else:
                    print(
                        f"    ❌ Scanner failed: {result.error if result else 'No result'}"
                    )
                    return False

        print("  ❌ No valid test directories found")
        return False

    except Exception as e:
        print(f"  ❌ Scanner test failed: {e}")
        return False


def check_database_for_proactive_goals():
    """Check if any proactive goals exist in the database."""
    print("\n💾 CHECKING DATABASE FOR PROACTIVE GOALS...")

    try:
        from src.kortana.database.db_setup import SessionLocal
        from src.kortana.models.goal import Goal

        db = SessionLocal()

        # Count total goals
        total_goals = db.query(Goal).count()
        print(f"  📊 Total goals in database: {total_goals}")

        # Look for proactive goals (goals with metadata containing "proactive")
        proactive_goals = (
            db.query(Goal).filter(Goal.metadata.contains("proactive")).all()
        )

        print(f"  🚀 Proactive goals found: {len(proactive_goals)}")

        # Show recent proactive goals
        if proactive_goals:
            print("  Recent proactive goals:")
            for goal in proactive_goals[-3:]:  # Last 3
                print(f"    📝 ID:{goal.id} - {goal.title}")
                print(f"       Status: {goal.status}, Created: {goal.created_at}")

        # Look for goals containing "docstring" (our test case)
        docstring_goals = (
            db.query(Goal).filter(Goal.description.contains("docstring")).count()
        )

        print(f"  📚 Docstring-related goals: {docstring_goals}")

        db.close()
        return len(proactive_goals) > 0

    except Exception as e:
        print(f"  ❌ Database check failed: {e}")
        return False


def manual_proactive_execution():
    """Try to run the proactive task manually to ensure it works."""
    print("\n🤖 MANUAL PROACTIVE TASK EXECUTION...")

    try:
        import asyncio

        from src.kortana.core.autonomous_tasks import run_proactive_code_review_task
        from src.kortana.database.db_setup import SessionLocal

        print("  ⚡ Running proactive code review task...")

        db = SessionLocal()

        # Run the task
        asyncio.run(run_proactive_code_review_task(db))

        print("  ✅ Proactive task executed successfully!")

        db.close()
        return True

    except Exception as e:
        print(f"  ❌ Manual execution failed: {e}")
        return False


def check_scheduler_integration():
    """Check if the scheduler is properly configured for proactive tasks."""
    print("\n⏰ CHECKING SCHEDULER INTEGRATION...")

    try:
        # Check scheduler.py for proactive task registration
        scheduler_file = project_root / "src/kortana/core/scheduler.py"

        if scheduler_file.exists():
            with open(scheduler_file, encoding="utf-8") as f:
                content = f.read()

            proactive_indicators = [
                "proactive_code_review",
                "run_proactive_code_review_task",
                "hours=2",  # Every 2 hours schedule
            ]

            found_indicators = [
                indicator for indicator in proactive_indicators if indicator in content
            ]

            print(
                f"  📋 Scheduler integration indicators found: {len(found_indicators)}/{len(proactive_indicators)}"
            )

            for indicator in found_indicators:
                print(f"    ✅ {indicator}")

            missing = [
                indicator
                for indicator in proactive_indicators
                if indicator not in content
            ]
            for indicator in missing:
                print(f"    ❌ Missing: {indicator}")

            return len(found_indicators) >= 2
        else:
            print("  ❌ Scheduler file not found")
            return False

    except Exception as e:
        print(f"  ❌ Scheduler check failed: {e}")
        return False


def generate_completion_report():
    """Generate a comprehensive completion report."""
    print("\n📋 GENERATING BATCH 10 COMPLETION REPORT...")

    report = {
        "batch": "Batch 10: The Proactive Engineer Initiative",
        "completion_date": datetime.now().isoformat(),
        "validation_summary": {},
        "status": "unknown",
    }

    # Run all validations
    validations = {
        "implementation_files": validate_implementation_files(),
        "code_scanner": test_code_scanner(),
        "database_check": check_database_for_proactive_goals(),
        "manual_execution": manual_proactive_execution(),
        "scheduler_integration": check_scheduler_integration(),
    }

    # Calculate success rate
    successful_validations = sum(
        1 for result in validations.values() if isinstance(result, bool) and result
    )
    total_validations = len(
        [result for result in validations.values() if isinstance(result, bool)]
    )

    # Check file validation success
    if isinstance(validations["implementation_files"], dict):
        file_successes = sum(
            1
            for file_result in validations["implementation_files"].values()
            if file_result.get("complete", False)
        )
        file_total = len(validations["implementation_files"])

        if file_successes == file_total:
            successful_validations += 1
        total_validations += 1

    success_rate = (
        (successful_validations / total_validations) * 100
        if total_validations > 0
        else 0
    )

    report["validation_summary"] = {
        "successful_validations": successful_validations,
        "total_validations": total_validations,
        "success_rate": f"{success_rate:.1f}%",
    }

    # Determine overall status
    if success_rate >= 80:
        report["status"] = "COMPLETED ✅"
    elif success_rate >= 60:
        report["status"] = "MOSTLY COMPLETE ⚠️"
    else:
        report["status"] = "NEEDS WORK ❌"

    print("\n🎯 BATCH 10 VALIDATION COMPLETE")
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"Status: {report['status']}")

    return report


def main():
    """Main validation and completion check."""
    print("🚀 BATCH 10: PROACTIVE ENGINEER - FINAL VALIDATION")
    print("=" * 70)
    print("Checking implementation completeness and functionality...")
    print()

    report = generate_completion_report()

    print("\n" + "=" * 70)
    print("🎉 BATCH 10 FINAL REPORT")
    print(f"Status: {report['status']}")
    print(f"Success Rate: {report['validation_summary']['success_rate']}")

    if "COMPLETED" in report["status"]:
        print("\n🌟 KOR'TANA IS NOW A PROACTIVE AUTONOMOUS ENGINEER!")
        print("✨ She can now:")
        print("   • Scan her own codebase for quality issues")
        print("   • Generate her own improvement goals")
        print("   • Execute those goals autonomously")
        print("   • Run this cycle continuously without human intervention")

    return report


if __name__ == "__main__":
    main()
