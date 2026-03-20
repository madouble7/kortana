
import asyncio
import os
import sys

# Set path to include backend/src
sys.path.append(os.path.join(os.getcwd(), 'backend', 'src'))

from sqlalchemy import text, select
from kortana.database import get_db_manager
from kortana.config import get_settings
from kortana.models import GitHubTask

async def test_db():
    print(f"DATABASE_URL: {get_settings().DATABASE_URL}")
    manager = get_db_manager()
    try:
        await manager.initialize()
        print("Manager initialized")
        
        async with manager.session_factory() as session:
            # Simple query
            res = await session.execute(text("SELECT 1"))
            print(f"SELECT 1 result: {res.scalar()}")
            
            # Model query
            res2 = await session.execute(select(GitHubTask).limit(1))
            print("Successfully queried GitHubTask")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_db())
