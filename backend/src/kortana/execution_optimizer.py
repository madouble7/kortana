""""""











































































































































































































































































        }            "can_parallelize": self.graph.can_parallelize(),            "critical_path_length": len(critical_path),            "potential_speedup": f"{total_duration / critical_duration:.1f}x" if critical_duration > 0 else "N/A",            "parallelization_efficiency": f"{parallelization_efficiency:.1%}",            "critical_path_duration": critical_duration,            "total_duration_seconds": total_duration,            "failed": failure_count,            "successful": success_count,            "total_tasks": len(self.metrics),        return {        failure_count = len(self.metrics) - success_count        success_count = sum(1 for m in self.metrics.values() if m.success)            parallelization_efficiency = 1.0        else:            parallelization_efficiency = critical_duration / total_duration        if critical_duration > 0:        # Parallelization efficiency        )            if t in self.metrics            for t in critical_path            self.metrics.get(t, ExecutionMetrics("")).duration_seconds        critical_duration = sum(        critical_path = self.graph.get_critical_path()        total_duration = sum(m.duration_seconds for m in self.metrics.values())            return {"status": "no_executions"}        if not self.metrics:        """Analyze execution efficiency"""    def get_optimization_report(self) -> dict:        return results            )                *[execute_with_semaphore(task_id) for task_id in level_tasks]            await asyncio.gather(            logger.info(f"Executing level {level}: {level_tasks}")        for level, level_tasks in levels.items():        # Execute level by level                    self.active_tasks.discard(task_id)                finally:                        on_progress(task_id, False)                    if on_progress:                    logger.error(f"Task {task_id} failed: {e}")                    self.metrics[task_id] = metric                    metric.record_completion(duration, False, str(e))                    metric = ExecutionMetrics(task_id=task_id)                    duration = (datetime.utcnow() - start).total_seconds()                except Exception as e:                        on_progress(task_id, True)                    if on_progress:                    logger.info(f"Task {task_id} completed in {duration:.2f}s")                    results[task_id] = result                    self.metrics[task_id] = metric                    metric.record_completion(duration, True)                    metric = ExecutionMetrics(task_id=task_id)                    duration = (datetime.utcnow() - start).total_seconds()                    result = await tasks[task_id]()                    self.active_tasks.add(task_id)                    start = datetime.utcnow()                try:            async with semaphore:            """Execute task with concurrency limiting"""        async def execute_with_semaphore(task_id: str) -> None:        semaphore = asyncio.Semaphore(self.max_workers)        results = {}        )            f"can parallelize: {self.graph.can_parallelize()}"            f"critical path length: {len(critical_path)}, "            f"Execution plan: {len(levels)} levels, "        logger.info(        critical_path = self.graph.get_critical_path()        levels = self.graph.get_levels()        # Analyze execution levels        """            {task_id: result} execution results        Returns:            on_progress: Optional callback(task_id, success)            tasks: {task_id: async callable} mapping        Args:        Execute tasks with optimal parallelization.        """    ) -> dict[str, any]:        on_progress: Optional[Callable[[str, bool], None]] = None,        tasks: dict[str, Callable],        self,    async def execute_optimized(                self.graph.add_dependency(task_id, dep)            for dep in depends_on:        if depends_on:        self.graph.add_task(task_id)        """Register task with optional dependencies"""    def add_task(self, task_id: str, depends_on: list[str] = None) -> None:        self.active_tasks: set[str] = set()        self.metrics: dict[str, ExecutionMetrics] = {}        self.graph = DependencyGraph()        self.max_workers = max_workers    def __init__(self, max_workers: int = 8):    """    - Performance monitoring    - Resource-aware scheduling    - Parallel execution planning    - Dependency analysis    Optimizes asymptotically-bound task execution through:    """class ExecutionOptimizer:        return critical        critical = max(paths, key=len) if paths else []        paths = [longest_path_from(node) for node in self.nodes]            return path            memo[node] = path                path = [node] + longest_dep_path                )                    default=[]                    key=len,                    (longest_path_from(d, memo) for d in deps),                longest_dep_path = max(            else:                path = [node]            if not deps:            deps = self.edges.get(node, set())                return memo[node]            if node in memo:                memo = {}            if memo is None:        def longest_path_from(node: str, memo: dict = None) -> list[str]:        longest_paths = {}        # Calculate longest path from each node        """Identify critical path (longest dependency chain)"""    def get_critical_path(self) -> list[str]:        return any(len(tasks) > 1 for tasks in levels.values())        levels = self.get_levels()        """Check if execution graph has parallelizable tasks"""    def can_parallelize(self) -> bool:        return dict(sorted(levels.items()))            levels[level].append(node)                levels[level] = []            if level not in levels:        for node, level in level_map.items():                level_map[node] = max(level_map.get(d, 0) for d in deps) + 1            if deps:        for node, deps in self.edges.items():        level_map = {node: 0 for node in self.nodes}        levels = {}        """Group tasks by execution level (can run at same level in parallel)"""    def get_levels(self) -> dict[int, list[str]]:        return result            return []            logger.warning("Circular dependency detected in task graph")        if len(result) != len(self.nodes):                        queue.append(task)                    if in_degree[task] == 0:                    in_degree[task] -= 1                if current in deps:            for task, deps in self.edges.items():            # Find tasks that depend on current            result.append(current)            current = queue.pop(0)        while queue:        result = []        queue = [node for node in self.nodes if in_degree.get(node, 0) == 0]        in_degree = {node: len(deps) for node, deps in self.edges.items()}        # Kahn's algorithm for topological sort        """Return tasks in execution order (topological sort)"""    def topological_sort(self) -> list[str]:        self.edges[task_id].add(depends_on)            self.edges[task_id] = set()        if task_id not in self.edges:        """Add edge: task_id depends on depends_on"""    def add_dependency(self, task_id: str, depends_on: str) -> None:        self.edges[task_id] = set()        self.nodes[task_id] = metadata or {}        """Add task to graph"""    def add_task(self, task_id: str, metadata: dict = None) -> None:        self.edges: dict[str, set[str]] = {}        self.nodes: dict[str, dict] = {}    def __init__(self):    """    Uses topological sorting to identify tasks that can run concurrently.    Represents task dependencies to enable optimal parallel execution.    """class DependencyGraph:        self.error_message = error        self.success = success        self.duration_seconds = duration        self.end_time = datetime.utcnow()        """Record task completion"""    def record_completion(self, duration: float, success: bool, error: Optional[str] = None) -> None:    error_message: Optional[str] = None    success: bool = False    memory_mb: float = 0.0    cpu_percent: float = 0.0    duration_seconds: float = 0.0    end_time: Optional[datetime] = None    start_time: datetime = field(default_factory=datetime.utcnow)    task_id: str    """Tracks execution performance"""class ExecutionMetrics:@dataclasslogger = get_logger(__name__)from src.kortana.logger import get_loggerfrom typing import Callable, Optionalfrom datetime import datetimefrom dataclasses import dataclass, fieldimport asynciofrom __future__ import annotations"""- Intelligent task batching- Real-time performance profiling- Execution bottleneck detection- Dynamic resource allocation- Thread/process pool management- Dependency graph analysis and topological sortingMaximizes parallel execution efficiency through:KOR'TANA Execution OptimizerKOR'TANA Execution Optimizer

Maximizes parallel execution efficiency through:
- Dependency graph analysis and topological sorting
- Thread/process pool management
- Dynamic resource allocation
- Execution bottleneck detection
- Real-time performance profiling
- Intelligent task batching
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Optional

from src.kortana.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ExecutionMetrics:
    """Tracks execution performance"""

    task_id: str
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    success: bool = False
    error_message: Optional[str] = None

    def record_completion(self, duration: float, success: bool, error: Optional[str] = None) -> None:
        """Record task completion"""
        self.end_time = datetime.utcnow()
        self.duration_seconds = duration
        self.success = success
        self.error_message = error


class DependencyGraph:
    """
    Represents task dependencies to enable optimal parallel execution.
    Uses topological sorting to identify tasks that can run concurrently.
    """

    def __init__(self):
        self.nodes: dict[str, dict] = {}
        self.edges: dict[str, set[str]] = {}

    def add_task(self, task_id: str, metadata: dict = None) -> None:
        """Add task to graph"""
        self.nodes[task_id] = metadata or {}
        self.edges[task_id] = set()

    def add_dependency(self, task_id: str, depends_on: str) -> None:
        """Add edge: task_id depends on depends_on"""
        if task_id not in self.edges:
            self.edges[task_id] = set()
        self.edges[task_id].add(depends_on)

    def topological_sort(self) -> list[str]:
        """Return tasks in execution order (topological sort)"""
        # Kahn's algorithm for topological sort
        in_degree = {node: len(self.edges.get(node, set())) for node in self.nodes}
        queue = [node for node in self.nodes if in_degree[node] == 0]
        result = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            # Find tasks that depend on current
            for task, deps in self.edges.items():
                if current in deps:
                    in_degree[task] -= 1
                    if in_degree[task] == 0:
                        queue.append(task)

        if len(result) != len(self.nodes):
            logger.warning("Circular dependency detected in task graph")
            return []

        return result

    def get_levels(self) -> dict[int, list[str]]:
        """Group tasks by execution level (can run at same level in parallel)"""
        levels = {}
        level_map = {node: 0 for node in self.nodes}

        for node, deps in self.edges.items():
            if deps:
                level_map[node] = max(level_map.get(d, 0) for d in deps) + 1

        for node, level in level_map.items():
            if level not in levels:
                levels[level] = []
            levels[level].append(node)

        return dict(sorted(levels.items()))

    def can_parallelize(self) -> bool:
        """Check if execution graph has parallelizable tasks"""
        levels = self.get_levels()
        return any(len(tasks) > 1 for tasks in levels.values())

    def get_critical_path(self) -> list[str]:
        """Identify critical path (longest dependency chain)"""
        # Calculate longest path from each node
        longest_paths = {}

        def longest_path_from(node: str, memo: dict = None) -> list[str]:
            if memo is None:
                memo = {}
            if node in memo:
                return memo[node]

            deps = self.edges.get(node, set())
            if not deps:
                path = [node]
            else:
                longest_dep_path = max(
                    (longest_path_from(d, memo) for d in deps),
                    key=len,
                    default=[]
                )
                path = [node] + longest_dep_path

            memo[node] = path
            return path

        paths = [longest_path_from(node) for node in self.nodes]
        critical = max(paths, key=len) if paths else []
        return critical


class ExecutionOptimizer:
    """
    Optimizes asymptotically-bound task execution through:
    - Dependency analysis
    - Parallel execution planning
    - Resource-aware scheduling
    - Performance monitoring
    """

    def __init__(self, max_workers: int = 8):
        self.max_workers = max_workers
        self.graph = DependencyGraph()
        self.metrics: dict[str, ExecutionMetrics] = {}
        self.active_tasks: set[str] = set()

    def add_task(self, task_id: str, depends_on: list[str] = None) -> None:
        """Register task with optional dependencies"""
        self.graph.add_task(task_id)
        if depends_on:
            for dep in depends_on:
                self.graph.add_dependency(task_id, dep)

    async def execute_optimized(
        self,
        tasks: dict[str, Callable],
        on_progress: Optional[Callable[[str, bool], None]] = None,
    ) -> dict[str, any]:
        """
        Execute tasks with optimal parallelization.

        Args:
            tasks: {task_id: async callable} mapping
            on_progress: Optional callback(task_id, success)

        Returns:
            {task_id: result} execution results
        """
        # Analyze execution levels
        levels = self.graph.get_levels()
        critical_path = self.graph.get_critical_path()

        logger.info(
            f"Execution plan: {len(levels)} levels, "
            f"critical path length: {len(critical_path)}, "
            f"can parallelize: {self.graph.can_parallelize()}"
        )

        results = {}
        semaphore = asyncio.Semaphore(self.max_workers)

        async def execute_with_semaphore(task_id: str) -> None:
            """Execute task with concurrency limiting"""
            async with semaphore:
                try:
                    start = datetime.utcnow()
                    self.active_tasks.add(task_id)

                    result = await tasks[task_id]()
                    duration = (datetime.utcnow() - start).total_seconds()

                    metric = ExecutionMetrics(task_id=task_id)
                    metric.record_completion(duration, True)
                    self.metrics[task_id] = metric

                    results[task_id] = result
                    logger.info(f"Task {task_id} completed in {duration:.2f}s")

                    if on_progress:
                        on_progress(task_id, True)

                except Exception as e:
                    duration = (datetime.utcnow() - start).total_seconds()
                    metric = ExecutionMetrics(task_id=task_id)
                    metric.record_completion(duration, False, str(e))
                    self.metrics[task_id] = metric

                    logger.error(f"Task {task_id} failed: {e}")

                    if on_progress:
                        on_progress(task_id, False)

                finally:
                    self.active_tasks.discard(task_id)

        # Execute level by level
        for level, level_tasks in levels.items():
            logger.info(f"Executing level {level}: {level_tasks}")
            await asyncio.gather(
                *[execute_with_semaphore(task_id) for task_id in level_tasks]
            )

        return results

    def get_optimization_report(self) -> dict:
        """Analyze execution efficiency"""
        if not self.metrics:
            return {"status": "no_executions"}

        total_duration = sum(m.duration_seconds for m in self.metrics.values())
        critical_path = self.graph.get_critical_path()
        critical_duration = sum(
            self.metrics.get(t, ExecutionMetrics("")).duration_seconds
            for t in critical_path
            if t in self.metrics
        )

        # Parallelization efficiency
        if critical_duration > 0:
            parallelization_efficiency = critical_duration / total_duration
        else:
            parallelization_efficiency = 1.0

        success_count = sum(1 for m in self.metrics.values() if m.success)
        failure_count = len(self.metrics) - success_count

        return {
            "total_tasks": len(self.metrics),
            "successful": success_count,
            "failed": failure_count,
            "total_duration_seconds": total_duration,
            "critical_path_duration": critical_duration,
            "parallelization_efficiency": f"{parallelization_efficiency:.1%}",
            "potential_speedup": f"{total_duration / critical_duration:.1f}x" if critical_duration > 0 else "N/A",
            "critical_path_length": len(critical_path),
            "can_parallelize": self.graph.can_parallelize(),
        }
