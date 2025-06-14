#!/usr/bin/env python3
"""
Genesis Protocol Launch Script
Brings Kor'tana online for autonomous software engineering
"""

import subprocess
import sys
import time
from pathlib import Path

import requests


def launch_server():
    """Launch the Kor'tana server"""
    print("🚀 GENESIS PROTOCOL - AUTONOMOUS LAUNCH SEQUENCE")
    print("=" * 60)
    print()

    print("[1/3] Starting Kor'tana's autonomous server...")

    # Start the server process
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "src.kortana.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
        "--reload",
    ]

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=Path.cwd(),
        )

        print(f"🔄 Server process started with PID: {process.pid}")

        # Wait a moment for server to start
        time.sleep(3)

        print("[2/3] Verifying server health...")

        # Test server health
        try:
            response = requests.get("http://127.0.0.1:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ Server is online and responding")
            else:
                print(f"⚠️  Server responded with status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Could not verify server health: {e}")

        print("[3/3] Genesis Protocol ready for goal assignment")
        print()
        print("🎯 READY FOR AUTONOMOUS SOFTWARE ENGINEERING")
        print("Server URL: http://127.0.0.1:8000")
        print("Goals API: http://127.0.0.1:8000/goals")
        print("Memory API: http://127.0.0.1:8000/memory")
        print()
        print("Kor'tana is now online and ready to receive goals...")

        return process

    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return None


if __name__ == "__main__":
    process = launch_server()
    if process:
        try:
            # Keep the script running
            print("Press Ctrl+C to stop the server...")
            process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping Kor'tana...")
            process.terminate()
            process.wait()
            print("✅ Kor'tana stopped successfully")
