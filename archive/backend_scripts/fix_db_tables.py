import asyncio
import os
import sys
from pathlib import Path

# Ensure we are running relative to this backend checkout
backend_root = Path(__file__).resolve().parent
os.chdir(backend_root)
sys.path.append(str(backend_root / "src"))

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
