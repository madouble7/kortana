#!/usr/bin/env python3
"""
Simple Genesis Protocol Launcher
================================
Start Kor'tana for The Proving Ground
"""

import os
import sys
from pathlib import Path

# Ensure we're in the right directory
project_root = Path(r"C:\project-kortana")
os.chdir(project_root)
sys.path.insert(0, str(project_root))

print("🚀 STARTING KOR'TANA FOR THE PROVING GROUND")
print("=" * 50)

try:
    print("📦 Loading Kor'tana modules...")
    from kortana.main import app

    print("✅ Main application loaded successfully")

    print("\n🔧 Starting server...")
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)

except Exception as e:
    print(f"❌ Error starting server: {e}")
    import traceback

    traceback.print_exc()
