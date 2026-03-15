#!/usr/bin/env python
"""
Practical Monitoring Examples for Kor'tana's Agentic Workflow

This script demonstrates real-world monitoring patterns and techniques.
"""

import asyncio
import logging
import time
from collections import deque
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================================================
# Example 1: Real-time Metrics Monitoring
# ============================================================================


async def example_basic_metrics_monitoring():
    """Example 1: Monitor basic operational metrics."""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Basic Metrics Monitoring")
    print("=" * 70)

    # Simulating engine initialization
    # from kortana.brain import ChatEngine
    # engine = ChatEngine(config)

    print("\n📊 Getting operational metrics:\n")

    # This is what you would do:
    code = """
from kortana.brain import ChatEngine

engine = ChatEngine(config)

# Generate some activity
await engine.get_response("First query")
await engine.get_response("Second query")
await engine.get_response("First query")  # Cached

# Get metrics
metrics = engine.metrics.get_summary()

for operation, stats in metrics.items():
    print(f"\\n{operation}:")
    print(f"  Total Requests: {stats['total_requests']}")
    print(f"  Avg Latency: {stats['avg_time_ms']:.0f}ms")
    print(f"  Success Rate: {stats['success_rate']:.0f}%")
    print(f"  Min/Max: {stats['min_time_ms']:.0f}ms / {stats['max_time_ms']:.0f}ms")
"""
    print(code)


# ============================================================================
# Example 2: Cache Performance Analysis
# ============================================================================


class CacheAnalyzer:
    """Analyze cache performance."""

    def __init__(self, hits: int = 0, misses: int = 0):
        self.hits = hits
        self.misses = misses

    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0

    def calculate_time_saved(self, llm_time_ms: float = 2000, cache_time_ms: float = 5):
        """Calculate time saved by caching."""
        time_saved = self.hits * (llm_time_ms - cache_time_ms)
        return time_saved / 1000  # Convert to seconds


async def example_cache_monitoring():
    """Example 2: Monitor cache performance."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Cache Performance Analysis")
    print("=" * 70)

    # Simulating cache data
    analyzer = CacheAnalyzer(hits=70, misses=30)

    print("\n📈 Cache Performance Report:")
    print(f"  Hits: {analyzer.hits}")
    print(f"  Misses: {analyzer.misses}")
    print(f"  Hit Rate: {analyzer.hit_rate():.1%}")
    print(f"  Time Saved: {analyzer.calculate_time_saved():.1f} seconds")

    print("\n💡 Analysis:")
    if analyzer.hit_rate() > 0.7:
        print("  ✅ Excellent - High cache efficiency")
    elif analyzer.hit_rate() > 0.5:
        print("  ✅ Good - Reasonable cache efficiency")
    else:
        print("  ⚠️  Low - Consider increasing cache TTL")


# ============================================================================
# Example 3: Circuit Breaker Monitoring
# ============================================================================


class CircuitBreakerMonitor:
    """Monitor circuit breaker state."""

    def __init__(self):
        self.state_history = deque(maxlen=10)
        self.state_changes = 0

    def record_state(self, state: str, failure_count: int):
        self.state_history.append(
            {"timestamp": datetime.now(), "state": state, "failures": failure_count}
        )
        self.state_changes += 1

    def report(self):
        """Generate state change report."""
        print("\n🔄 Circuit Breaker State History:")
        for entry in self.state_history:
            print(
                f"  {entry['timestamp'].strftime('%H:%M:%S')} - "
                f"State: {entry['state']:12} | Failures: {entry['failures']}"
            )


async def example_circuit_breaker_monitoring():
    """Example 3: Monitor circuit breaker state."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Circuit Breaker Monitoring")
    print("=" * 70)

    monitor = CircuitBreakerMonitor()

    # Simulate circuit breaker events
    monitor.record_state("CLOSED", 0)
    await asyncio.sleep(0.1)
    monitor.record_state("CLOSED", 1)
    await asyncio.sleep(0.1)
    monitor.record_state("CLOSED", 3)
    await asyncio.sleep(0.1)
    monitor.record_state("OPEN", 5)
    await asyncio.sleep(0.1)
    monitor.record_state("HALF_OPEN", 5)
    await asyncio.sleep(0.1)
    monitor.record_state("CLOSED", 0)

    monitor.report()

    print(f"\n📊 Summary: {monitor.state_changes} state changes recorded")


# ============================================================================
# Example 4: Workflow Performance Tracking
# ============================================================================


class WorkflowProgressTracker:
    """Track workflow execution metrics."""

    def __init__(self):
        self.steps = []
        self.start_time = time.perf_counter()

    def record_step(self, step_name: str, success: bool, duration_ms: float = 0):
        """Record a workflow step."""
        self.steps.append(
            {
                "name": step_name,
                "success": success,
                "duration_ms": duration_ms,
                "timestamp": time.perf_counter(),
            }
        )

    def report(self):
        """Generate workflow report."""
        if not self.steps:
            return

        total_time = sum(s["duration_ms"] for s in self.steps)
        print("\n🔄 Workflow Execution Report:")

        for i, step in enumerate(self.steps, 1):
            status = "✅" if step["success"] else "❌"
            pct = (step["duration_ms"] / total_time * 100) if total_time > 0 else 0
            print(
                f"  {i}. {status} {step['name']:20} {step['duration_ms']:6.0f}ms ({pct:5.1f}%)"
            )

        print(f"\n  Total: {total_time:.0f}ms")


async def example_workflow_monitoring():
    """Example 4: Monitor workflow performance."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Workflow Performance Tracking")
    print("=" * 70)

    tracker = WorkflowProgressTracker()

    # Simulate workflow steps
    print("\n🚀 Simulating agentic workflow:")

    # Step 1: Input processing
    print("  1. Processing user input...")
    tracker.record_step("input_processing", True, 50)
    await asyncio.sleep(0.05)

    # Step 2: LLM call
    print("  2. Calling LLM...")
    tracker.record_step("llm_generation", True, 1500)
    await asyncio.sleep(0.1)

    # Step 3: Memory update
    print("  3. Updating memory...")
    tracker.record_step("memory_update", True, 100)
    await asyncio.sleep(0.05)

    # Step 4: Output formatting
    print("  4. Formatting output...")
    tracker.record_step("output_formatting", True, 30)
    await asyncio.sleep(0.05)

    tracker.report()


# ============================================================================
# Example 5: Error Rate Analysis
# ============================================================================


class ErrorRateTracker:
    """Track error rates over time."""

    def __init__(self, window_size: int = 100, error_threshold: float = 0.05):
        self.window = deque(maxlen=window_size)
        self.error_threshold = error_threshold

    def record(self, success: bool):
        """Record operation success/failure."""
        self.window.append(success)

    def error_rate(self) -> float:
        """Calculate current error rate."""
        if not self.window:
            return 0
        failures = sum(1 for s in self.window if not s)
        return failures / len(self.window)

    def should_alert(self) -> bool:
        """Check if error rate is above threshold."""
        return self.error_rate() > self.error_threshold

    def report(self):
        """Generate error rate report."""
        rate = self.error_rate()
        print(f"\n⚠️  Error Rate: {rate:.1%}")

        if self.should_alert():
            print(
                f"  🚨 ALERT: Error rate above threshold ({self.error_threshold:.1%})"
            )
        else:
            print("  ✅ Within acceptable range")


async def example_error_rate_monitoring():
    """Example 5: Monitor error rates."""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Error Rate Monitoring")
    print("=" * 70)

    tracker = ErrorRateTracker(window_size=50, error_threshold=0.05)

    # Simulate operations with 2% error rate
    print("\n📊 Simulating 50 operations with ~2% error rate:")
    success_count = 0
    for i in range(50):
        success = (i % 50) != 0  # One error every 50 operations
        tracker.record(success)
        if success:
            success_count += 1

    print(f"  Successful: {success_count}/50")
    tracker.report()


# ============================================================================
# Example 6: Latency Percentiles
# ============================================================================


class LatencyPercentileTracker:
    """Track latency percentiles."""

    def __init__(self, window_size: int = 100):
        self.latencies = deque(maxlen=window_size)

    def record(self, duration_ms: float):
        """Record operation duration."""
        self.latencies.append(duration_ms)

    def percentile(self, p: int) -> float:
        """Calculate percentile (e.g., p=95 for P95)."""
        if not self.latencies:
            return 0
        sorted_latencies = sorted(self.latencies)
        index = int(len(sorted_latencies) * (p / 100))
        return sorted_latencies[index]

    def report(self):
        """Generate latency report."""
        print(f"\n⏱️  Latency Distribution (from {len(self.latencies)} samples):")
        print(f"  Min:  {min(self.latencies):.0f}ms")
        print(f"  P50:  {self.percentile(50):.0f}ms")
        print(f"  P95:  {self.percentile(95):.0f}ms")
        print(f"  P99:  {self.percentile(99):.0f}ms")
        print(f"  Max:  {max(self.latencies):.0f}ms")


async def example_latency_percentiles():
    """Example 6: Monitor latency percentiles."""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Latency Percentile Tracking")
    print("=" * 70)

    tracker = LatencyPercentileTracker(window_size=100)

    print("\n📊 Simulating 100 request latencies:")

    # Simulate realistic latency distribution
    import random

    random.seed(42)

    for _ in range(100):
        # Most requests: 1000-1500ms
        if random.random() < 0.95:
            latency = random.gauss(1200, 100)
        # Slow requests: 2000-3000ms
        else:
            latency = random.gauss(2500, 300)

        tracker.record(max(100, latency))  # Min 100ms

    tracker.report()


# ============================================================================
# Example 7: Real-time Dashboard Simulation
# ============================================================================


async def example_real_time_dashboard():
    """Example 7: Real-time monitoring dashboard."""
    print("\n" + "=" * 70)
    print("EXAMPLE 7: Real-time Monitoring Dashboard")
    print("=" * 70)

    print("\n📊 Live Dashboard (updating every 2 seconds):\n")

    # Simulate dashboard updates
    for iteration in range(3):
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] Dashboard Update #{iteration + 1}"
        )
        print("-" * 70)

        # Metrics
        print("PERFORMANCE METRICS:")
        print("  llm_call:      1245.3ms avg | 99.5% success | 1,234 requests")
        print("  memory_load:     52.1ms avg | 100.0% success |    45 requests")
        print("  cache_hit:        4.8ms avg | 100.0% success |   862 requests")

        # Cache status
        print("\nCACHE STATUS:")
        print("  Hit Rate: 75.2% (862 hits / 1,145 total)")
        print("  Size: 87/100 items | TTL: 300s")
        print("  Time Saved: 6.8 seconds")

        # Circuit breaker
        print("\nCIRCUIT BREAKER:")
        print("  State: CLOSED ✅ | Failures: 0/5 | Recovery: 60s")

        # Resource usage
        print("\nRESOURCE USAGE:")
        print("  Memory: 125.3 MB | CPU: 23.4%")

        if iteration < 2:
            print("\nWaiting 2s for next update...\n")
            await asyncio.sleep(2)


# ============================================================================
# Example 8: Health Check Endpoint
# ============================================================================


async def example_health_check():
    """Example 8: Health check endpoint."""
    print("\n" + "=" * 70)
    print("EXAMPLE 8: Health Check Endpoint")
    print("=" * 70)

    print("\n🏥 GET /health")
    print("-" * 70)

    health_response = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "circuit_breaker": "closed",
        "cache_hit_rate": 0.752,
        "operations": {
            "llm_call": {"avg_ms": 1245, "success_rate": 99.5},
            "memory_load": {"avg_ms": 52, "success_rate": 100.0},
        },
    }

    import json

    print(json.dumps(health_response, indent=2))


# ============================================================================
# Main
# ============================================================================


async def main():
    """Run all examples."""
    print("\n")
    print("█" * 70)
    print("█ KOR'TANA MONITORING - PRACTICAL EXAMPLES")
    print("█" * 70)

    # Run all examples
    await example_basic_metrics_monitoring()
    await example_cache_monitoring()
    await example_circuit_breaker_monitoring()
    await example_workflow_monitoring()
    await example_error_rate_monitoring()
    await example_latency_percentiles()
    await example_real_time_dashboard()
    await example_health_check()

    print("\n" + "=" * 70)
    print("✅ All monitoring examples completed!")
    print("=" * 70)
    print("\nSee MONITORING_GUIDE.md for detailed explanations and more patterns.")
    print("\nIntegrate these patterns into your production system for comprehensive")
    print("observability of Kor'tana's agentic workflow.\n")


if __name__ == "__main__":
    asyncio.run(main())
