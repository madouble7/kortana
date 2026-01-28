"""
Always-On Autonomous Development Router
REST API endpoints for the always-on monitoring system
"""

from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from src.kortana.database import get_db_manager
from src.kortana.logger import get_logger
from src.kortana.models import GitHubTask
from src.kortana.services.always_on_monitor import (
    get_always_on_monitor,
    start_always_on_monitor,
    stop_always_on_monitor,
)

router = APIRouter()
logger = get_logger(__name__)


@router.post("/start")
async def start_monitoring() -> Dict[str, Any]:
    """Start the always-on monitoring system in the background"""
    try:
        import asyncio

        from src.kortana.services.always_on_monitor import get_always_on_monitor

        monitor = get_always_on_monitor()
        if monitor.is_running:
            return {
                "message": "Always-on monitoring is already running",
                "status": "running",
                "timestamp": datetime.utcnow().isoformat(),
            }

        # Start in background using asyncio.create_task
        # This allows the request to return immediately
        asyncio.create_task(start_always_on_monitor())

        return {
            "message": "Always-on monitoring start initiated in background",
            "status": "starting",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to initiate monitoring start: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start monitoring: {str(e)}")


@router.post("/stop")
async def stop_monitoring() -> Dict[str, Any]:
    """Stop the always-on monitoring system"""
    try:
        stop_always_on_monitor()
        return {
            "message": "Always-on monitoring stopped successfully",
            "status": "stopped",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to stop monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to stop monitoring: {str(e)}")


@router.get("/status")
async def get_monitoring_status() -> Dict[str, Any]:
    """Get current monitoring system status"""
    try:
        monitor = get_always_on_monitor()
        return monitor.get_status()
    except Exception as e:
        logger.error(f"Failed to get monitoring status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.get("/tasks/status")
async def get_task_status() -> Dict[str, Any]:
    """Get current task status across all stages"""
    try:
        monitor = get_always_on_monitor()
        return await monitor.get_task_status()
    except Exception as e:
        logger.error(f"Failed to get task status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")


@router.post("/force-check")
async def force_monitoring_check() -> Dict[str, Any]:
    """Force an immediate monitoring cycle"""
    try:
        monitor = get_always_on_monitor()
        result = await monitor.force_check()
        return {
            "message": "Forced monitoring check completed",
            "result": result,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to force monitoring check: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to force check: {str(e)}")


@router.get("/tasks")
async def get_recent_tasks(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent tasks for monitoring dashboard"""
    try:
        db_manager = get_db_manager()
        async with db_manager.get_session() as db:
            tasks = db.query(GitHubTask).order_by(GitHubTask.updated_at.desc()).limit(limit).all()

            return [
                {
                    "id": str(task.id),
                    "github_issue_number": int(task.github_issue_number),
                    "title": str(task.title),
                    "status": str(task.status),
                    "classification": str(task.classification) if task.classification else None,
                    "priority": str(task.priority) if task.priority else None,
                    "branch_name": str(task.branch_name) if task.branch_name else None,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "updated_at": task.updated_at.isoformat() if task.updated_at else None,
                }
                for task in tasks
            ]
    except Exception as e:
        logger.error(f"Failed to get recent tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get tasks: {str(e)}")


@router.get("/health")
async def monitoring_health_check() -> Dict[str, Any]:
    """Health check for the monitoring system"""
    try:
        monitor = get_always_on_monitor()
        status = monitor.get_status()

        return {
            "status": "healthy" if status["is_running"] else "stopped",
            "monitoring_enabled": status["monitoring_enabled"],
            "is_running": status["is_running"],
            "tasks_processed": status["statistics"]["tasks_processed"],
            "tasks_completed": status["statistics"]["tasks_completed"],
            "human_interventions": status["statistics"]["human_interventions"],
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


@router.post("/tasks/{task_id}/retry")
async def retry_task(task_id: str) -> Dict[str, Any]:
    """Retry a failed task"""
    try:
        db_manager = get_db_manager()
        async with db_manager.get_session() as db:
            task = db.query(GitHubTask).filter(GitHubTask.id == task_id).first()
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")

            # Reset task status for retry
            task.status = "pending"
            task.error_message = None
            task.updated_at = datetime.utcnow()

            await db.commit()

            return {
                "message": f"Task {task_id} reset for retry",
                "task_id": task_id,
                "status": "pending",
                "timestamp": datetime.utcnow().isoformat(),
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retry task: {str(e)}")


@router.get("/actions")
async def get_monitoring_actions(limit: int = 20) -> List[Dict[str, Any]]:
    """Get recent monitoring actions for dashboard"""
    try:
        db_manager = get_db_manager()
        async with db_manager.get_session() as db:
            tasks = db.query(GitHubTask).order_by(GitHubTask.updated_at.desc()).limit(limit).all()

            actions = []
            for task in tasks:
                actions.append(
                    {
                        "id": str(task.id),
                        "type": "task_update",
                        "message": f"Task {task.id} ({task.title}) moved to {task.status}",
                        "status": str(task.status),
                        "timestamp": task.updated_at.isoformat()
                        if task.updated_at
                        else datetime.utcnow().isoformat(),
                    }
                )

            return actions
    except Exception as e:
        logger.error(f"Failed to get monitoring actions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get actions: {str(e)}")


@router.post("/log")
async def log_monitoring_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Log an event from the monitoring system"""
    try:
        logger.info(f"Monitoring Event: {payload}")
        return {
            "status": "logged",
            "event": payload,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to log monitoring event: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to log event: {str(e)}")


@router.get("/metrics")
async def get_monitoring_metrics() -> Dict[str, Any]:
    """Get monitoring system metrics"""
    try:
        monitor = get_always_on_monitor()
        status = monitor.get_status()

        return {
            "monitoring": {
                "enabled": status["monitoring_enabled"],
                "running": status["is_running"],
                "check_interval": status["check_interval"],
                "max_concurrent_tasks": status["max_concurrent_tasks"],
            },
            "tasks": status["statistics"],
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get monitoring metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.post("/tasks/{task_id}/approve")
async def approve_task(task_id: str, approved: bool, notes: str | None = None) -> Dict[str, Any]:
    """Approve or reject a task requiring human oversight"""
    try:
        db_manager = get_db_manager()
        async with db_manager.get_session() as db:
            task = db.query(GitHubTask).filter(GitHubTask.id == task_id).first()
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")

            if task.status != "waiting_for_ho":
                raise HTTPException(
                    status_code=400,
                    detail=f"Task is not awaiting approval (status: {task.status})",
                )

            if approved:
                task.status = "pending"  # Ready for execution
                task.classification = "auto"  # Upgrade to auto after approval
            else:
                task.status = "cancelled"

            # Store approval metadata
            if not task.metadata_json:
                task.metadata_json = {}

            task.metadata_json["approval"] = {
                "approved": approved,
                "notes": notes,
                "timestamp": datetime.utcnow().isoformat(),
            }

            task.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(task)

            return {
                "message": f"Task {task_id} {'approved' if approved else 'rejected'}",
                "task_id": task_id,
                "status": task.status,
                "approved": approved,
                "timestamp": datetime.utcnow().isoformat(),
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to approve task: {str(e)}")


@router.get("/dashboard")
async def get_monitoring_dashboard() -> Dict[str, Any]:
    """Get comprehensive monitoring dashboard data"""
    try:
        monitor = get_always_on_monitor()
        status = monitor.get_status()
        task_status = await monitor.get_task_status()

        return {
            "monitor": status,
            "tasks": task_status,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get monitoring dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard: {str(e)}")
