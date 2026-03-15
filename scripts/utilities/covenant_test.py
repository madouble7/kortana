#!/usr/bin/env python3
"""Test script for covenant rules configuration."""

import os
import sys
from typing import Any, Dict

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kortana.config import load_config
from kortana.core.covenant_enforcer import CovenantEnforcer


def validate_covenant_rules(rules: Dict[str, Any]) -> bool:
    """Validate the structure and content of covenant rules."""
    required_keys = ["ethical_principles", "safety_guidelines", "operational_limits"]
    for key in required_keys:
        if key not in rules:
            print(f"❌ Missing required section: {key}")
            return False
    return True


def main() -> bool:
    """Test covenant rules configuration."""
    print("\n=== COVENANT RULES TEST ===")
    try:
        settings = load_config()
        enforcer = CovenantEnforcer(settings=settings)
        print("\nTesting Covenant Rules:")
        rules = enforcer.covenant_rules
        if rules is None or not isinstance(rules, dict):
            print("❌ Invalid covenant rules format")
            return False
        if not rules:
            print("❌ Empty covenant rules")
            return False
        is_valid = validate_covenant_rules(rules)
        if not is_valid:
            return False
        print("✅ Covenant rules validated successfully")
        return True
    except Exception as e:
        print(f"\n❌ Error testing covenant rules: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
        print(f"* covenant_rules is None: {settings.covenant_rules is None}")
        print(f"* covenant_rules type: {type(settings.covenant_rules)}")
        covenant_empty = (
            len(settings.covenant_rules) == 0
            if settings.covenant_rules
            else "N/A (None)"
        )
        print(f"* covenant_rules empty: {covenant_empty}")

    print("\n=== ERROR MESSAGES ===")
    print("covenant.yaml path:", settings.paths.covenant_file_path)


if __name__ == "__main__":
    main()
