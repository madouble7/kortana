"""
Optimization module inspired by RebelBrowser/Chromium architecture.

This module provides memory optimization, resource management,
and performance enhancements for Kortana.
"""

from .memory_optimizer import CacheStrategy, MemoryOptimizer
from .performance_metrics import MetricsCollector, PerformanceMetrics
from .priority_queue import DecisionQueue, Priority, PriorityQueue, TaskProcessor
from .resource_manager import ResourceManager, ResourcePool

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
