#!/usr/bin/env python3
"""
Test script to verify Kor'tana server can start
"""

import os
import sys

# Add src to path so we can import kortana
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from kortana.main import app
    print("✅ Successfully imported Kor'tana FastAPI app")

    # Test the health endpoint
    import asyncio

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/health")
    print(f"✅ Health check response: {response.status_code}")
    print(f"✅ Health check data: {response.json()}")

    # Test the LobeChat adapter endpoint
    test_message = {
        "messages": [
            {"role": "user", "content": "Hello, Kor'tana!"}
        ]
    }

    response = client.post("/adapters/lobechat/chat", json=test_message)
    print(f"✅ LobeChat adapter response: {response.status_code}")
    print(f"✅ LobeChat adapter data: {response.json()}")

    print("\n🚀 Kor'tana server is ready to start!")
    print("Run this command to start the server:")
    print("python src\\kortana\\main.py")
    print("\nOr use uvicorn:")
    print("cd src && python -m uvicorn kortana.main:app --reload --port 8000")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure FastAPI and uvicorn are installed:")
    print("pip install fastapi uvicorn")

except Exception as e:
    print(f"❌ Error testing server: {e}")
