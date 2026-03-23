"""
Phase 7 Cycle #4: Advanced Orchestration Router
Exposes meta-task coordination and resource allocation via REST API
"""

from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from src.kortana.logger import log_error, log_request
from src.kortana.services.advanced_orchestration_service import (
    AdvancedOrchestrationService,
    OrchestrationStrategy,
    ResourceType,
)

router = APIRouter()
orchestration_service = AdvancedOrchestrationService()


@router.post("/create", response_model=Dict[str, Any])
async def create_orchestration(
    root_task_id: str,
    child_tasks: list[str],
    dependencies: Dict[str, list[Any]] = {},
    strategy: OrchestrationStrategy = OrchestrationStrategy.PRIORITY_WEIGHTED,
) -> Dict[str, Any]:
    """Create a new orchestration context for meta-task coordination."""
    try:
        context = await orchestration_service.create_orchestration(
            root_task_id=root_task_id,
            child_tasks=child_tasks,
            dependencies=dependencies,
            strategy=strategy,
        )
        log_request(
            "orchestration",
            f"Created orchestration context {context.orchestration_id}",
            root_task_id=root_task_id,
        )
        return {
            "orchestration_id": context.orchestration_id,
            "status": "initialized",
            "strategy": strategy,
        }
    except Exception as e:
        log_error("orchestration", f"Failed to create orchestration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/{orchestration_id}/plan", response_model=Dict[str, Any])
async def create_execution_plan(
    orchestration_id: str, tasks_with_priorities: Dict[str, int] = {}
) -> Dict[str, Any]:
    """Generate a detailed execution plan for an orchestration context."""
    try:
        plan = await orchestration_service.plan_execution(
            orchestration_id, tasks_with_priorities
        )
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Orchestration {orchestration_id} not found",
            )
        return {
            "orchestration_id": orchestration_id,
            "phases": plan.phases,
            "critical_path": plan.critical_path,
            "estimated_duration": plan.estimated_duration,
            "budget_utilization": plan.budget_utilization,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        log_error("orchestration", f"Failed to create execution plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/{orchestration_id}/execute", response_model=Dict[str, Any])
async def execute_orchestration(orchestration_id: str) -> Dict[str, Any]:
    """Execute the coordinated task set for an orchestration."""
    try:
        results = await orchestration_service.execute_orchestration(orchestration_id)
        return {
            "orchestration_id": orchestration_id,
            "status": "completed",
            "results": results,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        log_error("orchestration", f"Execution failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/metrics", response_model=Dict[str, Any])
async def get_orchestration_metrics() -> Dict[str, Any]:
    """Get global orchestration metrics and resource pool status."""
    return {
        "active_orchestrations": len(orchestration_service.active_orchestrations),
        "resource_pools": {
            k.value: v for k, v in orchestration_service.resource_pools.items()
        },
    }
