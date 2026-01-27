#!/usr/bin/env python3
"""
Simple Genesis Protocol server - handles all path issues
"""

import os
import sys

# Ensure we're in the right directory and path is set
os.chdir(r"c:\project-kortana")
sys.path.insert(0, r"c:\project-kortana")

print("🚀 GENESIS PROTOCOL - SIMPLE STARTUP")
print("=" * 40)
print(f"Working directory: {os.getcwd()}")
print(f"Python path includes: {sys.path[0]}")

try:
    print("Importing FastAPI app...")
    from kortana.main import app

    print("✅ Import successful!")

    print("Starting server on http://127.0.0.1:8000")
    print("Press Ctrl+C to stop")
    print("=" * 40)

    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info", reload=False)

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Checking if main.py exists...")
    if os.path.exists("src/kortana/main.py"):
        print("✅ main.py found")
    else:
        print("❌ main.py not found")
    input("Press Enter to exit...")

except Exception as e:
    print(f"❌ Startup error: {e}")
    import traceback

    traceback.print_exc()
    input("Press Enter to exit...")
