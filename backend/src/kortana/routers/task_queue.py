"""
Task Queue Service - Autonomous task management and branch creation
"""

import os
import re
import subprocess
from datetime import datetime

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.kortana.config import get_settings

router = APIRouter()
settings = get_settings()


class Task(BaseModel):
    id: str
    name: str
    description: str | None = None
    status: str = "pending"  # pending, in_progress, completed, failed
    created_at: str | None = None
    branch_name: str | None = None


# In-memory task store
task_queue: dict[str, Task] = {}


def slugify(text: str) -> str:
    """Convert text to slug format for branch names"""
    slug = text.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug


def create_branch(task_id: str, task_name: str) -> str:
    """Create a git branch for a task via GitHub API or local git"""
    # Use evolution/ prefix for concurrent autonomous development
    branch_name = f"evolution/{task_id}-{slugify(task_name)}"

    try:
        # Try to create branch locally first
        subprocess.run(
            ["git", "checkout", "-b", branch_name],
            cwd=settings.REPO_ROOT,
            check=True,
            capture_output=True,
        )

        # Create stub commit with Sacred Lineage metadata
        stub_content = f"""# Task {task_id}: {task_name}
# 🔱 SACRED LINEAGE: {datetime.utcnow().isoformat()}
# Status: Evolution In-Progress

## Description
{task_name}

## Status
- [ ] In Progress
- [ ] Testing
- [ ] Self-Assessment Ready
- [ ] Ready for Sacred Absorption

## Related Issue
{task_id}
"""

        # Write stub file
        stub_file = f".task-stubs/task-{task_id}.md"
        os.makedirs(os.path.dirname(stub_file), exist_ok=True)
        with open(stub_file, "w") as f:
            f.write(stub_content)

        # Commit stub with the Sacred absorption signature
        subprocess.run(
            ["git", "add", stub_file],
            cwd=settings.REPO_ROOT,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                f"evolution: Sacred absorption of task {task_id} - {task_name}",
            ],
            cwd=settings.REPO_ROOT,
            check=True,
            capture_output=True,
        )

        return branch_name
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Failed to create branch: {str(e)}")


def parse_covenant_tasks() -> list[Task]:
    """Parse COVENANT_INDEX.md front-matter to extract tasks"""
    covenant_path = os.path.join(settings.REPO_ROOT, "COVENANT_INDEX.md")

    try:
        with open(covenant_path) as f:
            content = f.read()

        # Extract YAML front-matter
        if content.startswith("---"):
            parts = content.split("---")
            if len(parts) >= 3:
                yaml_content = parts[1]
                data = yaml.safe_load(yaml_content)

                tasks = []
                if "tasks" in data:
                    for idx, task_data in enumerate(data["tasks"]):
                        task = Task(
                            id=task_data.get("id", f"task-{idx}"),
                            name=task_data.get("name", "Unnamed Task"),
                            description=task_data.get("description"),
                            status=task_data.get("status", "pending"),
                            created_at=task_data.get("created_at"),
                        )
                        tasks.append(task)

                return tasks
    except Exception as e:
        print(f"Error parsing covenant: {e}")

    return []


@router.get("/")
async def list_tasks():
    """List all tasks in queue"""
    return {
        "count": len(task_queue),
        "tasks": list(task_queue.values()),
        "covenant_tasks": parse_covenant_tasks(),
    }


@router.post("/queue")
async def queue_task(task: Task):
    """Add a task to the queue"""
    if task.id in task_queue:
        raise HTTPException(status_code=400, detail="Task already exists")

    task.status = "pending"
    task.created_at = datetime.now().isoformat()
    task_queue[task.id] = task

    return {"status": "queued", "task": task}


@router.get("/")
async def list_tasks():
    """List all tasks in the queue"""
    return {"tasks": list(task_queue.values())}


@router.post("/")
async def add_task(payload: dict):
    """Add a new task to the queue"""
    name = payload.get("name")
    description = payload.get("description")
    payload.get("priority", 5)

    if not name:
        raise HTTPException(status_code=400, detail="Missing 'name'")

    task_id = str(len(task_queue) + 1)
    task = Task(
        id=task_id,
        name=name,
        description=description,
        status="pending",
        created_at=datetime.now().isoformat(),
    )
    task_queue[task_id] = task
    return task


@router.delete("/{task_id}")
async def delete_task(task_id: str):
    """Remove a task from the queue"""
    if task_id in task_queue:
        del task_queue[task_id]
        return {"status": "deleted", "task_id": task_id}
    raise HTTPException(status_code=404, detail="Task not found")


@router.post("/create-branch/{task_id}")
async def create_task_branch(task_id: str):
    """Create a git branch for a task"""
    if task_id not in task_queue:
        raise HTTPException(status_code=404, detail="Task not found")

    task = task_queue[task_id]

    try:
        branch_name = create_branch(task_id, task.name)
        task.branch_name = branch_name
        task.status = "in_progress"

        return {
            "status": "branch_created",
            "task_id": task_id,
            "branch": branch_name,
            "message": f"Branch created: {branch_name}",
        }
    except Exception as e:
        task.status = "failed"
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-covenant")
async def sync_from_covenant():
    """Load tasks from COVENANT_INDEX.md and queue them"""
    tasks = parse_covenant_tasks()

    for task in tasks:
        if task.id not in task_queue:
            task_queue[task.id] = task

    return {"status": "synced", "count": len(tasks), "tasks": tasks}


@router.post("/{task_id}/status")
async def update_task_status(task_id: str, payload: dict):
    """Update task status"""
    if task_id not in task_queue:
        raise HTTPException(status_code=404, detail="Task not found")

    new_status = payload.get("status")
    if new_status not in ["pending", "in_progress", "completed", "failed"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    task_queue[task_id].status = new_status

    return {"task_id": task_id, "status": new_status}


@router.get("/{task_id}")
async def get_task(task_id: str):
    """Get a specific task"""
    if task_id not in task_queue:
        raise HTTPException(status_code=404, detail="Task not found")

    return task_queue[task_id]


@router.post("/execute/{task_id}")
async def execute_task(task_id: str):
    """Execute a task (create branch if needed)"""
    if task_id not in task_queue:
        raise HTTPException(status_code=404, detail="Task not found")

    task = task_queue[task_id]

    # If no branch yet, create one
    if not task.branch_name:
        try:
            branch_name = create_branch(task_id, task.name)
            task.branch_name = branch_name
        except Exception as e:
            task.status = "failed"
            raise HTTPException(status_code=500, detail=str(e))

    task.status = "in_progress"

    return {
        "status": "executing",
        "task_id": task_id,
        "branch": task.branch_name,
        "message": f"Task {task_id} is now in progress on branch {task.branch_name}",
    }
