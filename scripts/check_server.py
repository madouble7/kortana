#!/usr/bin/env python3
"""
Quick server status check
"""

import requests

try:
    response = requests.get('http://localhost:8000/docs', timeout=3)
    print(f"✅ Backend server is running! Status: {response.status_code}")
    print("🌐 Available at: http://localhost:8000")
    print("📚 API docs at: http://localhost:8000/docs")
except Exception as e:
    print(f"❌ Backend server not responding: {e}")
    print("🔧 You may need to start it manually with:")
    print("   python -m uvicorn src.kortana.main:app --host 0.0.0.0 --port 8000")
