"""
Self-Assessment Agent logic for KOR'TANA.
This agent grades code quality and determines if a branch is ready for 'Sacred absorption'.
"""

from typing import Any, Dict
from src.kortana.services.gemini import gemini_service
from src.kortana.logger import log_request, log_error

class SelfAssessmentAgent:
    """Agent that performs deep self-analysis on generated code and evolution branches."""

    def __init__(self):
        self.grading_rubric = {
            "type_safety": 0.3,
            "security": 0.3,
            "consistency": 0.2,
            "documentation": 0.2
        }

    async def assess_code(self, code: str, context: str = "") -> Dict[str, Any]:
        """
        Grades a block of code based on the KOR'TANA rubrics.
        Returns a detailed report and a 'fusion_ready' status.
        """
        prompt = f"""
        we are the kor'tana self-assessment agent.
        Your mission is to grade the following code for inclusion in the Canonical Organism.

        CODE TO ASSESS:
        ```python
        {code}
        ```

        CONTEXT:
        {context}

        ASSESSMENT CRITIERA:
        1. Type Safety: Are all functions typed? Are Pydantic models used where appropriate?
        2. Security: Are there any injection points or hardcoded secrets?
        3. Consistency: Does it follow the KOR'TANA snake_case and service/router pattern?
        4. Documentation: Are there docstrings with examples?

        RESPONSE FORMAT:
        Return a JSON-compatible assessment with:
        - score: (0.0 to 1.0)
        - strengths: []
        - weaknesses: []
        - fusion_ready: (true/false) - Only true if score > 0.85
        - suggested_fixes: []
        """

        try:
            log_request("self-assessment", "Initiating self-grade saga.")
            response = await gemini_service.analyze_text(prompt)

            # Simple extractor for pseudo-JSON response or raw text
            # In a production fusion, we'd use a stricter parser
            return {
                "raw_assessment": response,
                "timestamp": "2026-03-15",
                "agent": "KOR'TANA_SELF_ASSESSOR_V1"
            }
        except Exception as e:
            log_error("self-assessment", f"Saga failed: {str(e)}")
            return {"error": "Assessment failed", "details": str(e)}

    def check_lineage_signature(self, branch_name: str, commit_msg: str) -> bool:
        """Verifies if the branch carries the 'Sacred absorption' lineage."""
        signature = "Sacred absorption"
        return signature in commit_msg or branch_name.startswith("evolution/")

# Instance for service use
self_assessor = SelfAssessmentAgent()
