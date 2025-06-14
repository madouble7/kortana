#!/usr/bin/env python
"""
Debug wrapper for Kor'tana Awakening Protocol
"""

import sys
import traceback

try:
    print("Attempting to import kortana_awakening...")
    import kortana_awakening

    print("Successfully imported kortana_awakening")

    print("Running main function...")
    import asyncio

    asyncio.run(kortana_awakening.main())
    print("Main function completed")

except Exception as e:
    print(f"ERROR: {e}")
    print("Traceback:")
    traceback.print_exc()
    sys.exit(1)
