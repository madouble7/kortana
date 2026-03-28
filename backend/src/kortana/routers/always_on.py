"""
Always-On Autonomous Development Router
REST API endpoints for the always-on monitoring system
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from src.kortana.database import get_db_manager
from src.kortana.logger import get_logger
from src.kortana.models import GitHubTask
from src.kortana.services.always_on_monitor import (
    get_always_on_monitor,
    start_always_on_monitor,
    stop_always_on_monitor,
)
from src.kortana.services.autonomy_daemon import get_autonomy_daemon
from src.kortana.services.autonomy_loop_bridge_service import AutonomyLoopBridgeService
from src.kortana.services.operator_directive_service import OperatorDirectiveService
from src.kortana.services.task_approval_service import TaskApprovalService
from src.kortana.services.workspace_bridge_service import get_workspace_bridge

router = APIRouter()
logger = get_logger(__name__)


class DirectiveRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)
    directive_type: str | None = Field(default=None, max_length=32)
    priority: int = Field(default=50, ge=1, le=100)
    source: str = Field(default="user", max_length=64)
    scope: str = Field(default="global", max_length=64)


class CommentRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)
    priority: int = Field(default=50, ge=1, le=100)


def _refresh_daemon_guidance(summary: Any) -> Dict[str, Any]:
    daemon = get_autonomy_daemon()
    daemon._apply_operator_guidance(summary)
    return {
        "running": daemon.get_status().get("running"),
        "control_mode": daemon.get_status().get("control_mode"),
        "safe_mode": daemon.get_status().get("safe_mode"),
        "live_execution_enabled": daemon.get_status().get("live_execution_enabled"),
        "max_tasks_per_cycle": daemon.get_status().get("max_tasks_per_cycle"),
        "system_state": daemon.get_status().get("system_state"),
    }


def _serialize_task(task: GitHubTask | None) -> Dict[str, Any]:
    if task is None:
        return {
            "id": None,
            "github_issue_number": None,
            "title": None,
            "status": None,
            "classification": None,
            "priority": None,
            "branch_name": None,
            "commit_sha": None,
            "github_pr_number": None,
            "code_changes": None,
            "error_message": None,
            "validation_report": None,
            "validation_summary": TaskApprovalService.summarize_validation(None),
            "sandbox_result": None,
            "created_at": None,
            "updated_at": None,
        }

    return {
        "id": str(task.id),
        "github_issue_number": task.github_issue_number,
        "title": str(task.title),
        "status": str(task.status),
        "classification": str(task.classification) if task.classification else None,
        "priority": str(task.priority) if task.priority else None,
        "branch_name": str(task.branch_name) if task.branch_name else None,
        "commit_sha": str(task.commit_sha) if task.commit_sha else None,
        "github_pr_number": task.github_pr_number,
        "code_changes": task.code_changes,
        "error_message": task.error_message,
        "validation_report": task.validation_report,
        "validation_summary": TaskApprovalService.summarize_validation(task),
        "sandbox_result": task.sandbox_result,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }


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
        raise HTTPException(
            status_code=500, detail=f"Failed to start monitoring: {str(e)}"
        )


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
        raise HTTPException(
            status_code=500, detail=f"Failed to stop monitoring: {str(e)}"
        )


@router.get("/status")
async def get_monitoring_status() -> Dict[str, Any]:
    """Get current monitoring system status"""
    try:
        monitor = get_always_on_monitor()
        return monitor.get_status()
    except Exception as e:
        logger.error(f"Failed to get monitoring status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.post("/comment")
async def create_operator_comment(body: CommentRequest) -> Dict[str, Any]:
    """Record a steering comment for the always-on daemon."""
    try:
        service = OperatorDirectiveService()
        directive = await service.create_directive(
            content=body.content,
            directive_type="comment",
            priority=body.priority,
            source="comment",
        )
        summary = await service.get_active_summary()
        daemon_state = _refresh_daemon_guidance(summary)
        return {
            "message": "Operator comment recorded",
            "directive": service.serialize(directive),
            "summary": {
                "protocol_version": summary.protocol_version,
                "pause_requested": summary.pause_requested,
                "focus_topics": summary.focus_topics,
                "avoid_topics": summary.avoid_topics,
                "max_tasks_override": summary.max_tasks_override,
                "execution_mode": summary.execution_mode,
                "approval_mode": summary.approval_mode,
                "approval_required": summary.approval_required,
                "handoff_rules": summary.handoff_rules,
                "override_mode": summary.override_mode,
                "active_count": summary.active_count,
            },
            "daemon": daemon_state,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to record operator comment: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to record comment: {str(e)}"
        )


@router.post("/prompt")
async def create_operator_prompt(body: CommentRequest) -> Dict[str, Any]:
    """Alias for operator steering input from IDE/chat surfaces."""
    return await create_operator_comment(body)


@router.post("/directives")
async def create_operator_directive(body: DirectiveRequest) -> Dict[str, Any]:
    """Create a persistent operator directive for the always-on daemon."""
    try:
        service = OperatorDirectiveService()
        directive = await service.create_directive(
            content=body.content,
            directive_type=body.directive_type,
            priority=body.priority,
            source=body.source,
            scope=body.scope,
        )
        summary = await service.get_active_summary()
        daemon_state = _refresh_daemon_guidance(summary)
        return {
            "message": "Operator directive recorded",
            "directive": service.serialize(directive),
            "summary": {
                "protocol_version": summary.protocol_version,
                "pause_requested": summary.pause_requested,
                "focus_topics": summary.focus_topics,
                "avoid_topics": summary.avoid_topics,
                "max_tasks_override": summary.max_tasks_override,
                "execution_mode": summary.execution_mode,
                "approval_mode": summary.approval_mode,
                "approval_required": summary.approval_required,
                "handoff_rules": summary.handoff_rules,
                "override_mode": summary.override_mode,
                "active_count": summary.active_count,
            },
            "daemon": daemon_state,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to create operator directive: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create directive: {str(e)}"
        )


@router.get("/directives")
async def list_operator_directives(
    status: str | None = "active", limit: int = 20
) -> Dict[str, Any]:
    """List operator directives and the current merged guidance."""
    try:
        service = OperatorDirectiveService()
        directives = await service.list_directives(status=status, limit=limit)
        summary = await service.get_active_summary()
        return {
            "directives": [service.serialize(item) for item in directives],
            "summary": {
                "protocol_version": summary.protocol_version,
                "pause_requested": summary.pause_requested,
                "focus_topics": summary.focus_topics,
                "avoid_topics": summary.avoid_topics,
                "max_tasks_override": summary.max_tasks_override,
                "execution_mode": summary.execution_mode,
                "approval_mode": summary.approval_mode,
                "approval_required": summary.approval_required,
                "handoff_rules": summary.handoff_rules,
                "override_mode": summary.override_mode,
                "active_count": summary.active_count,
                "prompt_preamble": summary.prompt_preamble,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to list operator directives: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list directives: {str(e)}"
        )


@router.get("/course")
async def get_operator_course() -> Dict[str, Any]:
    """Return the merged course state that guides always-on work."""
    try:
        service = OperatorDirectiveService()
        summary = await service.get_active_summary()
        daemon = get_autonomy_daemon().get_status()
        return {
            "summary": {
                "protocol_version": summary.protocol_version,
                "pause_requested": summary.pause_requested,
                "focus_topics": summary.focus_topics,
                "avoid_topics": summary.avoid_topics,
                "max_tasks_override": summary.max_tasks_override,
                "execution_mode": summary.execution_mode,
                "approval_mode": summary.approval_mode,
                "approval_required": summary.approval_required,
                "handoff_rules": summary.handoff_rules,
                "override_mode": summary.override_mode,
                "active_count": summary.active_count,
                "notes": summary.notes,
                "prompt_preamble": summary.prompt_preamble,
            },
            "daemon": {
                "running": daemon.get("running"),
                "control_mode": daemon.get("control_mode"),
                "safe_mode": daemon.get("safe_mode"),
                "live_execution_enabled": daemon.get("live_execution_enabled"),
                "max_tasks_per_cycle": daemon.get("max_tasks_per_cycle"),
                "system_state": daemon.get("system_state"),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get operator course: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get course: {str(e)}")


@router.get("/protocol")
async def get_operator_protocol() -> Dict[str, Any]:
    """Return the explicit operator protocol for always-on steering."""
    try:
        return {
            "protocol": OperatorDirectiveService.protocol_spec(),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get operator protocol: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get protocol: {str(e)}")


@router.post("/directives/{directive_id}/resolve")
async def resolve_operator_directive(directive_id: str) -> Dict[str, Any]:
    """Resolve an operator directive once it is no longer relevant."""
    try:
        service = OperatorDirectiveService()
        directive = await service.resolve_directive(directive_id)
        if directive is None:
            raise HTTPException(status_code=404, detail="Directive not found")
        summary = await service.get_active_summary()
        daemon_state = _refresh_daemon_guidance(summary)
        return {
            "message": "Operator directive resolved",
            "directive": service.serialize(directive),
            "summary": {
                "protocol_version": summary.protocol_version,
                "pause_requested": summary.pause_requested,
                "focus_topics": summary.focus_topics,
                "avoid_topics": summary.avoid_topics,
                "max_tasks_override": summary.max_tasks_override,
                "execution_mode": summary.execution_mode,
                "approval_mode": summary.approval_mode,
                "approval_required": summary.approval_required,
                "handoff_rules": summary.handoff_rules,
                "override_mode": summary.override_mode,
                "active_count": summary.active_count,
            },
            "daemon": daemon_state,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resolve operator directive: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to resolve directive: {str(e)}"
        )


@router.get("/workspace")
async def get_workspace_status() -> Dict[str, Any]:
    """Return local workspace bridge status for the always-on daemon."""
    try:
        bridge = get_workspace_bridge()
        status = await bridge.poll()
        return {
            "workspace": status,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get workspace status: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get workspace status: {str(e)}"
        )


@router.get("/tasks/status")
async def get_task_status() -> Dict[str, Any]:
    """Get current task status across all stages"""
    try:
        monitor = get_always_on_monitor()
        return await monitor.get_task_status()
    except Exception as e:
        logger.error(f"Failed to get task status: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get task status: {str(e)}"
        )


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
        async with db_manager.session_scope() as db:
            result = await db.execute(
                select(GitHubTask).order_by(GitHubTask.updated_at.desc()).limit(limit)
            )
            tasks = result.scalars().all()

            return [_serialize_task(task) for task in tasks]
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
        async with db_manager.session_scope() as db:
            result = await db.execute(
                select(GitHubTask).filter(GitHubTask.id == task_id)
            )
            task = result.scalar_one_or_none()
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")

            # Reset task status for retry
            task.status = "pending"
            task.error_message = None
            task.updated_at = datetime.utcnow()

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
        async with db_manager.session_scope() as db:
            result = await db.execute(
                select(GitHubTask).order_by(GitHubTask.updated_at.desc()).limit(limit)
            )
            tasks = result.scalars().all()

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
async def approve_task(
    task_id: str, approved: bool, notes: str | None = None
) -> Dict[str, Any]:
    """Approve or reject a task requiring human oversight"""
    try:
        db_manager = get_db_manager()
        async with db_manager.session_scope() as db:
            service = TaskApprovalService(db)
            try:
                task = await service.approve_task(
                    task_id,
                    approved=approved,
                    reviewer="operator",
                    notes=notes,
                )
            except ValueError as exc:
                message = str(exc)
                if message == "Task not found":
                    raise HTTPException(status_code=404, detail=message) from exc
                raise HTTPException(status_code=400, detail=message) from exc

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


@router.get("/approval-queue")
async def get_approval_queue(limit: int = 20) -> Dict[str, Any]:
    """List tasks currently waiting in the approval queue."""
    try:
        db_manager = get_db_manager()
        async with db_manager.session_scope() as db:
            service = TaskApprovalService(db)
            approvals = await service.list_pending(limit=limit)

            task_ids = [approval.github_task_id for approval in approvals]
            tasks_by_id: Dict[str, GitHubTask] = {}
            if task_ids:
                result = await db.execute(
                    select(GitHubTask).where(GitHubTask.id.in_(task_ids))
                )
                tasks_by_id = {str(task.id): task for task in result.scalars().all()}

            items = []
            for approval in approvals:
                task = tasks_by_id.get(approval.github_task_id)
                task_payload = _serialize_task(task)
                if task is None:
                    task_payload["id"] = approval.github_task_id
                items.append(
                    {
                        **service.serialize(approval),
                        "task": task_payload,
                    }
                )

            return {
                "items": items,
                "count": len(items),
                "timestamp": datetime.utcnow().isoformat(),
            }
    except Exception as e:
        logger.error(f"Failed to get approval queue: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get approval queue: {str(e)}"
        )


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
        raise HTTPException(
            status_code=500, detail=f"Failed to get dashboard: {str(e)}"
        )

@router.post("/sandbox/dry-run")
async def execute_dry_run_sandbox(task_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes an explicitly isolated dry-run cycle of a task within the Autonomy Loop Sandbox.
    Will never mutate the repository, write to the production database, or perform network merges.
    Used purely for diagnostic verification of the agent bridge.
    """
    try:
        if "id" not in task_payload or "description" not in task_payload:
            raise HTTPException(
                status_code=400,
                detail="Invalid Task format. Requires at least 'id' and 'description'.",
            )
        result = await asyncio.to_thread(
            AutonomyLoopBridgeService.run_dry_run, task_payload
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Exception invoking sandbox bridge directly: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed bridging task to sandbox: {e}"
        )
