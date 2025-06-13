"""
Task Coordinator for Autonomous Operations
Manages scheduling and execution of autonomous tasks.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta

from ..execution_engine import ExecutionEngine, OperationResult
from .models import Task, TaskResult, TaskStatus

logger = logging.getLogger(__name__)


class TaskCoordinator:
    """Coordinates execution of autonomous tasks"""

    def __init__(self, execution_engine: ExecutionEngine):
        self.execution_engine = execution_engine
        self._tasks: dict[str, Task] = {}
        self._in_progress: set[str] = set()
        self._schedules: dict[str, datetime] = {}
        self._task_locks: dict[str, asyncio.Lock] = {}

    async def add_task(self, task: Task) -> str:
        """Add a new task to be executed."""
        self._tasks[task.id] = task
        self._task_locks[task.id] = asyncio.Lock()

        # If task has dependencies, schedule after them
        if task.dependencies:
            await self._schedule_after_dependencies(task)
        else:
            self._schedules[task.id] = datetime.now()

        logger.info(f"Added task {task.id} - {task.description}")
        return task.id

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or in-progress task."""
        if task_id not in self._tasks:
            return False

        task = self._tasks[task_id]
        async with self._task_locks[task_id]:
            if task.status in (
                TaskStatus.PENDING,
                TaskStatus.SCHEDULED,
                TaskStatus.IN_PROGRESS,
            ):
                task.status = TaskStatus.CANCELLED
                if task_id in self._in_progress:
                    self._in_progress.remove(task_id)
                return True
        return False

    async def get_task_status(self, task_id: str) -> TaskStatus | None:
        """Get current status of a task."""
        return self._tasks[task_id].status if task_id in self._tasks else None

    async def get_task_result(self, task_id: str) -> TaskResult | None:
        """Get the result of a completed task."""
        return self._tasks[task_id].result if task_id in self._tasks else None

    async def _schedule_after_dependencies(self, task: Task) -> None:
        """Schedule a task to run after its dependencies complete."""
        max_dep_time = datetime.now()
        for dep_id in task.dependencies:
            if dep_id in self._schedules:
                if self._schedules[dep_id] > max_dep_time:
                    max_dep_time = self._schedules[dep_id]
            else:
                # If dependency not scheduled, schedule it ASAP
                self._schedules[dep_id] = datetime.now()

        # Schedule this task after latest dependency
        self._schedules[task.id] = max_dep_time + timedelta(seconds=1)

    async def execute_pending_tasks(self) -> None:
        """Execute all pending tasks that are ready and don't have incomplete dependencies."""
        while True:
            ready_tasks = []
            now = datetime.now()

            # Find tasks ready for execution
            for task_id, scheduled_time in self._schedules.items():
                if scheduled_time <= now:
                    task = self._tasks[task_id]
                    if task.status == TaskStatus.PENDING:
                        if self._are_dependencies_met(task):
                            ready_tasks.append(task)

            # Execute ready tasks in parallel
            if ready_tasks:
                await asyncio.gather(
                    *[self._execute_task(task) for task in ready_tasks]
                )
            else:
                await asyncio.sleep(1)  # Wait before checking again

    def _are_dependencies_met(self, task: Task) -> bool:
        """Check if all dependencies of a task are completed successfully."""
        for dep_id in task.dependencies:
            if dep_id not in self._tasks:
                return False
            dep_task = self._tasks[dep_id]
            if dep_task.status != TaskStatus.COMPLETED:
                return False
        return True

    async def _execute_task(self, task: Task) -> None:
        """Execute a single task."""
        if task.id in self._in_progress:
            return

        async with self._task_locks[task.id]:
            try:
                self._in_progress.add(task.id)
                task.status = TaskStatus.IN_PROGRESS
                task.started_at = datetime.now()

                # Execute any subtasks first
                for subtask in task.subtasks:
                    await self._execute_task(subtask)

                # Execute the main task operation
                result = await self._run_task_operation(task)

                if not result.success and task.retries < task.max_retries:
                    # Retry failed task
                    task.retries += 1
                    logger.warning(
                        f"Task {task.id} failed, retrying ({task.retries}/{task.max_retries})"
                    )
                    self._schedules[task.id] = datetime.now() + timedelta(
                        seconds=5
                    )  # Retry after 5s
                    task.status = TaskStatus.PENDING
                else:
                    # Record final task result
                    completion_time = datetime.now()
                    task.completed_at = completion_time
                    task.status = (
                        TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
                    )
                    task.result = TaskResult(
                        success=result.success,
                        completion_time=completion_time,
                        output=result.data,
                        error=result.error,
                        metrics={
                            "duration": result.duration,
                            "operation_type": result.operation_type,
                        },
                    )

            except Exception as e:
                logger.error(f"Error executing task {task.id}: {str(e)}")
                task.status = TaskStatus.FAILED
                task.result = TaskResult(
                    success=False, completion_time=datetime.now(), error=str(e)
                )

            finally:
                self._in_progress.remove(task.id)

    async def _run_task_operation(self, task: Task) -> OperationResult:
        """Execute the actual task operation using the execution engine."""
        if not task.context.workspace_root:
            return OperationResult(
                success=False,
                error="No workspace root specified in task context",
                operation_type="task_execution",
            )

        start = time.time()

        try:
            # For now, execute as shell command - could be expanded to handle different types
            command_result = await self.execution_engine.execute_shell_command(
                command=f"python {task.context.workspace_root}/manage_task.py execute {task.id}",
                working_dir=task.context.workspace_root,
            )

            return OperationResult(
                success=command_result.success,
                data=command_result.data,
                error=command_result.error,
                duration=time.time() - start,
                operation_type="task_execution",
            )

        except Exception as e:
            return OperationResult(
                success=False,
                error=str(e),
                duration=time.time() - start,
                operation_type="task_execution",
            )
