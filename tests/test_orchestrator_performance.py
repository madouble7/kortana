"""
Performance tests for orchestrator memory extraction under simulated load.
Tests throughput and response times to ensure appropriate thresholds are met.
"""

import asyncio
import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestOrchestratorPerformance:
    """Test orchestrator memory extraction performance under load."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return MagicMock()

    @pytest.fixture
    def mock_memory_results(self):
        """Mock memory search results."""
        return [
            {
                "memory": MagicMock(
                    content="Previous conversation about AI capabilities",
                    created_at=time.time(),
                ),
                "relevance": 0.95,
            },
            {
                "memory": MagicMock(
                    content="Discussion about machine learning models",
                    created_at=time.time(),
                ),
                "relevance": 0.87,
            },
            {
                "memory": MagicMock(
                    content="Questions about ethical AI development",
                    created_at=time.time(),
                ),
                "relevance": 0.82,
            },
        ]

    @pytest.mark.asyncio
    async def test_single_query_performance(self, mock_db, mock_memory_results):
        """Test single query performance and measure response time."""
        from src.kortana.core.orchestrator import KorOrchestrator

        with patch.object(
            KorOrchestrator, "_load_models_config", return_value=self._get_test_config()
        ):
            orchestrator = KorOrchestrator(db=mock_db)

            # Mock the memory service
            orchestrator.memory_service.search_memories_semantic = MagicMock(
                return_value=mock_memory_results
            )

            # Mock the LLM client
            mock_llm_response = {
                "content": "This is a test response based on the query.",
                "model_id_used": "gpt-4.1-nano",
                "usage": {"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70},
            }

            mock_client = AsyncMock()
            mock_client.generate_response = AsyncMock(return_value=mock_llm_response)
            orchestrator.llm_factory.get_client = MagicMock(return_value=mock_client)

            # Mock ethical evaluation
            orchestrator.arrogance_evaluator.evaluate_response = AsyncMock(
                return_value={"flag": False, "reason": None}
            )
            orchestrator.uncertainty_handler.manage_uncertainty = AsyncMock(
                return_value="This is a test response based on the query."
            )

            # Measure execution time
            start_time = time.perf_counter()
            result = await orchestrator.process_query("What is AI?")
            end_time = time.perf_counter()

            execution_time_ms = (end_time - start_time) * 1000

            # Assertions
            assert result is not None
            assert "final_kortana_response" in result
            assert execution_time_ms < 5000, f"Query took {execution_time_ms:.2f}ms, should be < 5000ms"

            print(f"\n✓ Single query performance: {execution_time_ms:.2f}ms")

    @pytest.mark.asyncio
    async def test_memory_extraction_timing(self, mock_db, mock_memory_results):
        """Test memory extraction timing specifically."""
        from src.kortana.modules.memory_core.services import MemoryCoreService

        service = MemoryCoreService(mock_db)

        # Mock the actual search to return quickly
        with patch.object(
            service, "search_memories_semantic", return_value=mock_memory_results
        ):
            start_time = time.perf_counter()
            results = service.search_memories_semantic("test query", top_k=3)
            end_time = time.perf_counter()

            memory_extraction_ms = (end_time - start_time) * 1000

            assert len(results) == 3
            assert memory_extraction_ms < 100, f"Memory extraction took {memory_extraction_ms:.2f}ms, should be < 100ms"

            print(f"\n✓ Memory extraction timing: {memory_extraction_ms:.2f}ms")

    @pytest.mark.asyncio
    async def test_concurrent_load_simulation(self, mock_db, mock_memory_results):
        """Simulate concurrent load with multiple queries."""
        from src.kortana.core.orchestrator import KorOrchestrator

        num_concurrent_queries = 10

        with patch.object(
            KorOrchestrator, "_load_models_config", return_value=self._get_test_config()
        ):
            orchestrator = KorOrchestrator(db=mock_db)

            # Mock dependencies
            orchestrator.memory_service.search_memories_semantic = MagicMock(
                return_value=mock_memory_results
            )

            mock_llm_response = {
                "content": "Test response",
                "model_id_used": "gpt-4.1-nano",
                "usage": {"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70},
            }

            mock_client = AsyncMock()
            mock_client.generate_response = AsyncMock(return_value=mock_llm_response)
            orchestrator.llm_factory.get_client = MagicMock(return_value=mock_client)

            orchestrator.arrogance_evaluator.evaluate_response = AsyncMock(
                return_value={"flag": False}
            )
            orchestrator.uncertainty_handler.manage_uncertainty = AsyncMock(
                return_value="Test response"
            )

            # Create concurrent queries
            queries = [f"Test query {i}" for i in range(num_concurrent_queries)]

            start_time = time.perf_counter()
            tasks = [orchestrator.process_query(query) for query in queries]
            results = await asyncio.gather(*tasks)
            end_time = time.perf_counter()

            total_time_ms = (end_time - start_time) * 1000
            avg_time_ms = total_time_ms / num_concurrent_queries

            # Assertions
            assert len(results) == num_concurrent_queries
            assert all("final_kortana_response" in r for r in results)

            # Throughput calculation (queries per second)
            throughput = (num_concurrent_queries / total_time_ms) * 1000

            print(f"\n✓ Concurrent load test:")
            print(f"  - Total queries: {num_concurrent_queries}")
            print(f"  - Total time: {total_time_ms:.2f}ms")
            print(f"  - Average time per query: {avg_time_ms:.2f}ms")
            print(f"  - Throughput: {throughput:.2f} queries/second")

            # Assert reasonable performance
            assert avg_time_ms < 1000, f"Average query time {avg_time_ms:.2f}ms exceeds 1000ms threshold"
            assert throughput > 5, f"Throughput {throughput:.2f} queries/sec is below 5 queries/sec threshold"

    @pytest.mark.asyncio
    async def test_performance_report(self, mock_db, mock_memory_results):
        """Generate a comprehensive performance report."""
        from src.kortana.core.orchestrator import KorOrchestrator

        with patch.object(
            KorOrchestrator, "_load_models_config", return_value=self._get_test_config()
        ):
            orchestrator = KorOrchestrator(db=mock_db)

            # Mock dependencies
            orchestrator.memory_service.search_memories_semantic = MagicMock(
                return_value=mock_memory_results
            )

            mock_llm_response = {
                "content": "Test response",
                "model_id_used": "gpt-4.1-nano",
                "usage": {"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70},
            }

            mock_client = AsyncMock()
            mock_client.generate_response = AsyncMock(return_value=mock_llm_response)
            orchestrator.llm_factory.get_client = MagicMock(return_value=mock_client)

            orchestrator.arrogance_evaluator.evaluate_response = AsyncMock(
                return_value={"flag": False}
            )
            orchestrator.uncertainty_handler.manage_uncertainty = AsyncMock(
                return_value="Test response"
            )

            # Run multiple iterations to get statistics
            iterations = 20
            timings = []

            for i in range(iterations):
                start_time = time.perf_counter()
                await orchestrator.process_query(f"Query {i}")
                end_time = time.perf_counter()
                timings.append((end_time - start_time) * 1000)

            # Calculate statistics
            avg_time = sum(timings) / len(timings)
            min_time = min(timings)
            max_time = max(timings)

            # Generate report
            report = f"""
=== ORCHESTRATOR PERFORMANCE REPORT ===
Test Date: {time.strftime('%Y-%m-%d %H:%M:%S')}
Iterations: {iterations}

Memory Extraction Performance:
  - Average query time: {avg_time:.2f}ms
  - Min query time: {min_time:.2f}ms
  - Max query time: {max_time:.2f}ms
  - Throughput: {(1000 / avg_time):.2f} queries/second

Thresholds:
  ✓ Average < 1000ms: {'PASS' if avg_time < 1000 else 'FAIL'}
  ✓ Max < 2000ms: {'PASS' if max_time < 2000 else 'FAIL'}
  ✓ Throughput > 1 qps: {'PASS' if (1000 / avg_time) > 1 else 'FAIL'}
"""

            print(report)

            # Write report to file
            report_path = "/home/runner/work/kortana/kortana/tests/performance_report.txt"
            with open(report_path, "w") as f:
                f.write(report)

            print(f"\n✓ Performance report saved to: {report_path}")

    def _get_test_config(self) -> dict[str, Any]:
        """Return test configuration for models."""
        return {
            "models": {
                "gpt-4.1-nano": {
                    "provider": "openai",
                    "api_key_env": "OPENAI_API_KEY",
                    "model_name": "gpt-4.1-nano",
                }
            },
            "default": {"model": "gpt-4.1-nano"},
        }
