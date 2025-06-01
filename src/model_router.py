import json
import logging
import os
import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

# Import strategic layer components
from src.strategic_config import (
    SacredPrinciple,
    TaskCategory,
    UltimateLivingSacredConfig,
)

logger = logging.getLogger(__name__)


# Define Archetype Enum for clarity in routing logic
class ModelArchetype(Enum):
    ORACLE = "oracle"
    SWIFT_RESPONDER = "swift_responder"
    MEMORY_WEAVER = "memory_weaver"
    DEV_AGENT = "dev_agent"
    BUDGET_WORKHORSE = "budget_workhorse"
    MULTIMODAL_SEER = "multimodal_seer"


@dataclass
class AugmentedModelConfig:
    """Represents model configuration augmented with strategic data."""

    model_id: str
    provider: str
    model_name: str
    api_key_env: str
    base_url: Optional[str]
    default_params: Dict[str, Any]
    benchmarks: Dict[str, Any]
    sacred_alignment_scores: Dict[str, float]
    archetype_fit_scores: Dict[str, float]
    # Add other relevant fields from models_config.json
    cost_per_1m_input: Optional[float] = None
    cost_per_1m_output: Optional[float] = None
    context_window: Optional[int] = None


class SacredModelRouter:
    """
    Tactical model router that selects the best model based on task requirements,
    constraints, and strategic guidance from the UltimateLivingSacredConfig.
    """

    def __init__(self, models_config_path: str = "config/models_config.json"):
        self.models_config_path = models_config_path
        self.loaded_models_config: Dict[str, Any] = self._load_models_config()
        self.sacred_config = UltimateLivingSacredConfig()  # Instantiate strategic layer
        self.routing_history: List[Dict[str, Any]] = []

        # Define mapping from TaskCategory to primary ModelArchetype (can be
        # refined)
        self.category_to_archetype_map: Dict[TaskCategory, ModelArchetype] = {
            TaskCategory.ORACLE: ModelArchetype.ORACLE,
            TaskCategory.SWIFT_RESPONDER: ModelArchetype.SWIFT_RESPONDER,
            TaskCategory.MEMORY_WEAVER: ModelArchetype.MEMORY_WEAVER,
            TaskCategory.DEV_AGENT: ModelArchetype.DEV_AGENT,
            TaskCategory.BUDGET_WORKHORSE: ModelArchetype.BUDGET_WORKHORSE,
            TaskCategory.MULTIMODAL_SEER: ModelArchetype.MULTIMODAL_SEER,
            # Creative tasks often need high reasoning
            TaskCategory.CREATIVE_WRITING: ModelArchetype.ORACLE,
            # Technical analysis fits dev agent
            TaskCategory.TECHNICAL_ANALYSIS: ModelArchetype.DEV_AGENT,
            TaskCategory.PROBLEM_SOLVING: ModelArchetype.ORACLE,  # General problem solving
            # Conversation falls under Oracle
            TaskCategory.COMMUNICATION: ModelArchetype.ORACLE,
            # Research involves processing info
            TaskCategory.RESEARCH: ModelArchetype.MEMORY_WEAVER,
            TaskCategory.CODE_GENERATION: ModelArchetype.DEV_AGENT,  # Explicit code tasks
            TaskCategory.ETHICAL_REASONING: ModelArchetype.ORACLE,  # Complex reasoning
        }

    def _load_models_config(self) -> Dict[str, Any]:
        """Loads the existing models_config.json file."""
        if not os.path.exists(self.models_config_path):
            logger.error(f"Models config file not found at {self.models_config_path}")
            # Return a structure that allows the router to still initialize
            return {"default_llm_id": None, "models": {}}
        try:
            with open(self.models_config_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(
                f"Error decoding models config file {self.models_config_path}: {e}"
            )
            return {"default_llm_id": None, "models": {}}
        except Exception as e:
            logger.error(
                f"Error loading models config file {self.models_config_path}: {e}"
            )
            return {"models": {}}

    def get_model_config(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves the base configuration for a model from the loaded file."""
        return self.loaded_models_config.get("models", {}).get(model_id)

    def select_model_with_sacred_guidance(
        self, task_category: TaskCategory, constraints: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Selects the best model_id for a given task category, applying strategic guidance
        and tactical constraints.

        Args:
            task_category: The category of the task.
            constraints: Dictionary of tactical constraints (e.g., {"priority": "cost", "max_latency": 500}).

        Returns:
            The selected model_id or None if no suitable model is found.
        """
        logger.info(f"Selecting model for task category: {task_category.value}")
        if constraints is None:
            constraints = {}

        # 1. Get strategic guidance based on task category
        strategic_guidance = self.sacred_config.get_task_guidance(task_category)
        logger.debug(f"Strategic guidance: {strategic_guidance}")

        selected_model_id = None
        selection_reason = "dynamic"

        # NEW: 2. Check for explicit model routing in models_config.json
        explicit_routed_model_id = self.loaded_models_config.get(
            "model_routing", {}
        ).get(task_category.value)
        if explicit_routed_model_id:
            logger.info(
                f"Explicit routing found for task category {task_category.value}: {explicit_routed_model_id}"
            )
            routed_model_config = self.get_model_config(explicit_routed_model_id)
            if routed_model_config:
                # Check if the explicitly routed model is enabled and has an
                # API key and is one of the approved models
                is_enabled = routed_model_config.get("enabled", True)
                api_key_env = routed_model_config.get("api_key_env", "")
                api_key_set = bool(api_key_env and os.environ.get(api_key_env))
                is_approved = explicit_routed_model_id in ["gemini-2.5-flash", "gpt-4.1-nano"]

                if is_enabled and api_key_set and is_approved:
                    logger.info(
                        f"Using explicitly routed and approved model: {explicit_routed_model_id} for task category {task_category.value}"
                    )
                    selected_model_id = explicit_routed_model_id
                    selection_reason = "explicit_route"
                else:
                    reason = "not available" if not (is_enabled and api_key_set) else "not approved"
                    logger.warning(
                        f"Explicitly routed model {explicit_routed_model_id} for {task_category.value} is {reason}."
                        " Falling back to approved dynamic selection."
                    )
            else:
                logger.warning(
                    f"Explicitly routed model {explicit_routed_model_id} for {task_category.value} not found in models config."
                    " Falling back to approved dynamic selection."
                )

        # Original logic for dynamic selection if no explicit route or route is invalid/not approved
        if selected_model_id is None:
            # Determine primary archetype for this category
            primary_archetype = self.category_to_archetype_map.get(task_category)
            if not primary_archetype:
                logger.warning(
                    f"No primary archetype mapped for task category: {task_category.value}"
                )
                # Fallback to a default archetype like ORACLE if no specific
                # mapping
                primary_archetype = ModelArchetype.ORACLE

            # 2. Identify candidate models - ONLY ENABLED AND APPROVED ONES
            candidate_models: List[AugmentedModelConfig] = []
            approved_model_ids = ["gemini-2.5-flash", "gpt-4.1-nano"]

            for model_id, core_details in self.loaded_models_config.get(
                "models", {}
            ).items():
                # NEW: Check if model is enabled AND is one of the approved models
                if not core_details.get("enabled", True) or model_id not in approved_model_ids:
                    logger.debug(f"Model {model_id} is disabled or not approved, skipping dynamic selection")
                    continue

                # Check API key availability
                api_key_env = core_details.get("api_key_env", "")
                if api_key_env and not os.environ.get(api_key_env):
                    logger.warning(
                        f"Approved model {model_id} missing API key {api_key_env}, skipping dynamic selection"
                    )
                    continue

                # Augment core_details with strategic data (from internal dicts in SacredConfig)
                # Safely access nested keys
                performance_scores = core_details.get("performance_scores", {})
                augmented_details = AugmentedModelConfig(
                    model_id=model_id,
                    provider=core_details.get("provider", "unknown"),
                    model_name=core_details.get("model_name", model_id),
                    api_key_env=core_details.get("api_key_env", ""),
                    base_url=core_details.get("base_url"),
                    default_params=core_details.get("default_params", {}),
                    benchmarks=performance_scores,  # Use the mapped existing field
                    cost_per_1m_input=core_details.get("cost_per_1m_input"),
                    cost_per_1m_output=core_details.get("cost_per_1m_output"),
                    context_window=core_details.get("context_window"),
                    sacred_alignment_scores=self.sacred_config.get_model_sacred_scores(
                        model_id
                    ),  # Get from strategic config
                    archetype_fit_scores=self.sacred_config.get_model_archetype_fits(
                        model_id
                    ),  # Get from strategic config
                )

                # Basic filtering: Must have a non-zero fit score for the primary
                # archetype (within the approved list)
                if (
                    augmented_details.archetype_fit_scores.get(primary_archetype.value, 0)
                    > 0
                ):
                    candidate_models.append(augmented_details)
                else:
                    logger.debug(
                        f"Approved model {model_id} filtered out during dynamic selection: Low fit for archetype {primary_archetype.value}"
                    )

            if not candidate_models:
                logger.warning(
                    f"No approved candidate models found for task category {task_category.value} and archetype {primary_archetype.value}."
                )
                # Fallback logic: Use default model from the loaded config if it exists and is a candidate
                # Check if default model ID exists in the loaded config AND has a
                # non-zero fit for the archetype AND is approved
                default_model_id = self.loaded_models_config.get("default_llm_id")
                if default_model_id in approved_model_ids:
                    default_model_details = self.sacred_config.get_model_archetype_fits(
                        default_model_id
                    )
                    if default_model_details.get(primary_archetype.value, 0) > 0:
                        logger.info(f"Falling back to approved default model: {default_model_id}")
                        selected_model_id = default_model_id
                        selection_reason = "fallback_default"
                    else:
                        logger.warning(
                            f"Approved default model {default_model_id} has low fit for archetype {primary_archetype.value}."
                            " Attempting universal fallback (gpt-4.1-nano) if approved."
                        )

                # Or fallback to a hardcoded universal default if no suitable model found at all
                # This requires a model ID that's expected to *always* be available and is approved
                universal_fallback_id: str = "gpt-4.1-nano"  # Example universal fallback

                if universal_fallback_id in approved_model_ids:
                    if universal_fallback_id is not None:
                        assert isinstance(universal_fallback_id, str)
                        universal_fallback_details = self.sacred_config.get_model_archetype_fits(
                            universal_fallback_id # type: ignore [arg-type]
                        )
                        if universal_fallback_details.get(primary_archetype.value, 0) > 0:
                            logger.warning(
                                f"Falling back to approved universal fallback model: {universal_fallback_id}"
                            )
                            selected_model_id = universal_fallback_id
                            selection_reason = "universal_fallback"


        # Final check and logging
        if selected_model_id:
            logger.info(f"Selected model: {selected_model_id} (Reason: {selection_reason})")
        else:
            logger.error("Failed to select any approved model.")

        # Log details if dynamic selection occurred from approved list
        if selection_reason == "dynamic" and selected_model_id:
             logger.info(f"Dynamic selection from approved models: {selected_model_id}")
        elif selected_model_id == "gpt-4.1-nano":
             logger.info(f"Prioritizing GPT-4.1 Nano as per directive.")
        elif selected_model_id == "google/gemini-2.0-flash-001":
             logger.info(f"Using Gemini 2.0 Flash as selected from approved models.")

        return selected_model_id

    def get_routing_stats(self) -> Dict[str, Any]:
        """Provides statistics on routing decisions."""
        # TODO: Implement detailed routing statistics analysis
        # Example: Count usage per model, average score per category, etc.
        return {
            "message": "Routing statistics not yet fully implemented.",
            "history_count": len(self.routing_history),
        }

    # Helper method to get model Sacred Alignment Scores
    def get_model_sacred_alignment(self, model_id: str) -> Dict[str, float]:
        """Retrieves sacred alignment scores for a model from the strategic config."""
        return self.sacred_config.get_model_sacred_scores(model_id)


# Example usage (for testing the class independently)
if __name__ == "__main__":
    # Assume config/models_config.json exists with a basic structure
    # and src/strategic_config.py exists with UltimateLivingSacredConfig

    # Create a dummy models_config.json for testing if it doesn't exist
    # This dummy config should match the structure read from your environment
    dummy_config_path = "config/models_config.json"
    if not os.path.exists("config"):
        os.makedirs("config")
    if not os.path.exists(dummy_config_path):
        dummy_content = {
            # Example default based on your read config
            "default_llm_id": "gemini-2.5-flash",
            "models": {
                "gemini-2.5-flash": {
                    "provider": "google_gemini",  # Provider name from your read config
                    "model_name": "gemini-1.5-flash-latest",  # Model name from your read config
                    "api_key_env": "GOOGLE_API_KEY",
                    "base_url": "https://generativelanguage.googleapis.com/v1beta",
                    "performance_scores": {
                        "gpqa": 82.8,
                        "reasoning": "excellent",
                        "efficiency": "maximum",
                        "tokens_per_sec_median": 330.3,  # Added for speed testing
                        "latency_first_chunk_sec": 0.4,  # Added for speed testing
                    },
                    "cost_per_1m_input": 0.15,  # From your read config
                    "cost_per_1m_output": 0.6,  # From your read config
                    "context_window": 1048576,  # From your read config
                    "use_cases": [
                        "primary",
                        "memory_processing",
                        "bulk_analysis",
                    ],  # From your read config
                },
                "grok-3-mini-reasoning": {
                    "provider": "xai_grok",  # From your read config
                    "model_name": "grok-3-mini",  # From your read config
                    "api_key_env": "XAI_API_KEY",
                    "base_url": "https://api.x.ai/v1",
                    "performance_scores": {
                        "gpqa": 84.6,
                        "reasoning": "exceptional",
                        "autonomous_capability": "optimized",
                        "latency_first_chunk_sec": 0.35,  # Added for speed testing
                    },
                    "cost_per_1m_input": 0.3,  # From your read config
                    "cost_per_1m_output": 0.5,  # From your read config
                    "context_window": 128000,  # From your read config
                    "use_cases": [
                        "autonomous_development",
                        "code_generation",
                        "reasoning",
                    ],  # From your read config
                },
                "claude-3.7-sonnet": {
                    "provider": "anthropic",  # From your read config
                    "model_name": "claude-3-5-sonnet-20241022",  # From your read config
                    "api_key_env": "ANTHROPIC_API_KEY",
                    "base_url": "https://api.anthropic.com/v1",
                    "performance_scores": {
                        "gpqa": 84.8,
                        "reasoning": "superior",
                        "empathy": "maximum",
                    },
                    "cost_per_1m_input": 3.00,  # From your read config
                    "cost_per_1m_output": 15.00,  # From your read config
                    "context_window": 200000,  # From your read config
                    "use_cases": [
                        "intimate_conversations",
                        "empathetic_responses",
                        "deep_analysis",
                    ],  # From your read config
                },
                "gpt-4o-mini-openai": {  # This ID was in the config you tried to create
                    "provider": "openai",
                    "model_name": "gpt-4o-mini",
                    "api_key_env": "OPENAI_API_KEY",
                    "base_url": "https://api.openai.com/v1",
                    "performance_scores": {
                        "aider_polyglot_percent_correct": 72.0,
                        "dubesor_overall_score": 65.8,
                        "tokens_per_sec_median": 125.7,
                        "latency_first_chunk_sec": 0.8,
                        "gpqa": 80.0,  # Example GPQA if not in original dump
                    },
                    "cost_per_1m_input": 0.15,
                    "cost_per_1m_output": 0.60,
                    "context_window": 128000,
                },
            },
        }
        with open(dummy_config_path, "w") as f:
            json.dump(dummy_content, f, indent=2)
        print(f"Created dummy config at {dummy_config_path}")

    # Initialize the router
    router = SacredModelRouter()
    print("\nSacredModelRouter initialized.")
    print(
        f"Loaded config with {len(router.loaded_models_config.get('models', {}))} models."
    )

    # Test model selection for different task categories and constraints
    print("\nTesting model selection:")

    # Test Case 1: Creative Writing (Prioritize Compassion/Wisdom, Quality)
    selected1 = router.select_model_with_sacred_guidance(
        TaskCategory.CREATIVE_WRITING, {"priority": "quality"}
    )
    print(
        f"Task: Creative Writing (Quality) -> Selected: {selected1}"
    )  # Expected: claude-3.7-sonnet or gemini-2.5-pro-google

    # Test Case 2: Code Generation (Prioritize Wisdom/Truth, Quality)
    selected2 = router.select_model_with_sacred_guidance(
        TaskCategory.CODE_GENERATION, {"priority": "quality"}
    )
    # Expected: grok-3-mini-reasoning or gpt-4o-mini-openai (depending on
    # score weights)
    print(f"Task: Code Generation (Quality) -> Selected: {selected2}")

    # Test Case 3: Swift Responder (Prioritize Speed)
    selected3 = router.select_model_with_sacred_guidance(
        TaskCategory.SWIFT_RESPONDER, {"priority": "speed"}
    )
    print(
        f"Task: Swift Responder (Speed) -> Selected: {selected3}"
    )  # Expected: gemini-2.5-flash-google

    # Test Case 4: Budget Workhorse (Prioritize Cost)
    selected4 = router.select_model_with_sacred_guidance(
        TaskCategory.BUDGET_WORKHORSE, {"priority": "cost"}
    )
    # Expected: gemini-2.5-flash-google (based on dummy cost, maybe
    # grok-3-mini-xai if added to dummy)
    print(f"Task: Budget Workhorse (Cost) -> Selected: {selected4}")

    # Test Case 5: Memory Weaver (Prioritize Context Window)
    selected5 = router.select_model_with_sacred_guidance(
        TaskCategory.MEMORY_WEAVER, {"priority": "context"}
    )  # Need context handling in calculate_combined_score
    print(
        f"Task: Memory Weaver (Context) -> Selected: {selected5}"
    )  # Expected: gemini-2.5-flash-google or gemini-2.5-pro-google

    print("\nRouting Stats:")
    print(router.get_routing_stats())
