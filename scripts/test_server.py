#!/usr/bin/env python3
"""
Simple test script to diagnose import issues
"""
import os
import sys

# Add the project root to Python path
project_root = r"c:\project-kortana"
sys.path.insert(0, project_root)
os.chdir(project_root)

print("Python path set up successfully")
print(f"Current directory: {os.getcwd()}")
print(f"Python path: {sys.path[:3]}")

try:
    print("Testing basic imports...")
    from src.kortana.main import app
    print("✅ FastAPI app imported successfully!")

    print("Testing uvicorn...")
    import uvicorn
    print("✅ Uvicorn imported successfully!")

    print("Starting server...")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Other error: {e}")
    import traceback
    traceback.print_exc()
