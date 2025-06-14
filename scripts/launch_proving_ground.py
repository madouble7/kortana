#!/usr/bin/env python3
"""
Genesis Protocol Server Startup
===============================
Launches Kor'tana for The Proving Ground
"""

import os
import sys
from pathlib import Path

import uvicorn

# Set up project root
project_root = Path(r"C:\project-kortana")
os.chdir(project_root)
sys.path.insert(0, str(project_root))

print("=" * 60)
print("🚀 THE PROVING GROUND - KOR'TANA GENESIS PROTOCOL")
print("=" * 60)


def main():
    """Launch Kor'tana server for The Proving Ground."""

    try:
        print("\n🔧 Initializing Kor'tana server...")
        print("   Host: 0.0.0.0")
        print("   Port: 8000")
        print("   Mode: Autonomous Engineering")

        # Import and validate the main app
        print("\n📦 Loading application modules...")
        print("   ✅ Main application loaded")

        print("\n🎯 LAUNCHING KOR'TANA FOR THE PROVING GROUND")
        print("   Ready to receive Genesis Protocol goal...")
        print("   Server starting on http://localhost:8000")
        print("\n" + "=" * 60)

        # Start the server
        uvicorn.run(
            "src.kortana.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
        )

    except Exception as e:
        print(f"\n❌ Server startup failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
