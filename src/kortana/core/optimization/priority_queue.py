"""
Priority Queue System inspired by Chromium's task scheduling.

This module provides:
- Priority-based task queuing
- Adaptive scheduling based on priority
- Efficient task processing and throughput optimization
"""

import heapq
import logging
import threading
import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class Priority(IntEnum):
    """Task priority levels (lower value = higher priority)."""

    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


@dataclass(order=True)
class PriorityTask:
    """A task with priority."""

    priority: int
    timestamp: float = field(compare=True)
    task_id: str = field(compare=False)
    callback: Callable = field(compare=False)
    args: tuple = field(default_factory=tuple, compare=False)
    kwargs: dict = field(default_factory=dict, compare=False)


class PriorityQueue:
    """
    Thread-safe priority queue for task scheduling.
    
    Inspired by Chromium's task scheduler for efficient processing.
    """

    def __init__(self, name: str = "default"):
        """
        Initialize priority queue.

        Args:
            name: Queue name for identification
        """
        self.name = name
        self._queue: list[PriorityTask] = []
        self._lock = threading.RLock()
        self._not_empty = threading.Condition(self._lock)
        self._task_count = 0
        self._completed_count = 0
        self._failed_count = 0
        logger.info(f"PriorityQueue '{name}' initialized")

    def enqueue(
        self,
        callback: Callable,
        priority: Priority = Priority.NORMAL,
        task_id: str | None = None,
        *args,
        **kwargs,
    ) -> str:
        """
        Enqueue a task with priority.

        Args:
            callback: Task callback function
            priority: Task priority
            task_id: Optional task ID (auto-generated if None)
            *args: Positional arguments for callback
            **kwargs: Keyword arguments for callback

        Returns:
            Task ID
        """
        with self._lock:
            if task_id is None:
                task_id = f"task_{self._task_count}_{time.time()}"

            task = PriorityTask(
                priority=priority.value,
                timestamp=time.time(),
                task_id=task_id,
                callback=callback,
                args=args,
                kwargs=kwargs,
            )

            heapq.heappush(self._queue, task)
            self._task_count += 1
            self._not_empty.notify()

            logger.debug(
                f"Enqueued task '{task_id}' with priority {priority.name} "
                f"(queue size: {len(self._queue)})"
            )
            return task_id

    def dequeue(self, timeout: float | None = None) -> PriorityTask | None:
        """
        Dequeue highest priority task.

        Args:
            timeout: Maximum time to wait for a task (None = wait forever)

        Returns:
            Task or None if timeout
        """
        with self._not_empty:
            while not self._queue:
                if not self._not_empty.wait(timeout):
                    return None

            task = heapq.heappop(self._queue)
            logger.debug(
                f"Dequeued task '{task.task_id}' (remaining: {len(self._queue)})"
            )
            return task

    def size(self) -> int:
        """
        Get queue size.

        Returns:
            Number of pending tasks
        """
        with self._lock:
            return len(self._queue)

    def clear(self) -> None:
        """Clear all pending tasks."""
        with self._lock:
            self._queue.clear()
            logger.info(f"Queue '{self.name}' cleared")

    def get_stats(self) -> dict[str, Any]:
        """
        Get queue statistics.

        Returns:
            Dictionary with queue stats
        """
        with self._lock:
            return {
                "name": self.name,
                "pending": len(self._queue),
                "total_enqueued": self._task_count,
                "completed": self._completed_count,
                "failed": self._failed_count,
            }


class TaskProcessor:
    """
    Task processor with worker threads for parallel execution.
    
    Provides efficient task processing with priority-based scheduling.
    """

    def __init__(
        self, queue: PriorityQueue, num_workers: int = 4, name: str = "default"
    ):
        """
        Initialize task processor.

        Args:
            queue: Priority queue to process
            num_workers: Number of worker threads
            name: Processor name
        """
        self.queue = queue
        self.num_workers = num_workers
        self.name = name
        self._workers: list[threading.Thread] = []
        self._running = False
        logger.info(
            f"TaskProcessor '{name}' initialized with {num_workers} workers"
        )

    def start(self) -> None:
        """Start worker threads."""
        if self._running:
            logger.warning(f"TaskProcessor '{self.name}' already running")
            return

        self._running = True

        for i in range(self.num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                daemon=True,
                name=f"Worker-{self.name}-{i}",
            )
            worker.start()
            self._workers.append(worker)

        logger.info(f"Started {self.num_workers} workers for processor '{self.name}'")

    def stop(self, timeout: float = 5.0) -> None:
        """
        Stop worker threads.

        Args:
            timeout: Maximum time to wait for workers to stop
        """
        self._running = False

        for worker in self._workers:
            worker.join(timeout=timeout)

        self._workers.clear()
        logger.info(f"Stopped task processor '{self.name}'")

    def _worker_loop(self) -> None:
        """Worker thread main loop."""
        while self._running:
            try:
                task = self.queue.dequeue(timeout=1.0)
                if task is None:
                    continue

                # Execute task
                try:
                    task.callback(*task.args, **task.kwargs)
                    self.queue._completed_count += 1
                    logger.debug(f"Completed task '{task.task_id}'")
                except Exception as e:
                    self.queue._failed_count += 1
                    logger.error(
                        f"Error executing task '{task.task_id}': {e}", exc_info=True
                    )

            except Exception as e:
                logger.error(f"Worker error: {e}", exc_info=True)


class DecisionQueue:
    """
    High-level decision queue for managing AI decision-making tasks.
    
    Provides a convenient interface for Kortana's decision processing.
    """

    def __init__(self, num_workers: int = 4):
        """
        Initialize decision queue.

        Args:
            num_workers: Number of worker threads
        """
        self.queue = PriorityQueue(name="decisions")
        self.processor = TaskProcessor(
            self.queue, num_workers=num_workers, name="decisions"
        )
        logger.info(f"DecisionQueue initialized with {num_workers} workers")

    def start(self) -> None:
        """Start processing decisions."""
        self.processor.start()

    def stop(self) -> None:
        """Stop processing decisions."""
        self.processor.stop()

    def submit_decision(
        self,
        callback: Callable,
        priority: Priority = Priority.NORMAL,
        task_id: str | None = None,
        *args,
        **kwargs,
    ) -> str:
        """
        Submit a decision task.

        Args:
            callback: Decision callback function
            priority: Task priority
            task_id: Optional task ID
            *args: Positional arguments for callback
            **kwargs: Keyword arguments for callback

        Returns:
            Task ID
        """
        return self.queue.enqueue(
            callback, priority, task_id, *args, **kwargs
        )

    def get_stats(self) -> dict[str, Any]:
        """
        Get decision queue statistics.

        Returns:
            Dictionary with statistics
        """
        return self.queue.get_stats()
