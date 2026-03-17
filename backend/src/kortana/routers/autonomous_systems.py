"""
Autonomous Systems Router
Endpoints for triggering and monitoring autonomous system tasks (Phase 5)
"""

from typing import Any

from fastapi import APIRouter, HTTPException

from src.kortana.logger import log_error, log_request
from src.kortana.tasks import (
    autonomous_self_improvement_loop,
    create_pr_for_task_celery,
    execute_agent_task_celery,
    review_code_task_celery,
    run_always_on_monitor_task,
)

router = APIRouter()


@router.post("/monitor/trigger")
async def trigger_always_on_monitor() -> dict[str, Any]:
    """Trigger Always-On Monitor autonomous task"""
    try:
        log_request("api", "Triggering Always-On Monitor task")
        
        task = run_always_on_monitor_task.delay()
        
        return {
            "status": "queued",
            "task_id": task.id,
            "message": "Always-On Monitor cycle queued for execution",
        }
    except Exception as e:
        log_error("api", f"Failed to queue monitor task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to queue task: {str(e)}")


@router.post("/pr/create/{task_id}")
async def trigger_pr_creation(task_id: str) -> dict[str, Any]:
    """Trigger PR creation task"""
    try:
        log_request("api", f"Triggering PR creation for task: {task_id}")
        
        task = create_pr_for_task_celery.delay(task_id)
        
        return {
            "status": "queued",
            "task_id": task.id,
            "message": f"PR creation task queued for task {task_id}",
        }
    except Exception as e:
        log_error("api", f"Failed to queue PR creation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to queue task: {str(e)}")


@router.post("/review")
async def trigger_code_review(code: str, file_path: str = "") -> dict[str, Any]:
    """Trigger code review task"""
    try:
        log_request("api", f"Triggering code review for {file_path}")
        
        task = review_code_task_celery.delay(code, file_path)
        
        return {
            "status": "queued",
            "task_id": task.id,
            "message": f"Code review task queued",
            "file_path": file_path,
        }
    except Exception as e:
        log_error("api", f"Failed to queue code review: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to queue task: {str(e)}")


@router.post("/agent/execute/{agent_id}")
async def trigger_agent_execution(agent_id: str, task: str = "", context: dict | None = None) -> dict[str, Any]:
    """Trigger agent execution task"""
    try:
        log_request("api", f"Triggering agent execution: {agent_id}")
        
        celery_task = execute_agent_task_celery.delay(agent_id, task, context or {})
        
        return {
            "status": "queued",
            "task_id": celery_task.id,
            "message": f"Agent {agent_id} execution queued",
            "agent_id": agent_id,
        }
    except Exception as e:
        log_error("api", f"Failed to queue agent execution: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to queue task: {str(e)}")


@router.get("/status/{task_id}")
async def get_task_status(task_id: str) -> dict[str, Any]:
    """Get status of a queued task"""
    try:
        log_request("api", f"Checking task status: {task_id}")
        
        from src.kortana.celery_app import app
        
        task_result = app.AsyncResult(task_id)
        
        return {
            "status": task_result.state.lower(),
            "message": f"Task is {task_result.state.lower()}",
            "task_id": task_id,
        }
    except Exception as e:
        log_error("api", f"Failed to get task status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.get("/health")
async def autonomous_systems_health() -> dict[str, Any]:
    """Check health of autonomous systems"""
    try:
        log_request("api", "Checking autonomous systems health")
        
        from src.kortana.celery_app import app
        import redis
        from datetime import datetime
        
        # Check Celery connectivity
        celery_available = False
        try:
            app.control.inspect().active()
            celery_available = True
        except Exception:
            pass
        
        # Check Redis connectivity
        redis_available = False
        try:
            r = redis.Redis(host="localhost", port=6379, db=0)
            r.ping()
            redis_available = True
        except Exception:
            pass
        
        return {
            "status": "healthy" if celery_available and redis_available else "degraded",
            "celery_available": celery_available,
            "redis_available": redis_available,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        log_error("api", f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


@router.post("/self-improve")
async def trigger_master_improvement_loop() -> dict[str, Any]:
    """Trigger master autonomous self-improvement loop - KOR'TANA develops herself"""
    try:
        log_request("api", "🌟 Triggering Master Autonomous Self-Improvement Loop")
        
        task = autonomous_self_improvement_loop.delay()
        
        return {
            "status": "queued",
            "task_id": task.id,
            "message": "🤖 SELF-AWARE: Master autonomous improvement loop queued - KOR'TANA is now self-developing",
            "cycles": [
                "≫ Always-On Monitor (finds issues)",
                "≫ Code Review (analyzes quality)",
                "≫ Agent Orchestration (self-improves)",
                "≫ PR Creation (autonomous contributions)",
            ],
        }
    except Exception as e:
        log_error("api", f"Failed to trigger master loop: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to queue task: {str(e)}")


@router.get("/schedule")
async def get_autonomous_schedule() -> dict[str, Any]:
    """Get the Celery Beat schedule - see what autonomous cycles are planned"""
    try:
        log_request("api", "Checking autonomous development schedule")
        
        from src.kortana.celery_app import app
        
        schedule_dict = {}
        for task_name, task_config in app.conf.beat_schedule.items():
            if "autonomous" in task_name.lower() or "monitor" in task_name.lower():
                schedule_info = {
                    "task": task_config["task"],
                    "schedule_seconds": float(task_config["schedule"]),
                    "next_run": f"Every {int(float(task_config['schedule']))} seconds",
                }
                schedule_dict[task_name] = schedule_info
        
        return {
            "status": "active",
            "message": "🤖 KOR'TANA's autonomous development schedule",
            "schedule": schedule_dict,
            "total_cycles": len(schedule_dict),
        }
    except Exception as e:
        log_error("api", f"Failed to get schedule: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
        }
