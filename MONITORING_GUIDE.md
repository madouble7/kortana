# Monitoring Kor'tana's Agentic Workflow

**Complete guide to monitoring, observing, and troubleshooting Kor'tana's performance and behavior**

---

## Quick Reference

```python
from kortana.brain import ChatEngine

# Initialize with session
engine = ChatEngine(config, session_id="my-session")

# 1. **Real-time Metrics**
metrics = engine.metrics.get_summary()
print(f"LLM avg latency: {metrics['llm_call']['avg_time_ms']:.0f}ms")

# 2. **Cache Performance**
print(f"Cache hit rate: {engine.response_cache.hit_rate:.1%}")

# 3. **Circuit Breaker Status**
print(f"LLM Service: {engine.llm_circuit_breaker.state.value}")

# 4. **Log Analysis**
import logging
logging.basicConfig(level=logging.DEBUG)  # Enable debug logs
```

---

## 1. Built-in Metrics Collection

### Overview

Kor'tana automatically collects performance metrics for all major operations:

```python
from kortana.brain import ChatEngine

engine = ChatEngine(config)

# Generate some activity
response = await engine.get_response("What is 2+2?")
response = await engine.get_response("What is 2+2?")  # Second call cached

# Get metrics
metrics = engine.metrics.get_summary()

# Output:
# {
#     'llm_call': {
#         'avg_time_ms': 1500.5,
#         'min_time_ms': 1200.0,
#         'max_time_ms': 1800.0,
#         'success_rate': 100.0,
#         'total_requests': 2
#     },
#     'memory_load': {
#         'avg_time_ms': 45.2,
#         'min_time_ms': 42.0,
#         'max_time_ms': 48.0,
#         'success_rate': 100.0,
#         'total_requests': 1
#     }
# }
```

### Key Metrics Explained

| Metric | Meaning | Healthy Range |
|--------|---------|---------------|
| `avg_time_ms` | Average operation duration | Depends on operation type |
| `min_time_ms` | Fastest operation | Should be consistent |
| `max_time_ms` | Slowest operation | Investigate if spikes > 2x avg |
| `success_rate` | % of operations that succeeded | 99%+ |
| `total_requests` | Number of operations tracked | Increases with usage |

### Detailed Metrics Breakdown

```python
from kortana.brain import ChatEngine

engine = ChatEngine(config)

# ... perform operations ...

metrics = engine.metrics.get_summary()

for operation, stats in metrics.items():
    print(f"\n📊 {operation.upper()}")
    print(f"   Total Requests: {stats['total_requests']}")
    print(f"   Success Rate: {stats['success_rate']:.1f}%")
    print(f"   Avg Latency: {stats['avg_time_ms']:.0f}ms")
    print(f"   Min: {stats['min_time_ms']:.0f}ms | Max: {stats['max_time_ms']:.0f}ms")

    # Red flags
    if stats['success_rate'] < 95:
        print(f"   ⚠️  SUCCESS RATE LOW: {stats['success_rate']:.0f}%")
    if stats['avg_time_ms'] > 3000:
        print(f"   ⚠️  LATENCY HIGH: {stats['avg_time_ms']:.0f}ms")
```

---

## 2. Cache Performance Monitoring

### Check Cache Hit Rate

```python
# Direct from cache object
cache = engine.response_cache

print(f"Cache Hit Rate: {cache.hit_rate:.1%}")
print(f"Hits: {cache.hits}")
print(f"Misses: {cache.misses}")
print(f"Size: {len(cache.cache)} / {cache.max_size} items")

# Calculate efficiency
if cache.hits + cache.misses > 0:
    efficiency = cache.hits / (cache.hits + cache.misses)
    print(f"Cache Efficiency: {efficiency:.1%}")

    # Speedup calculation
    # Assuming LLM call = 2000ms, cache hit = 5ms
    time_saved_ms = cache.hits * (2000 - 5)
    print(f"Time Saved: {time_saved_ms / 1000:.1f}s")
```

### Expected Cache Behavior

```
Scenario: ChatBot with 100 queries/day, 70% repeats

Without Cache:
- All 100 queries: 100 × 2000ms = 200 seconds

With Cache (5-minute TTL):
- Unique queries (30): 30 × 2000ms = 60 seconds
- Cached (70): 70 × 5ms = 350ms
- Total: ~60.35 seconds

Improvement: 3.3x faster!
```

### Cache Diagnostics

```python
# Monitor cache for problems
async def diagnose_cache(engine):
    cache = engine.response_cache

    # Issue 1: Hit rate too low
    if cache.hit_rate < 0.5:
        print("⚠️  Hit rate below 50% - consider:")
        print("   - Reducing TTL for more frequent updates")
        print("   - Queries may not be repeating enough")
        print("   - TTL may be expiring too quickly")

    # Issue 2: Cache is full
    if len(cache.cache) >= cache.max_size * 0.9:
        print("⚠️  Cache is 90% full")
        print("   - Consider increasing max_size")
        print("   - Or reducing TTL to clear old entries")
        print("   - Current entries:", len(cache.cache))

    # Issue 3: Cache not being used
    if cache.hits + cache.misses == 0:
        print("⚠️  Cache has no activity")
        print("   - Verify queries are identical")
        print("   - Verify cache is being accessed")
```

---

## 3. Circuit Breaker Monitoring

### Real-time Status

```python
from kortana.utils.performance import CircuitState

breaker = engine.llm_circuit_breaker

print(f"State: {breaker.state.value.upper()}")
print(f"Failures: {breaker.failure_count}")
print(f"Recovery in: ~{breaker.config.recovery_timeout}s")

# State meanings:
if breaker.state == CircuitState.CLOSED:
    print("✅ HEALTHY - Service operating normally")
elif breaker.state == CircuitState.HALF_OPEN:
    print("🔄 RECOVERING - Testing service recovery")
elif breaker.state == CircuitState.OPEN:
    print("🚫 FAILURE - Service is down, rejecting requests temporarily")
```

### Circuit Breaker Behavior

```
Timeline of Circuit Breaker:

1. CLOSED (Normal)
   - Service responds normally
   - All requests pass through

2. Failure occurs (1st-5th)
   - Still CLOSED
   - Failures accumulate (5 threshold)

3. Threshold reached → OPEN
   - New requests fail immediately (< 1ms)
   - Prevents cascade failure
   - Waits 60 seconds

4. HALF_OPEN (Testing)
   - Allows test requests through
   - If success: back to CLOSED ✅
   - If failure: back to OPEN ❌

5. 60-second recovery window
   - HALF_OPEN → CLOSED if stable
   - HALF_OPEN → OPEN if continued failures
```

### Alerting Patterns

```python
async def monitor_circuit_breaker(engine, alert_callback):
    breaker = engine.llm_circuit_breaker
    last_state = None

    while True:
        if breaker.state != last_state:
            last_state = breaker.state

            if last_state == CircuitState.OPEN:
                # ALERT: Service is down
                await alert_callback(
                    severity="CRITICAL",
                    message=f"LLM Service has {breaker.failure_count} failures - circuit OPEN"
                )
            elif last_state == CircuitState.HALF_OPEN:
                # INFO: Service recovering
                await alert_callback(
                    severity="WARNING",
                    message="LLM Service recovering - circuit HALF_OPEN"
                )
            elif last_state == CircuitState.CLOSED:
                # RESOLVED: Service recovered
                await alert_callback(
                    severity="INFO",
                    message="LLM Service healthy - circuit CLOSED"
                )

        await asyncio.sleep(5)  # Check every 5 seconds
```

---

## 4. Logging Configuration

### Enable Debug Logging

```python
import logging
import sys

# Basic setup
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('kortana.log')
    ]
)

# Or use Kor'tana's config
from kortana.config.schema import LoggingConfig

log_config = LoggingConfig(
    level="DEBUG",
    file_enabled=True,
    console_enabled=True
)
```

### Key Log Levels

| Level | Used For | When to Enable |
|-------|----------|----------------|
| DEBUG | Detailed diagnostic info | Development, troubleshooting |
| INFO | Operational milestones | Always (production too) |
| WARNING | Potential issues | Always (may indicate problems) |
| ERROR | Errors requiring attention | Always |
| CRITICAL | System failures | Always |

### Log Patterns to Watch

```python
# Search for these in logs to detect issues

# 1. Circuit breaker state changes
"Circuit breaker opened after 5 failures"
"Circuit breaker entering HALF_OPEN state"
"Circuit breaker reset to CLOSED"

# 2. Cache operations
"Cache hit for get_response"  # Good!
"Cached value: query_response_xyz"  # Cache storing

# 3. Error conditions
"ServiceError"  # External service failed
"ModelError"    # Model initialization failed
"TimeoutError"  # Operation took too long

# 4. Memory operations
"Memory appended successfully"
"Memory append failed"

# 5. Performance timing (at INFO level when > 100ms)
"llm_call took 1245.3ms"
"memory_load took 52.1ms"
```

### Parsing Logs for Metrics

```python
import re
from collections import defaultdict

def analyze_logs(log_file: str):
    """Extract metrics from log file."""
    metrics = defaultdict(list)

    with open(log_file, 'r') as f:
        for line in f:
            # Extract timing
            match = re.search(r'(\w+) took ([\d.]+)ms', line)
            if match:
                operation = match.group(1)
                duration = float(match.group(2))
                metrics[operation].append(duration)

            # Extract errors
            if "ERROR" in line or "CRITICAL" in line:
                print(f"Found error: {line.strip()}")

            # Extract circuit breaker state changes
            if "Circuit breaker" in line and ("opened" in line or "CLOSED" in line):
                print(f"Circuit breaker event: {line.strip()}")

    # Calculate statistics
    for operation, times in metrics.items():
        print(f"\n{operation}:")
        print(f"  Calls: {len(times)}")
        print(f"  Avg: {sum(times)/len(times):.1f}ms")
        print(f"  Min: {min(times):.1f}ms")
        print(f"  Max: {max(times):.1f}ms")

analyze_logs("kortana.log")
```

---

## 5. Real-time Monitoring Dashboard

### Simple Text Dashboard

```python
import asyncio
from rich.console import Console
from rich.table import Table
from kurta.brain import ChatEngine

console = Console()

async def live_dashboard(engine: ChatEngine, refresh_interval: int = 5):
    """Display live monitoring dashboard."""

    while True:
        console.clear()
        console.print("[bold cyan]Kor'tana Monitoring Dashboard[/bold cyan]")
        console.print(f"Session: {engine.session_id}\n")

        # Metrics table
        metrics_table = Table(title="Performance Metrics")
        metrics_table.add_column("Operation")
        metrics_table.add_column("Avg (ms)", justify="right")
        metrics_table.add_column("Success %", justify="right")
        metrics_table.add_column("Requests", justify="right")

        metrics = engine.metrics.get_summary()
        for op, stats in metrics.items():
            color = "green" if stats['success_rate'] > 99 else "yellow" if stats['success_rate'] > 95 else "red"
            metrics_table.add_row(
                op,
                f"{stats['avg_time_ms']:.0f}",
                f"[{color}]{stats['success_rate']:.0f}%[/{color}]",
                str(stats['total_requests'])
            )
        console.print(metrics_table)

        # Cache status
        cache_table = Table(title="Cache Status")
        cache_table.add_column("Property")
        cache_table.add_column("Value")
        cache = engine.response_cache
        cache_table.add_row("Hit Rate", f"{cache.hit_rate:.1%}")
        cache_table.add_row("Size", f"{len(cache.cache)}/{cache.max_size} items")
        cache_table.add_row("TTL", f"{cache.default_ttl}s")
        console.print(cache_table)

        # Circuit breaker status
        cb_table = Table(title="Circuit Breaker")
        cb_table.add_column("Property")
        cb_table.add_column("Value")
        breaker = engine.llm_circuit_breaker
        state_color = {
            "closed": "green",
            "open": "red",
            "half_open": "yellow"
        }[breaker.state.value]
        cb_table.add_row("State", f"[{state_color}]{breaker.state.value.upper()}[/{state_color}]")
        cb_table.add_row("Failures", str(breaker.failure_count))
        cb_table.add_row("Threshold", str(breaker.config.failure_threshold))
        console.print(cb_table)

        console.print(f"\nUpdating in {refresh_interval}s... (Ctrl+C to exit)")
        await asyncio.sleep(refresh_interval)

# Run dashboard
# asyncio.run(live_dashboard(engine))
```

### Prometheus-style Metrics Export

```python
from prometheus_client import Counter, Histogram, Gauge

# Define custom metrics
llm_requests = Counter('llm_requests_total', 'Total LLM requests')
llm_duration = Histogram('llm_request_duration_ms', 'LLM request duration')
cache_hit_rate = Gauge('cache_hit_rate', 'Cache hit rate')
circuit_breaker_open = Gauge('circuit_breaker_open', 'Is circuit breaker open (1=yes)')

def export_metrics_to_prometheus(engine):
    """Export Kor'tana metrics to Prometheus format."""
    metrics = engine.metrics.get_summary()

    if 'llm_call' in metrics:
        llm_metrics = metrics['llm_call']
        llm_requests.inc(llm_metrics['total_requests'])
        llm_duration.observe(llm_metrics['avg_time_ms'])

    cache_hit_rate.set(engine.response_cache.hit_rate)

    breaker_open = 1 if engine.llm_circuit_breaker.state.value == 'open' else 0
    circuit_breaker_open.set(breaker_open)
```

---

## 6. Workflow-Specific Monitoring

### Agent Loop Monitoring

```python
import time
from dataclasses import dataclass

@dataclass
class WorkflowMetrics:
    step: str
    duration_ms: float
    success: bool
    error: str = None

async def monitor_agent_workflow(engine: ChatEngine):
    """Monitor the agentic workflow."""
    workflow_metrics = []

    # Step 1: Get user input
    step_start = time.perf_counter()
    user_input = "What should I work on today?"
    step_duration = (time.perf_counter() - step_start) * 1000
    workflow_metrics.append(WorkflowMetrics("input", step_duration, True))

    # Step 2: Get response from LLM
    step_start = time.perf_counter()
    try:
        response = await engine.get_response(user_input)
        step_duration = (time.perf_counter() - step_start) * 1000
        workflow_metrics.append(WorkflowMetrics("llm_generate", step_duration, True))
    except Exception as e:
        step_duration = (time.perf_counter() - step_start) * 1000
        workflow_metrics.append(WorkflowMetrics("llm_generate", step_duration, False, str(e)))

    # Step 3: Update memory
    step_start = time.perf_counter()
    try:
        engine.add_assistant_message(response)
        step_duration = (time.perf_counter() - step_start) * 1000
        workflow_metrics.append(WorkflowMetrics("memory_update", step_duration, True))
    except Exception as e:
        step_duration = (time.perf_counter() - step_start) * 1000
        workflow_metrics.append(WorkflowMetrics("memory_update", step_duration, False, str(e)))

    # Report workflow
    print("\n🔄 Workflow Execution Report:")
    total_time = sum(m.duration_ms for m in workflow_metrics)

    for metric in workflow_metrics:
        status = "✅" if metric.success else "❌"
        pct = (metric.duration_ms / total_time * 100) if total_time > 0 else 0
        print(f"  {status} {metric.step}: {metric.duration_ms:.0f}ms ({pct:.0f}%)")
        if metric.error:
            print(f"      Error: {metric.error}")

    print(f"\n  Total: {total_time:.0f}ms")

    return workflow_metrics
```

### Agentic Decision Monitoring

```python
async def monitor_agent_decisions(engine: ChatEngine):
    """Monitor agent decision-making process."""

    # Track decision points
    decisions = []

    # Decision 1: Which model to use
    if engine.router:
        chosen_model = engine.router.select_model("task")
        decisions.append({
            "type": "model_selection",
            "chosen": chosen_model,
            "timestamp": time.time()
        })

    # Decision 2: Whether to use cache
    query = "test query"
    cache_hit = False
    if engine.response_cache:
        key = engine.response_cache._make_key(query)
        cached = await engine.response_cache.get(key)
        cache_hit = cached is not None
        decisions.append({
            "type": "cache_decision",
            "used_cache": cache_hit,
            "timestamp": time.time()
        })

    # Decision 3: Circuit breaker status
    breaker_status = engine.llm_circuit_breaker.state.value
    decisions.append({
        "type": "circuit_breaker",
        "status": breaker_status,
        "timestamp": time.time()
    })

    # Print decision tree
    print("🧠 Agent Decision Tree:")
    for decision in decisions:
        print(f"  [{decision['type']}]")
        for key, value in decision.items():
            if key != 'type' and key != 'timestamp':
                print(f"    {key}: {value}")
```

---

## 7. Health Check Endpoints

### Web API for Monitoring

```python
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get("/health")
async def health_check(engine: ChatEngine):
    """Check system health."""
    breaker = engine.llm_circuit_breaker
    metrics = engine.metrics.get_summary()

    is_healthy = (
        breaker.state.value == 'closed' and
        all(m['success_rate'] > 95 for m in metrics.values() if m['total_requests'] > 0)
    )

    return {
        "status": "healthy" if is_healthy else "degraded",
        "circuit_breaker": breaker.state.value,
        "cache_hit_rate": engine.response_cache.hit_rate,
        "operations": {
            op: {
                "avg_ms": stats['avg_time_ms'],
                "success_rate": stats['success_rate']
            }
            for op, stats in metrics.items()
        }
    }

@app.get("/metrics")
async def metrics(engine: ChatEngine):
    """Return all metrics."""
    return {
        "timestamp": time.time(),
        "metrics": engine.metrics.get_summary(),
        "cache": {
            "hit_rate": engine.response_cache.hit_rate,
            "hits": engine.response_cache.hits,
            "misses": engine.response_cache.misses,
            "size": len(engine.response_cache.cache)
        },
        "circuit_breaker": {
            "state": engine.llm_circuit_breaker.state.value,
            "failures": engine.llm_circuit_breaker.failure_count
        }
    }

@app.get("/logs")
async def get_logs(level: str = "INFO"):
    """Stream recent logs."""
    # Implementation would read from log file
    pass
```

---

## 8. Common Monitoring Patterns

### Pattern 1: P95 Latency Tracking

```python
from collections import deque

class LatencyTracker:
    def __init__(self, window_size: int = 100):
        self.latencies = deque(maxlen=window_size)

    def record(self, duration_ms: float):
        self.latencies.append(duration_ms)

    def p95(self):
        """95th percentile latency."""
        if not self.latencies:
            return 0
        sorted_latencies = sorted(self.latencies)
        index = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[index]

    def p99(self):
        """99th percentile latency."""
        if not self.latencies:
            return 0
        sorted_latencies = sorted(self.latencies)
        index = int(len(sorted_latencies) * 0.99)
        return sorted_latencies[index]

# Usage
tracker = LatencyTracker()
metrics = engine.metrics.get_summary()
for latency_ms in [...]:  # Track each call
    tracker.record(latency_ms)

print(f"P95 Latency: {tracker.p95():.0f}ms")
print(f"P99 Latency: {tracker.p99():.0f}ms")
```

### Pattern 2: Error Rate Alerts

```python
class ErrorRateMonitor:
    def __init__(self, threshold: float = 0.05, window_size: int = 100):
        self.threshold = threshold  # Alert if > 5% error rate
        self.window_size = window_size
        self.recent_requests = deque(maxlen=window_size)

    def record(self, success: bool):
        self.recent_requests.append(success)

    def error_rate(self) -> float:
        if not self.recent_requests:
            return 0
        errors = sum(1 for s in self.recent_requests if not s)
        return errors / len(self.recent_requests)

    def check_alert(self) -> bool:
        return self.error_rate() > self.threshold

# Usage
monitor = ErrorRateMonitor(threshold=0.05)
for request in [...]:
    monitor.record(request.success)
    if monitor.check_alert():
        print(f"🚨 Alert: Error rate {monitor.error_rate():.1%}")
```

### Pattern 3: Resource Usage Tracking

```python
import psutil

class ResourceMonitor:
    def __init__(self, engine: ChatEngine):
        self.engine = engine
        self.process = psutil.Process()

    def get_memory_usage(self):
        """Get memory used by cache."""
        cache_size = sum(
            sys.getsizeof(entry.value)
            for entry in self.engine.response_cache.cache.values()
        )
        return cache_size / (1024 * 1024)  # MB

    def get_cpu_usage(self):
        """Get CPU percentage."""
        return self.process.cpu_percent(interval=0.1)

    def report(self):
        print(f"Memory (cache): {self.get_memory_usage():.1f}MB")
        print(f"CPU Usage: {self.get_cpu_usage():.1f}%")

monitor = ResourceMonitor(engine)
monitor.report()
```

---

## 9. Integration with Observability Platforms

### DataDog Integration

```python
from datadog import initialize, api
import logging

options = {
    'api_key': 'YOUR_API_KEY',
    'app_key': 'YOUR_APP_KEY'
}
initialize(**options)

def send_metrics_to_datadog(engine: ChatEngine):
    """Send Kor'tana metrics to DataDog."""
    metrics = engine.metrics.get_summary()

    for operation, stats in metrics.items():
        # Send timing metrics
        api.Metric.send(
            metric=f'kortana.{operation}.latency_ms',
            points=stats['avg_time_ms'],
            tags=['service:kortana']
        )

        # Send success rate
        api.Metric.send(
            metric=f'kortana.{operation}.success_rate',
            points=stats['success_rate'],
            tags=['service:kortana']
        )
```

### New Relic Integration

```python
import newrelic.agent

@newrelic.agent.function_trace()
async def get_response_with_tracing(engine: ChatEngine, query: str):
    """Get response with New Relic tracing."""
    response = await engine.get_response(query)

    # Record custom metrics
    newrelic.agent.record_custom_metric(
        'Custom/cache_hit_rate',
        engine.response_cache.hit_rate
    )

    return response
```

### ELK Stack Integration

```python
from pythonjsonlogger import jsonlogger
import logging

# Configure JSON logging for ELK
logger = logging.getLogger()
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# All logs will now be in JSON format, easily parseable by ELK
logger.info("Agent workflow started", extra={
    "session_id": engine.session_id,
    "cache_hit_rate": engine.response_cache.hit_rate,
    "circuit_breaker_state": engine.llm_circuit_breaker.state.value
})
```

---

## 10. Troubleshooting Guide

### Issue: High Latency

```python
async def diagnose_high_latency(engine: ChatEngine):
    """Diagnose high latency issues."""
    metrics = engine.metrics.get_summary()

    print("🔍 Latency Diagnosis:")

    # Check LLM latency
    if 'llm_call' in metrics:
        llm_avg = metrics['llm_call']['avg_time_ms']
        print(f"  LLM avg: {llm_avg:.0f}ms", end="")
        if llm_avg > 3000:
            print(" ❌ SLOW - Check LLM provider")
        else:
            print(" ✅")

    # Check cache efficiency
    cache_hr = engine.response_cache.hit_rate
    print(f"  Cache hit rate: {cache_hr:.0%}", end="")
    if cache_hr < 0.5:
        print(" ⚠️  Low - Most queries are uncached")
    else:
        print(" ✅")

    # Check memory operations
    if 'memory_load' in metrics:
        mem_avg = metrics['memory_load']['avg_time_ms']
        print(f"  Memory ops: {mem_avg:.0f}ms", end="")
        if mem_avg > 500:
            print(" ⚠️  Slow - Large memory dataset?")
        else:
            print(" ✅")

    # Check circuit breaker
    if engine.llm_circuit_breaker.state.value == 'open':
        print("  Circuit Breaker: ❌ OPEN - Service down")
```

### Issue: Low Cache Hit Rate

```python
async def diagnose_low_cache_rate(engine: ChatEngine):
    """Diagnose low cache hit rate."""
    cache = engine.response_cache

    if cache.hit_rate < 0.2:
        print("⚠️  Cache hit rate < 20%")
        print("Possible causes:")
        print("  1. Queries are all unique - cache won't help")
        print("  2. TTL too short - entries expiring too fast")
        print("  3. Cache size too small - entries being evicted")
        print("\nFix options:")
        print("  1. Increase TTL:", cache.default_ttl, "→", cache.default_ttl * 2)
        print("  2. Increase size:", cache.max_size, "→", cache.max_size * 2)
```

### Issue: Circuit Breaker Open

```python
async def diagnose_circuit_breaker_open(engine: ChatEngine):
    """Diagnose why circuit breaker is open."""
    breaker = engine.llm_circuit_breaker

    if breaker.state.value == 'open':
        print("❌ Circuit Breaker is OPEN")
        print(f"  Failures: {breaker.failure_count}/{breaker.config.failure_threshold}")
        print(f"  Recovery in: ~{breaker.config.recovery_timeout}s")
        print("\nActions to take:")
        print("  1. Check LLM service status (OpenAI API, etc.)")
        print("  2. Check API key and rate limits")
        print("  3. Wait for auto-recovery in 60s")
        print("  4. Or reset manually:")
        print("     breaker.state = CircuitState.CLOSED")
```

---

## 11. Best Practices

### ✅ DO

- ✅ **Monitor in production** - Real-world metrics reveal issues
- ✅ **Set alerts** - High latency, low success rate, circuit breaker opens
- ✅ **Track trends** - Compare daily/weekly metrics
- ✅ **Use structured logs** - JSON logs are easier to parse
- ✅ **Monitor cascade failures** - Circuit breaker + memory system status
- ✅ **Check P95/P99 latency** - Not just averages
- ✅ **Alert on error rates** - Not just individual failures

### ❌ DON'T

- ❌ **Ignore warnings** - They predict failures
- ❌ **Set alert thresholds too low** - Creates noise
- ❌ **Monitor only averages** - P95/P99 are more important
- ❌ **Disable debug logs in development** - They help troubleshooting
- ❌ **Ignore cache misses** - May indicate configuration issue
- ❌ **Leave circuit breaker manual reset** - Use auto-recovery

---

## Summary

Monitor Kor'tana using:

1. **Built-in Metrics** - `engine.metrics.get_summary()`
2. **Cache Performance** - `engine.response_cache.hit_rate`
3. **Circuit Breaker** - `engine.llm_circuit_breaker.state`
4. **Logging** - `logging.DEBUG` level
5. **Real-time Dashboard** - Custom UI or Prometheus
6. **Health Endpoints** - REST API for status
7. **Observability Platforms** - DataDog, New Relic, ELK

**Key Metrics to Watch:**

- LLM latency (should be 1000-3000ms first call, <5ms cached)
- Cache hit rate (target >50%)
- Success rate (target >99%)
- Circuit breaker state (should be CLOSED)
- Error rate (should be <1%)

---

*See [OPTIMIZATIONS_GUIDE.md](OPTIMIZATIONS_GUIDE.md) for more configuration options.*
