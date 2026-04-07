#!/usr/bin/env python
"""Quick autonomy status check"""
import json
import time

import requests

time.sleep(3)
print("\n" + "=" * 60)
print("KOR'TANA Autonomy System Status Check")
print("=" * 60 + "\n")

try:
    # Check backend health
    response = requests.get("http://localhost:8000/api/autonomy/health", timeout=5)
    if response.status_code == 200:
        print("STATUS: Backend Online ✅\n")
        data = response.json()
        print(json.dumps(data, indent=2))
        print("\n" + "=" * 60)
        print("AUTONOMOUS CYCLES ACTIVE:")
        print("=" * 60)
        print("- Health Check: Every 2 minutes")
        print("- Monitor: Every 5 minutes")
        print("- Code Review: Every 10 minutes")
        print("- Agent Cycle: Every 15 minutes")
        print("- Self-Improvement: Every 20 minutes")
        print("- System Monitor: Every 30 minutes")
        print("\n" + "=" * 60)
        print("Watching for autonomous activity...")
        print("=" * 60 + "\n")

        # Try to get dashboard
        dashboard = requests.get(
            "http://localhost:8000/api/autonomy/monitor/dashboard", timeout=5
        )
        if dashboard.status_code == 200:
            dash_data = dashboard.json()
            print("\nDASHBOARD DATA:")
            print(json.dumps(dash_data, indent=2))
    else:
        print(f"Status Code: {response.status_code}")
except requests.exceptions.ConnectionError as e:
    print("❌ Cannot connect to backend at localhost:8000")
    print(f"Error: {str(e)[:100]}")
except Exception as e:
    print(f"⚠️  Error: {str(e)}")
