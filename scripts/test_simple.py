"""
Very simple test to check if covenant.yaml is properly loaded.
"""

import sys
from pathlib import Path

# Add current dir to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    print("Importing config module...")
    from kortana.config import load_config

    print("Loading configuration...")
    config = load_config()

    print(f"Config loaded. Environment: {config.app.environment}")

    if hasattr(config, "covenant_rules"):
        print(f"covenant_rules exists: {bool(config.covenant_rules)}")
        if config.covenant_rules:
            print(
                f"Covenant version: {config.covenant_rules.get('covenant_version', 'Not found')}"
            )
            print("SUCCESS: covenant.yaml was loaded into settings.covenant_rules")
        else:
            print("ERROR: covenant_rules exists but is empty")
    else:
        print("ERROR: covenant_rules attribute not found on config object")

except Exception as e:
    print(f"ERROR: {str(e)}")
    import traceback

    traceback.print_exc()
