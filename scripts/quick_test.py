import requests

try:
    r = requests.get("http://127.0.0.1:8000/", timeout=5)
    print(f"✅ Server responding! Status: {r.status_code}")
    print(f"Response: {r.text[:100]}...")
except Exception as e:
    print(f"❌ Server not responding: {e}")

try:
    r2 = requests.get("http://127.0.0.1:8000/docs", timeout=5)
    print(f"✅ Docs endpoint: {r2.status_code}")
except Exception as e:
    print(f"❌ Docs endpoint error: {e}")
