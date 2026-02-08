"""
YAML-based Model Router for Kor'tana

This router reads from models.yaml and provides intelligent model selection
based on capabilities, cost optimization, and task requirements.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """Model information structure."""

    id: str
    name: str
    provider: str
    context_window: int
    cost_tier: str
    cost_per_1m_input: float
    cost_per_1m_output: float
    capabilities: list[str]


class YamlModelRouter:
    """
    YAML-based model router that provides intelligent model selection
    based on the models.yaml configuration.
    """

    def __init__(self, config_path: str = "src/kortana/config/models.yaml"):
        self.config_path = Path(config_path)
        self.models: dict[str, ModelInfo] = {}
        self.default_routing: dict[str, str] = {}
        self._load_config()

    def _load_config(self):
        """Load the models.yaml configuration file."""
        try:
            with open(self.config_path) as f:
                config = yaml.safe_load(f)

            # Parse models
            for model_data in config.get("models", []):
                model_info = ModelInfo(
                    id=model_data["id"],
                    name=model_data["name"],
                    provider=model_data["provider"],
                    context_window=model_data["context_window"],
                    cost_tier=model_data["cost_tier"],
                    cost_per_1m_input=model_data.get("cost_per_1m_input", 0.0),
                    cost_per_1m_output=model_data.get("cost_per_1m_output", 0.0),
                    capabilities=model_data.get("capabilities", []),
                )
                self.models[model_info.id] = model_info

            # Parse default routing
            self.default_routing = config.get("default_routing", {})

            logger.info(f"Loaded {len(self.models)} models from {self.config_path}")

        except Exception as e:
            logger.error(f"Failed to load model configuration: {e}")
            raise

    def get_model(self, model_id: str) -> ModelInfo | None:
        """Get model information by ID."""
        return self.models.get(model_id)

    def select_model_by_capability(
        self, capability: str, prefer_free: bool = True
    ) -> ModelInfo | None:
        """
        Select the best model based on a capability.

        Args:
            capability: The desired capability (e.g., "fast", "long_context", "reasoning")
            prefer_free: Whether to prefer free models when possible

        Returns:
            The selected model info
        """
        # Find models with the capability
        suitable_models = [
            model for model in self.models.values() if capability in model.capabilities
        ]

        if not suitable_models:
            logger.warning(f"No models found with capability '{capability}'")
            return None

        # Sort by preference
        def sort_key(model: ModelInfo):
            is_free = model.cost_tier == "free"
            cost_score = 1.0 if is_free else 1.0 / (model.cost_per_1m_input + 1)

            if prefer_free:
                return (-int(is_free), -cost_score, -model.context_window)
            else:
                return (-model.context_window, -cost_score)

        suitable_models.sort(key=sort_key)
        return suitable_models[0]

    def select_model_by_task(self, task_type: str) -> ModelInfo | None:
        """
        Select model by predefined task type from default_routing.

        Args:
            task_type: Task type like "default_chat", "default_planning", etc.

        Returns:
            The selected model info
        """
        model_id = self.default_routing.get(task_type)
        if not model_id:
            logger.warning(f"No default routing found for task '{task_type}'")
            return None

        return self.get_model(model_id)

    def select_cheapest_model(self, min_context_window: int = 0) -> ModelInfo | None:
        """Select the cheapest model that meets context requirements."""
        suitable_models = [
            model
            for model in self.models.values()
            if model.context_window >= min_context_window
        ]

        if not suitable_models:
            return None

        # Sort by cost (free first, then by input cost)
        def cost_sort_key(model: ModelInfo):
            if model.cost_tier == "free":
                return (0, 0)  # Free models first
            return (1, model.cost_per_1m_input)

        suitable_models.sort(key=cost_sort_key)
        return suitable_models[0]

    def select_best_for_context(
        self, context_length: int, prefer_free: bool = True
    ) -> ModelInfo | None:
        """Select the best model for a given context length requirement."""
        suitable_models = [
            model
            for model in self.models.values()
            if model.context_window >= context_length
        ]

        if not suitable_models:
            logger.warning(f"No models can handle context length {context_length}")
            return None

        # Sort by preference
        def sort_key(model: ModelInfo):
            is_free = model.cost_tier == "free"
            1.0 if is_free else 1.0 / (model.cost_per_1m_input + 1)

            if prefer_free:
                return (-int(is_free), model.cost_per_1m_input, -model.context_window)
            else:
                return (model.cost_per_1m_input, -model.context_window)

        suitable_models.sort(key=sort_key)
        return suitable_models[0]

    def estimate_cost(
        self, model_id: str, input_tokens: int, output_tokens: int
    ) -> float:
        """Estimate cost for a request."""
        model = self.get_model(model_id)
        if not model:
            return 0.0

        input_cost = (input_tokens / 1_000_000) * model.cost_per_1m_input
        output_cost = (output_tokens / 1_000_000) * model.cost_per_1m_output

        return input_cost + output_cost

    def get_free_models(self) -> list[ModelInfo]:
        """Get all free models."""
        return [model for model in self.models.values() if model.cost_tier == "free"]

    def get_models_by_capability(self, capability: str) -> list[ModelInfo]:
        """Get all models that have a specific capability."""
        return [
            model for model in self.models.values() if capability in model.capabilities
        ]

    def list_all_models(self) -> list[ModelInfo]:
        """Get all available models."""
        return list(self.models.values())

    def export_summary(self) -> str:
        """Export a summary of available models and routing."""
        summary = []
        summary.append("=== Kor'tana Model Configuration Summary ===\n")

        # Group models by cost tier
        tiers = {}
        for model in self.models.values():
            tier = model.cost_tier
            if tier not in tiers:
                tiers[tier] = []
            tiers[tier].append(model)

        for tier, models in sorted(tiers.items()):
            summary.append(f"{tier.upper()} Models:")
            for model in models:
                cost_str = (
                    "FREE"
                    if model.cost_tier == "free"
                    else f"${model.cost_per_1m_input:.3f}/${model.cost_per_1m_output:.3f}"
                )
                capabilities_str = ", ".join(model.capabilities)
                summary.append(f"  • {model.id}")
                summary.append(f"    {model.name} ({cost_str})")
                summary.append(f"    Context: {model.context_window:,} tokens")
                summary.append(f"    Capabilities: {capabilities_str}")
            summary.append("")

        # Default routing
        summary.append("Default Task Routing:")
        for task, model_id in self.default_routing.items():
            summary.append(f"  • {task}: {model_id}")

        return "\n".join(summary)


# Singleton instance
yaml_router = YamlModelRouter()
