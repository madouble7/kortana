import time
from typing import Any


class AlgorithmicArroganceEvaluator:
    def __init__(self, confidence_threshold: float = 0.95):
        self.confidence_threshold = confidence_threshold
        # Keywords that might indicate problematic patterns
        self.arrogance_keywords = [
            "obviously", "clearly", "undoubtedly", "certainly", "definitely",
            "always", "never", "must", "cannot possibly"
        ]
        self.uncertainty_phrases = [
            "i think", "perhaps", "maybe", "might", "could be",
            "it seems", "appears to", "likely", "possibly"
        ]

    async def evaluate_response(
        self,
        response_text: str,
        llm_metadata: dict | None = None,
        original_query_context: str | None = None,
    ) -> dict[str, Any]:
        """
        Evaluate a single response for ethical alignment with detailed traceability.

        Returns:
            Dictionary with evaluation results and decision metadata
        """
        evaluation_start = time.time()

        # Initialize evaluation results
        evaluation = {
            "flag": False,
            "confidence_check": None,
            "arrogance_check": None,
            "uncertainty_check": None,
            "bias_check": None,
            "transparency_check": None,
            "decision_trace": [],
            "evaluation_time_ms": 0,
        }

        decision_trace = []

        # 1. Check confidence score from metadata
        confidence = llm_metadata.get("confidence_score") if llm_metadata else None
        if confidence is not None:
            if confidence >= self.confidence_threshold:
                evaluation["flag"] = True
                evaluation["confidence_check"] = {
                    "flagged": True,
                    "score": confidence,
                    "threshold": self.confidence_threshold,
                }
                decision_trace.append({
                    "criterion": "confidence_threshold",
                    "result": "flagged",
                    "reason": f"Confidence {confidence} >= threshold {self.confidence_threshold}",
                })
            else:
                evaluation["confidence_check"] = {
                    "flagged": False,
                    "score": confidence,
                }
                decision_trace.append({
                    "criterion": "confidence_threshold",
                    "result": "passed",
                    "reason": f"Confidence {confidence} < threshold {self.confidence_threshold}",
                })

        # 2. Check for arrogance keywords
        response_lower = response_text.lower()
        arrogance_found = [kw for kw in self.arrogance_keywords if kw in response_lower]
        if arrogance_found:
            evaluation["arrogance_check"] = {
                "flagged": True,
                "keywords_found": arrogance_found,
                "count": len(arrogance_found),
            }
            decision_trace.append({
                "criterion": "arrogance_keywords",
                "result": "flagged",
                "reason": f"Found {len(arrogance_found)} arrogance indicators: {arrogance_found}",
            })
        else:
            evaluation["arrogance_check"] = {"flagged": False}
            decision_trace.append({
                "criterion": "arrogance_keywords",
                "result": "passed",
                "reason": "No arrogance indicators found",
            })

        # 3. Check for uncertainty markers (positive indicator)
        uncertainty_found = [phrase for phrase in self.uncertainty_phrases if phrase in response_lower]
        evaluation["uncertainty_check"] = {
            "has_uncertainty": len(uncertainty_found) > 0,
            "phrases_found": uncertainty_found,
            "count": len(uncertainty_found),
        }
        decision_trace.append({
            "criterion": "uncertainty_markers",
            "result": "info",
            "reason": f"Found {len(uncertainty_found)} uncertainty markers (good practice)",
        })

        # 4. Bias detection - check for absolute statements
        absolute_count = response_lower.count("always") + response_lower.count("never")
        evaluation["bias_check"] = {
            "absolute_statements": absolute_count,
            "flagged": absolute_count > 2,
        }
        if absolute_count > 2:
            evaluation["flag"] = True
            decision_trace.append({
                "criterion": "bias_detection",
                "result": "flagged",
                "reason": f"Found {absolute_count} absolute statements (>2 threshold)",
            })
        else:
            decision_trace.append({
                "criterion": "bias_detection",
                "result": "passed",
                "reason": f"Absolute statements within acceptable range ({absolute_count})",
            })

        # 5. Transparency check - does response acknowledge limitations?
        transparency_indicators = ["i don't know", "i'm not sure", "i cannot", "beyond my", "i cannot provide"]
        transparency_found = [ind for ind in transparency_indicators if ind in response_lower]
        evaluation["transparency_check"] = {
            "has_transparency": len(transparency_found) > 0,
            "indicators_found": transparency_found,
        }
        decision_trace.append({
            "criterion": "transparency",
            "result": "info",
            "reason": f"Transparency indicators: {len(transparency_found)}",
        })

        # Store decision trace
        evaluation["decision_trace"] = decision_trace
        evaluation["evaluation_time_ms"] = int((time.time() - evaluation_start) * 1000)

        return evaluation

    async def evaluate_batch(
        self,
        responses: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Batch evaluate multiple responses for improved throughput.

        Args:
            responses: List of dicts with 'response_text', 'llm_metadata', 'query_context'

        Returns:
            List of evaluation results in the same order
        """
        batch_start = time.time()
        results = []

        for response_data in responses:
            eval_result = await self.evaluate_response(
                response_text=response_data.get("response_text", ""),
                llm_metadata=response_data.get("llm_metadata"),
                original_query_context=response_data.get("query_context"),
            )
            results.append(eval_result)

        batch_time = time.time() - batch_start
        print(f"Batch evaluation completed: {len(responses)} responses in {batch_time:.3f}s")

        return results


class UncertaintyHandler:
    """Handles uncertainty in LLM responses with enhanced metadata."""

    async def manage_uncertainty(
        self, original_query: str, llm_response: str, evaluation_results: dict
    ) -> str:
        """
        Manage uncertainty based on evaluation results.

        In a real implementation, this would modify the response based on evaluation
        to add appropriate caveats or disclaimers.
        """
        # If flagged for arrogance or bias, add a caveat
        if evaluation_results.get("flag", False):
            flagged_reasons = [
                trace["reason"]
                for trace in evaluation_results.get("decision_trace", [])
                if trace["result"] == "flagged"
            ]

            # For now, just return the original response
            # In production, you might want to add disclaimers or rephrase
            print(f"Response flagged in evaluation: {flagged_reasons}")

        return llm_response
