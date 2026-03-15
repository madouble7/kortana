"""Test suite for the TaskCoordinator class.

This test suite verifies the core functionality of the TaskCoordinator
including task management, scheduling, execution, error handling, dependencies,
and concurrency control.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from kortana.core.execution_engine import ExecutionEngine
from kortana.core.task_management.coordinator import TaskCoordinator
from kortana.core.task_management.models import (
    Task,
    TaskCategory,
    TaskPriority,
    TaskStatus,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture
def execution_engine():
    """Create a mock execution engine for testing."""
    mock_engine = MagicMock(spec=ExecutionEngine)
    mock_engine.execute_operation = MagicMock()
    return mock_engine


@pytest.fixture
def task_coordinator(execution_engine):
    """Create a TaskCoordinator instance for testing."""
    return TaskCoordinator(execution_engine=execution_engine)


def create_test_task(
    task_id: str = "test-task-1",
    category: TaskCategory = TaskCategory.SYSTEM,
    priority: TaskPriority = TaskPriority.MEDIUM,
    description: str = "Test task",
    dependencies: list[str] = None,
) -> Task:
    """Helper function to create test tasks."""
    return Task(
        id=task_id,
        category=category,
        description=description,
        priority=priority,
        status=TaskStatus.PENDING,
        dependencies=dependencies or [],
    )


class TestTaskCoordinator:
    """Test cases for the TaskCoordinator class."""

    async def test_task_creation_and_queuing(self, task_coordinator):
        """Test creating and queuing a new task."""
        task = create_test_task()
        await task_coordinator.schedule_task(task)

        assert task.id in task_coordinator._tasks
        assert task_coordinator._tasks[task.id].status == TaskStatus.PENDING

    async def test_task_execution(self, task_coordinator):
        """Test successful task execution."""
        task = create_test_task()
        await task_coordinator.schedule_task(task)
        await task_coordinator.execute_task(task.id)

        assert task_coordinator._tasks[task.id].status == TaskStatus.COMPLETED
        task_coordinator.execution_engine.execute_operation.assert_called_once()

    async def test_task_execution_error_handling(self, task_coordinator):
        """Test error handling during task execution."""
        task_coordinator.execution_engine.execute_operation.side_effect = Exception(
            "Test error"
        )
        task = create_test_task()
        await task_coordinator.schedule_task(task)
        await task_coordinator.execute_task(task.id)

        assert task_coordinator._tasks[task.id].status == TaskStatus.FAILED

    async def test_task_dependencies(self, task_coordinator):
        """Test task dependency resolution and execution order."""
        # Create a chain of dependent tasks
        task1 = create_test_task("task-1")
        task2 = create_test_task("task-2", dependencies=["task-1"])
        task3 = create_test_task("task-3", dependencies=["task-2"])

        # Schedule tasks in reverse order
        await task_coordinator.schedule_task(task3)
        await task_coordinator.schedule_task(task2)
        await task_coordinator.schedule_task(task1)

        # Execute tasks
        tasks_executed = []
        original_execute = task_coordinator.execution_engine.execute_operation

        def track_execution(*args, **kwargs):
            tasks_executed.append(args[0].id)
            return original_execute(*args, **kwargs)

        task_coordinator.execution_engine.execute_operation = MagicMock(
            side_effect=track_execution
        )

        await task_coordinator.execute_pending_tasks()

        # Verify execution order respects dependencies
        assert tasks_executed == ["task-1", "task-2", "task-3"]

    async def test_concurrent_task_execution(self, task_coordinator):
        """Test concurrent execution of independent tasks."""
        independent_tasks = [create_test_task(f"concurrent-task-{i}") for i in range(3)]

        # Schedule all tasks
        for task in independent_tasks:
            await task_coordinator.schedule_task(task)

        # Mock execution time
        async def delayed_execution(*args, **kwargs):
            await asyncio.sleep(0.1)
            return True

        task_coordinator.execution_engine.execute_operation = MagicMock(
            side_effect=delayed_execution
        )

        # Execute tasks concurrently
        start_time = datetime.now()
        await task_coordinator.execute_pending_tasks()
        execution_time = datetime.now() - start_time

        # Verify all tasks completed
        assert all(
            task_coordinator._tasks[task.id].status == TaskStatus.COMPLETED
            for task in independent_tasks
        )

        # Verify tasks executed concurrently (total time less than sequential execution)
        assert execution_time < timedelta(seconds=0.3)

    async def test_task_cancellation(self, task_coordinator):
        """Test cancellation of a task."""
        task = create_test_task()
        await task_coordinator.schedule_task(task)

        # Mock long-running task
        async def long_running_task(*args, **kwargs):
            await asyncio.sleep(1)
            return True

        task_coordinator.execution_engine.execute_operation = MagicMock(
            side_effect=long_running_task
        )

        # Start task execution in background
        execution_task = asyncio.create_task(task_coordinator.execute_task(task.id))

        # Cancel the task
        await task_coordinator.cancel_task(task.id)
        await execution_task

        assert task_coordinator._tasks[task.id].status == TaskStatus.CANCELLED

    async def test_task_priority_ordering(self, task_coordinator):
        """Test tasks are executed in priority order."""
        # Create tasks with different priorities
        tasks = [
            create_test_task("low-priority", priority=TaskPriority.LOW),
            create_test_task("medium-priority", priority=TaskPriority.MEDIUM),
            create_test_task("high-priority", priority=TaskPriority.HIGH),
        ]

        # Schedule tasks in reverse priority order
        for task in tasks:
            await task_coordinator.schedule_task(task)

        # Track execution order
        execution_order = []

        def track_execution(*args, **kwargs):
            execution_order.append(args[0].id)
            return True

        task_coordinator.execution_engine.execute_operation = MagicMock(
            side_effect=track_execution
        )
        await task_coordinator.execute_pending_tasks()

        # Verify high priority tasks were executed first
        assert execution_order == ["high-priority", "medium-priority", "low-priority"]

    async def test_task_retry_mechanism(self, task_coordinator):
        """Test task retry mechanism for failed tasks."""
        task = create_test_task()
        await task_coordinator.schedule_task(task)

        # Mock execution to fail twice then succeed
        fail_count = 0

        def fail_then_succeed(*args, **kwargs):
            nonlocal fail_count
            fail_count += 1
            if fail_count <= 2:
                raise Exception(f"Failure {fail_count}")
            return True

        task_coordinator.execution_engine.execute_operation = MagicMock(
            side_effect=fail_then_succeed
        )
        await task_coordinator.execute_task(task.id, max_retries=3)

        assert task_coordinator._tasks[task.id].status == TaskStatus.COMPLETED
        assert task_coordinator.execution_engine.execute_operation.call_count == 3
