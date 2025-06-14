#!/usr/bin/env python3
"""
Quick API Key Test
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

print("=== QUICK API KEY TEST ===")

try:
    from config import load_config

    settings = load_config()
    print(f"✓ Configuration loaded: {type(settings)}")
    print(f"✓ api_keys: {type(settings.api_keys)}")

    if settings.api_keys:
        print(f"✓ openai key: '{settings.api_keys.openai}'")
        print(f"✓ anthropic key: '{settings.api_keys.anthropic}'")

        # Test get_api_key method
        openai_key = settings.get_api_key("openai")
        print(f"✓ get_api_key('openai'): '{openai_key}'")

        # Test boolean evaluation
        print(f"✓ bool(openai_key): {bool(openai_key)}")
        print(f"✓ not openai_key: {not openai_key}")

    else:
        print("❌ api_keys is None or False")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()

print("=== TEST COMPLETE ===")
