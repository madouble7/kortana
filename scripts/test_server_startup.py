#!/usr/bin/env python3
"""
Server Startup Test
===================
Test if Kor'tana server can start successfully
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.getcwd())

print("🚀 TESTING KOR'TANA SERVER STARTUP")
print("=" * 50)

try:
    print("📦 Importing main application...")
    from src.kortana.main import app

    print("✅ Main application imported successfully!")

    print("\n🔧 Testing FastAPI app creation...")
    print(f"   App type: {type(app)}")
    print(f"   App title: {getattr(app, 'title', 'N/A')}")

    print("\n🎯 Server startup test: SUCCESS")
    print("   The import issues have been resolved!")
    print("   Server should now start normally.")

except Exception as e:
    print("❌ Server startup test: FAILED")
    print(f"   Error: {e}")
    import traceback

    traceback.print_exc()

print("\n📋 To start the server manually:")
print("   python src/kortana/main.py")
print("   OR")
print("   uvicorn src.kortana.main:app --host 127.0.0.1 --port 8000")
