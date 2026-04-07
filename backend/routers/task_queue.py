"""
Task Queue Service - Autonomous task management and branch creation
"""

import os
import re
import subprocess
from datetime import datetime
from typing import List, Optional

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class Task(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    status: str = "pending"  # pending, in_progress, completed, failed
    created_at: Optional[str] = None
    branch_name: Optional[str] = None


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
    branch_name = f"evolution/{task_id}-{slugify(task_name)}"

    try:
        # Try to create branch locally first
        subprocess.run(
            ["git", "checkout", "-b", branch_name],
            cwd=os.getenv("REPO_ROOT", "."),
            check=True,
            capture_output=True,
        )

        # Create stub commit with Sacred Lineage metadata
        stub_content = f"""# Task {task_id}: {task_name}
# Sacred Evolution Metadata
# Absorption Date: 2026-03-15
# Lineage: GitHub-3.5-Flash -> Canonical Organism

## Description
{task_name}

## Status
- [ ] In Progress
- [ ] Parallel Testing Enabled
- [ ] Ready for Lineage Merge

## Related Issue
{task_id}
"""

        # Write stub file
        stub_file = f".task-stubs/task-{task_id}.md"
        os.makedirs(os.path.dirname(stub_file), exist_ok=True)
        with open(stub_file, "w") as f:
            f.write(stub_content)

        # Commit stub with ritualistic message
        commit_msg = f"sacred: initiation of task {task_id} - {task_name} into lineage"
        subprocess.run(
            ["git", "add", stub_file],
            cwd=os.getenv("REPO_ROOT", "."),
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=os.getenv("REPO_ROOT", "."),
            check=True,
            capture_output=True,
        )

        return branch_name
    except subprocess.CalledProcessError as e:
        # If branch already exists, just return it for parallel work
        if "already exists" in str(e.stderr):
            return branch_name
        raise HTTPException(
            status_code=500, detail=f"Failed to create branch: {str(e)}"
        )


def parse_covenant_tasks() -> List[Task]:
    """Parse COVENANT_INDEX.md front-matter to extract tasks"""
    covenant_path = os.path.join(os.getenv("REPO_ROOT", "."), "COVENANT_INDEX.md")

    try:
        with open(covenant_path, "r") as f:
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
