"""Test suite for the Scheduler class."""

import logging
import time

import pytest

from src.kortana.scheduler import Scheduler, TaskStatus

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture
def scheduler():
    """Create a scheduler instance for testing."""
    s = Scheduler()
    yield s
    s.stop()  # Cleanup after each test


def test_task_creation(scheduler):
    """Test that tasks can be created with different priorities."""

    def task1():
        pass

    def task2():
        pass

    task1_id = scheduler.add_task(task1, priority=2)
    task2_id = scheduler.add_task(task2, priority=1)

    assert task1_id == 1
    assert task2_id == 2
    assert len(scheduler.tasks) == 2

    # Check priority ordering
    assert scheduler.tasks[0][0] == 1  # First task should have priority 1
    assert scheduler.tasks[1][0] == 2  # Second task should have priority 2


def test_task_execution(scheduler):
    """Test that tasks are executed successfully."""
    result: bool | None = None

    def test_task():
        nonlocal result
        result = True

    task_id = scheduler.add_task(test_task)
    scheduler.start()

    # Wait for task to complete
    time.sleep(2)

    task_result = scheduler.get_task_result(task_id)
    assert task_result is not None
    assert task_result.status == TaskStatus.COMPLETED
    assert result is True


def test_task_error_handling(scheduler):
    """Test error handling during task execution."""

    def failing_task():
        raise ValueError("Test error")

    task_id = scheduler.add_task(failing_task)
    scheduler.start()

    # Wait for task to fail
    time.sleep(2)

    task_result = scheduler.get_task_result(task_id)
    assert task_result is not None
    assert task_result.status == TaskStatus.FAILED
    assert isinstance(task_result.error, ValueError)
    assert str(task_result.error) == "Test error"


def test_task_cancellation(scheduler):
    """Test task cancellation."""

    def long_task():
        time.sleep(10)

    task_id = scheduler.add_task(long_task)
    assert scheduler.get_task_status(task_id) == TaskStatus.PENDING

    # Cancel the task before it starts
    cancelled = scheduler.cancel_task(task_id)
    assert cancelled is True
    assert scheduler.get_task_status(task_id) == TaskStatus.CANCELLED


def test_priority_execution_order(scheduler):
    """Test that tasks execute in priority order."""
    execution_order = []

    def make_task(name: str):
        def task():
            execution_order.append(name)
            time.sleep(0.1)  # Small delay to ensure deterministic ordering

        return task

    # Add tasks in reverse priority order
    scheduler.add_task(make_task("low"), priority=3)
    scheduler.add_task(make_task("medium"), priority=2)
    scheduler.add_task(make_task("high"), priority=1)

    scheduler.start()
    time.sleep(1)  # Wait for all tasks to complete

    assert execution_order == ["high", "medium", "low"]


def test_scheduler_stop(scheduler):
    """Test that scheduler can be stopped gracefully."""

    def long_task():
        time.sleep(5)

    scheduler.add_task(long_task)
    scheduler.start()

    assert scheduler._running is True
    assert scheduler._thread is not None

    scheduler.stop()

    assert scheduler._running is False
    assert scheduler._thread is None


def test_concurrent_tasks(scheduler):
    """Test that independent tasks can run concurrently."""
    start_times = []
    end_times = []

    def task():
        start_times.append(time.time())
        time.sleep(0.5)  # Simulate work
        end_times.append(time.time())

    # Add multiple tasks
    for _ in range(3):
        scheduler.add_task(task)

    scheduler.start()
    time.sleep(2)  # Wait for tasks to complete

    # Check that tasks overlapped in time
    for i in range(len(start_times) - 1):
        assert start_times[i + 1] - start_times[i] < 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
