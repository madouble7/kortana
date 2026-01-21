"""
Tests for enhanced ethical evaluation module with edge cases and bias detection.
"""

import pytest

from src.kortana.modules.ethical_discernment_module.evaluators import (
    AlgorithmicArroganceEvaluator,
    EthicalEvaluationResult,
    UncertaintyHandler,
)


class TestEthicalEvaluationResult:
    """Test the ethical evaluation result structure."""

    def test_create_result(self):
        """Test creating an evaluation result."""
        result = EthicalEvaluationResult()
        assert result.flags == []
        assert result.scores == {}
        assert result.trace == []

    def test_add_flag(self):
        """Test adding a flag to the result."""
        result = EthicalEvaluationResult()
        result.add_flag("test_category", "test reason", "warning")

        assert len(result.flags) == 1
        assert result.flags[0]["category"] == "test_category"
        assert result.flags[0]["severity"] == "warning"
        assert len(result.trace) == 1

    def test_add_score(self):
        """Test adding a score to the result."""
        result = EthicalEvaluationResult()
        result.add_score("metric1", 0.75)

        assert result.scores["metric1"] == 0.75
        assert len(result.trace) == 1

    def test_to_dict(self):
        """Test converting result to dictionary."""
        result = EthicalEvaluationResult()
        result.add_flag("test", "reason", "error")
        result.add_score("score1", 0.5)

        dict_result = result.to_dict()
        assert "flags" in dict_result
        assert "scores" in dict_result
        assert "trace" in dict_result
        assert dict_result["has_concerns"] is True


class TestAlgorithmicArroganceEvaluator:
    """Test the enhanced arrogance evaluator."""

    @pytest.fixture
    def evaluator(self):
        """Create an evaluator instance."""
        return AlgorithmicArroganceEvaluator()

    @pytest.mark.asyncio
    async def test_detect_overconfident_language(self, evaluator):
        """Test detection of overconfident language."""
        text = "This is obviously the correct answer. There is no doubt that this is true."

        result = await evaluator.evaluate_response(text)

        assert result["scores"]["arrogance"] > 0.0
        arrogance_flags = [f for f in result["flags"] if f["category"] == "arrogance"]
        assert len(arrogance_flags) > 0

    @pytest.mark.asyncio
    async def test_detect_absolute_language(self, evaluator):
        """Test detection of absolute language."""
        text = "This will always work. It never fails. This is impossible to break."

        result = await evaluator.evaluate_response(text)

        assert result["scores"]["arrogance"] > 0.3

    @pytest.mark.asyncio
    async def test_no_arrogance_in_humble_response(self, evaluator):
        """Test that humble language doesn't trigger arrogance detection."""
        text = "This might work in some cases. It could depend on the specific situation."

        result = await evaluator.evaluate_response(text)

        assert result["scores"]["arrogance"] < 0.3

    @pytest.mark.asyncio
    async def test_detect_bias(self, evaluator):
        """Test detection of biased language."""
        text = "All men are naturally better at this task."

        result = await evaluator.evaluate_response(text)

        assert result["scores"]["bias"] > 0.0
        bias_flags = [f for f in result["flags"] if f["category"] == "bias"]
        assert len(bias_flags) > 0
        assert bias_flags[0]["severity"] == "error"

    @pytest.mark.asyncio
    async def test_no_bias_in_neutral_response(self, evaluator):
        """Test that neutral language doesn't trigger bias detection."""
        text = "Different people have different strengths and preferences."

        result = await evaluator.evaluate_response(text)

        assert result["scores"]["bias"] == 0.0

    @pytest.mark.asyncio
    async def test_detect_medical_edge_case(self, evaluator):
        """Test detection of medical advice edge case."""
        text = "You should take this medication to cure your condition."
        query = "What should I do about my symptoms?"

        result = await evaluator.evaluate_response(text, original_query_context=query)

        edge_flags = [f for f in result["flags"] if f["category"] == "edge_case"]
        assert len(edge_flags) > 0
        assert "medical_advice" in str(edge_flags[0])

    @pytest.mark.asyncio
    async def test_detect_legal_edge_case(self, evaluator):
        """Test detection of legal advice edge case."""
        text = "You should sue them for this. Your rights are being violated."

        result = await evaluator.evaluate_response(text)

        edge_flags = [f for f in result["flags"] if f["category"] == "edge_case"]
        assert len(edge_flags) > 0

    @pytest.mark.asyncio
    async def test_detect_financial_edge_case(self, evaluator):
        """Test detection of financial advice edge case."""
        text = "You should invest in this stock. It's a guaranteed return."

        result = await evaluator.evaluate_response(text)

        edge_flags = [f for f in result["flags"] if f["category"] == "edge_case"]
        assert len(edge_flags) > 0

    @pytest.mark.asyncio
    async def test_consistency_check(self, evaluator):
        """Test consistency checking."""
        inconsistent_text = "This is always true. But on the other hand, it's sometimes false. However, it actually depends."

        result = await evaluator.evaluate_response(inconsistent_text)

        # Should have lower consistency score due to many contradictions
        assert "consistency" in result["scores"]

    @pytest.mark.asyncio
    async def test_transparency_evaluation(self, evaluator):
        """Test transparency scoring."""
        transparent_text = "I think this might be the case. It could depend on various factors. Perhaps we should consider other options."

        result = await evaluator.evaluate_response(transparent_text)

        assert result["scores"]["transparency"] > 0.5

    @pytest.mark.asyncio
    async def test_low_transparency_detection(self, evaluator):
        """Test detection of low transparency."""
        opaque_text = "This is the answer. Do this."

        result = await evaluator.evaluate_response(opaque_text)

        assert result["scores"]["transparency"] < 0.5

    @pytest.mark.asyncio
    async def test_gpt4_alignment_check(self, evaluator):
        """Test GPT-4 alignment checking."""
        text = "I apologize, but I cannot assist with that request as an AI language model."

        result = await evaluator.evaluate_response(text)

        gpt4_flags = [f for f in result["flags"] if f["category"] == "gpt4_alignment"]
        assert len(gpt4_flags) > 0

    @pytest.mark.asyncio
    async def test_comprehensive_evaluation(self, evaluator):
        """Test that all evaluation components are included."""
        text = "This is a reasonable response that acknowledges uncertainty."

        result = await evaluator.evaluate_response(
            text,
            llm_metadata={"model": "gpt-4"},
            original_query_context="test query",
        )

        # Should have all score components
        assert "arrogance" in result["scores"]
        assert "bias" in result["scores"]
        assert "consistency" in result["scores"]
        assert "transparency" in result["scores"]

        # Should have metadata
        assert "query_context" in result["metadata"]
        assert "model_info" in result["metadata"]

        # Should have trace
        assert len(result["trace"]) > 0


class TestUncertaintyHandler:
    """Test the enhanced uncertainty handler."""

    @pytest.fixture
    def handler(self):
        """Create a handler instance."""
        return UncertaintyHandler()

    @pytest.mark.asyncio
    async def test_no_modification_for_clean_response(self, handler):
        """Test that clean responses are not modified."""
        query = "What is AI?"
        response = "AI is artificial intelligence."
        evaluation = {"has_concerns": False, "flags": [], "scores": {}}

        result = await handler.manage_uncertainty(query, response, evaluation)

        assert result == response

    @pytest.mark.asyncio
    async def test_add_disclaimer_for_edge_cases(self, handler):
        """Test that disclaimers are added for edge cases."""
        query = "Should I take this medication?"
        response = "You should consider this treatment."
        evaluation = {
            "has_concerns": True,
            "flags": [
                {"category": "edge_case", "reason": "medical_advice", "severity": "error"}
            ],
            "scores": {},
        }

        result = await handler.manage_uncertainty(query, response, evaluation)

        assert "⚠️ Important" in result
        assert "qualified professionals" in result

    @pytest.mark.asyncio
    async def test_add_uncertainty_note_for_arrogance(self, handler):
        """Test that uncertainty notes are added for high arrogance."""
        query = "What is the best approach?"
        response = "This is definitely the best way."
        evaluation = {
            "has_concerns": True,
            "flags": [{"category": "arrogance", "reason": "overconfident", "severity": "warning"}],
            "scores": {"arrogance": 0.8},
        }

        result = await handler.manage_uncertainty(query, response, evaluation)

        assert "individual circumstances may vary" in result.lower()

    @pytest.mark.asyncio
    async def test_filter_biased_content(self, handler):
        """Test that biased content is filtered."""
        query = "Tell me about differences."
        response = "All people from that group are the same."
        evaluation = {
            "has_concerns": True,
            "flags": [{"category": "bias", "reason": "stereotyping", "severity": "error"}],
            "scores": {"bias": 0.9},
        }

        result = await handler.manage_uncertainty(query, response, evaluation)

        assert "filtered" in result.lower()

    @pytest.mark.asyncio
    async def test_api_tracing_examples(self, handler):
        """Test that evaluation provides examples for API tracing."""
        # This test documents how the ethical evaluation provides traceability
        # for debugging and monitoring purposes

        from src.kortana.modules.ethical_discernment_module.evaluators import (
            AlgorithmicArroganceEvaluator,
        )

        evaluator = AlgorithmicArroganceEvaluator()

        # Example 1: Overconfident response
        response1 = "This is obviously the only correct answer."
        result1 = await evaluator.evaluate_response(response1)

        assert "trace" in result1
        assert len(result1["trace"]) > 0
        print("\n=== Example 1: Overconfident Response ===")
        print("Response:", response1)
        print("Trace:")
        for trace_item in result1["trace"]:
            print(f"  {trace_item}")

        # Example 2: Edge case detection
        response2 = "You should invest all your money in this."
        result2 = await evaluator.evaluate_response(response2)

        print("\n=== Example 2: Financial Advice Edge Case ===")
        print("Response:", response2)
        print("Flags:", result2["flags"])
        print("Trace:")
        for trace_item in result2["trace"]:
            print(f"  {trace_item}")

        # Example 3: Bias detection
        response3 = "All members of that group inherently lack this ability."
        result3 = await evaluator.evaluate_response(response3)

        print("\n=== Example 3: Biased Statement ===")
        print("Response:", response3)
        print("Flags:", result3["flags"])
        print("Trace:")
        for trace_item in result3["trace"]:
            print(f"  {trace_item}")

        # These examples demonstrate API tracing for monitoring
        assert all(
            "trace" in result for result in [result1, result2, result3]
        ), "All results should include tracing"
