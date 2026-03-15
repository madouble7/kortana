#!/usr/bin/env python3
"""
Simple proactive code review trigger
"""

import asyncio
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath("."))

from src.kortana.core.autonomous_tasks import run_proactive_code_review_task
from src.kortana.services.database import get_db_sync


async def main():
    print("🔍 Running proactive code review...")
    db_gen = get_db_sync()
    db = next(db_gen)
    try:
        await run_proactive_code_review_task(db)
        print("✅ Proactive review completed!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
