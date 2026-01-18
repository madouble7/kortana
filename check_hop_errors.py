import asyncio
import os
import sys

# Add backend to path
backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
sys.path.insert(0, backend_path)

from database import DatabaseManager
from models import Task
from sqlalchemy import select


async def check_task_errors():
    db_manager = DatabaseManager()
    async for session in db_manager.get_session():
        result = await session.execute(select(Task).where(Task.error != None))
        tasks = result.scalars().all()

        print(f"Found {len(tasks)} tasks with errors:")
        for t in tasks:
            print(f"--- Task: {t.title} ({t.id}) ---")
            print(f"Error: {t.error}")
            print(f"Result: {t.result}")
            print("-" * 40)


if __name__ == "__main__":
    asyncio.run(check_task_errors())
