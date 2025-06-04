#!/usr/bin/env python3
"""Test script for covenant rules configuration."""

import sys

sys.path.insert(0, ".")

from config import load_config


def main():
    """Test covenant rules configuration."""
    print("\n=== COVENANT RULES TEST ===")

    settings = load_config()

    print("\nCovenant Rules:")
    print(f"* Has covenant_rules attribute: {hasattr(settings, 'covenant_rules')}")

    if hasattr(settings, "covenant_rules"):
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
