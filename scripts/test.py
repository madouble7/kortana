#!/usr/bin/env python3
import os
import httpx

BACKEND_URL = os.getenv("KORTANA_BACKEND_URL", "http://localhost:8000")
resp = httpx.get(f"{BACKEND_URL}/api/consciousness/memory/self", params={"limit": 5})
print(resp.json())
