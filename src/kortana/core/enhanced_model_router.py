"""
Enhanced Model Router for Kor'tana

This module provides intelligent model selection and routing based on:
- Task type analysis
- Cost optimization
- Model capabilities
- Context length requirements
- Performance characteristics
"""

import json
import logging
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path  # Added import
from typing import Any

from kortana.config.schema import KortanaConfig

# from ..config import get_project_root # May be needed for path resolution

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Task types for intelligent model routing."""

    REASONING = "reasoning"
    EMOTIONAL_SUPPORT = "emotional_support"
    GENERAL_CHAT = "general_chat"
    CREATIVE_WRITING = "creative_writing"
    VISION = "vision"
    FUNCTION_CALL = "function_call"
    CODING = "coding"
    ANALYSIS = "analysis"
    LONGFORM = "longform"


@dataclass
class ModelCapabilities:
    """Model capabilities and characteristics."""

    supports_vision: bool = False
    supports_function_calls: bool = False
    supports_reasoning: bool = False
    context_window: int = 4096
    cost_per_1m_input: float = 0.0
    cost_per_1m_output: float = 0.0
    max_output_tokens: int = 4096
    performance_score: float = 1.0  # Relative performance rating


@dataclass
class ModelMetadata:
    """Complete model metadata."""

    model_id: str
    provider: str
    capabilities: ModelCapabilities
    default_style: str
    preferred_tasks: list[TaskType]


class EnhancedModelRouter:
    """
    Enhanced model router with intelligent task-based routing and cost optimization.
    """

    def __init__(self, settings: KortanaConfig):
        """
        Initialize the enhanced router.

        Args:
            settings: The application configuration.
        """
        self.settings = settings
        self.models_config = {}  # Initialize as empty dict
        self.model_metadata = {}  # Initialize as empty dict

        config_file_path_str = settings.paths.models_config_file_path
        absolute_config_path = Path(config_file_path_str)

        if not absolute_config_path.is_absolute():
            try:
                from ..config import get_project_root  # Delayed import

                absolute_config_path = get_project_root() / config_file_path_str
            except ImportError:
                logger.warning(
                    "get_project_root not available for resolving models_config_file_path in EnhancedModelRouter, assuming CWD relative or absolute."
                )

        if absolute_config_path.exists():
            try:
                with open(absolute_config_path, encoding="utf-8") as f:
                    loaded_json = json.load(f)
                    # Assuming the loaded JSON directly contains the models configuration
                    # e.g., {"models": {...}, "routing_rules": [...]} or just {"model_id": {...}}
                    # The original code used self._load_models_config() which might have specific logic
                    # For now, let's assume the JSON file IS the models_config
                    self.models_config = loaded_json
                logger.info(
                    f"Successfully loaded models configuration for EnhancedModelRouter from {absolute_config_path}"
                )
            except json.JSONDecodeError as e:
                logger.error(
                    f"Failed to decode JSON for EnhancedModelRouter from {absolute_config_path}: {e}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to load models configuration for EnhancedModelRouter from {absolute_config_path}: {e}"
                )
        else:
            logger.error(
                f"Models configuration file for EnhancedModelRouter not found at {absolute_config_path}. Using empty config."
            )

        # self.model_metadata = self._build_model_metadata() # This needs self.models_config to be populated
        # Re-enable _build_model_metadata if it relies on self.models_config
        if self.models_config:  # Only build if config was loaded
            self.model_metadata = self._build_model_metadata()
        else:
            self.model_metadata = {}  # Ensure it's an empty dict if no config

        # Voice styles (seems independent of models_config file)
        self.voice_styles = {
            "presence": {
                "description": "Grounded, steady, like a hand on your back",
                "temperature": 0.7,
                "top_p": 0.9,
            },
            "fire": {
                "description": "Catalytic, bold, the voice that dares you to rise",
                "temperature": 0.85,
                "top_p": 0.95,
            },
            "whisper": {
                "description": "Intimate, soothing, a balm when you are raw",
                "temperature": 0.6,
                "top_p": 0.85,
            },
            "tactical": {
                "description": "Clear, precise, when you just need to know what's next",
                "temperature": 0.5,
                "top_p": 0.8,
            },
        }

    def _load_models_config(self) -> dict[str, Any]:
        """Load models configuration from file."""
        try:
            # Try multiple possible config file paths
            config_paths = [
                getattr(self.settings, "paths", {}).get("models_config_file_path"),
                "config/models_config.json",
                "src/kortana/config/models_config.json",
                "models_config.json",
            ]

            for config_path in config_paths:
                if config_path and Path(config_path).exists():
                    with open(config_path) as f:
                        return json.load(f)

            logger.warning("No models configuration file found, using default config")
            return self._get_default_config()
        except Exception as e:
            logger.error(f"Failed to load models configuration: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> dict[str, Any]:
        """Get default fallback configuration."""
        return {
            "models": {
                "deepseek-r1-0528-free": {
                    "provider": "openrouter",
                    "model_name": "deepseek/deepseek-r1-0528:free",
                    "style": "tactical",
                }
            },
            "routing": {"reasoning_tasks": "deepseek-r1-0528-free"},
            "default": {"model": "deepseek-r1-0528-free", "style": "tactical"},
        }

    def _build_model_metadata(self) -> dict[str, ModelMetadata]:
        """Build comprehensive model metadata."""
        metadata = {}

        for model_id, config in self.models_config.get("models", {}).items():
            capabilities = ModelCapabilities(
                supports_vision="vision" in config.get("capabilities", []),
                supports_function_calls="function_call"
                in config.get("capabilities", []),
                supports_reasoning="reasoning" in config.get("capabilities", []),
                context_window=config.get("context_window", 4096),
                cost_per_1m_input=config.get("cost_per_1m_input", 0.0),
                cost_per_1m_output=config.get("cost_per_1m_output", 0.0),
                max_output_tokens=config.get("default_params", {}).get(
                    "max_tokens", 4096
                ),
            )

            # Determine preferred tasks based on model characteristics
            preferred_tasks = self._determine_preferred_tasks(
                model_id, config, capabilities
            )

            metadata[model_id] = ModelMetadata(
                model_id=model_id,
                provider=config.get("provider", "unknown"),
                capabilities=capabilities,
                default_style=config.get("style", "presence"),
                preferred_tasks=preferred_tasks,
            )

        return metadata

    def _determine_preferred_tasks(
        self, model_id: str, config: dict, capabilities: ModelCapabilities
    ) -> list[TaskType]:
        """Determine which tasks a model is best suited for."""
        tasks = []

        # Free models are good for general tasks
        if capabilities.cost_per_1m_input == 0.0:
            tasks.extend([TaskType.GENERAL_CHAT, TaskType.REASONING])

        # Reasoning capabilities
        if (
            capabilities.supports_reasoning
            or "r1" in model_id.lower()
            or "reasoning" in model_id.lower()
        ):
            tasks.append(TaskType.REASONING)

        # Vision capabilities
        if capabilities.supports_vision:
            tasks.append(TaskType.VISION)

        # Function calling
        if capabilities.supports_function_calls:
            tasks.append(TaskType.FUNCTION_CALL)

        # Provider-specific preferences
        provider = config.get("provider", "")
        if provider == "anthropic" or "claude" in model_id.lower():
            tasks.extend([TaskType.EMOTIONAL_SUPPORT, TaskType.ANALYSIS])
        elif provider == "openai" or "gpt" in model_id.lower():
            tasks.extend([TaskType.GENERAL_CHAT, TaskType.FUNCTION_CALL])
        elif "grok" in model_id.lower():
            tasks.append(TaskType.CREATIVE_WRITING)
        elif "deepseek" in model_id.lower():
            tasks.extend([TaskType.REASONING, TaskType.CODING])

        # Large context models for longform
        if capabilities.context_window > 100000:
            tasks.append(TaskType.LONGFORM)

        return tasks

    def analyze_task_type(
        self, user_input: str, conversation_context: dict[str, Any]
    ) -> TaskType:
        """
        Analyze the user input to determine task type.

        Args:
            user_input: The user's input text.
            conversation_context: Context about the current conversation.

        Returns:
            The determined task type.
        """
        text = user_input.lower()

        # Reasoning indicators
        reasoning_patterns = [
            r"\b(analyze|explain|reason|logic|why|how|because|therefore|thus|solve|problem)\b",
            r"\b(step by step|break down|walk through|think through)\b",
            r"\b(math|calculation|compute|derive|prove)\b",
        ]

        # Emotional support indicators
        emotional_patterns = [
            r"\b(feel|feeling|sad|happy|angry|upset|hurt|anxious|worried|stressed)\b",
            r"\b(support|help me|comfort|understand|listen)\b",
            r"\b(advice|guidance|what should i)\b",
        ]

        # Creative writing indicators
        creative_patterns = [
            r"\b(write|story|poem|creative|imagine|fiction|character)\b",
            r"\b(brainstorm|ideas|inspiration|innovative)\b",
        ]

        # Vision task indicators
        vision_patterns = [
            r"\b(image|picture|photo|visual|see|look|describe|identify)\b",
            r"\b(chart|graph|diagram|screenshot)\b",
        ]

        # Coding indicators
        coding_patterns = [
            r"\b(code|programming|function|class|variable|debug|error)\b",
            r"\b(python|javascript|html|css|sql|api)\b",
        ]

        # Check patterns in order of specificity
        if any(re.search(pattern, text) for pattern in vision_patterns):
            return TaskType.VISION
        elif any(re.search(pattern, text) for pattern in coding_patterns):
            return TaskType.CODING
        elif any(re.search(pattern, text) for pattern in reasoning_patterns):
            return TaskType.REASONING
        elif any(re.search(pattern, text) for pattern in emotional_patterns):
            return TaskType.EMOTIONAL_SUPPORT
        elif any(re.search(pattern, text) for pattern in creative_patterns):
            return TaskType.CREATIVE_WRITING
        elif len(user_input) > 1000:  # Long input might need longform response
            return TaskType.LONGFORM
        else:
            return TaskType.GENERAL_CHAT

    def select_optimal_model(
        self,
        task_type: TaskType,
        prefer_free: bool = True,
        context_length_needed: int = 0,
    ) -> str:
        """
        Select the optimal model for a given task type.

        Args:
            task_type: The type of task to perform.
            prefer_free: Whether to prefer free models when possible.
            context_length_needed: Minimum context length required.

        Returns:
            The selected model ID.
        """
        suitable_models = []

        for model_id, metadata in self.model_metadata.items():
            # Check if model can handle the task
            if task_type in metadata.preferred_tasks:
                # Check context length requirement
                if metadata.capabilities.context_window >= context_length_needed:
                    suitable_models.append((model_id, metadata))

        if not suitable_models:
            # Fallback to any model that meets context requirements
            for model_id, metadata in self.model_metadata.items():
                if metadata.capabilities.context_window >= context_length_needed:
                    suitable_models.append((model_id, metadata))

        if not suitable_models:
            # Ultimate fallback
            return self.models_config.get("default", {}).get(
                "model", "deepseek-r1-0528-free"
            )

        # Sort by preference: free models first if preferred, then by performance
        def sort_key(item):
            model_id, metadata = item
            is_free = metadata.capabilities.cost_per_1m_input == 0.0
            cost_score = (
                1.0 if is_free else 1.0 / (metadata.capabilities.cost_per_1m_input + 1)
            )

            if prefer_free:
                return (
                    -int(is_free),
                    -cost_score,
                    -metadata.capabilities.performance_score,
                )
            else:
                return (-metadata.capabilities.performance_score, -cost_score)

        suitable_models.sort(key=sort_key)

        selected_model = suitable_models[0][0]
        logger.info(f"Selected model {selected_model} for task type {task_type.value}")

        return selected_model

    def determine_voice_style(self, task_type: TaskType, user_input: str) -> str:
        """
        Determine the appropriate voice style based on task type and content.

        Args:
            task_type: The type of task.
            user_input: The user's input text.

        Returns:
            The selected voice style.
        """
        text = user_input.lower()

        # Task-based defaults
        task_style_mapping = {
            TaskType.REASONING: "tactical",
            TaskType.EMOTIONAL_SUPPORT: "whisper",
            TaskType.CREATIVE_WRITING: "fire",
            TaskType.CODING: "tactical",
            TaskType.ANALYSIS: "tactical",
            TaskType.GENERAL_CHAT: "presence",
            TaskType.VISION: "presence",
            TaskType.FUNCTION_CALL: "tactical",
            TaskType.LONGFORM: "presence",
        }

        base_style = task_style_mapping.get(task_type, "presence")

        # Override based on emotional indicators
        if any(
            word in text
            for word in ["feel", "sad", "upset", "hurt", "anxious", "worried"]
        ):
            return "whisper"
        elif any(
            word in text
            for word in ["inspire", "motivate", "challenge", "push", "dare"]
        ):
            return "fire"
        elif any(
            word in text for word in ["how", "what", "when", "where", "step", "process"]
        ):
            return "tactical"

        return base_style

    def route(
        self,
        user_input: str,
        conversation_context: dict[str, Any],
        prefer_free: bool = True,
    ) -> tuple[str, str, dict[str, Any]]:
        """
        Route the request to the optimal model with appropriate parameters.

        Args:
            user_input: The user's input text.
            conversation_context: Context about the current conversation.
            prefer_free: Whether to prefer free models when possible.

        Returns:
            A tuple containing (model_id, voice_style, model_params).
        """
        # Analyze the task
        task_type = self.analyze_task_type(user_input, conversation_context)

        # Estimate context length needed
        context_length = len(user_input) + conversation_context.get("context_length", 0)

        # Select optimal model
        model_id = self.select_optimal_model(task_type, prefer_free, context_length)

        # Determine voice style
        voice_style = self.determine_voice_style(task_type, user_input)

        # Get model parameters
        model_params = self.voice_styles.get(
            voice_style, self.voice_styles["presence"]
        ).copy()

        # Add model-specific parameters
        if model_id in self.model_metadata:
            model_config = self.models_config["models"].get(model_id, {})
            default_params = model_config.get("default_params", {})
            model_params.update(default_params)

        # Add task-specific adjustments
        if task_type == TaskType.REASONING:
            model_params["temperature"] = min(model_params.get("temperature", 0.7), 0.5)
        elif task_type == TaskType.CREATIVE_WRITING:
            model_params["temperature"] = max(model_params.get("temperature", 0.7), 0.8)

        logger.info(
            f"Routed to model: {model_id}, task: {task_type.value}, style: {voice_style}"
        )

        return model_id, voice_style, model_params

    def estimate_cost(
        self, model_id: str, input_tokens: int, output_tokens: int
    ) -> float:
        """
        Estimate the cost for a request.

        Args:
            model_id: The model to use.
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.

        Returns:
            Estimated cost in USD.
        """
        if model_id not in self.model_metadata:
            return 0.0

        metadata = self.model_metadata[model_id]

        input_cost = (
            input_tokens / 1_000_000
        ) * metadata.capabilities.cost_per_1m_input
        output_cost = (
            output_tokens / 1_000_000
        ) * metadata.capabilities.cost_per_1m_output

        return input_cost + output_cost

    def get_model_info(self, model_id: str) -> ModelMetadata | None:
        """Get metadata for a specific model."""
        return self.model_metadata.get(model_id)

    def get_available_models(self, task_type: TaskType | None = None) -> list[str]:
        """Get list of available models, optionally filtered by task type."""
        if task_type is None:
            return list(self.model_metadata.keys())

        return [
            model_id
            for model_id, metadata in self.model_metadata.items()
            if task_type in metadata.preferred_tasks
        ]
