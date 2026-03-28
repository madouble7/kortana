#!/usr/bin/env python
"""Launch canonical autonomy stack with daemon enabled."""
import os
import subprocess
import sys

# Set env vars BEFORE starting the process so they're inherited
os.environ["AUTONOMY_DAEMON_ENABLED"] = "true"
os.environ["AUTONOMY_CYCLE_INTERVAL"] = "30"

print("Environment variables set:")
print(f"  AUTONOMY_DAEMON_ENABLED = {os.environ.get('AUTONOMY_DAEMON_ENABLED')}")
print(f"  AUTONOMY_CYCLE_INTERVAL = {os.environ.get('AUTONOMY_CYCLE_INTERVAL')}")
print()
print("Launching uvicorn on port 8003...")
print()

# Launch uvicorn as subprocess with inherited env vars
subprocess.run(
    [
        sys.executable,
        "-m",
        "uvicorn",
        "src.kortana.main:app",
        "--port",
        "8003",
        "--host",
        "127.0.0.1",
    ],
    cwd="backend",
)
