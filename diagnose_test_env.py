#!/usr/bin/env python
"""Diagnose the test environment."""

import sys
import os

print(f"Python: {sys.executable}")
print(f"Version: {sys.version}")
print(f"CWD: {os.getcwd()}")

# Check key imports
imports_to_check = [
    'pytest',
    'numpy',
    'pydantic',
    'sqlalchemy',
    'dotenv',
    'kortana',
]

for imp in imports_to_check:
    try:
        mod = __import__(imp)
        print(f"✓ {imp}: {getattr(mod, '__version__', 'unknown version')}")
    except Exception as e:
        print(f"✗ {imp}: {e}")

# Try to import kortana config
try:
    from kortana.config import KortanaConfig, get_config
    print("✓ KortanaConfig imported successfully")
except Exception as e:
    print(f"✗ KortanaConfig: {e}")

# Try to import brain
try:
    from kortana.brain import ChatEngine
    print("✓ ChatEngine imported successfully")
except Exception as e:
    print(f"✗ ChatEngine: {e}")
