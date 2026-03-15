#!/usr/bin/env python
"""
Simple script to test covenant rules loading
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    # Import the config module
    from kortana.config import load_config

    # Load the config
    print("Loading configuration...")
    settings = load_config()
    print(f"Configuration loaded successfully! Type: {type(settings).__name__}")

    # Check for covenant_rules
    if hasattr(settings, "covenant_rules"):
        print("\n✅ settings.covenant_rules attribute exists")

        if settings.covenant_rules:
            print("✅ covenant_rules has content")
            print(
                f"Covenant version: {settings.covenant_rules.get('covenant_version', 'Not found')}"
            )

            # Print first few keys to keep output manageable
            print("\nCovenant rules keys:")
            for i, key in enumerate(settings.covenant_rules.keys()):
                print(f"  - {key}")
                if i >= 10:
                    print(f"  - ... and {len(settings.covenant_rules) - 10} more keys")
                    break

            # Check for critical sections we expect
            critical_sections = [
                "sacred_principles",
                "protected_files",
                "human_approval_required",
                "operational_boundaries",
            ]

            print("\nChecking for critical covenant sections:")
            for section in critical_sections:
                print(
                    f"  - {section}: {'✅ Found' if section in settings.covenant_rules else '❌ Missing'}"
                )
        else:
            print("❌ settings.covenant_rules exists but is empty/None")
    else:
        print("❌ settings object has no covenant_rules attribute")
        print(f"Available attributes on settings: {dir(settings)}")

except Exception as e:
    print(f"Error testing covenant loading: {str(e)}")
    import traceback

    traceback.print_exc()
