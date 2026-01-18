import asyncio
import os
import sys

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, "backend")
sys.path.insert(0, backend_dir)

from config import get_settings
from human_only_protocol import HumanOnlyProtocol


async def run_cycle():
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    hop = HumanOnlyProtocol()

    async with async_session() as session:
        print("Synchronizing tasks...")
        await hop.synchronize_tasks(session)

        print("Running autonomous cycle...")
        result = await hop.run_autonomous_cycle(session)
        print(f"Cycle Result: {result}")

        # Check for errors
        from models import Task
        from sqlalchemy import select

        err_result = await session.execute(select(Task).where(Task.status == "failed"))
        errors = err_result.scalars().all()
        if errors:
            print(f"\n❌ Found {len(errors)} tasks with errors:")
            for t in errors:
                print(f"--- {t.title} ---")
                print(f"Error: {t.error}")
        else:
            print("\n✅ No tasks with errors.")


if __name__ == "__main__":
    asyncio.run(run_cycle())
