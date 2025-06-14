#!/usr/bin/env python3
"""
Debug Configuration Loading
Test the configuration loading step by step to identify the api_keys issue.
"""

import sys
import traceback
from pathlib import Path

# Add src to path if needed
project_root = Path(__file__).parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

print("=== DEBUGGING CONFIGURATION LOADING ===")

print("\n1. Testing YAML loading...")
try:
    import yaml

    config_path = project_root / "config" / "default.yaml"
    print(f"Loading: {config_path}")

    with open(config_path) as f:
        raw_yaml = yaml.safe_load(f)

    print("Raw YAML loaded successfully")
    print(f"api_keys in YAML: {raw_yaml.get('api_keys', 'NOT FOUND')}")
    print(f"api_keys type: {type(raw_yaml.get('api_keys'))}")

except Exception as e:
    print(f"YAML loading failed: {e}")
    traceback.print_exc()

print("\n2. Testing load_config() function...")
try:
    from config import load_config

    print("Calling load_config()...")
    settings = load_config()

    print(f"Settings loaded: {type(settings)}")
    print(f"settings.api_keys: {settings.api_keys}")
    print(f"settings.api_keys type: {type(settings.api_keys)}")

    if settings.api_keys:
        print(f"settings.api_keys.openai: {settings.api_keys.openai}")
    else:
        print("api_keys is None!")

except Exception as e:
    print(f"load_config() failed: {e}")
    traceback.print_exc()

print("\n3. Testing manual KortanaConfig creation...")
try:
    from config.schema import KortanaConfig

    # Create manually with api_keys dict
    test_config = {
        "api_keys": {
            "openai": "sk-test-key-for-validation-only",
            "anthropic": "test-anthropic-key",
        },
        "default_llm_id": "gpt-4",
    }

    print("Creating KortanaConfig manually...")
    manual_config = KortanaConfig(**test_config)

    print(f"Manual config created: {type(manual_config)}")
    print(f"manual_config.api_keys: {manual_config.api_keys}")
    print(f"manual_config.api_keys type: {type(manual_config.api_keys)}")

    if manual_config.api_keys:
        print(f"manual_config.api_keys.openai: {manual_config.api_keys.openai}")

except Exception as e:
    print(f"Manual config creation failed: {e}")
    traceback.print_exc()

print("\n=== DEBUG COMPLETE ===")
