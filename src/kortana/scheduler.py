"""Task scheduler for Kor'tana system.

This module provides a thread-safe task scheduler that can execute tasks with priorities
and track their execution status.
"""

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# Setup logging
logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Enum representing the possible states of a task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskResult:
    """Container for task execution results."""

    status: TaskStatus
    start_time: datetime | None = None
    end_time: datetime | None = None
    error: Exception | None = None
    result: object | None = None


class Scheduler:
    """Thread-safe task scheduler with priority support."""

    def __init__(self) -> None:
        """Initialize the scheduler."""
        self.tasks: list[tuple[int, Callable[[], None]]] = []
        self.lock = threading.Lock()
        self.task_results: dict[int, TaskResult] = {}
        self._task_counter = 0
        self._running = False
        self._thread: threading.Thread | None = None

    def add_task(self, task: Callable[[], None], priority: int = 1) -> int:
        """Add a task to the scheduler with the given priority.

        Args:
            task: The task function to execute
            priority: Priority level (lower number = higher priority)

        Returns:
            task_id: Unique identifier for the task
        """
        with self.lock:
            self._task_counter += 1
            task_id = self._task_counter
            self.tasks.append((priority, task))
            self.tasks.sort(key=lambda x: x[0])  # Sort by priority
            self.task_results[task_id] = TaskResult(status=TaskStatus.PENDING)
            logger.info(f"Added task {task_id} with priority {priority}")
            return task_id

    def cancel_task(self, task_id: int) -> bool:
        """Cancel a pending task.

        Args:
            task_id: ID of the task to cancel

        Returns:
            bool: True if task was cancelled, False if not found or already complete
        """
        with self.lock:
            if task_id in self.task_results:
                result = self.task_results[task_id]
                if result.status == TaskStatus.PENDING:
                    result.status = TaskStatus.CANCELLED
                    logger.info(f"Task {task_id} cancelled")
                    return True
        return False

    def get_task_status(self, task_id: int) -> TaskStatus | None:
        """Get the current status of a task.

        Args:
            task_id: ID of the task to check

        Returns:
            TaskStatus | None: Current status of the task, or None if not found
        """
        with self.lock:
            if task_id in self.task_results:
                return self.task_results[task_id].status
        return None

    def get_task_result(self, task_id: int) -> TaskResult | None:
        """Get the result details of a task.

        Args:
            task_id: ID of the task to check

        Returns:
            TaskResult | None: Task result details, or None if not found
        """
        with self.lock:
            return self.task_results.get(task_id)

    def execute_tasks(self) -> None:
        """Main task execution loop."""
        while self._running:
            with self.lock:
                if self.tasks:
                    priority, task = self.tasks.pop(0)
                    # Find task_id by looking through results
                    task_id = next(
                        (
                            tid
                            for tid, result in self.task_results.items()
                            if result.status == TaskStatus.PENDING
                        ),
                        None,
                    )
                    if task_id:
                        result = self.task_results[task_id]
                        result.status = TaskStatus.RUNNING
                        result.start_time = datetime.now()

                        try:
                            logger.info(
                                f"Executing task {task_id} with priority {priority}"
                            )
                            result.result = task()
                            result.status = TaskStatus.COMPLETED
                        except Exception as e:
                            logger.error(
                                f"Task {task_id} failed: {str(e)}", exc_info=True
                            )
                            result.error = e
                            result.status = TaskStatus.FAILED
                        finally:
                            result.end_time = datetime.now()
                else:
                    logger.debug("No tasks to execute. Waiting...")
            time.sleep(1)

    def start(self) -> None:
        """Start the scheduler."""
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self.execute_tasks, daemon=True)
            self._thread.start()
            logger.info("Scheduler started")

    def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False
        if self._thread:
            self._thread.join()
            self._thread = None
            logger.info("Scheduler stopped")


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    def sample_task() -> None:
        """Sample task that simulates work."""
        time.sleep(0.5)
        logger.info("Task executed!")

    # Create and start scheduler
    scheduler = Scheduler()
    scheduler.add_task(sample_task, priority=2)
    scheduler.add_task(sample_task, priority=1)
    scheduler.start()

    # Let tasks run for a bit
    time.sleep(5)
    scheduler.stop()
