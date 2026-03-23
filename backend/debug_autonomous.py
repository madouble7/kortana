#!/usr/bin/env python
"""Debug AUTONOMOUS_MODE configuration."""

import os

from src.kortana.config import get_settings

s = get_settings()
print(f"AUTONOMOUS_MODE: {s.AUTONOMOUS_MODE}")
print(f"Type: {type(s.AUTONOMOUS_MODE)}")
print(f"Env var KORTANA_AUTONOMOUS_MODE: {os.getenv('KORTANA_AUTONOMOUS_MODE')}")
