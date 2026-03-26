import asyncio, os, sys
sys.path.insert(0, "backend")
from src.kortana.database import get_db_manager
from sqlalchemy import select
from src.kortana.models import GitHubTask
async def run():
    manager=get_db_manager()
    async for db in manager.get_session():
        res=await db.execute(select(GitHubTask).where(GitHubTask.github_issue_number==65))
        task=res.scalar_one_or_none()
        if task:
            task.status="pending"; task.error_message=None; await db.commit()
            print("Issue 65 reset to pending.")
asyncio.run(run())
