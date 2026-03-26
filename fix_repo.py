import asyncio, sys
sys.path.insert(0, "backend")
from src.kortana.database import get_db_manager
from sqlalchemy import select
from src.kortana.models import GitHubTask

async def run():
    manager=get_db_manager()
    async for db in manager.get_session():
        res = await db.execute(select(GitHubTask).where(GitHubTask.github_issue_number.in_([65, 11000])))
        for task in res.scalars():
            task.github_repo = "madouble7/kortana"
        await db.commit()
        print("Updated to madouble7!")
        break

asyncio.run(run())
