#!/usr/bin/env python3
"""
🔧 VENV311 VERIFICATION & PYTHON PATH TEST
This script verifies that we're using the correct Python environment
"""

import os
import sys
from pathlib import Path


def main():
    print("🔧 VENV311 ENVIRONMENT DIAGNOSTIC")
    print("=" * 50)

    print(f"🐍 Python executable: {sys.executable}")
    print(f"🐍 Python version: {sys.version}")
    print(f"📁 Current directory: {os.getcwd()}")
    print(f"📁 Script location: {Path(__file__).parent.absolute()}")

    # Check if we're in venv311
    if "venv311" in sys.executable:
        print("✅ USING VENV311 - CORRECT!")
    else:
        print("❌ NOT USING VENV311 - PROBLEM!")
        print("🔧 Please activate venv311:")
        print("   c:\\kortana\\venv311\\Scripts\\activate.bat")

    # Check for virtual environment
    if hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    ):
        print("✅ Virtual environment detected")
        print(f"📍 Virtual env prefix: {sys.prefix}")
    else:
        print("❌ No virtual environment detected")

    # Check environment variables
    venv = os.environ.get("VIRTUAL_ENV")
    if venv:
        print(f"✅ VIRTUAL_ENV: {venv}")
    else:
        print("❌ VIRTUAL_ENV not set")

    # Test basic package availability
    print("\n📦 Testing package imports:")

    try:
        import json

        print("✅ json - builtin module")
    except ImportError:
        print("❌ json - MISSING")

    try:
        import requests

        print("✅ requests - external package")
    except ImportError:
        print("❌ requests - MISSING (run: pip install requests)")

    print("\n🎯 RECOMMENDATION:")
    if "venv311" in sys.executable:
        print("✅ Environment is correct - ready for development!")
    else:
        print("🔧 Fix steps:")
        print("1. Close current terminal")
        print("2. Open new terminal in VS Code")
        print("3. Run: c:\\kortana\\venv311\\Scripts\\activate.bat")
        print("4. Verify with: python test-venv.py")


if __name__ == "__main__":
    main()
