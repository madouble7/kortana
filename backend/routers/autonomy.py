from fastapi import APIRouter, HTTPException, BackgroundTasks
import os
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

router = APIRouter()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = os.getenv("GITHUB_REPO_OWNER", "KOR-TANA")
REPO_NAME = os.getenv("GITHUB_REPO_NAME", "kortana")
KORTANA_BACKEND_URL = os.getenv("KORTANA_BACKEND_URL", "http://localhost:8000")

# In-memory task queue (in production, use database)
task_queue: List[Dict[str, Any]] = []

class AutonomousTaskQueue:
    def __init__(self):
        self.tasks = task_queue

    def queue_from_github_issues(self) -> List[Dict[str, Any]]:
        """Fetch open issues and queue them as autonomous tasks."""
        if not GITHUB_TOKEN:
            raise HTTPException(status_code=500, detail="GitHub token not configured")

        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues?state=open"

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch issues")

        issues = response.json()
        queued_tasks = []

        for issue in issues:
            # Skip pull requests (they have 'pull_request' key)
            if 'pull_request' in issue:
                continue

            task = {
                "id": f"issue-{issue['number']}",
                "type": "github_issue",
                "title": issue["title"],
                "description": issue["body"],
                "github_issue_number": issue["number"],
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "branch_name": f"feature/{issue['number']}-{issue['title'].lower().replace(' ', '-').replace('/', '-').replace(':', '').replace('?', '').replace('!', '')[:50]}",
                "plan": None
            }

            # Check if task already exists
            existing = next((t for t in self.tasks if t["id"] == task["id"]), None)
            if not existing:
                self.tasks.append(task)
                queued_tasks.append(task)

        return queued_tasks

    def generate_task_plan(self, task: Dict[str, Any]) -> str:
        """Use Gemini to generate a plan for the task."""
        prompt = f"""
        Generate a detailed implementation plan for this GitHub issue:

        Title: {task['title']}
        Description: {task['description']}

        Provide a step-by-step plan including:
        1. Technical approach
        2. Files to modify/create
        3. Dependencies needed
        4. Testing strategy
        5. Success criteria

        Keep the plan concise but comprehensive.
        """

        gemini_payload = {"text": prompt}

        try:
            response = requests.post(f"{KORTANA_BACKEND_URL}/api/gemini/analyze", json=gemini_payload)
            if response.status_code == 200:
                result = response.json()
                return result.get("analysis", "Plan generation failed")
            else:
                return "Failed to generate plan via Gemini"
        except requests.RequestException as e:
            return f"Error connecting to Gemini service: {str(e)}"

    def create_branch(self, task: Dict[str, Any]) -> bool:
        """Create a GitHub branch for the task."""
        if not GITHUB_TOKEN:
            return False

        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }

        # Get main branch SHA
        main_ref_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/ref/heads/main"
        main_response = requests.get(main_ref_url, headers=headers)

        if main_response.status_code != 200:
            return False

        main_sha = main_response.json()["object"]["sha"]

        # Create new branch
        branch_data = {
            "ref": f"refs/heads/{task['branch_name']}",
            "sha": main_sha
        }

        create_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/refs"
        create_response = requests.post(create_url, headers=headers, json=branch_data)

        return create_response.status_code == 201

    def execute_task(self, task_id: str, background_tasks: BackgroundTasks) -> Dict[str, Any]:
        """Execute an autonomous task."""
        task = next((t for t in self.tasks if t["id"] == task_id), None)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task["status"] != "pending":
            raise HTTPException(status_code=400, detail="Task not in pending status")

        # Update status
        task["status"] = "in_progress"
        task["started_at"] = datetime.now().isoformat()

        # Generate plan
        task["plan"] = self.generate_task_plan(task)

        # Create branch
        if self.create_branch(task):
            task["branch_created"] = True
        else:
            task["branch_created"] = False
            task["status"] = "failed"
            task["error"] = "Failed to create branch"

        # For now, mark as completed (in production, this would trigger actual development)
        if task["status"] == "in_progress":
            task["status"] = "completed"
            task["completed_at"] = datetime.now().isoformat()

        return task

# Global instance
task_queue_manager = AutonomousTaskQueue()

@router.post("/task-queue")
async def queue_github_tasks() -> Dict[str, Any]:
    """Queue tasks from GitHub issues."""
    try:
        queued_tasks = task_queue_manager.queue_from_github_issues()
        return {
            "message": f"Queued {len(queued_tasks)} new tasks",
            "tasks": queued_tasks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_task_queue_status() -> Dict[str, Any]:
    """Get current task queue status."""
    pending = len([t for t in task_queue_manager.tasks if t["status"] == "pending"])
    in_progress = len([t for t in task_queue_manager.tasks if t["status"] == "in_progress"])
    completed = len([t for t in task_queue_manager.tasks if t["status"] == "completed"])
    failed = len([t for t in task_queue_manager.tasks if t["status"] == "failed"])

    return {
        "total_tasks": len(task_queue_manager.tasks),
        "pending": pending,
        "in_progress": in_progress,
        "completed": completed,
        "failed": failed,
        "tasks": task_queue_manager.tasks[-10:]  # Last 10 tasks
    }

@router.post("/execute/{task_id}")
async def execute_task(task_id: str, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Execute a specific autonomous task."""
    try:
        result = task_queue_manager.execute_task(task_id, background_tasks)
        return {
            "message": "Task execution initiated",
            "task": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/branch-sync")
async def sync_branches() -> Dict[str, Any]:
    """Sync local branches with GitHub (placeholder for future implementation)."""
    return {
        "message": "Branch sync not yet implemented",
        "status": "pending"
    }
