import json
from typing import Any


class PlanningEngine:
    def __init__(self):
        self._model_router = None  # Lazy initialization to avoid circular imports
        print("INFO: PlanningEngine initialized with Enhanced Model Router.")

    @property
    def model_router(self):
        """Lazy initialization of model router to avoid circular imports."""
        if self._model_router is None:
            from kortana.core.services import get_enhanced_model_router

            self._model_router = get_enhanced_model_router()
        return self._model_router

    async def create_plan_for_goal(
        self, goal_description: str, core_beliefs: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """
        Uses an LLM to break down a high-level goal into a sequence of executable steps, guided by core beliefs.
        """
        prompt = self._build_planning_prompt(goal_description, core_beliefs or [])

        print("INFO: PlanningEngine using Enhanced Model Router for plan generation...")

        # Use the enhanced model router for optimal model selection
        # Planning tasks benefit from reasoning capability and cost optimization

        # Route the planning request through our optimized model selection
        model_id, voice_style, model_params = self.model_router.route(
            f"Planning request: {goal_description}",
            {"task_type": "planning", "context_length": len(prompt)},
            prefer_free=True,
        )

        # Get the appropriate LLM client for the selected model
        from kortana.core.services import get_llm_client_factory

        llm_client_factory = get_llm_client_factory()
        llm_client = llm_client_factory.get_client(model_id)

        # Generate the plan using the optimal model
        llm_result = await llm_client.complete(prompt, **model_params)

        raw_plan = llm_result.get("content")
        if not raw_plan:
            print(
                f"ERROR: LLM failed to generate a plan using model {model_id}. Details: {llm_result.get('error')}"
            )
            return []

        print(f"INFO: Plan generated successfully using model: {model_id}")
        return self._parse_llm_plan(raw_plan)

    def _build_planning_prompt(
        self, goal_description: str, core_beliefs: list[str]
    ) -> str:
        belief_prompt_part = ""
        if core_beliefs:
            beliefs_text = "\n".join([f"- {belief}" for belief in core_beliefs])
            belief_prompt_part = f"""
My Core Beliefs & Best Practices (You MUST adhere to these):
{beliefs_text}
"""
        return f"""
You are an expert planning module for an autonomous AI agent named Kor'tana.
Your task is to take a high-level goal and decompose it into a precise, step-by-step plan.
{belief_prompt_part}
The output MUST be a valid JSON array of objects. Each object represents one step and must have 'action_type' and 'parameters' keys.

## Available `action_type` values:

1.  **`\"READ_FILE\"`**: Reads the full content of a specified file.
    - `parameters`: {{"filepath": "path/to/file.ext"}}

2.  **`\"WRITE_FILE\"`**: Writes new content to a specified file, overwriting it completely.
    - `parameters`: {{"filepath": "path/to/file.ext", "content": "The new content of the file."}}

3.  **`\"EXECUTE_SHELL\"`**: Executes a shell command in the project's root directory. Use this for tasks like running tests, linting, or installing dependencies.
    - `parameters`: {{"command": "shell command to run"}}

4.  **`\"SEARCH_CODEBASE\"`**: Finds relevant code snippets or files based on a natural language query.
    - `parameters`: {{"query": "natural language query for finding relevant code"}}

5.  **`\"APPLY_PATCH\"`**: Applies a targeted change to a file using a diff format (e.g., unified diff). This is safer than a full overwrite for minor changes.
    - `parameters`: {{"filepath": "path/to/file.ext", "patch_content": "the diff content to apply"}}

6.  **`\"RUN_TESTS\"`**: A specialized command for running the project's test suite and capturing the outcome.
    - `parameters`: {{ "test_command": "command to run tests (e.g., 'poetry run pytest')", "post_analysis_query": "optional: a natural language query for an LLM to analyze test results if they are complex (e.g., 'Were there any new failures related to user authentication?')"}}

7.  **`\"REASONING_COMPLETE\"`**: This MUST be the final step of every successful plan. It signifies the goal has been achieved.
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

    def _parse_llm_plan(self, raw_plan_text: str) -> list[dict[str, Any]]:
        """
        Safely parses the LLM's text response to extract the JSON plan.
        Handles common LLM formatting quirks like markdown code blocks.
        """
        try:
            # The LLM often wraps the JSON in ```json ... ```. This cleaning is robust.
            if "```json" in raw_plan_text:
                # Extract content between the first ```json and the final ```
                clean_text = raw_plan_text.split("```json\n", 1)[1].rsplit("\n```", 1)[
                    0
                ]
            else:
                # Sometimes the LLM just returns the raw JSON.
                clean_text = raw_plan_text

            plan = json.loads(clean_text)

            if isinstance(plan, list):
                # Basic validation of plan structure
                for step in plan:
                    if not all(k in step for k in ("action_type", "parameters")):
                        raise ValueError(
                            "Invalid plan step: missing 'action_type' or 'parameters'."
                        )
                return plan
            else:
                raise ValueError("Parsed JSON is not a list.")

        except (json.JSONDecodeError, IndexError, ValueError) as e:
            print(f"ERROR: Could not parse plan from LLM response. Reason: {e}")
            print("--- Raw LLM Response ---")
            print(raw_plan_text)
            print("--------------------------")
            return []


# Singleton instance for easy access
planning_engine = PlanningEngine()
