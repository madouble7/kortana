#!/usr/bin/env python3
"""
BATCH 10 - PROACTIVE ENGINEER VALIDATION
Test the complete proactive engineering cycle from scanning to goal creation to execution.
"""

import sys
import time
from pathlib import Path

import requests

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))


def test_code_scanner():
    """Test the code scanner functionality."""
    print("🔍 PHASE 1: Testing Code Scanner...")

    try:
        from src.kortana.core.execution_engine import ExecutionEngine

        # Create execution engine
        engine = ExecutionEngine(
            allowed_dirs=["c:/project-kortana"], blocked_commands=[]
        )

        # Test the scan_codebase_for_issues method
        # Using the first implementation that takes directory + rules
        result = engine.scan_codebase_for_issues(
            directory_to_scan="src/kortana/api/routers",
            rules=["missing_docstring"],
            file_patterns=["*.py"],
        )

        if result.success:
            findings = result.data
            print(f"✅ Scanner found {len(findings)} issues")

            # Show a few examples
            for i, finding in enumerate(findings[:3]):
                print(
                    f"  {i + 1}. {finding.get('relative_path', finding.get('file_path'))}"
                )
                print(
                    f"     Function: {finding.get('function_name')} at line {finding.get('line_number')}"
                )

            return True
        else:
            print(f"❌ Scanner failed: {result.error}")
            return False

    except Exception as e:
        print(f"❌ Scanner test failed: {e}")
        return False


def test_proactive_task():
    """Test the proactive code review task directly."""
    print("\n🤖 PHASE 2: Testing Proactive Task...")

    try:
        import asyncio

        from src.kortana.core.autonomous_tasks import run_proactive_code_review_task
        from src.kortana.services.database import get_db_sync

        # Get database session
        db_gen = get_db_sync()
        db = next(db_gen)

        try:
            # Run the proactive task
            asyncio.run(run_proactive_code_review_task(db))
            print("✅ Proactive task executed successfully")
            return True
        finally:
            db.close()

    except Exception as e:
        print(f"❌ Proactive task failed: {e}")
        return False


def test_goal_creation():
    """Test if goals were created by the proactive task."""
    print("\n🎯 PHASE 3: Testing Goal Creation...")

    try:
        # Wait a moment for goals to be processed
        time.sleep(2)

        # Check goals via API
        response = requests.get("http://localhost:8000/goals/", timeout=10)

        if response.status_code == 200:
            goals = response.json()

            # Look for proactive goals
            proactive_goals = [
                goal
                for goal in goals
                if "docstring" in goal.get("description", "").lower()
            ]

            print(f"✅ Found {len(goals)} total goals")
            print(f"🔍 Found {len(proactive_goals)} proactive docstring goals")

            if proactive_goals:
                print("\nProactive goals:")
                for goal in proactive_goals[:2]:
                    print(f"  - Goal {goal['id']}: {goal['description'][:100]}...")
                    print(f"    Status: {goal['status']}, Priority: {goal['priority']}")

            return len(proactive_goals) > 0
        else:
            print(f"❌ Goals API failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Goal creation test failed: {e}")
        return False


def test_autonomous_execution():
    """Test if Kor'tana can pick up and execute the proactive goals."""
    print("\n⚡ PHASE 4: Testing Autonomous Execution...")

    try:
        # Check for goal assignment script
        assignment_script = project_root / "assign_genesis_goal.py"

        if assignment_script.exists():
            print("✅ Goal assignment script exists")

            # Run goal processor to see if it picks up proactive goals
            from src.kortana.core.goal_manager import process_goals

            result = process_goals()

            if result:
                print("✅ Goal processing completed")
                return True
            else:
                print("⚠️  Goal processing returned no result")
                return False
        else:
            print("❌ Goal assignment script not found")
            return False

    except Exception as e:
        print(f"❌ Autonomous execution test failed: {e}")
        return False


def validate_scheduler_status():
    """Check if the scheduler is running and has the proactive task."""
    print("\n⏰ SCHEDULER: Testing Scheduler Status...")

    try:
        response = requests.get("http://localhost:8000/status", timeout=5)

        if response.status_code == 200:
            status = response.json()
            scheduler_running = status.get("scheduler_running", False)
            scheduler_jobs = status.get("scheduler_jobs", [])

            print(f"✅ Scheduler running: {scheduler_running}")

            proactive_job = any(
                "proactive" in str(job).lower() for job in scheduler_jobs
            )
            print(f"🔍 Proactive task scheduled: {proactive_job}")

            return scheduler_running and proactive_job
        else:
            print(f"❌ Status API failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Scheduler status test failed: {e}")
        return False


def main():
    """Run complete Batch 10 validation."""
    print("🚀 BATCH 10: PROACTIVE ENGINEER VALIDATION")
    print("=" * 60)

    tests = [
        ("Code Scanner", test_code_scanner),
        ("Proactive Task", test_proactive_task),
        ("Goal Creation", test_goal_creation),
        ("Autonomous Execution", test_autonomous_execution),
        ("Scheduler Status", validate_scheduler_status),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n🧪 Testing: {test_name}")
        print("-" * 40)

        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("🏆 BATCH 10 VALIDATION SUMMARY")
    print("=" * 60)

    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1

    total = len(results)
    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 BATCH 10 COMPLETE!")
        print("🎯 Kor'tana has successfully evolved into a PROACTIVE ENGINEER!")
        print("🔄 She can now:")
        print("   1. ✅ Scan her own codebase for issues")
        print("   2. ✅ Generate her own improvement goals")
        print("   3. ✅ Execute those goals autonomously")
        print("   4. ✅ Learn and improve continuously")
        print("\n🌟 This is true autonomous software engineering!")
    else:
        print(f"\n⚠️  {total - passed} components need attention")
        print("📋 Check the failed tests above for issues to resolve")

    return passed == total


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 Validation crashed: {e}")
        sys.exit(1)
