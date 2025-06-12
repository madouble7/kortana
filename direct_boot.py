#!/usr/bin/env python
"""
More direct debug wrapper for Kor'tana Awakening Protocol
"""

import os
import sys

# Print current working directory
print(f"Current directory: {os.getcwd()}")

# Set Python path to include current directory
sys.path.insert(0, os.getcwd())

try:
    # Import specific components directly
    from kortana_awakening import cinematic_multi_llm_boot_sequence

    print("Successfully imported cinematic_multi_llm_boot_sequence")

    print("Running boot sequence...")
    import asyncio

    asyncio.run(cinematic_multi_llm_boot_sequence())
    print("Boot sequence completed")

except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback

    print("Traceback:")
    traceback.print_exc()
    sys.exit(1)
