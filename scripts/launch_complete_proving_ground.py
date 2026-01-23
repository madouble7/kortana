#!/usr/bin/env python3
"""
The Proving Ground - Complete Launch Sequence
=============================================
Launches Kor'tana, submits the Genesis Protocol goal, and starts monitoring
"""

import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Set up project root
project_root = Path(r"C:\project-kortana")
os.chdir(project_root)
sys.path.insert(0, str(project_root))


def launch_proving_ground():
    """Launch The Proving Ground sequence."""

    print("=" * 80)
    print("🚀 THE PROVING GROUND - COMPLETE LAUNCH SEQUENCE")
    print("=" * 80)
    print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Project Root: {project_root}")
    print("\n🎯 MISSION: Witness Kor'tana's first autonomous engineering act")

    server_process = None

    try:
        # Step 1: Launch server
        print(f"\n{'=' * 60}")
        print("📡 STEP 1: LAUNCHING KOR'TANA SERVER")
        print("=" * 60)

        print("   Starting uvicorn server...")
        server_process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "src.kortana.main:app",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
                "--reload",
            ],
            cwd=project_root,
        )

        print("   ✅ Server process started")
        print("   🔍 Waiting for server to be ready...")        # Wait for server to be ready
        import requests

        for attempt in range(30):
            try:
                response = requests.get("http://localhost:8000/health", timeout=2)
                if response.status_code == 200:
                    print("   ✅ Server is online and ready!")
                    break
            except (requests.RequestException, ConnectionError) as e:
                if attempt >= 29:  # Only log on last attempt to avoid flooding
                    print(f"      Connection failed: {e}")
            time.sleep(2)
            print(f"      Attempt {attempt + 1}/30...")
        else:
            raise Exception("Server failed to start within timeout")

        # Step 2: Submit Genesis Protocol goal
        print(f"\n{'=' * 60}")
        print("🎯 STEP 2: SUBMITTING GENESIS PROTOCOL GOAL")
        print("=" * 60)

        print("   Executing goal submission script...")
        goal_result = subprocess.run(
            [sys.executable, "submit_genesis_goal.py"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        if goal_result.returncode == 0:
            print("   ✅ Genesis Protocol goal submitted successfully!")
            print("   📋 Kor'tana has received her first engineering challenge")
        else:
            print("   ⚠️  Goal submission completed with warnings")
            print(f"   Output: {goal_result.stdout}")

        # Step 3: Begin monitoring
        print(f"\n{'=' * 60}")
        print("👁️  STEP 3: AUTONOMOUS MONITORING INITIATED")
        print("=" * 60)

        print("   🔍 Beginning real-time monitoring of Kor'tana's work...")
        print("   📊 Tracking: logs, file changes, goal status, system metrics")
        print("   ⏱️  Update interval: 15 seconds")
        print(f"\n{'=' * 80}")
        print("🎭 THE PROVING GROUND IS NOW ACTIVE")
        print("=" * 80)
        print("   Kor'tana is working autonomously on the Genesis Protocol refactoring")
        print("   Monitor output will show her progress in real-time")
        print("   Press Ctrl+C to stop monitoring (server will continue running)")
        print("=" * 80)        # Start monitoring
        subprocess.run(
            [sys.executable, "monitor_proving_ground.py"], cwd=project_root
        )

        print(f"\n{'=' * 60}")
        print("📊 MONITORING COMPLETE")
        print("=" * 60)

        return True

    except KeyboardInterrupt:
        print("\n\n🛑 Proving Ground stopped by user")
        return True

    except Exception as e:
        print(f"\n❌ Launch sequence failed: {e}")
        return False

    finally:
        # Cleanup
        if server_process:
            print("\n🔧 Cleaning up server process...")
            try:
                server_process.terminate()
                server_process.wait(timeout=5)
                print("   ✅ Server stopped gracefully")
            except Exception as e:
                server_process.kill()
                print(f"   ⚠️  Server force-stopped: {e}")


def main():
    """Main execution function."""

    print(
        f"The Proving Ground Launcher - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    try:
        success = launch_proving_ground()

        if success:
            print("\n🎉 THE PROVING GROUND SEQUENCE COMPLETED")
            print("   Kor'tana's autonomous engineering test is now in progress")
            print("   Check the logs and file system for her continued work")

        return success

    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        return False


if __name__ == "__main__":
    success = main()

    if success:
        print("\n📋 NEXT STEPS:")
        print("1. Review Kor'tana's autonomous logs")
        print("2. Examine any files she created or modified")
        print("3. Validate her refactoring work")
        print("4. Analyze her learning and belief formation")
        print("5. Prepare for next autonomous engineering challenge")

    exit(0 if success else 1)
