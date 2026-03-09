"""Tests for enhanced ethical evaluation."""
import pytest
from kortana.modules.ethical_discernment_module.evaluators import (
    AlgorithmicArroganceEvaluator,
    UncertaintyHandler
)


class TestAlgorithmicArroganceEvaluator:
    """Test enhanced ethical evaluation."""
    
    @pytest.fixture
    def evaluator(self):
        return AlgorithmicArroganceEvaluator(confidence_threshold=0.9)
    
    @pytest.mark.asyncio
    async def test_high_confidence_flag(self, evaluator):
        """Test that high confidence scores are flagged."""
        result = await evaluator.evaluate_response(
            response_text="This is definitely correct.",
            llm_metadata={"confidence_score": 0.95},
            original_query_context="Test query"
        )
        
        assert result["flag"] is True
        assert result["confidence_check"]["flagged"] is True
        assert "decision_trace" in result
        assert len(result["decision_trace"]) > 0
    
    @pytest.mark.asyncio
    async def test_arrogance_keywords(self, evaluator):
        """Test detection of arrogance keywords."""
        response = "This is obviously the only correct answer. It's clearly the best solution."
        result = await evaluator.evaluate_response(
            response_text=response,
            llm_metadata={},
            original_query_context="Test"
        )
        
        assert result["arrogance_check"]["flagged"] is True
        assert len(result["arrogance_check"]["keywords_found"]) > 0
        assert "obviously" in result["arrogance_check"]["keywords_found"]
    
    @pytest.mark.asyncio
    async def test_uncertainty_markers(self, evaluator):
        """Test detection of uncertainty markers (positive indicator)."""
        response = "I think this might be the answer, but I'm not entirely sure."
        result = await evaluator.evaluate_response(
            response_text=response,
            llm_metadata={},
            original_query_context="Test"
        )
        
        assert result["uncertainty_check"]["has_uncertainty"] is True
        assert len(result["uncertainty_check"]["phrases_found"]) > 0
    
    @pytest.mark.asyncio
    async def test_bias_detection(self, evaluator):
        """Test bias detection through absolute statements."""
        response = "You should always do this and never do that. Always remember this."
        result = await evaluator.evaluate_response(
            response_text=response,
            llm_metadata={},
            original_query_context="Test"
        )
        
        assert result["bias_check"]["absolute_statements"] >= 3
        assert result["bias_check"]["flagged"] is True
    
    @pytest.mark.asyncio
    async def test_transparency_check(self, evaluator):
        """Test transparency indicator detection."""
        response = "I don't know the exact answer to that question."
        result = await evaluator.evaluate_response(
            response_text=response,
            llm_metadata={},
            original_query_context="Test"
        )
        
        assert result["transparency_check"]["has_transparency"] is True
        assert len(result["transparency_check"]["indicators_found"]) > 0
    
    @pytest.mark.asyncio
    async def test_decision_traceability(self, evaluator):
        """Test that decision trace is detailed and complete."""
        result = await evaluator.evaluate_response(
            response_text="Test response",
            llm_metadata={"confidence_score": 0.8},
            original_query_context="Test"
        )
        
        assert "decision_trace" in result
        trace = result["decision_trace"]
        assert len(trace) >= 5  # Should have multiple criteria
        
        # Check trace structure
        for entry in trace:
            assert "criterion" in entry
            assert "result" in entry
            assert "reason" in entry
    
    @pytest.mark.asyncio
    async def test_performance_tracking(self, evaluator):
        """Test that evaluation time is tracked."""
        result = await evaluator.evaluate_response(
            response_text="Test",
            llm_metadata={},
            original_query_context="Test"
        )
        
        assert "evaluation_time_ms" in result
        assert result["evaluation_time_ms"] >= 0
    
    @pytest.mark.asyncio
    async def test_batch_evaluation(self, evaluator):
        """Test batch evaluation of multiple responses."""
        responses = [
            {
                "response_text": "Obviously correct.",
                "llm_metadata": {},
                "query_context": "Q1"
            },
            {
                "response_text": "I think this might work.",
                "llm_metadata": {},
                "query_context": "Q2"
            },
            {
                "response_text": "Test response.",
                "llm_metadata": {"confidence_score": 0.95},
                "query_context": "Q3"
            }
        ]
        
        results = await evaluator.evaluate_batch(responses)
        
        assert len(results) == 3
        assert all("decision_trace" in r for r in results)
        assert results[0]["arrogance_check"]["flagged"] is True
        assert results[2]["flag"] is True  # High confidence


class TestUncertaintyHandler:
    """Test uncertainty handling."""
    
    @pytest.fixture
    def handler(self):
        return UncertaintyHandler()
    
    @pytest.mark.asyncio
    async def test_manage_uncertainty_no_flags(self, handler):
        """Test that clean responses pass through unchanged."""
        response = "This is a good answer."
        evaluation = {"flag": False, "decision_trace": []}
        
        result = await handler.manage_uncertainty(
            original_query="Test",
            llm_response=response,
            evaluation_results=evaluation
        )
        
        assert result == response
    
    @pytest.mark.asyncio
    async def test_manage_uncertainty_with_flags(self, handler):
        """Test handling of flagged responses."""
        response = "Obviously the best answer."
        evaluation = {
            "flag": True,
            "decision_trace": [
                {"criterion": "arrogance", "result": "flagged", "reason": "Keywords"}
            ]
        }
        
        result = await handler.manage_uncertainty(
            original_query="Test",
            llm_response=response,
            evaluation_results=evaluation
        )
        
        # Currently returns as-is, but function should handle it
        assert isinstance(result, str)
