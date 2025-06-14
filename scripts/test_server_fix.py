#!/usr/bin/env python3
"""
Quick server test to verify the main.py fix
"""

import os
import sys
from pathlib import Path

# Set up project root
project_root = Path(r"C:\project-kortana")
os.chdir(project_root)
sys.path.insert(0, str(project_root))


def test_main_import():
    """Test if the main module can be imported without errors."""
    try:
        print("Testing main.py import...")
        from src.kortana.main import app

        print("✅ Main module imported successfully!")
        print(f"✅ App type: {type(app)}")
        print("✅ Server fix confirmed - ready to start!")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


if __name__ == "__main__":
    success = test_main_import()
    if success:
        print("\n🚀 Server is ready to start!")
        print("Run: python -m uvicorn src.kortana.main:app --port 8000 --reload")
    else:
        print("\n❌ Server needs additional fixes")

    exit(0 if success else 1)
