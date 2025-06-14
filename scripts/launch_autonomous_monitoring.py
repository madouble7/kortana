#!/usr/bin/env python3
"""
Start Kor'tana's autonomous brain and monitor for activity
"""

import subprocess
import sys
import time

import requests


def start_autonomous_brain():
    """Start the autonomous brain in a separate process"""
    print("🧠 Starting Kor'tana's autonomous brain...")
    try:
        cmd = [sys.executable, "-m", "src.kortana.core.brain", "--autonomous"]
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        return process
    except Exception as e:
        print(f"❌ Error starting brain: {e}")
        return None

def monitor_goal_progress():
    """Monitor the assigned goal for changes"""
    print("📊 Monitoring goal progress...")
    last_status = None

    for i in range(30):  # Monitor for 5 minutes (30 * 10 seconds)
        try:
            response = requests.get("http://127.0.0.1:8000/goals/5", timeout=5)
            if response.status_code == 200:
                goal = response.json()
                current_status = goal['status']

                if current_status != last_status:
                    print(f"[{time.strftime('%H:%M:%S')}] Goal status changed: {current_status}")
                    last_status = current_status

                    if current_status in ['COMPLETED', 'FAILED']:
                        print(f"🎯 Goal finished with status: {current_status}")
                        return current_status

                elif i % 6 == 0:  # Print every minute
                    print(f"[{time.strftime('%H:%M:%S')}] Goal status: {current_status}")

        except Exception as e:
            if i % 12 == 0:  # Print every 2 minutes
                print(f"⚠️ Could not check goal status: {e}")

        time.sleep(10)

    print("⏰ Monitoring timeout reached")
    return None

if __name__ == "__main__":
    print("🚀 KOR'TANA AUTONOMOUS ACTIVATION & MONITORING")
    print("=" * 60)

    # Start the autonomous brain
    brain_process = start_autonomous_brain()

    if brain_process:
        print("✅ Autonomous brain started")
        print("🔍 Now monitoring goal progress...")
        print("💡 The brain should detect the pending goal and begin autonomous work...")
        print()

        try:
            # Monitor goal progress
            final_status = monitor_goal_progress()

            print(f"\n🏁 Final status: {final_status}")

        except KeyboardInterrupt:
            print("\n🛑 Monitoring interrupted by user")
        finally:
            # Clean up the brain process
            if brain_process.poll() is None:
                print("🧠 Stopping autonomous brain...")
                brain_process.terminate()
                try:
                    brain_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    brain_process.kill()
                    print("🔥 Brain process terminated forcefully")
    else:
        print("❌ Could not start autonomous brain")
