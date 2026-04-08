#!/usr/bin/env python3
"""Restart the daemon to reload fixed HTTP client code"""

import time

import requests

base_url = "http://127.0.0.1:9001"

print("Stopping daemon...")
response = requests.post(f"{base_url}/api/daemon/stop", timeout=5)
if response.status_code == 200:
    print(f"✓ Daemon stopped: {response.json()['status']}")
else:
    print(f"❌ Failed to stop daemon: {response.status_code}")

# Wait a moment for graceful shutdown
time.sleep(2)

print("\nStarting daemon with fixed HTTP client...")
response = requests.post(f"{base_url}/api/daemon/start", timeout=5)
if response.status_code == 200:
    data = response.json()
    print(f"✓ Daemon started: {data['status']}")
    print(f"  Uptime: {data.get('uptime_start')}")
    print("  Cycle interval: ~600 seconds")
    print("  Ready to process issue #11000 on next cycle")
else:
    print(f"❌ Failed to start daemon: {response.status_code}")

print("\n" + "=" * 70)
print("Next steps:")
print("  1. Daemon is restarted with FIXED HTTP client code")
print("  2. Issue #11000 is RESET and ready for processing")
print("  3. Next daemon cycle (~10 minutes) will execute the fixed pipeline")
print("  4. Monitor with: python check_11000_uuid.py")
print("=" * 70)
