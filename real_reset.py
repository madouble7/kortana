import asyncio, sys
sys.path.insert(0, "backend")
from src.kortana.database import get_db_manager
from sqlalchemy import select
from src.kortana.models import GitHubTask

async def run():
    manager=get_db_manager()
    async for db in manager.get_session():
        res = await db.execute(select(GitHubTask).where(GitHubTask.github_issue_number.in_([65, 11000])))
        tasks = res.scalars().all()
        for t in tasks:
            t.status = "pending"
            t.error_message = None
            t.plan = None
            t.analysis = None
        await db.commit()
        print("Done resetting 65 and 11000")
        break

asyncio.run(run())
