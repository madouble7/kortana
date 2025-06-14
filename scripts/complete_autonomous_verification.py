#!/usr/bin/env python3
"""
Complete Autonomous Verification System
Launches Kor'tana with comprehensive monitoring across all four channels
"""

import os
import subprocess
import sys
import time
from datetime import datetime

import requests


class AutonomousVerificationSystem:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.processes = {}
        self.start_time = datetime.now()

    def check_server_running(self) -> bool:
        """Check if the server is already running"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=3)
            return response.status_code == 200
        except Exception:
            return False

    def start_server(self):
        """Start the FastAPI server"""
        print("🚀 Starting Kor'tana FastAPI Server...")

        if self.check_server_running():
            print("✅ Server already running")
            return

        # Start server
        server_cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "src.kortana.main:app",
            "--reload",
            "--port",
            "8000",
        ]

        try:
            self.processes["server"] = subprocess.Popen(
                server_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                cwd=os.getcwd(),
            )

            # Wait for server to start
            print("⏳ Waiting for server to initialize...")
            for i in range(30):  # 30 second timeout
                if self.check_server_running():
                    print("✅ Server running successfully")
                    return
                time.sleep(1)

            print("❌ Server failed to start within 30 seconds")

        except Exception as e:
            print(f"❌ Failed to start server: {e}")

    def start_monitoring(self):
        """Start all monitoring processes"""
        print("\n📊 Starting Monitoring Systems...")

        # Monitor 1: API/Database Activity
        print("   🔄 Starting API/Database Monitor...")
        try:
            self.processes["api_monitor"] = subprocess.Popen(
                [sys.executable, "monitor_autonomous_activity_new.py"]
            )
            print("   ✅ API Monitor started")
        except Exception as e:
            print(f"   ❌ API Monitor failed: {e}")

        # Monitor 2: File System Changes
        print("   📁 Starting File System Monitor...")
        try:
            self.processes["file_monitor"] = subprocess.Popen(
                [sys.executable, "file_system_monitor.py"]
            )
            print("   ✅ File System Monitor started")
        except Exception as e:
            print(f"   ❌ File System Monitor failed: {e}")

        # Monitor 3: Learning/Memory Activity
        print("   🧠 Starting Learning/Memory Monitor...")
        try:
            self.processes["memory_monitor"] = subprocess.Popen(
                [sys.executable, "memory_verification.py"]
            )
            print("   ✅ Learning Monitor started")
        except Exception as e:
            print(f"   ❌ Learning Monitor failed: {e}")

    def submit_genesis_goal(self):
        """Submit the Genesis Protocol goal"""
        print("\n🎯 Submitting Genesis Protocol Goal...")

        try:
            subprocess.run([sys.executable, "initiate_proving_ground.py"], check=True)
            print("✅ Genesis goal submitted successfully")
        except Exception as e:
            print(f"❌ Failed to submit goal: {e}")

    def print_dashboard(self):
        """Print the main verification dashboard"""
        runtime = datetime.now() - self.start_time

        print(f"\n{'=' * 80}")
        print("🤖 KOR'TANA AUTONOMOUS VERIFICATION DASHBOARD")
        print(f"⏱️  Runtime: {runtime}")
        print(f"🌐 Server: {self.base_url}")
        print(f"{'=' * 80}")

        # Check process status
        print("\n📊 MONITORING SYSTEMS STATUS:")
        for name, process in self.processes.items():
            if process and process.poll() is None:
                print(f"   ✅ {name.replace('_', ' ').title()}: RUNNING")
            else:
                print(f"   ❌ {name.replace('_', ' ').title()}: STOPPED")

        # Check server health
        if self.check_server_running():
            print("\n💚 SERVER STATUS: OPERATIONAL")

            # Try to get some basic stats
            try:
                # Check for active goals
                goals_response = requests.get(f"{self.base_url}/goals/")
                if goals_response.status_code == 200:
                    goals = goals_response.json()
                    active_goals = [
                        g
                        for g in goals
                        if g.get("status") not in ["COMPLETED", "FAILED"]
                    ]
                    print(f"🎯 Active Goals: {len(active_goals)}")

                # Check for recent memories
                memories_response = requests.get(f"{self.base_url}/memories/?limit=10")
                if memories_response.status_code == 200:
                    memories = memories_response.json()
                    core_beliefs = [
                        m for m in memories if m.get("memory_type") == "CORE_BELIEF"
                    ]
                    print(f"🧠 Recent CORE_BELIEF Memories: {len(core_beliefs)}")

            except Exception as e:
                print(f"⚠️  Could not fetch stats: {e}")
        else:
            print("\n❌ SERVER STATUS: NOT ACCESSIBLE")

        print(f"\n{'=' * 80}")

    def cleanup(self):
        """Clean up all processes"""
        print("\n🧹 Cleaning up processes...")

        for name, process in self.processes.items():
            if process and process.poll() is None:
                print(f"   🛑 Stopping {name}")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()

    def run_verification_system(self):
        """Run the complete verification system"""
        print("🚀 LAUNCHING KOR'TANA AUTONOMOUS VERIFICATION SYSTEM")
        print("=" * 60)

        try:
            # Step 1: Start server
            self.start_server()

            # Step 2: Start monitoring
            self.start_monitoring()

            # Step 3: Submit goal
            self.submit_genesis_goal()

            # Step 4: Run dashboard
            print("\n📊 Starting Real-Time Dashboard...")
            print("Press Ctrl+C to stop all monitoring and exit")

            while True:
                self.print_dashboard()

                print("\n🔍 AUTONOMOUS ACTIVITY EVIDENCE TO LOOK FOR:")
                print("   ✅ Goal status changes in API Monitor")
                print("   ✅ New files appearing in File System Monitor")
                print("   ✅ CORE_BELIEF formation in Learning Monitor")
                print("   ✅ Task execution logs in server output")
                print("\n⏳ Next update in 30 seconds...")

                time.sleep(30)

        except KeyboardInterrupt:
            print("\n\n🛑 Autonomous verification stopped by user")
        finally:
            self.cleanup()
            runtime = datetime.now() - self.start_time
            print(f"\n📊 Total verification time: {runtime}")
            print("👋 Verification system shutdown complete")


def main():
    """Main entry point"""
    print("🤖 Kor'tana Autonomous Verification System")
    print("=" * 50)
    print("This system will:")
    print("1. 🚀 Start the FastAPI server")
    print("2. 📊 Launch comprehensive monitoring")
    print("3. 🎯 Submit the Genesis Protocol goal")
    print("4. 👀 Provide real-time verification dashboard")
    print("=" * 50)

    input("Press Enter to begin autonomous verification...")

    verifier = AutonomousVerificationSystem()
    verifier.run_verification_system()


if __name__ == "__main__":
    main()
