import asyncio
import os
import sys

# Ensure we are in the right directory
os.chdir(r"C:\KOR-TANA\kortana\backend")
sys.path.append("src")

from kortana.database import get_db_manager
from kortana.models import Base


async def run():
    print("Initializng Database Manager...")
    m = get_db_manager()
    await m.initialize()
    print(f"Engine: {m.engine.url}")
    async with m.engine.begin() as conn:
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
    print("TABLES_READY")


if __name__ == "__main__":
    asyncio.run(run())
