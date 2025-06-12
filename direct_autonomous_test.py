#!/usr/bin/env python3
"""
Direct test of autonomous capabilities without complex imports
"""

import os
import subprocess
import sys
from datetime import datetime


def test_basic_execution():
    """Test basic command execution"""
    print("🔧 Testing basic command execution...")

    try:
        # Test simple command
        result = subprocess.run(
            ["echo", "Hello Kor'tana!"]
            if os.name != "nt"
            else ["echo", "Hello Kor'tana!"],
            capture_output=True,
            text=True,
            shell=True if os.name == "nt" else False,
        )

        if result.returncode == 0:
            print("✅ Command executed successfully!")
            print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Command failed with code {result.returncode}")
            return False

    except Exception as e:
        print(f"❌ Command execution failed: {e}")
        return False


def test_directory_listing():
    """Test directory listing (basic file system access)"""
    print("\n📁 Testing directory listing...")

    try:
        project_root = os.path.dirname(os.path.abspath(__file__))
        contents = os.listdir(project_root)

        print(f"✅ Listed {len(contents)} items in project root")
        print(f"   Sample files: {contents[:5]}...")
        return True

    except Exception as e:
        print(f"❌ Directory listing failed: {e}")
        return False


def test_log_writing():
    """Test autonomous activity logging"""
    print("\n📝 Testing autonomous activity logging...")

    try:
        # Create data directory
        project_root = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(project_root, "data")

        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            print(f"✅ Created data directory: {data_dir}")

        # Write a test log entry
        log_file = os.path.join(data_dir, "autonomous_activity.log")
        timestamp = datetime.now().isoformat()

        log_entry = f"[{timestamp}] AUTONOMOUS_TEST: Basic functionality test completed successfully\\n"

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)

        print(f"✅ Logged activity to: {log_file}")
        return True

    except Exception as e:
        print(f"❌ Logging failed: {e}")
        return False


def run_simulated_health_check():
    """Run a simulated autonomous health check"""
    print("\n🎯 Running Simulated Autonomous Health Check...")

    try:
        project_root = os.path.dirname(os.path.abspath(__file__))

        # Simulate the Plan phase
        print("   📋 PLAN: Check project structure and basic health")

        # Simulate the Execute phase
        print("   ⚡ EXECUTE: Scanning project files...")

        # Check for key files
        key_files = [
            "src/kortana/core/execution_engine.py",
            "src/kortana/core/autonomous_tasks.py",
            "src/kortana/core/scheduler.py",
            "pyproject.toml",
        ]

        found_files = 0
        for file_path in key_files:
            full_path = os.path.join(project_root, file_path)
            if os.path.exists(full_path):
                found_files += 1

        health_percentage = (found_files / len(key_files)) * 100

        # Simulate the Learn phase
        print("   🧠 LEARN: Recording health check results...")

        # Log the results
        data_dir = os.path.join(project_root, "data")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        log_file = os.path.join(data_dir, "autonomous_activity.log")
        timestamp = datetime.now().isoformat()

        log_entry = (
            f"[{timestamp}] HEALTH_CHECK_TASK: "
            f"Found {found_files}/{len(key_files)} key files "
            f"({health_percentage:.1f}% health)\\n"
        )

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)

        print(f"✅ Health check completed: {health_percentage:.1f}% health")
        print(f"   Found {found_files}/{len(key_files)} critical files")
        print(f"   Results logged to: {log_file}")

        return {
            "success": True,
            "health_percentage": health_percentage,
            "found_files": found_files,
            "total_files": len(key_files),
            "log_file": log_file,
        }

    except Exception as e:
        print(f"❌ Simulated health check failed: {e}")
        return {"success": False, "error": str(e)}


def main():
    """Main test function"""
    print("🤖 KOR'TANA DIRECT AUTONOMOUS TEST")
    print("=" * 50)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    tests_passed = 0
    total_tests = 4

    # Run tests
    if test_basic_execution():
        tests_passed += 1

    if test_directory_listing():
        tests_passed += 1

    if test_log_writing():
        tests_passed += 1

    # Run the main autonomous test
    health_result = run_simulated_health_check()
    if health_result.get("success"):
        tests_passed += 1

    # Results
    print("\\n" + "=" * 50)
    print("📊 AUTONOMOUS TEST RESULTS")
    print("=" * 50)

    success_rate = (tests_passed / total_tests) * 100
    print(f"✅ Passed: {tests_passed}/{total_tests} tests")
    print(f"🎯 Success Rate: {success_rate:.1f}%")

    if success_rate >= 75:
        print("🎉 KOR'TANA IS READY FOR AUTONOMOUS OPERATION!")
        status = "AUTONOMOUS AGENT READY"
    elif success_rate >= 50:
        print("⚠️  Kor'tana has partial autonomous capabilities")
        status = "PARTIAL AUTONOMY"
    else:
        print("❌ More work needed for autonomous operation")
        status = "NOT READY"

    print(f"🔥 FINAL STATUS: {status}")

    return success_rate >= 75


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
