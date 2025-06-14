#!/usr/bin/env python3
"""
Manual trigger for the proactive code review task
Part of Batch 10: The Proactive Engineer Initiative
"""

import asyncio
import logging
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_proactive_review():
    """Test the proactive code review functionality."""

    try:
        # Import database utilities
        from src.kortana.core.autonomous_tasks import run_proactive_code_review_task
        from src.kortana.services.database import get_db_sync

        logger.info("🚀 BATCH 10: Testing Proactive Engineer Initiative")
        logger.info("🔍 Starting proactive code review task...")

        # Get database session
        db_gen = get_db_sync()
        db = next(db_gen)

        try:
            # Run the proactive code review task
            await run_proactive_code_review_task(db)
            logger.info("✅ Proactive code review completed successfully!")

        finally:
            db.close()

    except Exception as e:
        logger.error(f"❌ Error in proactive code review: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_proactive_review())
