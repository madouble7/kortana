#!/usr/bin/env python3
"""
Quick Genesis Protocol server startup test
"""

import os
import sys

# Set up paths
project_root = r"c:\project-kortana"
sys.path.insert(0, project_root)
os.chdir(project_root)

print("🚀 Testing Genesis Protocol Server Startup")
print("=" * 50)

try:
    print("Testing basic import...")
    from kortana.main import app

    print("✅ FastAPI app imported successfully!")

    print("Starting uvicorn server...")
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
        reload=False,  # Disable reload to avoid import issues
    )

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
    input("Press Enter to continue...")
