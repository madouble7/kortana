#!/usr/bin/env python
"""Direct test launcher using subprocess"""

import os
import subprocess
import sys

os.chdir(r"c:\kortana")

# Direct command - no activation needed
cmd = [
    r"c:\kortana\.kortana_config_test_env\Scripts\python.exe",
    "-m",
    "pytest",
    "tests/",
    "-v",
    "--tb=short",
]

env = os.environ.copy()
env["PYTHONPATH"] = r"c:\kortana\src"
env["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

print("=" * 70)
print("KOR'TANA TEST SUITE")
print("=" * 70)
print(f"Command: {' '.join(cmd)}")
print(f"PYTHONPATH: {env['PYTHONPATH']}")
print("=" * 70 + "\n")

result = subprocess.run(cmd, env=env)
sys.exit(result.returncode)
