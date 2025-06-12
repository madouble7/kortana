import json
from typing import List, Dict, Any
from kortana.services.llm_service import llm_service

class PlanningEngine:
    def __init__(self):
        print("INFO: PlanningEngine initialized.")

    async def create_plan_for_goal(self, goal_description: str) -> List[Dict[str, Any]]:
        """
        Uses an LLM to break down a high-level goal into a sequence of executable steps.
        """
        prompt = self._build_planning_prompt(goal_description)
        # Use lower temperature for more deterministic, structured output
        llm_result = await llm_service.generate_response(prompt, temperature=0.1, model="gpt-4o")

        raw_plan = llm_result.get("content")
        if not raw_plan:
            print(f"ERROR: LLM failed to generate a plan. Details: {llm_result.get('error')}")
            return []

        return self._parse_llm_plan(raw_plan)

    def _build_planning_prompt(self, goal_description: str) -> str:
        """
        Constructs the detailed prompt for the LLM to generate a plan.
        This prompt engineering is critical for reliable output.
        """
        return f"""
You are an expert planning module for an autonomous AI agent named Kor'tana.
Your task is to take a high-level goal and decompose it into a precise, step-by-step plan.
The output MUST be a valid JSON array of objects. Each object represents one step and must have 'action_type' and 'parameters' keys.

## Available `action_type` values:

1.  **`\"READ_FILE\"`**: Reads the full content of a specified file.
    - `parameters`: {{"filepath": "path/to/file.ext"}}

2.  **`\"WRITE_FILE\"`**: Writes new content to a specified file, overwriting it completely.
    - `parameters`: {{"filepath": "path/to/file.ext", "content": "The new content of the file."}}

3.  **`\"EXECUTE_SHELL\"`**: Executes a shell command in the project's root directory. Use this for tasks like running tests, linting, or installing dependencies.
    - `parameters`: {{"command": "shell command to run"}}

4.  **`\"REASONING_COMPLETE\"`**: This MUST be the final step of every successful plan. It signifies the goal has been achieved.
    - `parameters`: {{"final_summary": "A brief, one-sentence summary of what was accomplished."}}

## Instructions:
- Think step-by-step.
- The `filepath` parameter must be a relative path from the project root (e.g., "src/kortana/core/main.py").
- The `content` for `WRITE_FILE` must be a single JSON-compatible string. Escape newlines with `\\n`.
- Do not add any commentary or explanation outside of the JSON structure. Your entire response must be ONLY the JSON array.

## Goal to Plan:
"{goal_description}"

## Your JSON Plan:
"""

    def _parse_llm_plan(self, raw_plan_text: str) -> List[Dict[str, Any]]:
        """
        Safely parses the LLM's text response to extract the JSON plan.
        Handles common LLM formatting quirks like markdown code blocks.
        """
        try:
            # The LLM often wraps the JSON in ```json ... ```. This cleaning is robust.
            if "```json" in raw_plan_text:
                # Extract content between the first ```json and the final ```
                clean_text = raw_plan_text.split("```json\n", 1)[1].rsplit("\n```", 1)[0]
            else:
                # Sometimes the LLM just returns the raw JSON.
                clean_text = raw_plan_text

            plan = json.loads(clean_text)

            if isinstance(plan, list):
                # Basic validation of plan structure
                for step in plan:
                    if not all(k in step for k in ("action_type", "parameters")):
                        raise ValueError("Invalid plan step: missing 'action_type' or 'parameters'.")
                return plan
            else:
                raise ValueError("Parsed JSON is not a list.")

        except (json.JSONDecodeError, IndexError, ValueError) as e:
            print(f"ERROR: Could not parse plan from LLM response. Reason: {e}")
            print(f"--- Raw LLM Response ---")
            print(raw_plan_text)
            print("--------------------------")
            return []

# Singleton instance for easy access
planning_engine = PlanningEngine()
