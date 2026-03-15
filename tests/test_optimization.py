"""
Tests for optimization module inspired by RebelBrowser/Chromium.
"""

import sys
import os
import time
import unittest
from unittest.mock import MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.kortana.core.optimization.memory_optimizer import (
    MemoryOptimizer,
    CacheStrategy,
    LRUCache,
    MemoryPool,
)
from src.kortana.core.optimization.resource_manager import (
    ResourceManager,
    ResourcePool,
)
from src.kortana.core.optimization.performance_metrics import (
    PerformanceMetrics,
    MetricsCollector,
    Timer,
)
from src.kortana.core.optimization.priority_queue import (
    PriorityQueue,
    Priority,
    DecisionQueue,
    TaskProcessor,
)


class TestMemoryOptimizer(unittest.TestCase):
    """Test memory optimization features."""

    def test_lru_cache_basic(self):
        """Test basic LRU cache operations."""
        optimizer = MemoryOptimizer(cache_capacity=3)
        cache = optimizer.get_cache("test")

        # Test put and get
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")

        self.assertEqual(cache.get("key1"), "value1")
        self.assertEqual(cache.get("key2"), "value2")
        self.assertEqual(cache.get("key3"), "value3")

    def test_lru_cache_eviction(self):
        """Test LRU cache eviction."""
        optimizer = MemoryOptimizer(cache_capacity=2)
        cache = optimizer.get_cache("test")

        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")  # Should evict key1

        self.assertIsNone(cache.get("key1"))
        self.assertEqual(cache.get("key2"), "value2")
        self.assertEqual(cache.get("key3"), "value3")

    def test_cache_stats(self):
        """Test cache statistics."""
        optimizer = MemoryOptimizer(cache_capacity=5)
        cache = optimizer.get_cache("test")

        cache.put("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss

        stats = cache.get_stats()
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(stats["size"], 1)

    def test_memory_pool(self):
        """Test memory pool object reuse."""

        def factory():
            return {"data": []}

        optimizer = MemoryOptimizer()
        pool = optimizer.get_pool("test", factory=factory, max_size=10)

        # Acquire and release
        obj1 = pool.acquire()
        obj1["data"].append(1)
        pool.release(obj1)

        obj2 = pool.acquire()
        self.assertIsNotNone(obj2)

        stats = pool.get_stats()
        self.assertGreater(stats["reused"], 0)

    def test_optimizer_stats(self):
        """Test optimizer statistics collection."""
        optimizer = MemoryOptimizer()
        optimizer.get_cache("cache1")
        optimizer.get_pool("pool1", factory=lambda: {})

        stats = optimizer.get_stats()
        self.assertIn("caches", stats)
        self.assertIn("pools", stats)
        self.assertIn("cache1", stats["caches"])
        self.assertIn("pool1", stats["pools"])


class TestResourceManager(unittest.TestCase):
    """Test resource management features."""

    def test_resource_pool_acquire_release(self):
        """Test resource acquisition and release."""

        def factory():
            return {"id": time.time()}

        pool = ResourcePool("test", factory=factory, min_size=2, max_size=5)

        resource1 = pool.acquire()
        resource2 = pool.acquire()

        self.assertIsNotNone(resource1)
        self.assertIsNotNone(resource2)

        pool.release(resource1)
        pool.release(resource2)

        stats = pool.get_stats()
        self.assertEqual(stats["available"], 2)

    def test_resource_pool_max_size(self):
        """Test resource pool max size enforcement."""

        def factory():
            return {"id": time.time()}

        pool = ResourcePool("test", factory=factory, min_size=1, max_size=3)

        resources = [pool.acquire() for _ in range(5)]

        stats = pool.get_stats()
        # Should create temporary resources beyond max
        self.assertGreaterEqual(stats["total_created"], 3)

    def test_resource_cleanup(self):
        """Test resource cleanup function."""
        cleanup_called = []

        def factory():
            return {"id": time.time()}

        def cleanup(resource):
            cleanup_called.append(resource)

        pool = ResourcePool(
            "test", factory=factory, cleanup=cleanup, min_size=1, max_size=2
        )

        resource = pool.acquire()
        pool.release(resource)

        # Acquire more than max to trigger cleanup
        for _ in range(5):
            pool.acquire()

        self.assertGreater(len(cleanup_called), 0)

    def test_resource_manager(self):
        """Test resource manager coordination."""
        manager = ResourceManager()

        pool1 = manager.create_pool("pool1", factory=lambda: {}, min_size=2)
        pool2 = manager.create_pool("pool2", factory=lambda: [], min_size=3)

        self.assertIsNotNone(pool1)
        self.assertIsNotNone(pool2)

        stats = manager.get_stats()
        self.assertEqual(stats["total_pools"], 2)


class TestPerformanceMetrics(unittest.TestCase):
    """Test performance metrics features."""

    def test_counter_metrics(self):
        """Test counter metrics."""
        metrics = PerformanceMetrics("test")

        metrics.increment("requests")
        metrics.increment("requests")
        metrics.increment("errors", 5)

        self.assertEqual(metrics.get_counter("requests"), 2)
        self.assertEqual(metrics.get_counter("errors"), 5)

    def test_timer_metrics(self):
        """Test timer metrics."""
        metrics = PerformanceMetrics("test")

        metrics.record_time("operation", 0.1)
        metrics.record_time("operation", 0.2)
        metrics.record_time("operation", 0.3)

        stats = metrics.get_timer_stats("operation")
        self.assertEqual(stats["count"], 3)
        self.assertAlmostEqual(stats["min"], 0.1, places=6)
        self.assertAlmostEqual(stats["max"], 0.3, places=6)
        self.assertAlmostEqual(stats["avg"], 0.2, places=6)

    def test_gauge_metrics(self):
        """Test gauge metrics."""
        metrics = PerformanceMetrics("test")

        metrics.set_gauge("memory_usage", 123.45)
        metrics.set_gauge("cpu_usage", 67.89)

        self.assertEqual(metrics.get_gauge("memory_usage"), 123.45)
        self.assertEqual(metrics.get_gauge("cpu_usage"), 67.89)

    def test_timer_context_manager(self):
        """Test timer context manager."""
        metrics = PerformanceMetrics("test")

        with Timer(metrics, "operation"):
            time.sleep(0.01)

        stats = metrics.get_timer_stats("operation")
        self.assertEqual(stats["count"], 1)
        self.assertGreater(stats["avg"], 0.01)

    def test_metrics_collector(self):
        """Test metrics collector."""
        collector = MetricsCollector()

        metrics1 = collector.get_metrics("namespace1")
        metrics2 = collector.get_metrics("namespace2")

        metrics1.increment("count1")
        metrics2.increment("count2")

        all_metrics = collector.get_all_metrics()
        self.assertIn("namespace1", all_metrics)
        self.assertIn("namespace2", all_metrics)


class TestPriorityQueue(unittest.TestCase):
    """Test priority queue and task scheduling."""

    def test_priority_queue_ordering(self):
        """Test priority-based task ordering."""
        queue = PriorityQueue("test")

        queue.enqueue(lambda: None, priority=Priority.LOW, task_id="low")
        queue.enqueue(lambda: None, priority=Priority.CRITICAL, task_id="critical")
        queue.enqueue(lambda: None, priority=Priority.NORMAL, task_id="normal")

        task1 = queue.dequeue(timeout=1.0)
        task2 = queue.dequeue(timeout=1.0)
        task3 = queue.dequeue(timeout=1.0)

        self.assertEqual(task1.task_id, "critical")
        self.assertEqual(task2.task_id, "normal")
        self.assertEqual(task3.task_id, "low")

    def test_priority_queue_empty(self):
        """Test dequeue from empty queue."""
        queue = PriorityQueue("test")

        task = queue.dequeue(timeout=0.1)
        self.assertIsNone(task)

    def test_task_processor(self):
        """Test task processor execution."""
        queue = PriorityQueue("test")
        processor = TaskProcessor(queue, num_workers=2, name="test")

        results = []

        def task_func(value):
            results.append(value)

        processor.start()

        queue.enqueue(task_func, Priority.NORMAL, "task1", 1)
        queue.enqueue(task_func, Priority.NORMAL, "task2", 2)
        queue.enqueue(task_func, Priority.NORMAL, "task3", 3)

        # Wait for tasks to complete
        time.sleep(0.5)

        processor.stop()

        self.assertEqual(len(results), 3)
        self.assertIn(1, results)
        self.assertIn(2, results)
        self.assertIn(3, results)

    def test_decision_queue(self):
        """Test decision queue."""
        decision_queue = DecisionQueue(num_workers=2)
        decision_queue.start()

        executed = []

        def decision_func(decision_id):
            executed.append(decision_id)

        decision_queue.submit_decision(
            decision_func, Priority.HIGH, "decision1", "dec1"
        )
        decision_queue.submit_decision(
            decision_func, Priority.NORMAL, "decision2", "dec2"
        )

        # Wait for execution
        time.sleep(0.5)

        decision_queue.stop()

        self.assertEqual(len(executed), 2)

    def test_queue_stats(self):
        """Test queue statistics."""
        queue = PriorityQueue("test")

        queue.enqueue(lambda: None, Priority.NORMAL, "task1")
        queue.enqueue(lambda: None, Priority.HIGH, "task2")

        stats = queue.get_stats()
        self.assertEqual(stats["pending"], 2)
        self.assertEqual(stats["total_enqueued"], 2)


class TestIntegration(unittest.TestCase):
    """Integration tests for optimization features."""

    def test_full_optimization_stack(self):
        """Test integration of all optimization features."""
        # Setup
        optimizer = MemoryOptimizer(cache_capacity=10)
        resource_manager = ResourceManager()
        collector = MetricsCollector()
        decision_queue = DecisionQueue(num_workers=2)

        # Create resources
        cache = optimizer.get_cache("test")
        pool = resource_manager.create_pool("test", factory=lambda: {})
        metrics = collector.get_metrics("test")

        # Use features
        cache.put("key1", "value1")
        resource = pool.acquire()
        metrics.increment("operations")

        decision_queue.start()

        results = []

        def decision(value):
            results.append(value)

        decision_queue.submit_decision(decision, Priority.HIGH, "test", 42)

        time.sleep(0.5)
        decision_queue.stop()

        # Verify
        self.assertEqual(cache.get("key1"), "value1")
        self.assertIsNotNone(resource)
        self.assertEqual(metrics.get_counter("operations"), 1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], 42)

        # Get all stats
        optimizer_stats = optimizer.get_stats()
        manager_stats = resource_manager.get_stats()
        metrics_stats = collector.get_all_metrics()
        queue_stats = decision_queue.get_stats()

        self.assertIsNotNone(optimizer_stats)
        self.assertIsNotNone(manager_stats)
        self.assertIsNotNone(metrics_stats)
        self.assertIsNotNone(queue_stats)


if __name__ == "__main__":
    unittest.main()
