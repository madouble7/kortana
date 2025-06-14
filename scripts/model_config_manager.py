#!/usr/bin/env python3
"""
Model Configuration Management Utility

This utility helps manage and validate Kor'tana's AI model configurations,
including adding new models, updating costs, and validating API keys.
"""

import json
import logging
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Model configuration structure."""

    provider: str
    api: str
    api_key_env: str
    model_name: str
    base_url: str
    style: str
    cost_per_1m_input: float
    cost_per_1m_output: float
    context_window: int
    capabilities: list[str]
    default_params: dict[str, Any]


class ModelConfigManager:
    """Manages model configurations."""

    def __init__(self, config_path: str = "config/models_config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """Load the current configuration."""
        try:
            if self.config_path.exists():
                with open(self.config_path) as f:
                    return json.load(f)
            else:
                logger.warning(
                    f"Config file {self.config_path} not found, creating new one"
                )
                return {"models": {}, "routing": {}, "default": {}, "fallback": {}}
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {"models": {}, "routing": {}, "default": {}, "fallback": {}}

    def _save_config(self):
        """Save the configuration to file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise

    def add_model(self, model_id: str, model_config: ModelConfig):
        """Add a new model configuration."""
        if "models" not in self.config:
            self.config["models"] = {}

        self.config["models"][model_id] = asdict(model_config)
        logger.info(f"Added model configuration for {model_id}")

    def remove_model(self, model_id: str):
        """Remove a model configuration."""
        if model_id in self.config.get("models", {}):
            del self.config["models"][model_id]
            logger.info(f"Removed model configuration for {model_id}")
        else:
            logger.warning(f"Model {model_id} not found in configuration")

    def update_model_costs(self, model_id: str, input_cost: float, output_cost: float):
        """Update model costs."""
        if model_id in self.config.get("models", {}):
            self.config["models"][model_id]["cost_per_1m_input"] = input_cost
            self.config["models"][model_id]["cost_per_1m_output"] = output_cost
            logger.info(f"Updated costs for {model_id}")
        else:
            logger.error(f"Model {model_id} not found")

    def list_models(self) -> list[str]:
        """List all configured models."""
        return list(self.config.get("models", {}).keys())

    def get_model(self, model_id: str) -> dict[str, Any] | None:
        """Get model configuration."""
        return self.config.get("models", {}).get(model_id)

    def validate_api_keys(self) -> dict[str, bool]:
        """Validate that all required API keys are set."""
        results = {}

        for model_id, config in self.config.get("models", {}).items():
            api_key_env = config.get("api_key_env")
            if api_key_env:
                results[model_id] = bool(os.getenv(api_key_env))
            else:
                results[model_id] = False

        return results

    def set_default_model(self, model_id: str, style: str = "presence"):
        """Set the default model."""
        self.config["default"] = {"model": model_id, "style": style}
        logger.info(f"Set default model to {model_id}")

    def set_fallback_model(self, model_id: str, style: str = "presence"):
        """Set the fallback model."""
        self.config["fallback"] = {"model": model_id, "style": style}
        logger.info(f"Set fallback model to {model_id}")

    def update_routing(self, task_type: str, model_id: str):
        """Update routing configuration."""
        if "routing" not in self.config:
            self.config["routing"] = {}

        self.config["routing"][task_type] = model_id
        logger.info(f"Set routing for {task_type} to {model_id}")

    def save(self):
        """Save configuration."""
        self._save_config()

    def export_summary(self) -> str:
        """Export a summary of the configuration."""
        summary = []
        summary.append("=== Kor'tana Model Configuration Summary ===\n")

        # Models
        summary.append("Configured Models:")
        for model_id, config in self.config.get("models", {}).items():
            provider = config.get("provider", "unknown")
            cost_input = config.get("cost_per_1m_input", 0)
            cost_output = config.get("cost_per_1m_output", 0)
            cost_str = (
                "FREE"
                if cost_input == 0 and cost_output == 0
                else f"${cost_input:.3f}/${cost_output:.3f}"
            )
            summary.append(f"  • {model_id} ({provider}) - {cost_str}")

        # API Key status
        summary.append("\nAPI Key Status:")
        api_status = self.validate_api_keys()
        for model_id, has_key in api_status.items():
            status = "✓" if has_key else "✗"
            summary.append(f"  {status} {model_id}")

        # Routing
        summary.append("\nTask Routing:")
        for task, model in self.config.get("routing", {}).items():
            summary.append(f"  • {task}: {model}")

        # Defaults
        default_model = self.config.get("default", {}).get("model", "Not set")
        fallback_model = self.config.get("fallback", {}).get("model", "Not set")
        summary.append(f"\nDefault Model: {default_model}")
        summary.append(f"Fallback Model: {fallback_model}")

        return "\n".join(summary)


def add_deepseek_r1_model():
    """Add the DeepSeek R1 0528 free model to configuration."""
    manager = ModelConfigManager()

    deepseek_config = ModelConfig(
        provider="openrouter",
        api="openrouter",
        api_key_env="OPENROUTER_API_KEY",
        model_name="deepseek/deepseek-r1-0528:free",
        base_url="https://openrouter.ai/api/v1",
        style="tactical",
        cost_per_1m_input=0.0,
        cost_per_1m_output=0.0,
        context_window=163840,
        capabilities=["text", "reasoning"],
        default_params={"temperature": 0.7, "max_tokens": 4096},
    )

    manager.add_model("deepseek-r1-0528-free", deepseek_config)
    manager.update_routing("reasoning_tasks", "deepseek-r1-0528-free")
    manager.update_routing("free_tier", "deepseek-r1-0528-free")
    manager.set_default_model("deepseek-r1-0528-free", "tactical")

    manager.save()

    print("✓ Added DeepSeek R1 0528 free model configuration")
    print("✓ Updated routing for reasoning tasks")
    print("✓ Set as default model")


def setup_recommended_models():
    """Set up a recommended model configuration."""
    manager = ModelConfigManager()

    # DeepSeek R1 (Free reasoning model)
    deepseek_config = ModelConfig(
        provider="openrouter",
        api="openrouter",
        api_key_env="OPENROUTER_API_KEY",
        model_name="deepseek/deepseek-r1-0528:free",
        base_url="https://openrouter.ai/api/v1",
        style="tactical",
        cost_per_1m_input=0.0,
        cost_per_1m_output=0.0,
        context_window=163840,
        capabilities=["text", "reasoning"],
        default_params={"temperature": 0.7, "max_tokens": 4096},
    )

    # Claude Haiku (Emotional support)
    claude_config = ModelConfig(
        provider="openrouter",
        api="openrouter",
        api_key_env="OPENROUTER_API_KEY",
        model_name="anthropic/claude-3-haiku",
        base_url="https://openrouter.ai/api/v1",
        style="whisper",
        cost_per_1m_input=0.25,
        cost_per_1m_output=1.25,
        context_window=200000,
        capabilities=["text", "vision", "function_call"],
        default_params={"temperature": 0.6, "max_tokens": 4096},
    )

    # GPT-4o-mini (General purpose)
    gpt_config = ModelConfig(
        provider="openai",
        api="openai",
        api_key_env="OPENAI_API_KEY",
        model_name="gpt-4o-mini",
        base_url="https://api.openai.com/v1",
        style="presence",
        cost_per_1m_input=0.15,
        cost_per_1m_output=0.6,
        context_window=128000,
        capabilities=["text", "vision", "function_call"],
        default_params={"temperature": 0.7, "max_tokens": 4096},
    )

    # Gemini Flash (Vision tasks)
    gemini_config = ModelConfig(
        provider="google",
        api="google_gemini",
        api_key_env="GOOGLE_API_KEY",
        model_name="gemini-1.5-flash",
        base_url="https://generativelanguage.googleapis.com/v1beta",
        style="presence",
        cost_per_1m_input=0.075,
        cost_per_1m_output=0.3,
        context_window=1000000,
        capabilities=["text", "vision", "function_call"],
        default_params={"temperature": 0.7, "max_tokens": 4096},
    )

    # Grok (Creative writing)
    grok_config = ModelConfig(
        provider="xai",
        api="xai",
        api_key_env="XAI_API_KEY",
        model_name="grok-3-mini-beta",
        base_url="https://api.x.ai/v1",
        style="fire",
        cost_per_1m_input=0.1,
        cost_per_1m_output=0.1,
        context_window=131072,
        capabilities=["text"],
        default_params={"temperature": 0.85, "max_tokens": 4096},
    )

    # Add all models
    manager.add_model("deepseek-r1-0528-free", deepseek_config)
    manager.add_model("anthropic/claude-3-haiku", claude_config)
    manager.add_model("gpt-4o-mini-openai", gpt_config)
    manager.add_model("gemini-1.5-flash", gemini_config)
    manager.add_model("x-ai/grok-3-mini-beta", grok_config)

    # Set up routing
    routing_config = {
        "reasoning_tasks": "deepseek-r1-0528-free",
        "emotional_support": "anthropic/claude-3-haiku",
        "general_chat": "gpt-4o-mini-openai",
        "creative_writing": "x-ai/grok-3-mini-beta",
        "vision_tasks": "gemini-1.5-flash",
        "free_tier": "deepseek-r1-0528-free",
    }

    for task, model in routing_config.items():
        manager.update_routing(task, model)

    # Set defaults
    manager.set_default_model("deepseek-r1-0528-free", "tactical")
    manager.set_fallback_model("gemini-1.5-flash", "presence")

    manager.save()

    print("✓ Set up recommended model configuration")
    print("✓ Configured task-based routing")
    print("✓ Set default and fallback models")


def main():
    """Main CLI interface."""
    if len(sys.argv) < 2:
        print("Model Configuration Management Utility")
        print("\nUsage:")
        print("  python model_config_manager.py <command>")
        print("\nCommands:")
        print("  add-deepseek      Add DeepSeek R1 0528 free model")
        print("  setup-recommended Set up recommended model configuration")
        print("  list              List all configured models")
        print("  summary           Show configuration summary")
        print("  validate          Validate API keys")
        return

    command = sys.argv[1]
    manager = ModelConfigManager()

    if command == "add-deepseek":
        add_deepseek_r1_model()

    elif command == "setup-recommended":
        setup_recommended_models()

    elif command == "list":
        models = manager.list_models()
        print("Configured models:")
        for model in models:
            print(f"  • {model}")

    elif command == "summary":
        print(manager.export_summary())

    elif command == "validate":
        api_status = manager.validate_api_keys()
        print("API Key Validation:")
        for model, has_key in api_status.items():
            status = "✓" if has_key else "✗"
            print(f"  {status} {model}")

    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
