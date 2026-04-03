import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.kortana.database import get_db
from src.kortana.services.goal_manager import GoalManager

async def fetch_goals():
    try:
        mgr = GoalManager()
        await mgr.load_from_db()
        
        status = mgr.get_status()
        print("\n\n/// KOR'TANA CONSCIOUSNESS STATUS ///")
        print(f"Goal Graph Nodes:      {status['total_goals']}")
        print(f"Executing:             {status['active']}")
        print(f"Blocked dependencies:  {status['blocked']}")
        print(f"Completed nodes:       {status['completed']}")
        print("\n=== CURRENT TOP PRIORITIES ===")
        for i, g in enumerate(status['top_3']):
            print(f"{i+1}. [{g['tier']}] {g['title']} (Progress: {g['progress']}%)")
    except Exception as e:
        print(f"Error reading graph: {e}")

if __name__ == '__main__':
    asyncio.run(fetch_goals())
