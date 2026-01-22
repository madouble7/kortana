"""
Optimization module inspired by RebelBrowser/Chromium architecture.

This module provides memory optimization, resource management,
and performance enhancements for Kortana.
"""

from .memory_optimizer import MemoryOptimizer, CacheStrategy
from .resource_manager import ResourceManager, ResourcePool
from .performance_metrics import PerformanceMetrics, MetricsCollector
from .priority_queue import PriorityQueue, Priority, DecisionQueue, TaskProcessor

__all__ = [
    "MemoryOptimizer",
    "CacheStrategy",
    "ResourceManager",
    "ResourcePool",
    "PerformanceMetrics",
    "MetricsCollector",
    "PriorityQueue",
    "Priority",
    "DecisionQueue",
    "TaskProcessor",
]
