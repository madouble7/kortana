import asyncio

from src.kortana.core.autonomous_tasks import run_performance_analysis_task
from src.kortana.services.database import get_db_sync


async def main():
    print("--- Manually triggering the Self-Reflection & Performance Analysis task ---")
    db_session = next(get_db_sync())
    await run_performance_analysis_task(db_session)
    print("--- Trigger script finished ---")

if __name__ == "__main__":
    asyncio.run(main())
