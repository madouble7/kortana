"""
Phase 7 Cycle #4: Advanced Orchestration Service
Meta-task coordination with dynamic resource allocation
Enables cross-service dependency management and budget-aware execution
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Set

from sqlalchemy.ext.asyncio import AsyncSession

from src.kortana.database import get_db_manager
from src.kortana.logger import log_error, log_request


class ResourceType(str, Enum):
    """Types of computational resources for allocation"""

    CPU = "cpu"  # Percentage of available CPU
    MEMORY = "memory"  # MB of RAM
    NETWORK = "network"  # Network bandwidth priority
    API_CALLS = "api_calls"  # Gemini/OpenAI API call quota
    DISK_IO = "disk_io"  # Disk I/O operations per second


class OrchestrationStrategy(str, Enum):
    """Strategies for coordinating multi-task workflows"""

    PARALLEL = "parallel"  # Execute all independent tasks simultaneously
    SEQUENTIAL = "sequential"  # Execute tasks in order
    LAYERED = "layered"  # Execute independent layers in parallel
    PRIORITY_WEIGHTED = "priority_weighted"  # Allocate resources by priority
    BUDGET_AWARE = "budget_aware"  # Respect API/compute budgets


@dataclass
class ResourceAllocation:
    """Resource allocation for a single task"""

    task_id: str
    resource_type: ResourceType
    allocated_amount: float  # 0.0-1.0 for percent, or absolute units
    priority_level: int  # 1-10, higher = more resources
    is_critical: bool = False  # Critical tasks get guaranteed minimum resources
    can_preempt: bool = False  # Non-critical tasks can be preempted


@dataclass
class TaskDependency:
    """Represents a dependency between two tasks"""

    task_id: str
    depends_on: str  # ID of prerequisite task
    dependency_type: str  # "finish_before_start", "parallel", "data_transfer"
    is_blocking: bool = True  # Blocks execution if not satisfied


@dataclass
class OrchestrationContext:
    """Context for coordinating multiple tasks across services"""

    orchestration_id: str
    root_task_id: str  # Main task driving the orchestration
    child_tasks: List[str] = field(
        default_factory=list
    )  # Tasks spawned by this orchestration
    dependencies: Dict[str, List[TaskDependency]] = field(default_factory=dict)
    resource_budget: Dict[ResourceType, float] = field(default_factory=dict)
    resource_allocated: Dict[str, ResourceAllocation] = field(default_factory=dict)
    strategy: OrchestrationStrategy = OrchestrationStrategy.PRIORITY_WEIGHTED
    execution_order: List[str] = field(
        default_factory=list
    )  # Computed execution sequence
    is_completed: bool = False
    error_count: int = 0
    max_retries: int = 3


@dataclass
class ExecutionPlan:
    """Detailed execution plan for a coordinated task set"""

    orchestration_id: str
    phases: List[
        List[str]
    ]  # Phases of execution (each phase contains parallelizable tasks)
    resource_allocation_map: Dict[str, ResourceAllocation]
    estimated_duration: float  # Seconds
    critical_path: List[str]  # Tasks in the critical path
    budget_utilization: Dict[ResourceType, float]  # Projected usage


class AdvancedOrchestrationService:
    """Service for coordinating complex multi-task workflows"""

    def __init__(self):
        """Initialize orchestration service"""
        self.db_manager = get_db_manager()
        self.active_orchestrations: Dict[str, OrchestrationContext] = {}
        self.execution_plans: Dict[str, ExecutionPlan] = {}

        # Resource pools (can be updated from environment)
        self.resource_pools = {
            ResourceType.CPU: 100.0,  # Percent
            ResourceType.MEMORY: 4096.0,  # MB
            ResourceType.API_CALLS: 1000,  # Per minute
            ResourceType.DISK_IO: 1000.0,  # Ops/sec
        }

        # Default budget constraints
        self.budget_constraints = {
            ResourceType.API_CALLS: 0.8,  # Use max 80% of quota
            ResourceType.CPU: 0.85,  # Use max 85% of CPU
            ResourceType.MEMORY: 0.75,  # Use max 75% of RAM
        }

    async def create_orchestration(
        self,
        root_task_id: str,
        child_tasks: List[str],
        dependencies: Dict[str, List[TaskDependency]],
        strategy: OrchestrationStrategy = OrchestrationStrategy.PRIORITY_WEIGHTED,
    ) -> OrchestrationContext:
        """
        Create a new orchestration context for coordinating multiple tasks

        Args:
            root_task_id: Main task driving the orchestration
            child_tasks: Tasks to be coordinated
            dependencies: Task dependencies mapping
            strategy: Orchestration strategy to use

        Returns:
            OrchestrationContext with initial setup
        """
        from uuid import uuid4

        orchestration_id = str(uuid4())

        context = OrchestrationContext(
            orchestration_id=orchestration_id,
            root_task_id=root_task_id,
            child_tasks=child_tasks,
            dependencies=dependencies,
            strategy=strategy,
        )

        # Compute execution order based on dependencies
        context.execution_order = await self._compute_execution_order(
            child_tasks, dependencies
        )

        # Store in active orchestrations
        self.active_orchestrations[orchestration_id] = context

        log_request(
            "orchestration",
            f"Created orchestration {orchestration_id} for root task {root_task_id}",
            tasks_count=len(child_tasks),
            strategy=strategy.value,
        )

        return context

    async def allocate_resources(
        self, orchestration_id: str, phase_tasks: List[str]
    ) -> Dict[str, ResourceAllocation]:
        """
        Allocate resources to tasks in a phase

        Args:
            orchestration_id: ID of the orchestration
            phase_tasks: Tasks in this execution phase

        Returns:
            Mapping of task_id to ResourceAllocation
        """
        context = self.active_orchestrations.get(orchestration_id)
        if not context:
            raise ValueError(f"Orchestration {orchestration_id} not found")

        allocations = {}

        # Calculate available resources
        available = self._get_available_resources()

        # Fetch task priorities from database
        async with self.db_manager.session_scope() as db:
            priorities = await self._fetch_task_priorities(db, phase_tasks)

        # Allocate resources based on priority and availability
        for task_id in phase_tasks:
            priority = priorities.get(task_id, 5)  # Default priority 5
            allocation = await self._compute_resource_allocation(
                task_id, priority, available, context.strategy
            )
            allocations[task_id] = allocation
            context.resource_allocated[task_id] = allocation

        return allocations

    async def plan_execution(
        self, orchestration_id: str, tasks_with_priorities: Dict[str, int]
    ) -> ExecutionPlan:
        """
        Create a detailed execution plan with resource allocation

        Args:
            orchestration_id: ID of the orchestration
            tasks_with_priorities: Task priorities for planning

        Returns:
            ExecutionPlan with phases, resources, and timeline
        """
        context = self.active_orchestrations.get(orchestration_id)
        if not context:
            raise ValueError(f"Orchestration {orchestration_id} not found")

        # Organize tasks into execution phases
        phases = await self._organize_into_phases(
            context.child_tasks, context.dependencies
        )

        # Allocate resources for each phase
        resource_map = {}
        critical_path = []
        total_duration = 0.0

        for phase_idx, phase_tasks in enumerate(phases):
            phase_allocations = await self.allocate_resources(
                orchestration_id, phase_tasks
            )
            resource_map.update(phase_allocations)

            # Estimate phase duration (longest task in phase)
            phase_duration = await self._estimate_phase_duration(phase_tasks)
            total_duration += phase_duration

            # Track critical path (longest path through dependency graph)
            if phase_idx == 0 or any(
                t in critical_path for phase in phases[: phase_idx + 1] for t in phase
            ):
                critical_path.extend(phase_tasks)

        # Calculate budget utilization
        budget_util = self._calculate_budget_utilization(resource_map)

        plan = ExecutionPlan(
            orchestration_id=orchestration_id,
            phases=phases,
            resource_allocation_map=resource_map,
            estimated_duration=total_duration,
            critical_path=critical_path,
            budget_utilization=budget_util,
        )

        self.execution_plans[orchestration_id] = plan
        return plan

    async def execute_orchestration(self, orchestration_id: str) -> Dict[str, Any]:
        """
        Execute the coordinated task set according to the plan

        Args:
            orchestration_id: ID of the orchestration to execute

        Returns:
            Execution results and statistics
        """
        plan = self.execution_plans.get(orchestration_id)
        if not plan:
            raise ValueError(f"Execution plan for {orchestration_id} not found")

        context = self.active_orchestrations[orchestration_id]
        results = {
            "orchestration_id": orchestration_id,
            "phases_completed": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_duration": 0.0,
            "phase_results": [],
        }

        start_time = datetime.utcnow()

        try:
            # Execute phases in sequence (each phase parallel internally)
            for phase_idx, phase_tasks in enumerate(plan.phases):
                phase_start = datetime.utcnow()
                phase_result = await self._execute_phase(
                    phase_tasks, plan.resource_allocation_map
                )

                results["phase_results"].append(
                    {
                        "phase": phase_idx,
                        "tasks": len(phase_tasks),
                        "completed": phase_result["completed"],
                        "failed": phase_result["failed"],
                    }
                )

                results["tasks_completed"] += phase_result["completed"]
                results["tasks_failed"] += phase_result["failed"]
                results["phases_completed"] += 1

                # Check for critical failures
                if phase_result["failed"] > 0 and phase_idx < len(plan.critical_path):
                    context.error_count += 1
                    if context.error_count >= context.max_retries:
                        log_error(
                            "orchestration",
                            f"Critical phase {phase_idx} failed after {context.error_count} retries",
                        )
                        break

                phase_duration = (datetime.utcnow() - phase_start).total_seconds()
                results["total_duration"] += phase_duration

        except Exception as e:
            log_error(
                "orchestration",
                f"Orchestration {orchestration_id} failed: {str(e)}",
            )
            context.error_count += 1

        finally:
            total_duration = (datetime.utcnow() - start_time).total_seconds()
            results["total_duration"] = total_duration
            context.is_completed = True

        return results

    async def _compute_execution_order(
        self, tasks: List[str], dependencies: Dict[str, List[TaskDependency]]
    ) -> List[str]:
        """Compute task execution order using topological sort"""
        # Build dependency graph
        graph: Dict[str, Set[str]] = {task: set() for task in tasks}
        in_degree: Dict[str, int] = {task: 0 for task in tasks}

        for task, deps in dependencies.items():
            for dep in deps:
                if dep.task_id in graph:
                    graph[dep.task_id].add(task)
                    in_degree[task] += 1

        # Topological sort (Kahn's algorithm)
        queue = [task for task in tasks if in_degree[task] == 0]
        execution_order = []

        while queue:
            current = queue.pop(0)
            execution_order.append(current)

            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return execution_order

    async def _organize_into_phases(
        self, tasks: List[str], dependencies: Dict[str, List[TaskDependency]]
    ) -> List[List[str]]:
        """Organize tasks into execution phases (parallel batches)"""
        phases = []
        remaining = set(tasks)
        completed: Set[str] = set()

        while remaining:
            # Find tasks with satisfied dependencies
            phase_tasks = []
            for task in remaining:
                task_deps = dependencies.get(task, [])
                if all(dep.depends_on in completed for dep in task_deps):
                    phase_tasks.append(task)

            if not phase_tasks:
                # Circular dependency detected
                log_error(
                    "orchestration",
                    f"Circular dependency detected. Remaining: {remaining}",
                )
                break

            phases.append(phase_tasks)
            completed.update(phase_tasks)
            remaining -= set(phase_tasks)

        return phases

    async def _execute_phase(
        self,
        phase_tasks: List[str],
        allocations: Dict[str, ResourceAllocation],
    ) -> Dict[str, Any]:
        """Execute a single phase of tasks (parallelizable)"""
        # In production, this would use asyncio.gather or similar
        # For now, return simulation results
        completed = len(phase_tasks)
        failed = 0

        return {
            "completed": completed,
            "failed": failed,
            "tasks": phase_tasks,
        }

    async def _compute_resource_allocation(
        self,
        task_id: str,
        priority: int,
        available: Dict[ResourceType, float],
        strategy: OrchestrationStrategy,
    ) -> ResourceAllocation:
        """Compute resource allocation for a single task"""
        if strategy == OrchestrationStrategy.PRIORITY_WEIGHTED:
            # Formula: (priority / sum_of_priorities) * total_available
            # For simplistic approximation where we don't know total phase priority here:
            # Limit = 20% of total available for high priority, 5% for low
            max_share = 0.20 if priority >= 8 else 0.10
            cpu_allocation = min(
                (priority / 10.0) * available[ResourceType.CPU],
                available[ResourceType.CPU] * max_share,
            )
        else:
            # Equal distribution (capped at 10% per task)
            cpu_allocation = available[ResourceType.CPU] / 10.0

        return ResourceAllocation(
            task_id=task_id,
            resource_type=ResourceType.CPU,
            allocated_amount=cpu_allocation,
            priority_level=priority,
            is_critical=priority >= 8,
        )

    async def _fetch_task_priorities(
        self, db: AsyncSession, task_ids: List[str]
    ) -> Dict[str, int]:
        """Fetch task priorities from database"""
        # Placeholder - would query database for actual task properties
        return {task_id: 5 for task_id in task_ids}

    async def _estimate_phase_duration(self, tasks: List[str]) -> float:
        """Estimate duration of a phase (parallel execution)"""
        # Placeholder - would analyze task complexity
        return float(len(tasks) * 0.5)  # Assume 0.5s per task

    def _get_available_resources(self) -> Dict[ResourceType, float]:
        """Get currently available resources"""
        return self.resource_pools.copy()

    def _calculate_budget_utilization(
        self, allocations: Dict[str, ResourceAllocation]
    ) -> Dict[ResourceType, float]:
        """Calculate total budget utilization across all allocations"""
        utilization = {resource: 0.0 for resource in ResourceType}

        for allocation in allocations.values():
            utilization[allocation.resource_type] = min(
                utilization[allocation.resource_type] + allocation.allocated_amount,
                100.0,
            )

        return utilization

    def get_orchestration_status(self, orchestration_id: str) -> Dict[str, Any]:
        """Get status of an active orchestration"""
        context = self.active_orchestrations.get(orchestration_id)
        if not context:
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
