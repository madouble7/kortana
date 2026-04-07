"""
Execution optimizer for dependency-aware async task scheduling.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

from src.kortana.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ExecutionMetrics:
    task_id: str
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: datetime | None = None
    duration_seconds: float = 0.0
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    success: bool = False
    error_message: str | None = None

    def record_completion(
        self, duration: float, success: bool, error: str | None = None
    ) -> None:
        self.end_time = datetime.utcnow()
        self.duration_seconds = duration
        self.success = success
        self.error_message = error


class DependencyGraph:
    def __init__(self) -> None:
        self.nodes: dict[str, dict[str, Any]] = {}
        self.edges: dict[str, set[str]] = {}

    def add_task(self, task_id: str, metadata: dict[str, Any] | None = None) -> None:
        self.nodes[task_id] = metadata or {}
        self.edges[task_id] = set()

    def add_dependency(self, task_id: str, depends_on: str) -> None:
        self.edges.setdefault(task_id, set()).add(depends_on)

    def topological_sort(self) -> list[str]:
        in_degree = {node: len(self.edges.get(node, set())) for node in self.nodes}
        queue = [node for node in self.nodes if in_degree[node] == 0]
        ordered: list[str] = []

        while queue:
            current = queue.pop(0)
            ordered.append(current)
            for task, deps in self.edges.items():
                if current in deps:
                    in_degree[task] -= 1
                    if in_degree[task] == 0:
                        queue.append(task)

        if len(ordered) != len(self.nodes):
            logger.warning("Circular dependency detected in execution graph")
            return []
        return ordered

    def get_levels(self) -> dict[int, list[str]]:
        levels: dict[int, list[str]] = {}
        level_map = {node: 0 for node in self.nodes}

        for node, deps in self.edges.items():
            if deps:
                level_map[node] = max(level_map.get(dep, 0) for dep in deps) + 1

        for node, level in level_map.items():
            levels.setdefault(level, []).append(node)
        return dict(sorted(levels.items()))

    def can_parallelize(self) -> bool:
        return any(len(tasks) > 1 for tasks in self.get_levels().values())

    def get_critical_path(self) -> list[str]:
        def longest_path_from(node: str, memo: dict[str, list[str]]) -> list[str]:
            if node in memo:
                return memo[node]
            deps = self.edges.get(node, set())
            if not deps:
                path = [node]
            else:
                longest_dep_path = max(
                    (longest_path_from(dep, memo) for dep in deps),
                    key=len,
                    default=[],
                )
                path = [node] + longest_dep_path
            memo[node] = path
            return path

        paths = [longest_path_from(node, {}) for node in self.nodes]
        return max(paths, key=len) if paths else []


class ExecutionOptimizer:
    def __init__(self, max_workers: int = 8) -> None:
        self.max_workers = max_workers
        self.graph = DependencyGraph()
        self.metrics: dict[str, ExecutionMetrics] = {}
        self.active_tasks: set[str] = set()

    def add_task(self, task_id: str, depends_on: list[str] | None = None) -> None:
        self.graph.add_task(task_id)
        for dep in depends_on or []:
            self.graph.add_dependency(task_id, dep)

    async def execute_optimized(
        self,
        tasks: dict[str, Callable[[], Any]],
        on_progress: Callable[[str, bool], None] | None = None,
    ) -> dict[str, Any]:
        levels = self.graph.get_levels()
        critical_path = self.graph.get_critical_path()
        logger.info(
            "Execution plan: "
            f"{len(levels)} levels, critical path length={len(critical_path)}, "
            f"can_parallelize={self.graph.can_parallelize()}"
        )

        results: dict[str, Any] = {}
        semaphore = asyncio.Semaphore(self.max_workers)

        async def execute_with_semaphore(task_id: str) -> None:
            async with semaphore:
                started = datetime.utcnow()
                self.active_tasks.add(task_id)
                try:
                    result = await tasks[task_id]()
                    duration = (datetime.utcnow() - started).total_seconds()
                    metric = ExecutionMetrics(task_id=task_id)
                    metric.record_completion(duration, True)
                    self.metrics[task_id] = metric
                    results[task_id] = result
                    if on_progress:
                        on_progress(task_id, True)
                except Exception as exc:
                    duration = (datetime.utcnow() - started).total_seconds()
                    metric = ExecutionMetrics(task_id=task_id)
                    metric.record_completion(duration, False, str(exc))
                    self.metrics[task_id] = metric
                    logger.error(f"Task {task_id} failed: {exc}")
                    if on_progress:
                        on_progress(task_id, False)
                finally:
                    self.active_tasks.discard(task_id)

        for _, level_tasks in levels.items():
            await asyncio.gather(
                *[execute_with_semaphore(task_id) for task_id in level_tasks]
            )
        return results

    def get_optimization_report(self) -> dict[str, Any]:
        if not self.metrics:
            return {"status": "no_executions"}

        total_duration = sum(metric.duration_seconds for metric in self.metrics.values())
        critical_path = self.graph.get_critical_path()
        critical_duration = sum(
            self.metrics.get(task_id, ExecutionMetrics(task_id)).duration_seconds
            for task_id in critical_path
            if task_id in self.metrics
        )
        parallelization_efficiency = (
            critical_duration / total_duration if critical_duration > 0 else 1.0
        )
        success_count = sum(1 for metric in self.metrics.values() if metric.success)
        failure_count = len(self.metrics) - success_count
        return {
            "total_tasks": len(self.metrics),
            "successful": success_count,
            "failed": failure_count,
            "total_duration_seconds": total_duration,
            "critical_path_duration": critical_duration,
            "parallelization_efficiency": f"{parallelization_efficiency:.1%}",
            "potential_speedup": (
                f"{total_duration / critical_duration:.1f}x"
                if critical_duration > 0
                else "N/A"
            ),
            "critical_path_length": len(critical_path),
            "can_parallelize": self.graph.can_parallelize(),
        }
