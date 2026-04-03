"""One-time script: backfill embeddings for SelfMemory rows where embedding IS NULL.

Run from the backend directory:
    python scripts/backfill_embeddings.py

Requires GEMINI_API_KEY and DATABASE_URL to be set in the environment (or .env).
"""

import asyncio
import logging
import sys
from pathlib import Path

# Ensure src is importable when running from the backend directory
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402
from src.kortana.database import db_manager  # noqa: E402
from src.kortana.models import SelfMemory  # noqa: E402
from src.kortana.services.gemini import gemini_service  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def backfill() -> None:
    await db_manager.initialize()

    async for session in db_manager.get_session():
        stmt = select(SelfMemory).where(SelfMemory.embedding.is_(None))
        result = await session.execute(stmt)
        rows: list[SelfMemory] = list(result.scalars().all())

        if not rows:
            logger.info("No SelfMemory rows need backfilling.")
            return

        logger.info("Found %d rows to backfill.", len(rows))
        updated = 0
        skipped = 0

        for row in rows:
            if not row.summary:
                logger.debug("Row %s has no summary — skipping.", row.id)
                skipped += 1
                continue

            embedding = gemini_service.embed_text(row.summary)
            if embedding is None:
                logger.warning(
                    "embed_text returned None for row %s — skipping.", row.id
                )
                skipped += 1
                continue

            row.embedding = embedding
            session.add(row)
            updated += 1
            logger.info(
                "  [%d/%d] Embedded row %s", updated, len(rows) - skipped, row.id
            )

        await session.commit()
        logger.info("Backfill complete: %d updated, %d skipped.", updated, skipped)


if __name__ == "__main__":
    asyncio.run(backfill())
