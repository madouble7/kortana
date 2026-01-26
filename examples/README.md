# Optimization Examples

This directory contains examples demonstrating how to use Kor'tana's optimization features.

## Available Examples

### optimization_integration.py

Comprehensive example showing how to integrate all optimization features:

- **Memory Optimization**: LRU caching for embeddings and responses
- **Resource Pooling**: Reusable connection and processor pools
- **Performance Metrics**: Tracking API calls, cache hits, and timing
- **Priority Scheduling**: Prioritized decision processing

**Run the example:**

```bash
cd /home/runner/work/kortana/kortana
python examples/optimization_integration.py
```

**Expected output:**
```
============================================================
Kor'tana Optimization Features - Integration Example
============================================================

✓ Optimized Kor'tana initialized
1. Testing embedding cache...
   First: 384 dims, Second: 384 dims (cached)

2. Testing prioritized response generation...
   High priority: Response to: URGENT!......
   Normal priority: Response to: Tell me about AI....

3. System statistics:
   Memory:
     embeddings: 1/512 (hit rate: 50.00%)
     responses: 2/128 (hit rate: 0.00%)
   Resources:
     llm_connections: 5 available, 0 active
     processors: 10 available, 0 active

✓ Optimized Kor'tana shutdown complete
============================================================
```

## Key Features Demonstrated

### 1. Memory Optimization

```python
# Create optimizer with cache capacity
memory_optimizer = MemoryOptimizer(cache_capacity=256)

# Get named caches
embedding_cache = memory_optimizer.get_cache("embeddings", capacity=512)
response_cache = memory_optimizer.get_cache("responses", capacity=128)

# Use caching
cached = embedding_cache.get(key)
if cached is None:
    value = compute_expensive_operation()
    embedding_cache.put(key, value)
```

### 2. Resource Pooling

```python
# Create resource manager
resource_manager = ResourceManager()

# Create pools with factory functions
llm_pool = resource_manager.create_pool(
    name="llm_connections",
    factory=create_connection,
    cleanup=close_connection,
    min_size=5,
    max_size=20,
    timeout=300.0
)

# Acquire and release resources
connection = llm_pool.acquire()
try:
    # Use connection
    pass
finally:
    llm_pool.release(connection)
```

### 3. Performance Metrics

```python
# Create metrics collector
metrics = MetricsCollector()
api_metrics = metrics.get_metrics("api")

# Track metrics
api_metrics.increment("requests")
api_metrics.set_gauge("active_connections", 10)

# Time operations
with Timer(api_metrics, "operation"):
    # Timed code
    pass

# Get statistics
stats = api_metrics.get_all_metrics()
```

### 4. Priority Scheduling

```python
# Create decision queue
decision_queue = DecisionQueue(num_workers=4)
decision_queue.start()

# Submit tasks with priorities
def process_urgent_task():
    # Critical task logic
    pass

task_id = decision_queue.submit_decision(
    process_urgent_task,
    priority=Priority.CRITICAL
)

# Cleanup
decision_queue.stop()
```

## Creating Your Own Examples

To create a custom example:

1. Import optimization modules directly to avoid dependency issues:
   ```python
   import sys
   import os
   sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src/kortana/core'))
   
   import optimization.memory_optimizer as mem_opt
   import optimization.resource_manager as res_mgr
   import optimization.performance_metrics as perf_met
   import optimization.priority_queue as prio_queue
   ```

2. Initialize the components you need
3. Use the optimization features in your code
4. Collect and display statistics
5. Properly shutdown resources

## Performance Tips

1. **Cache Sizing**: Monitor hit rates and adjust cache capacities
2. **Pool Sizing**: Set min_size for baseline load, max_size for peak load
3. **Priority Assignment**: Use CRITICAL sparingly, NORMAL for most tasks
4. **Metrics Collection**: Enable for development, consider overhead in production
5. **Resource Cleanup**: Always shutdown queues and stop cleanup threads

## See Also

- [Optimization Features Documentation](../docs/OPTIMIZATION_FEATURES.md)
- [Tests](../tests/test_optimization_standalone.py)
