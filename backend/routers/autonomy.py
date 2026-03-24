import json
import os
from datetime import datetime
from typing import Any

import requests
from database import get_db
from fastapi import APIRouter, Depends, HTTPException
from logger import setup_logging
from models import GitHubTask
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Import CodeGenerator from same routers package
from .code_generator import CodeGenerator

router = APIRouter()
logger = setup_logging()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = os.getenv("GITHUB_REPO_OWNER", "KOR-TANA")
REPO_NAME = os.getenv("GITHUB_REPO_NAME", "kortana")
KORTANA_BACKEND_URL = os.getenv("KORTANA_BACKEND_URL", "http://localhost:8000")
MAX_RETRIES = int(os.getenv("TASK_MAX_RETRIES", 3))
RETRY_DELAY_SECONDS = int(os.getenv("TASK_RETRY_DELAY", 300))


class AutonomousTaskQueue:
    """Database-backed autonomous task management"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.code_gen = CodeGenerator()

    def _validate_token(self) -> None:
        """Validate GitHub token is configured"""
        if not GITHUB_TOKEN:
            raise HTTPException(status_code=500, detail="GitHub token not configured")

    async def queue_from_github_issues(
        self, repo: str | None = None
    ) -> list[GitHubTask]:
        """Fetch open issues and queue them as autonomous tasks"""
        self._validate_token()

        owner, name = repo.split("/") if repo else (REPO_OWNER, REPO_NAME)
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        url = f"https://api.github.com/repos/{owner}/{name}/issues?state=open&per_page=100"

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch GitHub issues: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to fetch issues: {str(e)}"
            )

        issues = response.json()
        queued_tasks = []

        for issue in issues:
            # Skip pull requests
            if "pull_request" in issue:
                continue

            # Check if task already exists
            result = await self.db.execute(
                select(GitHubTask).where(
                    GitHubTask.github_issue_number == issue["number"],
                    GitHubTask.github_repo == f"{owner}/{name}",
                )
            )
            existing = result.scalars().first()

            if existing:
                continue

            task = GitHubTask(
                github_issue_number=issue["number"],
                github_repo=f"{owner}/{name}",
                title=issue["title"],
                description=issue.get("body", ""),
                status="pending",
                priority=self._determine_priority(issue),
                branch_name=self._generate_branch_name(issue["number"], issue["title"]),
                estimated_effort="TBD",
            )

            self.db.add(task)
            queued_tasks.append(task)

        try:
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to save queued tasks: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to save tasks")

        return queued_tasks

    def _determine_priority(self, issue: dict[str, Any]) -> str:
        """Determine task priority from issue labels"""
        labels = [label.get("name", "").lower() for label in issue.get("labels", [])]
        if any(lbl in ["critical", "p0", "urgent"] for lbl in labels):
            return "high"
        elif any(lbl in ["p2", "low"] for lbl in labels):
            return "low"
        return "medium"

    def _generate_branch_name(self, issue_num: int, title: str) -> str:
        """Generate safe branch name from issue"""
        safe_title = (
            title.lower()
            .replace(" ", "-")
            .replace("/", "-")
            .replace(":", "-")
            .replace("?", "")
            .replace("!", "")
        )[:50]
        return f"feature/{issue_num}-{safe_title}"

    async def analyze_task(self, task_id: str) -> GitHubTask:
        """Analyze a task using Gemini"""
        result = await self.db.execute(
            select(GitHubTask).where(GitHubTask.id == task_id)
        )
        task = result.scalars().first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task.status not in ["pending"]:
            raise HTTPException(status_code=400, detail=f"Task in {task.status} status")

        task.status = "analyzing"
        task.updated_at = datetime.utcnow()
        await self.db.commit()

        try:
            # Call Gemini analysis
            analysis_prompt = f"""
Analyze this GitHub issue for autonomous development:

Issue: {task.github_repo}#{task.github_issue_number}
Title: {task.title}
Description: {task.description}

Provide:
1. Concise summary
2. Priority assessment
3. Implementation approach
4. Estimated effort
5. Risk factors
6. Success criteria

Format as JSON.
"""
            payload = {"text": analysis_prompt}
            response = requests.post(
                f"{KORTANA_BACKEND_URL}/api/gemini/analyze", json=payload, timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                task.analysis = result.get("analysis", "")  # type: ignore[attr-defined]
            else:
                task.analysis = "Analysis unavailable"

        except Exception as e:
            logger.error(f"Analysis failed for task {task_id}: {str(e)}")
            task.error_message = str(e)
            task.error_count += 1  # type: ignore[operator]
            if task.error_count >= MAX_RETRIES:
                task.status = "failed"
            else:
                task.status = "pending"
            await self.db.commit()
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

        task.status = "planning"
        task.analyzed_at = datetime.utcnow()
        task.updated_at = datetime.utcnow()
        await self.db.commit()

        return task

    async def generate_task_plan(self, task_id: str) -> GitHubTask:
        """Generate execution plan for task"""
        result = await self.db.execute(
            select(GitHubTask).where(GitHubTask.id == task_id)
        )
        task = result.scalars().first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task.status != "planning":
            raise HTTPException(status_code=400, detail="Task not in planning status")

        try:
            prompt = f"""
Generate a detailed implementation plan for:

Issue: {task.github_repo}#{task.github_issue_number}
Title: {task.title}
Analysis: {task.analysis}

Provide:
1. Step-by-step implementation plan
2. Files to create/modify
3. Code changes with FILE_CHANGES section
4. Testing strategy
5. Success validation

Include FILE_CHANGES section with format:
FILE_CHANGES:
- file: path/to/file.py
  action: create|modify|delete
  content: |
    actual code here
"""
            payload = {"text": prompt}
            response = requests.post(
                f"{KORTANA_BACKEND_URL}/api/gemini/analyze", json=payload, timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                task.plan = result.get("analysis", "")  # type: ignore[attr-defined]
            else:
                task.plan = "Plan generation failed"
                raise HTTPException(status_code=500, detail="Failed to generate plan")

        except Exception as e:
            logger.error(f"Plan generation failed for task {task_id}: {str(e)}")
            task.error_message = str(e)
            task.error_count += 1  # type: ignore[operator]
            if task.error_count >= MAX_RETRIES:
                task.status = "failed"
            await self.db.commit()
            raise HTTPException(
                status_code=500, detail=f"Plan generation failed: {str(e)}"
            )

        task.status = "ready_to_execute"
        task.updated_at = datetime.utcnow()
        await self.db.commit()

        return task

    async def execute_task(self, task_id: str, dry_run: bool = False) -> GitHubTask:
        """Execute task (create branch and code)"""
        result = await self.db.execute(
            select(GitHubTask).where(GitHubTask.id == task_id)
        )
        task = result.scalars().first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task.status not in ["ready_to_execute", "pending"]:
            raise HTTPException(status_code=400, detail=f"Task in {task.status} status")

        task.status = "executing"
        task.executed_at = datetime.utcnow()
        await self.db.commit()

        try:
            # Create branch
            if not self._create_branch(task):
                raise Exception("Failed to create branch")

            # Generate code from plan
            if task.plan:
                generation_result = self.code_gen.generate_from_gemini_plan(
                    task.plan, repo_path=".", dry_run=dry_run, validate_syntax=True
                )

                if generation_result.get("errors"):
                    task.error_message = json.dumps(generation_result["errors"])
                    task.error_count += 1  # type: ignore[operator]
                    if task.error_count >= MAX_RETRIES:
                        task.status = "failed"
                    else:
                        task.status = "ready_to_execute"
                    await self.db.commit()
                    raise Exception(
                        f"Code generation errors: {generation_result['errors']}"
                    )

            task.status = "completed"
            task.completed_at = datetime.utcnow()

        except Exception as e:
            logger.error(f"Task execution failed {task_id}: {str(e)}")
            task.error_message = str(e)
            task.error_count += 1  # type: ignore[operator]
            if task.error_count >= MAX_RETRIES:
                task.status = "failed"
            else:
                task.status = "ready_to_execute"

        task.updated_at = datetime.utcnow()
        await self.db.commit()

        return task

    def _create_branch(self, task: GitHubTask) -> bool:
        """Create GitHub branch for task"""
        if not GITHUB_TOKEN:
            return False

        try:
            owner, repo = task.github_repo.split("/")  # type: ignore[union-attr]
            headers = {
                "Authorization": f"token {GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3+json",
            }

            # Get main branch SHA
            ref_url = f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/main"
            ref_response = requests.get(ref_url, headers=headers, timeout=10)

            if ref_response.status_code != 200:
                # Try master branch
                ref_url = (
                    f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/master"
                )
                ref_response = requests.get(ref_url, headers=headers, timeout=10)
                if ref_response.status_code != 200:
                    return False

            main_sha = ref_response.json()["object"]["sha"]

            # Create branch
            branch_data = {"ref": f"refs/heads/{task.branch_name}", "sha": main_sha}

            create_url = f"https://api.github.com/repos/{owner}/{repo}/git/refs"
            create_response = requests.post(
                create_url, headers=headers, json=branch_data, timeout=10
            )

            return create_response.status_code == 201
        except Exception as e:
            logger.error(f"Branch creation failed: {str(e)}")
            return False


# Global database dependency (prefer passing db explicitly)
async def get_task_queue(db: AsyncSession = Depends(get_db)) -> AutonomousTaskQueue:
    """Get task queue instance"""
    return AutonomousTaskQueue(db)


@router.post("/task-queue")
async def queue_github_tasks(
    repo: str | None = None, task_queue: AutonomousTaskQueue = Depends(get_task_queue)
) -> dict[str, Any]:
    """Queue tasks from GitHub issues."""
    try:
        queued_tasks = await task_queue.queue_from_github_issues(repo)
        return {
            "message": f"Queued {len(queued_tasks)} new tasks",
            "count": len(queued_tasks),
            "tasks": [
                {
                    "id": t.id,
                    "issue_number": t.github_issue_number,
                    "title": t.title,
                    "status": t.status,
                    "priority": t.priority,
                }
                for t in queued_tasks
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Task queueing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_task_queue_status(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Get current task queue status with statistics"""
    statuses = {
        "pending": 0,
        "analyzing": 0,
        "planning": 0,
        "ready_to_execute": 0,
        "executing": 0,
        "completed": 0,
        "failed": 0,
    }

    result = await db.execute(select(GitHubTask))
    tasks = result.scalars().all()
    for task in tasks:
        if task.status in statuses:
            statuses[task.status] += 1

    # Calculate completion rate
    total = len(tasks)
    completed = statuses["completed"]
    completion_rate = (completed / total * 100) if total > 0 else 0

    recent_result = await db.execute(
        select(GitHubTask).order_by(GitHubTask.updated_at.desc()).limit(10)
    )
    recent_tasks = recent_result.scalars().all()

    return {
        "total_tasks": total,
        "stats": statuses,
        "completion_rate": f"{completion_rate:.1f}%",
        "recent_tasks": [
            {
                "id": t.id,
                "issue_number": t.github_issue_number,
                "title": t.title,
                "status": t.status,
                "updated_at": t.updated_at.isoformat(),  # type: ignore[union-attr]
            }
            for t in recent_tasks
        ],
    }


@router.post("/analyze/{task_id}")
async def analyze_task_endpoint(
    task_id: str, task_queue: AutonomousTaskQueue = Depends(get_task_queue)
) -> dict[str, Any]:
    """Analyze a specific task with Gemini"""
    try:
        task = await task_queue.analyze_task(task_id)
        return {
            "message": "Task analysis initiated",
            "task_id": task.id,
            "status": task.status,
            "analysis": task.analysis[:500] if task.analysis else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plan/{task_id}")
async def plan_task_endpoint(
    task_id: str, task_queue: AutonomousTaskQueue = Depends(get_task_queue)
) -> dict[str, Any]:
    """Generate execution plan for a task"""
    try:
        task = await task_queue.generate_task_plan(task_id)
        return {
            "message": "Task plan generated",
            "task_id": task.id,
            "status": task.status,
            "plan": task.plan[:500] if task.plan else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Planning endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute/{task_id}")
async def execute_task_endpoint(
    task_id: str,
    dry_run: bool = False,
    task_queue: AutonomousTaskQueue = Depends(get_task_queue),
) -> dict[str, Any]:
    """Execute a specific autonomous task."""
    try:
        result = await task_queue.execute_task(task_id, dry_run=dry_run)
        return {
            "message": "Task execution completed",
            "task_id": result.id,
            "status": result.status,
            "error": result.error_message,
            "branch": result.branch_name,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Execution endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}")
async def get_task_details(
    task_id: str, db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """Get detailed information about a task"""
    result = await db.execute(select(GitHubTask).where(GitHubTask.id == task_id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "id": task.id,
        "github_issue_number": task.github_issue_number,
        "repository": task.github_repo,
        "title": task.title,
        "status": task.status,
        "priority": task.priority,
        "analysis": task.analysis,
        "plan": task.plan,
        "branch_name": task.branch_name,
        "pr_number": task.github_pr_number,
        "error_message": task.error_message,
        "error_count": task.error_count,
        "estimated_effort": task.estimated_effort,
        "created_at": task.created_at.isoformat(),  # type: ignore[union-attr]
        "analyzed_at": task.analyzed_at.isoformat() if task.analyzed_at else None,
        "executed_at": task.executed_at.isoformat() if task.executed_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }


@router.post("/tasks/{task_id}/retry")
async def retry_failed_task(
    task_id: str, db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """Retry a failed task"""
    result = await db.execute(select(GitHubTask).where(GitHubTask.id == task_id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.error_count >= task.max_retries:  # type: ignore[operator]
        raise HTTPException(
            status_code=400,
            detail=f"Task has exceeded max retries ({task.max_retries})",
        )

    task.status = "pending"
    task.error_message = None
    task.updated_at = datetime.utcnow()

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"Retry failed for task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retry task")

    return {"message": "Task reset for retry", "task_id": task.id}


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint for autonomy system"""
    return {
        "status": "healthy",
        "service": "autonomy",
        "timestamp": datetime.utcnow().isoformat(),
        "github_configured": bool(GITHUB_TOKEN),
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
    }
