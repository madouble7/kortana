#!/usr/bin/env python
"""Check live autonomy daemon metrics without overstating the result."""

from __future__ import annotations

import os
from typing import Any

import requests

BASE_URL = os.getenv("KORTANA_BASE_URL", "http://127.0.0.1:8001")
TIMEOUT_SECONDS = 3

ENDPOINTS = {
    "Daemon": f"{BASE_URL}/api/daemon/status",
    "Autonomy": f"{BASE_URL}/api/autonomy/status",
    "Consciousness": f"{BASE_URL}/api/consciousness/status",
    "Goals": f"{BASE_URL}/api/intelligence/goals/status",
}


def print_mapping(data: dict[str, Any], indent: str = "  ") -> None:
    for key, value in data.items():
        if isinstance(value, dict):
            print(f"{indent}{key}:")
            print_mapping(value, indent + "  ")
        else:
            print(f"{indent}{key}: {value}")


print("=" * 70)
print("LIVE AUTONOMY / CONSCIOUSNESS METRICS")
print("=" * 70)
print()

daemon_data: dict[str, Any] | None = None

for name, url in ENDPOINTS.items():
    try:
        response = requests.get(url, timeout=TIMEOUT_SECONDS)
        print(f"{name}: {url}")
        print("-" * 70)

        if response.status_code != 200:
            print(f"  ERROR {response.status_code}: {response.text[:160]}")
            print()
            continue

        data = response.json()
        if name == "Daemon":
            daemon_data = data

        print_mapping(data)
        print(f"  status_code: {response.status_code}")
        print()
    except Exception as exc:
        print(f"{name}: {url}")
        print("-" * 70)
        print(f"  error: {exc}")
        print()

print("=" * 70)
if daemon_data is None:
    print("Daemon summary unavailable: /api/daemon/status did not return 200.")
elif daemon_data.get("running"):
    print(
        "Daemon is running."
        f" enabled={daemon_data.get('enabled')},"
        f" cycle_interval_seconds={daemon_data.get('cycle_interval_seconds')}"
    )
elif daemon_data.get("enabled"):
    print(
        "Daemon is enabled but currently idle/stopped."
        f" cycle_interval_seconds={daemon_data.get('cycle_interval_seconds')}"
    )
else:
    print(
        "Daemon is disabled in the live process."
        f" cycle_interval_seconds={daemon_data.get('cycle_interval_seconds')}"
    )
    print(
        "Start the canonical stack with AUTONOMY_DAEMON_ENABLED=true in the same"
        " process that launches uvicorn if you want background cycles."
    )
print("=" * 70)
