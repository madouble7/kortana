import sys

import requests


def validate_deployment(base_url):
    print(f"🚀 Starting Kor'tana Post-Deployment Validation on: {base_url}")
    print("-" * 60)

    # 1. API Health Check
    try:
        res = requests.get(f"{base_url}/api/health")
        if res.status_code == 200 and res.json().get("status") == "alive":
            print("✅ [API] Health Check: SUCCESS")
        else:
            print(f"❌ [API] Health Check: FAILED (Status: {res.status_code})")
    except Exception as e:
        print(f"❌ [API] Health Check: EXCEPTION ({e})")

    # 2. Static Asset Availability
    try:
        # Try fetching a known icon
        res = requests.get(f"{base_url}/icon-192.png")
        if res.status_code == 200:
            print("✅ [Assets] Static Icon Access: SUCCESS")
        else:
            print(f"❌ [Assets] Static Icon Access: FAILED (Status: {res.status_code})")
    except Exception as e:
        print(f"❌ [Assets] Static Icon Access: EXCEPTION ({e})")

    # 3. PWA Manifest & Service Worker
    try:
        res_m = requests.get(f"{base_url}/manifest.json")
        res_s = requests.get(f"{base_url}/sw.js")
        if res_m.status_code == 200 and res_s.status_code == 200:
            print("✅ [PWA] Manifest and SW: SUCCESS")
        else:
            print(
                f"❌ [PWA] Manifest/SW: FAILED ({res_m.status_code}/{res_s.status_code})"
            )
    except Exception as e:
        print(f"❌ [PWA] Manifest/SW: EXCEPTION ({e})")

    # 4. API Route Smoke Test
    try:
        res = requests.get(f"{base_url}/api/system/info")
        if res.status_code in [200, 401]:  # 401 is fine if auth is active
            print("✅ [API] Route Smoke Test: SUCCESS")
        else:
            print(f"❌ [API] Route Smoke Test: FAILED (Status: {res.status_code})")
    except Exception as e:
        print(f"❌ [API] Route Smoke Test: EXCEPTION ({e})")

    # 5. SPA Routing Test (Frontend routes return index.html)
    try:
        res = requests.get(f"{base_url}/vision")
        # In a unified build, this should return index.html (containing <!DOCTYPE html>)
        if res.status_code == 200 and "<!DOCTYPE html>" in res.text:
            print("✅ [SPA] Catch-all Routing: SUCCESS")
        else:
            print(f"❌ [SPA] Catch-all Routing: FAILED (Status: {res.status_code})")
    except Exception as e:
        print(f"❌ [SPA] Catch-all Routing: EXCEPTION ({e})")

    print("-" * 60)
    print("Validation Complete.")


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    validate_deployment(url)
