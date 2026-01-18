import asyncio
import os
import sys

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, "backend")
sys.path.insert(0, backend_dir)

from config import get_settings
from models import Task


async def reset():
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("Resetting tasks...")
        await session.execute(
            update(Task)
            .where(Task.status.in_(["in_progress", "failed"]))
            .values(status="pending", error=None)
        )
        await session.commit()
        print("Done.")


if __name__ == "__main__":
    asyncio.run(reset())
