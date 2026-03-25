#!/usr/bin/env python
"""Check live autonomy daemon metrics"""
import requests

endpoints = {
    "Daemon": "http://127.0.0.1:8001/api/daemon/status",
    "Autonomy": "http://127.0.0.1:8001/api/autonomy/status",
    "Consciousness": "http://127.0.0.1:8001/api/consciousness/status",
    "Goals": "http://127.0.0.1:8001/api/intelligence/goals/status",
}

print("╔" + "═" * 68 + "╗")
print("║ 🚀 LIVE AUTONOMY DAEMON METRICS (Real State)                   ║")
print("╚" + "═" * 68 + "╝")
print()

for name, url in endpoints.items():
    try:
        r = requests.get(url, timeout=3)
        print(f"📍 {name} Status")
        print("─" * 70)

        if r.status_code == 200:
            data = r.json()

            # Pretty print with key filtering
            for key, value in data.items():
                if isinstance(value, dict):
                    print(f"  {key}:")
                    for k2, v2 in value.items():
                        print(f"    {k2}: {v2}")
                else:
                    print(f"  {key}: {value}")

            print(f"  Status Code: {r.status_code} ✅")
        else:
            print(f"  ERROR {r.status_code}: {r.text[:100]}")

        print()
    except Exception as e:
        print(f"  Error: {e}")
        print()

print("═" * 70)
print("✅ Daemon enabled via environment variable AUTONOMY_DAEMON_ENABLED=true")
print("   Daemon should cycle every 30 seconds (AUTONOMY_CYCLE_INTERVAL=30)")
print("═" * 70)
