#!/usr/bin/env python3
"""
Simple Kor'tana Server Launcher for The Proving Ground
"""

import os
import subprocess
import sys


def launch_server():
    """Launch the Kor'tana server."""

    print("🚀 THE PROVING GROUND: SERVER LAUNCH")
    print("=" * 50)

    # Change to project directory
    project_dir = r"c:\project-kortana"
    os.chdir(project_dir)
    print(f"📁 Working directory: {os.getcwd()}")

    # Launch the server
    print("🔧 Starting Kor'tana server...")
    print("🌐 Server will be available at: http://localhost:8000")
    print("📊 Health check: http://localhost:8000/health")
    print("🎯 Goals API: http://localhost:8000/goals")
    print()
    print("⏳ Starting server... (Press Ctrl+C to stop)")
    print("=" * 50)

    try:
        # Start the server
        subprocess.run([sys.executable, "src/kortana/main.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Ensure you're in the correct directory")
        print("2. Check that virtual environment is activated")
        print("3. Verify all dependencies are installed")


if __name__ == "__main__":
    launch_server()
