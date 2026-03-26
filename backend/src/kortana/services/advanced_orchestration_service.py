"""
In-memory orchestration service for meta-task coordination.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.kortana.database import get_db_manager
from src.kortana.logger import log_error, log_request


class ResourceType(str, Enum):
    CPU = "cpu"
    MEMORY = "memory"
    NETWORK = "network"
    API_CALLS = "api_calls"
    DISK_IO = "disk_io"


class OrchestrationStrategy(str, Enum):
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    LAYERED = "layered"
    PRIORITY_WEIGHTED = "priority_weighted"
    BUDGET_AWARE = "budget_aware"


@dataclass
class ResourceAllocation:
    task_id: str
    resource_type: ResourceType
    allocated_amount: float
    priority_level: int
    is_critical: bool = False
    can_preempt: bool = False


@dataclass
class TaskDependency:
    task_id: str
    depends_on: str
    dependency_type: str = "finish_before_start"
    is_blocking: bool = True


@dataclass
class OrchestrationContext:
    orchestration_id: str
    root_task_id: str
    child_tasks: list[str] = field(default_factory=list)
    dependencies: dict[str, list[TaskDependency]] = field(default_factory=dict)
    resource_budget: dict[ResourceType, float] = field(default_factory=dict)
    resource_allocated: dict[str, ResourceAllocation] = field(default_factory=dict)
    strategy: OrchestrationStrategy = OrchestrationStrategy.PRIORITY_WEIGHTED
    execution_order: list[str] = field(default_factory=list)
    is_completed: bool = False
    error_count: int = 0
    max_retries: int = 3


@dataclass
class ExecutionPlan:
    orchestration_id: str
    phases: list[list[str]]
    resource_allocation_map: dict[str, ResourceAllocation]
    estimated_duration: float
    critical_path: list[str]
    budget_utilization: dict[ResourceType, float]


class AdvancedOrchestrationService:
    """Tracks dependency-aware orchestration in memory."""

    def __init__(self) -> None:
        self.db_manager = get_db_manager()
        self.active_orchestrations: dict[str, OrchestrationContext] = {}
        self.execution_plans: dict[str, ExecutionPlan] = {}
        self.resource_pools = {
            ResourceType.CPU: 100.0,
            ResourceType.MEMORY: 4096.0,
            ResourceType.API_CALLS: 1000.0,
            ResourceType.DISK_IO: 1000.0,
        }

    async def create_orchestration(
        self,
        root_task_id: str,
        child_tasks: list[str],
        dependencies: dict[str, list[TaskDependency]],
        strategy: OrchestrationStrategy = OrchestrationStrategy.PRIORITY_WEIGHTED,
    ) -> OrchestrationContext:
        orchestration_id = str(uuid4())
        context = OrchestrationContext(
            orchestration_id=orchestration_id,
            root_task_id=root_task_id,
            child_tasks=child_tasks,
            dependencies=dependencies,
            strategy=strategy,
        )
        context.execution_order = await self._compute_execution_order(
            child_tasks, dependencies
        )
        self.active_orchestrations[orchestration_id] = context
        log_request(
            "orchestration",
            f"Created orchestration {orchestration_id}",
            root_task_id=root_task_id,
            tasks_count=len(child_tasks),
        )
        return context

    async def allocate_resources(
        self, orchestration_id: str, phase_tasks: list[str]
    ) -> dict[str, ResourceAllocation]:
        context = self.active_orchestrations.get(orchestration_id)
        if context is None:
            raise ValueError(f"Orchestration {orchestration_id} not found")

        async with self.db_manager.session_scope() as db:
            priorities = await self._fetch_task_priorities(db, phase_tasks)

        allocations: dict[str, ResourceAllocation] = {}
        for task_id in phase_tasks:
            priority = priorities.get(task_id, 5)
            allocation = self._compute_resource_allocation(task_id, priority, context.strategy)
            allocations[task_id] = allocation
            context.resource_allocated[task_id] = allocation
        return allocations

    async def plan_execution(
        self, orchestration_id: str, tasks_with_priorities: dict[str, int]
    ) -> ExecutionPlan:
        context = self.active_orchestrations.get(orchestration_id)
        if context is None:
            raise ValueError(f"Orchestration {orchestration_id} not found")

        phases = await self._organize_into_phases(
            context.child_tasks, context.dependencies
        )
        resource_map: dict[str, ResourceAllocation] = {}
        total_duration = 0.0
        for phase_tasks in phases:
            resource_map.update(await self.allocate_resources(orchestration_id, phase_tasks))
            total_duration += await self._estimate_phase_duration(phase_tasks)

        critical_path = max(phases, key=len, default=[]) if phases else []
        plan = ExecutionPlan(
            orchestration_id=orchestration_id,
            phases=phases,
            resource_allocation_map=resource_map,
            estimated_duration=total_duration,
            critical_path=critical_path,
            budget_utilization=self._calculate_budget_utilization(resource_map),
        )
        self.execution_plans[orchestration_id] = plan
        return plan

    async def execute_orchestration(self, orchestration_id: str) -> dict[str, Any]:
        plan = self.execution_plans.get(orchestration_id)
        if plan is None:
            raise ValueError(f"Execution plan for {orchestration_id} not found")

        context = self.active_orchestrations[orchestration_id]
        started = datetime.utcnow()
        results = {
            "orchestration_id": orchestration_id,
            "phases_completed": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "phase_results": [],
            "total_duration": 0.0,
        }

        try:
            for index, phase_tasks in enumerate(plan.phases):
                phase_result = {
                    "phase": index,
                    "tasks": len(phase_tasks),
                    "completed": len(phase_tasks),
                    "failed": 0,
                }
                results["phase_results"].append(phase_result)
                results["phases_completed"] += 1
                results["tasks_completed"] += len(phase_tasks)
        except Exception as exc:
            context.error_count += 1
            log_error("orchestration", f"Execution failed: {exc}")
            raise
        finally:
            context.is_completed = True
            results["total_duration"] = (datetime.utcnow() - started).total_seconds()

        return results

    async def _compute_execution_order(
        self, tasks: list[str], dependencies: dict[str, list[TaskDependency]]
    ) -> list[str]:
        graph = {task: set() for task in tasks}
        in_degree = {task: 0 for task in tasks}

        for task, deps in dependencies.items():
            for dep in deps:
                if dep.depends_on in graph and task in in_degree:
                    graph[dep.depends_on].add(task)
                    in_degree[task] += 1

        queue = [task for task in tasks if in_degree[task] == 0]
        ordered: list[str] = []
        while queue:
            current = queue.pop(0)
            ordered.append(current)
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        return ordered or list(tasks)

    async def _organize_into_phases(
        self, tasks: list[str], dependencies: dict[str, list[TaskDependency]]
    ) -> list[list[str]]:
        phases: list[list[str]] = []
        remaining = set(tasks)
        completed: set[str] = set()

        while remaining:
            phase = [
                task
                for task in remaining
                if all(dep.depends_on in completed for dep in dependencies.get(task, []))
            ]
            if not phase:
                log_error(
                    "orchestration",
                    f"Circular dependency detected for remaining tasks: {sorted(remaining)}",
                )
                break
            phases.append(sorted(phase))
            completed.update(phase)
            remaining -= set(phase)

        return phases

    def _compute_resource_allocation(
        self, task_id: str, priority: int, strategy: OrchestrationStrategy
    ) -> ResourceAllocation:
        if strategy == OrchestrationStrategy.PRIORITY_WEIGHTED:
            max_share = 0.20 if priority >= 8 else 0.10
            allocated = self.resource_pools[ResourceType.CPU] * max_share
        else:
            allocated = self.resource_pools[ResourceType.CPU] / 10.0

        return ResourceAllocation(
            task_id=task_id,
            resource_type=ResourceType.CPU,
            allocated_amount=allocated,
            priority_level=priority,
            is_critical=priority >= 8,
        )

    async def _fetch_task_priorities(
        self, db: AsyncSession, task_ids: list[str]
    ) -> dict[str, int]:
        del db
        return {task_id: 5 for task_id in task_ids}

    async def _estimate_phase_duration(self, tasks: list[str]) -> float:
        return float(len(tasks) * 0.5)

    def _calculate_budget_utilization(
        self, allocations: dict[str, ResourceAllocation]
    ) -> dict[ResourceType, float]:
        utilization = {resource: 0.0 for resource in ResourceType}
        for allocation in allocations.values():
            utilization[allocation.resource_type] = min(
                utilization[allocation.resource_type] + allocation.allocated_amount,
                100.0,
            )
        return utilization

    def get_orchestration_status(self, orchestration_id: str) -> dict[str, Any]:
        context = self.active_orchestrations.get(orchestration_id)
        if context is None:
            return {"error": f"Orchestration {orchestration_id} not found"}

        plan = self.execution_plans.get(orchestration_id)
        return {
            "orchestration_id": orchestration_id,
            "root_task": context.root_task_id,
            "child_tasks": len(context.child_tasks),
            "strategy": context.strategy.value,
            "is_completed": context.is_completed,
            "error_count": context.error_count,
            "execution_order": context.execution_order,
            "phases": len(plan.phases) if plan else 0,
            "estimated_duration": plan.estimated_duration if plan else None,
            "critical_path_length": len(plan.critical_path) if plan else 0,
        }
