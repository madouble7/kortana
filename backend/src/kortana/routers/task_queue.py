import logging
import re
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException

from src.kortana.circuit_breaker import create_circuit_breaker
from src.kortana.config import get_settings
from src.kortana.distributed_lock import create_task_lock_manager
from src.kortana.schemas import Task, TaskCreate, TaskStatus

router = APIRouter(prefix="/api/tasks", tags=["tasks"])
logger = logging.getLogger("kortana.tasks")
settings = get_settings()

_task_breaker = create_circuit_breaker(settings.INTERNAL_REDIS_URL)
_task_lock = create_task_lock_manager(settings.INTERNAL_REDIS_URL)

_tasks_db: dict[str, dict] = {}


def slugify(text: str) -> str:
    slug = text.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


@router.get("/", response_model=List[Task])
async def list_tasks():
    return [Task.model_validate(t) for t in _tasks_db.values()]


@router.post("/", response_model=Task)
async def create_task(task_in: TaskCreate):
    task_id = str(uuid.uuid4())[:8]

    async def _git_provision():
        return f"evolution/{task_id}-{slugify(task_in.name)}"

    try:
        branch_name = await _task_breaker.call_async(
            f"git_branch_{task_id}", _git_provision
        )
        new_task = {
            "id": task_id,
            "name": task_in.name,
            "description": task_in.description,
            "classification": task_in.classification,
            "status": TaskStatus.PENDING,
            "command": task_in.command,
            "created_at": datetime.utcnow(),
            "completed_at": None,
        }
        _tasks_db[task_id] = new_task
        return Task.model_validate(new_task)
    except Exception as e:
        logger.error(f"Task creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
