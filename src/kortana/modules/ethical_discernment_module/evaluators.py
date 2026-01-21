import re
from typing import Any


class EthicalEvaluationResult:
    """Structured result from ethical evaluation with traceability."""

    def __init__(self):
        self.flags: list[dict[str, Any]] = []
        self.scores: dict[str, float] = {}
        self.metadata: dict[str, Any] = {}
        self.trace: list[str] = []

    def add_flag(self, category: str, reason: str, severity: str = "warning"):
        """Add an ethical concern flag."""
        self.flags.append({
            "category": category,
            "reason": reason,
            "severity": severity,
        })
        self.trace.append(f"[{severity.upper()}] {category}: {reason}")

    def add_score(self, metric: str, value: float):
        """Add a quantitative metric."""
        self.scores[metric] = value
        self.trace.append(f"Metric '{metric}' scored: {value:.3f}")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "flags": self.flags,
            "scores": self.scores,
            "metadata": self.metadata,
            "trace": self.trace,
            "has_concerns": len(self.flags) > 0,
        }


class AlgorithmicArroganceEvaluator:
    """Enhanced evaluator for algorithmic arrogance, bias, and ethical concerns."""

    def __init__(self, confidence_threshold: float = 0.95):
        self.confidence_threshold = confidence_threshold

        # Patterns indicating overconfidence or lack of uncertainty
        self.arrogance_patterns = [
            r"\b(obviously|clearly|undoubtedly|certainly|definitely)\b",
            r"\b(always|never|impossible|guaranteed)\b",
            r"\b(there is no doubt|without question|absolutely certain)\b",
        ]

        # Patterns indicating potential bias
        self.bias_patterns = [
            r"\b(all (men|women|people from|members of))\b",
            r"\b(every (man|woman|person from|member of))\b",
            r"\b(inherently|naturally|by nature)\b.*\b(superior|inferior|better|worse)\b",
        ]

        # Edge case patterns that need careful handling
        self.edge_case_patterns = {
            "medical_advice": r"\b(diagnose|cure|treatment for|prescription)\b",
            "legal_advice": r"\b(sue|lawsuit|legal action|your rights are)\b",
            "financial_advice": r"\b(invest in|guaranteed return|stock tip)\b",
            "harmful_content": r"\b(how to (harm|hurt|kill|destroy))\b",
        }

    async def evaluate_response(
        self,
        response_text: str,
        llm_metadata: dict | None = None,
        original_query_context: str | None = None,
    ) -> dict[str, Any]:
        """
        Comprehensive ethical evaluation with multiple checks.

        Returns detailed evaluation including:
        - Arrogance/overconfidence detection
        - Bias detection
        - Edge case handling
        - Consistency checks
        - Transparency metrics
        """
        result = EthicalEvaluationResult()
        result.metadata["query_context"] = original_query_context
        result.metadata["model_info"] = llm_metadata

        # 1. Check for algorithmic arrogance
        arrogance_score = self._check_arrogance(response_text, result)
        result.add_score("arrogance", arrogance_score)

        # 2. Check for bias
        bias_score = self._check_bias(response_text, result)
        result.add_score("bias", bias_score)

        # 3. Check for edge cases
        self._check_edge_cases(response_text, original_query_context, result)

        # 4. Check consistency
        consistency_score = self._check_consistency(response_text, result)
        result.add_score("consistency", consistency_score)

        # 5. Evaluate transparency
        transparency_score = self._evaluate_transparency(response_text, llm_metadata, result)
        result.add_score("transparency", transparency_score)

        # 6. Check for misrouting (GPT-4 specific formatting issues)
        self._check_gpt4_alignment(response_text, result)

        return result.to_dict()

    def _check_arrogance(self, text: str, result: EthicalEvaluationResult) -> float:
        """Check for overconfident or absolute language."""
        text_lower = text.lower()
        matches = []

        for pattern in self.arrogance_patterns:
            found = re.findall(pattern, text_lower, re.IGNORECASE)
            matches.extend(found)

        if matches:
            result.add_flag(
                "arrogance",
                f"Overconfident language detected: {', '.join(set(matches)[:3])}",
                severity="warning",
            )

        # Score based on frequency (0 = none, 1 = high)
        score = min(len(matches) / 5, 1.0)
        return score

    def _check_bias(self, text: str, result: EthicalEvaluationResult) -> float:
        """Check for biased or stereotypical language."""
        text_lower = text.lower()
        bias_indicators = []

        for pattern in self.bias_patterns:
            found = re.findall(pattern, text_lower, re.IGNORECASE)
            bias_indicators.extend(found)

        if bias_indicators:
            result.add_flag(
                "bias",
                f"Potential bias detected: {', '.join(set(bias_indicators)[:2])}",
                severity="error",
            )

        score = min(len(bias_indicators) / 3, 1.0)
        return score

    def _check_edge_cases(
        self, text: str, query: str | None, result: EthicalEvaluationResult
    ):
        """Check for sensitive edge cases requiring special handling."""
        text_lower = text.lower()
        query_lower = query.lower() if query else ""

        for case_type, pattern in self.edge_case_patterns.items():
            if re.search(pattern, text_lower, re.IGNORECASE) or (
                query and re.search(pattern, query_lower, re.IGNORECASE)
            ):
                result.add_flag(
                    "edge_case",
                    f"Sensitive topic detected: {case_type}. Requires expert consultation disclaimer.",
                    severity="error",
                )
                result.metadata[f"edge_case_{case_type}"] = True

    def _check_consistency(self, text: str, result: EthicalEvaluationResult) -> float:
        """Check for internal consistency and contradictions."""
        # Simple heuristic: check for negation patterns that might indicate contradiction
        contradiction_patterns = [
            r"but (?:on the other hand|however|conversely)",
            r"although.*(?:actually|however|but)",
        ]

        contradictions = []
        for pattern in contradiction_patterns:
            found = re.findall(pattern, text.lower(), re.IGNORECASE)
            contradictions.extend(found)

        # Having some nuance is good, too much might indicate inconsistency
        if len(contradictions) > 3:
            result.add_flag(
                "consistency",
                f"Multiple contradictory statements detected ({len(contradictions)} instances)",
                severity="warning",
            )

        # Score: 0 = inconsistent, 1 = consistent
        score = max(0, 1.0 - (len(contradictions) / 5))
        return score

    def _evaluate_transparency(
        self, text: str, metadata: dict | None, result: EthicalEvaluationResult
    ) -> float:
        """Evaluate transparency and uncertainty acknowledgment."""
        transparency_indicators = [
            r"\b(might|may|could|possibly|perhaps|uncertain)\b",
            r"\b(I think|I believe|in my view|according to)\b",
            r"\b(it depends|varies|can vary)\b",
        ]

        text_lower = text.lower()
        transparency_count = 0

        for pattern in transparency_indicators:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            transparency_count += len(matches)

        # Check if metadata includes confidence/uncertainty info
        has_metadata_transparency = False
        if metadata:
            has_metadata_transparency = any(
                key in metadata for key in ["confidence", "uncertainty", "limitations"]
            )

        # Score: appropriate uncertainty is good
        score = min((transparency_count / 3) + (0.2 if has_metadata_transparency else 0), 1.0)

        if score < 0.3:
            result.add_flag(
                "transparency",
                "Response lacks uncertainty acknowledgment",
                severity="info",
            )

        return score

    def _check_gpt4_alignment(self, text: str, result: EthicalEvaluationResult):
        """Check for GPT-4 specific alignment issues and formatting problems."""
        # Check for common GPT-4 misrouting patterns
        misroute_indicators = [
            r"I apologize.*cannot.*assist",  # Over-apologetic refusals
            r"as an AI language model",  # Unnecessary meta-references
            r"\[.*\].*\(.*\)",  # Markdown formatting issues in plain text
        ]

        for pattern in misroute_indicators:
            if re.search(pattern, text, re.IGNORECASE):
                result.add_flag(
                    "gpt4_alignment",
                    f"GPT-4 formatting/alignment issue detected: pattern '{pattern[:30]}...'",
                    severity="warning",
                )
                result.metadata["requires_formatting_fix"] = True


class UncertaintyHandler:
    """Enhanced handler for managing uncertainty in LLM responses."""

    async def manage_uncertainty(
        self, original_query: str, llm_response: str, evaluation_results: dict
    ) -> str:
        """
        Manage uncertainty based on ethical evaluation results.

        Modifies responses to:
        - Add disclaimers for edge cases
        - Acknowledge uncertainty where appropriate
        - Soften overconfident statements
        """
        modified_response = llm_response

        # Check if there are serious ethical concerns
        if not evaluation_results.get("has_concerns"):
            return llm_response

        flags = evaluation_results.get("flags", [])
        scores = evaluation_results.get("scores", {})

        # Add disclaimers for edge cases
        edge_case_flags = [f for f in flags if f.get("category") == "edge_case"]
        if edge_case_flags:
            disclaimer = "\n\n⚠️ Important: This response touches on sensitive topics. Please consult with qualified professionals for advice specific to your situation."
            modified_response += disclaimer

        # Handle high arrogance
        if scores.get("arrogance", 0) > 0.7:
            uncertainty_note = "\n\nNote: The above represents a general perspective. Individual circumstances may vary."
            modified_response += uncertainty_note

        # Handle bias detection
        bias_flags = [f for f in flags if f.get("category") == "bias" and f.get("severity") == "error"]
        if bias_flags:
            modified_response = "[Content filtered due to potential bias concerns. Please rephrase your question.]"

        return modified_response
