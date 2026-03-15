#!/usr/bin/env python3
"""
Standalone Kor'tana Autonomous Activation Test
Tests the core autonomous capabilities without FastAPI dependencies.
"""

import logging
import os
import sys
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_autonomous_core():
    """
    Test Kor'tana's core autonomous capabilities without external dependencies.
    """
    print("🤖 KOR'TANA STANDALONE AUTONOMOUS TEST")
    print("=" * 50)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    success_count = 0
    total_tests = 0

    # Test 1: Import execution engine
    total_tests += 1
    try:
        print("1. 🧠 Testing Execution Engine Import...")
        from kortana.core.execution_engine import execution_engine

        print("   ✅ Execution Engine imported successfully")
        success_count += 1
    except Exception as e:
        print(f"   ❌ Failed to import execution engine: {e}")

    # Test 2: Test execution engine basic functionality
    total_tests += 1
    try:
        print("\n2. ⚡ Testing Execution Engine Functionality...")
        # Test basic directory listing
        result = execution_engine.execute_shell_command(
            command="dir" if os.name == "nt" else "ls", working_dir=project_root
        )

        if result.get("success"):
            print("   ✅ Command executed successfully")
            print(f"   📋 Return code: {result.get('return_code')}")
            success_count += 1
        else:
            print(f"   ❌ Command failed: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ Execution engine test failed: {e}")

    # Test 3: Import autonomous tasks
    total_tests += 1
    try:
        print("\n3. 🚀 Testing Autonomous Tasks Import...")
        from kortana.core.autonomous_tasks import run_health_check_task

        print("   ✅ Autonomous tasks imported successfully")
        success_count += 1
    except Exception as e:
        print(f"   ❌ Failed to import autonomous tasks: {e}")

    # Test 4: Create data directory for autonomous logging
    total_tests += 1
    try:
        print("\n4. 📁 Testing Data Directory Creation...")
        data_dir = os.path.join(project_root, "data")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            print(f"   ✅ Created data directory: {data_dir}")
        else:
            print(f"   ✅ Data directory exists: {data_dir}")
        success_count += 1
    except Exception as e:
        print(f"   ❌ Failed to create data directory: {e}")

    # Test 5: Run autonomous health check (if imports were successful)
    if success_count >= 3:  # If core imports succeeded
        total_tests += 1
        try:
            print("\n5. 🎯 RUNNING AUTONOMOUS HEALTH CHECK...")
            print("   This is the core test - Kor'tana acting autonomously!")

            # Import the task function
            from kortana.core.autonomous_tasks import run_health_check_task

            # Run the autonomous task
            result = run_health_check_task()

            if result and result.get("success"):
                print("   🎉 AUTONOMOUS TASK COMPLETED SUCCESSFULLY!")
                print(f"   📊 Health Status: {result.get('health_status', 'Unknown')}")
                print(f"   📝 Summary: {result.get('summary', 'No summary')}")
                print(f"   📁 Logged to: {result.get('logged_to', 'Unknown')}")
                success_count += 1
            else:
                print(
                    f"   ❌ Autonomous task failed: {result.get('error') if result else 'No result returned'}"
                )

        except Exception as e:
            print(f"   ❌ Autonomous health check failed: {e}")
    else:
        print("\n5. ⏭️  Skipping autonomous health check due to import failures")

    # Results Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    print(f"✅ Successful tests: {success_count}/{total_tests}")
    print(f"❌ Failed tests: {total_tests - success_count}/{total_tests}")

    autonomy_percentage = (success_count / total_tests) * 100
    print(f"🤖 Autonomy Level: {autonomy_percentage:.1f}%")

    if autonomy_percentage >= 80:
        print("🎉 KOR'TANA IS READY FOR AUTONOMOUS OPERATION!")
        activation_status = "AUTONOMOUS AGENT ACTIVATED"
    elif autonomy_percentage >= 60:
        print("⚠️  Kor'tana has partial autonomous capabilities")
        activation_status = "PARTIAL AUTONOMY"
    else:
        print("❌ Kor'tana requires more setup for autonomous operation")
        activation_status = "AUTONOMY NOT READY"

    print(f"🔥 STATUS: {activation_status}")

    return {
        "success": autonomy_percentage >= 80,
        "autonomy_percentage": autonomy_percentage,
        "successful_tests": success_count,
        "total_tests": total_tests,
        "status": activation_status,
    }


if __name__ == "__main__":
    result = test_autonomous_core()

    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)
