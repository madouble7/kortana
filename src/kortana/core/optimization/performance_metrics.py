"""
Performance Metrics inspired by Chromium's telemetry and profiling systems.

This module provides:
- Performance measurement and tracking
- Metrics collection for analysis
- Real-time monitoring capabilities
"""

import logging
import threading
import time
from collections import defaultdict
from typing import Any

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """
    Performance metrics tracker for monitoring system performance.

    Inspired by Chromium's telemetry and tracing capabilities.
    """

    def __init__(self, name: str):
        """
        Initialize performance metrics.

        Args:
            name: Metrics namespace name
        """
        self.name = name
        self._lock = threading.RLock()
        self._counters: dict[str, int] = defaultdict(int)
        self._timers: dict[str, list[float]] = defaultdict(list)
        self._gauges: dict[str, float] = {}

    def increment(self, counter: str, value: int = 1) -> None:
        """
        Increment a counter metric.

        Args:
            counter: Counter name
            value: Increment value
        """
        with self._lock:
            self._counters[counter] += value

    def record_time(self, timer: str, duration: float) -> None:
        """
        Record a timing measurement.

        Args:
            timer: Timer name
            duration: Duration in seconds
        """
        with self._lock:
            self._timers[timer].append(duration)

    def set_gauge(self, gauge: str, value: float) -> None:
        """
        Set a gauge metric.

        Args:
            gauge: Gauge name
            value: Gauge value
        """
        with self._lock:
            self._gauges[gauge] = value

    def get_counter(self, counter: str) -> int:
        """
        Get counter value.

        Args:
            counter: Counter name

        Returns:
            Counter value
        """
        with self._lock:
            return self._counters.get(counter, 0)

    def get_timer_stats(self, timer: str) -> dict[str, float]:
        """
        Get statistics for a timer.

        Args:
            timer: Timer name

        Returns:
            Dictionary with min, max, avg, count
        """
        with self._lock:
            times = self._timers.get(timer, [])
            if not times:
                return {"count": 0, "min": 0.0, "max": 0.0, "avg": 0.0}

            return {
                "count": len(times),
                "min": min(times),
                "max": max(times),
                "avg": sum(times) / len(times),
            }

    def get_gauge(self, gauge: str) -> float:
        """
        Get gauge value.

        Args:
            gauge: Gauge name

        Returns:
            Gauge value or 0.0 if not found
        """
        with self._lock:
            return self._gauges.get(gauge, 0.0)

    def get_all_metrics(self) -> dict[str, Any]:
        """
        Get all metrics.

        Returns:
            Dictionary with all counters, timers, and gauges
        """
        with self._lock:
            return {
                "counters": dict(self._counters),
                "timers": {
                    name: self.get_timer_stats(name) for name in self._timers.keys()
                },
                "gauges": dict(self._gauges),
            }

    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._timers.clear()
            self._gauges.clear()


class MetricsCollector:
    """
    Central metrics collector managing multiple performance metrics.

    Provides unified metrics collection across the system.
    """

    def __init__(self):
        """Initialize metrics collector."""
        self._metrics: dict[str, PerformanceMetrics] = {}
        self._lock = threading.RLock()
        logger.info("MetricsCollector initialized")

    def get_metrics(self, name: str) -> PerformanceMetrics:
        """
        Get or create metrics namespace.

        Args:
            name: Namespace name

        Returns:
            Performance metrics instance
        """
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = PerformanceMetrics(name)
                logger.debug(f"Created metrics namespace '{name}'")
            return self._metrics[name]

    def get_all_metrics(self) -> dict[str, Any]:
        """
        Get all metrics from all namespaces.

        Returns:
            Dictionary mapping namespace to metrics
        """
        with self._lock:
            return {
                name: metrics.get_all_metrics()
                for name, metrics in self._metrics.items()
            }

    def reset_all(self) -> None:
        """Reset all metrics in all namespaces."""
        with self._lock:
            for metrics in self._metrics.values():
                metrics.reset()
        logger.info("All metrics reset")


class Timer:
    """
    Context manager for timing operations.

    Example:
        with Timer(metrics, "operation"):
            # ... code to time ...
    """

    def __init__(self, metrics: PerformanceMetrics, name: str):
        """
        Initialize timer.

        Args:
            metrics: Performance metrics instance
            name: Timer name
        """
        self.metrics = metrics
        self.name = name
        self.start_time = 0.0

    def __enter__(self) -> "Timer":
        """Start timing."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Stop timing and record duration."""
        duration = time.time() - self.start_time
        self.metrics.record_time(self.name, duration)
