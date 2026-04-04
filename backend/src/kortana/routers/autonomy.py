import os
from datetime import datetime
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.kortana.config import get_settings
from src.kortana.database import get_db
from src.kortana.logger import setup_logging
from src.kortana.models import GitHubTask

# Import Service and CodeGenerator
from src.kortana.services.github_autonomy_service import GitHubAutonomyService

router = APIRouter()
logger = setup_logging()


# Dependency for service
def get_autonomy_service(db: AsyncSession = Depends(get_db)) -> GitHubAutonomyService:
    """Get GitHub autonomy service instance"""
    return GitHubAutonomyService(db)


@router.post("/task-queue")
async def queue_github_tasks(
    repo: str | None = None,
    service: GitHubAutonomyService = Depends(get_autonomy_service),
) -> dict[str, Any]:
    """Queue tasks from GitHub issues."""
    try:
        queued_tasks = await service.fetch_and_queue_issues(repo)
        return {
            "message": f"Queued {len(queued_tasks)} new tasks",
            "count": len(queued_tasks),
            "tasks": [
                {
                    "id": str(t.id),
                    "issue_number": int(t.github_issue_number),
                    "title": str(t.title),
                    "status": str(t.status),
                    "priority": str(t.priority),
                }
                for t in queued_tasks
            ],
        }
    except Exception as e:
        logger.error(f"Task queueing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_task_queue_status(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Get current task queue status with statistics"""
    # Initialize status counts
    statuses: dict[str, int] = {
        "pending": 0,
        "analyzing": 0,
        "planning": 0,
        "ready_to_execute": 0,
        "executing": 0,
        "completed": 0,
        "failed": 0,
    }

    try:
        # Optimized query: Use GROUP BY to count statuses in single query
        result = await db.execute(
            select(GitHubTask.status, func.count()).group_by(GitHubTask.status)
        )
        status_counts = result.all()

        # Fetch recent tasks in a single query
        recent_tasks_result = await db.execute(
            select(GitHubTask).order_by(GitHubTask.updated_at.desc()).limit(10)
        )
        recent_tasks = recent_tasks_result.scalars().all()
    except SQLAlchemyError as exc:
        logger.warning("Autonomy status unavailable from database: %s", exc)
        status_counts = []
        recent_tasks = []

    # Update status counts from query results
    total = 0
    for status, count in status_counts:
        status_str = str(status)
        if status_str in statuses:
            statuses[status_str] = count
        total += count

    # Calculate completion rate
    completed = statuses["completed"]
    completion_rate = (completed / total * 100) if total > 0 else 0

    return {
        "total_tasks": total,
        "stats": statuses,
        "completion_rate": f"{completion_rate:.1f}%",
        "recent_tasks": [
            {
                "id": str(t.id),
                "issue_number": int(t.github_issue_number),
                "title": str(t.title),
                "status": str(t.status),
                "updated_at": t.updated_at.isoformat() if t.updated_at else None,
            }
            for t in recent_tasks
        ],
    }


@router.post("/analyze/{task_id}")
async def analyze_task_endpoint(
    task_id: str, service: GitHubAutonomyService = Depends(get_autonomy_service)
) -> dict[str, Any]:
    """Analyze a specific task with Gemini"""
    try:
        task = await service.analyze_task(task_id)
        return {
            "message": "Task analysis initiated",
            "task_id": str(task.id),
            "status": str(task.status),
            "analysis": str(task.analysis)[:500] if task.analysis else None,
        }
    except Exception as e:
        logger.error(f"Analysis endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plan/{task_id}")
async def plan_task_endpoint(
    task_id: str, service: GitHubAutonomyService = Depends(get_autonomy_service)
) -> dict[str, Any]:
    """Generate execution plan for a task"""
    try:
        task = await service.plan_task(task_id)
        return {
            "message": "Task plan generated",
            "task_id": str(task.id),
            "status": str(task.status),
            "plan": str(task.plan)[:500] if task.plan else None,
        }
    except Exception as e:
        logger.error(f"Planning endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute/{task_id}")
async def execute_task_endpoint(
    task_id: str,
    dry_run: bool = False,
    service: GitHubAutonomyService = Depends(get_autonomy_service),
) -> dict[str, Any]:
    """Execute a specific autonomous task."""
    try:
        result = await service.execute_task(task_id, dry_run=dry_run)
        return {
            "message": "Task execution completed",
            "task_id": str(result.id),
            "status": str(result.status),
            "error": str(result.error_message) if result.error_message else None,
            "branch": str(result.branch_name) if result.branch_name else None,
        }
    except Exception as e:
        logger.error(f"Execution endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}")
async def get_task_details(
    task_id: str, db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """Get detailed information about a task"""
    result = await db.execute(select(GitHubTask).where(GitHubTask.id == task_id))
    task = result.scalar_one_or_none()
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
        "created_at": task.created_at.isoformat(),
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
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.error_count >= task.max_retries:
        raise HTTPException(
            status_code=400,
            detail=f"Task has exceeded max retries ({task.max_retries})",
        )

    task_record = cast(Any, task)
    task_record.status = "pending"
    task_record.error_message = None
    task_record.updated_at = datetime.utcnow()

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"Retry failed for task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retry task")

    return {"message": "Task reset for retry", "task_id": task_record.id}


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint for autonomy system"""
    return {
        "status": "healthy",
        "service": "autonomy",
        "timestamp": datetime.utcnow().isoformat(),
        "github_configured": bool(
            os.getenv("GITHUB_TOKEN") or get_settings().GITHUB_TOKEN
        ),
        "gemini_configured": bool(
            os.getenv("GEMINI_API_KEY") or get_settings().GEMINI_API_KEY
        ),
    }


@router.get("/actions")
async def get_recent_actions(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Get recent autonomous actions for dashboard"""
    result = await db.execute(
        select(GitHubTask).order_by(GitHubTask.updated_at.desc()).limit(10)
    )
    tasks = result.scalars().all()
    actions = [
        {
            "id": t.id,
            "type": "task_update",
            "message": f"Task {t.id} ({t.title}) moved to {t.status}",
            "status": t.status,
            "timestamp": t.updated_at.isoformat()
            if t.updated_at
            else datetime.utcnow().isoformat(),
        }
        for t in tasks
    ]
    return {"actions": actions}


@router.post("/log")
async def log_autonomy_event(payload: dict[str, Any]) -> dict[str, Any]:
    """Log an event from the autonomy system"""
    logger.info(f"Autonomy Event: {payload}")
    return {"status": "logged"}
