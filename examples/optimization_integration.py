"""
Integration example showing how to use optimization features with Kor'tana.

This demonstrates backward-compatible integration without modifying existing code.
"""

import sys
import os
import time
from typing import Any, Dict, List

# Add optimization module directly to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src/kortana/core'))

# Import directly without triggering core __init__
import optimization.memory_optimizer as mem_opt
import optimization.resource_manager as res_mgr
import optimization.performance_metrics as perf_met
import optimization.priority_queue as prio_queue


class OptimizedKortanaExample:
    """Example showing Kor'tana enhanced with optimization features."""

    def __init__(self):
        """Initialize optimized Kor'tana components."""
        self.memory_optimizer = mem_opt.MemoryOptimizer(cache_capacity=256)
        self.resource_manager = res_mgr.ResourceManager()
        self.metrics = perf_met.MetricsCollector()
        self.decision_queue = prio_queue.DecisionQueue(num_workers=4)

        self.embedding_cache = self.memory_optimizer.get_cache("embeddings", capacity=512)
        self.response_cache = self.memory_optimizer.get_cache("responses", capacity=128)

        self._setup_resource_pools()

        self.api_metrics = self.metrics.get_metrics("api")
        self.decision_metrics = self.metrics.get_metrics("decisions")

        self.resource_manager.start_cleanup_thread(interval=60.0)
        self.decision_queue.start()

        print("✓ Optimized Kor'tana initialized")

    def _setup_resource_pools(self):
        """Setup resource pools for reusable objects."""
        self.llm_pool = self.resource_manager.create_pool(
            name="llm_connections",
            factory=lambda: {"id": f"conn_{time.time()}", "state": "connected"},
            cleanup=lambda conn: None,
            min_size=5,
            max_size=20,
        )

        self.processor_pool = self.resource_manager.create_pool(
            name="processors",
            factory=lambda: {"embeddings": [], "tokens": []},
            min_size=10,
            max_size=50,
        )

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding with caching."""
        with perf_met.Timer(self.api_metrics, "get_embedding"):
            cached = self.embedding_cache.get(text)
            if cached is not None:
                self.api_metrics.increment("embedding_cache_hits")
                return cached

            self.api_metrics.increment("embedding_cache_misses")
            embedding = [0.1] * 384  # Simulated embedding
            self.embedding_cache.put(text, embedding)
            return embedding

    def generate_response(self, prompt: str, priority: prio_queue.Priority = prio_queue.Priority.NORMAL) -> str:
        """Generate response with resource pooling and priority scheduling."""
        with perf_met.Timer(self.api_metrics, "generate_response"):
            self.api_metrics.increment("requests")

            cache_key = f"response:{hash(prompt)}"
            cached = self.response_cache.get(cache_key)
            if cached is not None:
                self.api_metrics.increment("response_cache_hits")
                return cached

            self.api_metrics.increment("response_cache_misses")

            llm_conn = self.llm_pool.acquire()
            processor = self.processor_pool.acquire()

            try:
                result = {"response": None}

                def process_decision():
                    with perf_met.Timer(self.decision_metrics, "decision_processing"):
                        result["response"] = f"Response to: {prompt[:50]}..."
                        self.decision_metrics.increment("decisions_processed")

                self.decision_queue.submit_decision(process_decision, priority)
                time.sleep(0.1)

                response = result["response"] or "Default response"
                self.response_cache.put(cache_key, response)
                return response

            finally:
                self.llm_pool.release(llm_conn)
                self.processor_pool.release(processor)

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        return {
            "memory": self.memory_optimizer.get_stats(),
            "resources": self.resource_manager.get_stats(),
            "metrics": self.metrics.get_all_metrics(),
            "decisions": self.decision_queue.get_stats(),
        }

    def shutdown(self):
        """Shutdown and cleanup resources."""
        self.decision_queue.stop()
        self.resource_manager.stop_cleanup_thread()
        print("✓ Optimized Kor'tana shutdown complete")


def main():
    """Run example demonstration."""
    print("=" * 60)
    print("Kor'tana Optimization Features - Integration Example")
    print("=" * 60)
    print()

    kortana = OptimizedKortanaExample()

    print("1. Testing embedding cache...")
    emb1 = kortana.get_embedding("Hello, world!")
    emb2 = kortana.get_embedding("Hello, world!")
    print(f"   First: {len(emb1)} dims, Second: {len(emb2)} dims (cached)")
    print()

    print("2. Testing prioritized response generation...")
    high = kortana.generate_response("URGENT!", prio_queue.Priority.HIGH)
    normal = kortana.generate_response("Tell me about AI", prio_queue.Priority.NORMAL)
    print(f"   High priority: {high[:30]}...")
    print(f"   Normal priority: {normal[:30]}...")
    print()

    print("3. System statistics:")
    stats = kortana.get_stats()
    
    print("   Memory:")
    for name, cache_stats in stats["memory"]["caches"].items():
        print(f"     {name}: {cache_stats['size']}/{cache_stats['capacity']} (hit rate: {cache_stats['hit_rate']})")

    print("   Resources:")
    for name, pool_stats in stats["resources"]["pools"].items():
        print(f"     {name}: {pool_stats['available']} available, {pool_stats['active']} active")

    print()
    kortana.shutdown()
    print("=" * 60)
    print("Integration example complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
