"""Factory for creating LLM clients based on configuration."""

import json
import logging
import os
from pathlib import Path  # Added import
from typing import Any

from kortana.config.schema import KortanaConfig

from .base_client import BaseLLMClient
from .genai_client import GoogleGenAIClient
from .google_client import (
    GoogleGeminiClient,  # Changed to use the more robust GoogleGeminiClient
)
from .openai_client import OpenAIClient
from .openrouter_client import OpenRouterClient
from .xai_client import XAIClient

logger = logging.getLogger(__name__)


class LLMClientFactory:
    """Factory for creating appropriate LLM clients.

    Centralizes client creation logic and handles API key management.
    """

    MODEL_CLIENTS = {
        # Premium models via OpenRouter
        "google/gemini-2.5-flash-preview-05-20": OpenRouterClient,
        "openai/gpt-4.1-nano": OpenRouterClient,
        "meta-llama/llama-4-maverick": OpenRouterClient,
        "google/gemini-2.0-flash-001": OpenRouterClient,
        "x-ai/grok-3-mini-beta": OpenRouterClient,
        # Free models via OpenRouter (High Priority)
        "deepseek/deepseek-r1-0528:free": OpenRouterClient,
        "deepseek/deepseek-r1-0528-qwen3-8b:free": OpenRouterClient,
        "mistralai/mistral-7b-instruct:free": OpenRouterClient,
        "google/gemma-2-9b-it:free": OpenRouterClient,
        "meta-llama/llama-3.1-8b-instruct:free": OpenRouterClient,
        "qwen/qwen-2-7b-instruct:free": OpenRouterClient,
        # Legacy models for backward compatibility
        "anthropic/claude-3-haiku": OpenRouterClient,
        "gpt-4.1-nano": OpenAIClient,
        "gpt-4o-mini-openai": OpenAIClient,
        "gemini-2.5-flash": GoogleGeminiClient,
        "gemini-2.0-flash-lite": GoogleGeminiClient,
        "gemini-1.5-flash": GoogleGeminiClient,
        "deepseek/deepseek-chat-v3-0324": OpenRouterClient,
        "deepseek-chat-v3-openrouter": OpenRouterClient,
        "deepseek-r1-0528-free": OpenRouterClient,  # Legacy alias
        "neversleep/noromaid-20b": OpenRouterClient,
        "meta-llama/llama-4-scout": OpenRouterClient,
        "qwen/qwen3-235b-a22b": OpenRouterClient,
    }

    def __init__(self, settings: KortanaConfig):
        """Initialize the factory with Kortana configuration.

        Args:
            settings: KortanaConfig instance containing models configuration
        """
        self.settings = settings
        self.models_config = {}

        config_file_path_str = settings.paths.models_config_file_path

        absolute_config_path = Path(config_file_path_str)
        if not absolute_config_path.is_absolute():
            # Attempt to resolve relative to project root if get_project_root is available
            try:
                from ..config import get_project_root  # Delayed import

                absolute_config_path = get_project_root() / config_file_path_str
            except ImportError:
                logger.warning(
                    "get_project_root not available for resolving models_config_file_path, assuming CWD relative or absolute."
                )

        if absolute_config_path.exists():
            try:
                with open(absolute_config_path, encoding="utf-8") as f:
                    self.models_config = json.load(f)
                logger.info(
                    f"Successfully loaded models configuration from {absolute_config_path}"
                )
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON from {absolute_config_path}: {e}")
            except Exception as e:
                logger.error(
                    f"Failed to load models configuration from {absolute_config_path}: {e}"
                )
        else:
            logger.error(
                f"Models configuration file not found at {absolute_config_path}. Using empty config."
            )

    def get_client(self, model_id: str) -> BaseLLMClient | None:
        """Get an LLM client for a specific model ID.

        Args:
            model_id: The identifier for the model

        Returns:
            Initialized client instance or None if creation fails
        """
        # Ensure models_config is not None, though __init__ initializes it to {}
        if self.models_config is None:
            logger.error(
                "LLMClientFactory.models_config is None. Cannot create client."
            )
            return None
        return self.create_client(model_id, self.models_config)  # models_config is dict

    @staticmethod
    def create_client(
        model_id: str,
        models_config: dict[str, Any],  # Ensure this expects dict
    ) -> BaseLLMClient | None:
        """Create an LLM client based on provider configuration.

        Args:
            model_id: The identifier for the model (e.g., "grok_3_mini", "gemini_flash_2_5").
            models_config: The full models configuration dictionary.
                           Expected structure: {"models": {"model_id": {config_details...}}}

        Returns:
            Initialized client instance inheriting from BaseLLMClient or None if config is missing.

        Raises:
            ValueError: If provider is unsupported or API key is missing.
        """

        model_conf = models_config.get("models", {}).get(model_id)
        if not model_conf:
            logging.error(
                f"Configuration for model_id '{model_id}' not found in models_config.json."
            )
            return None

        provider = model_conf.get("provider", "").lower()
        api_key_env = model_conf.get("api_key_env", "")
        api_key = os.getenv(api_key_env)

        if not api_key:
            logging.error(
                f"Missing API key for {provider} (model: {model_id}). Ensure {api_key_env} is set in your environment."
            )
            return None

        default_params = model_conf.get("default_params", {})

        try:
            client_class = LLMClientFactory.MODEL_CLIENTS.get(model_id)

            if not client_class:
                logging.error(
                    f"No client class mapped for model_id: {model_id} in MODEL_CLIENTS."
                )
                return None

            client: BaseLLMClient | None = None

            if client_class == OpenAIClient:
                client = OpenAIClient(
                    api_key=api_key,
                    model_name=model_conf.get("model_name", model_id),
                    base_url=model_conf.get("base_url", "https://api.openai.com/v1"),
                    default_params=default_params,
                )

            elif client_class == XAIClient:
                client = XAIClient(
                    api_key=api_key,
                    base_url=model_conf.get("base_url", "https://api.x.ai/v1"),
                )  # Ensure model_name is passed if XAIClient expects it
            elif client_class == GoogleGeminiClient:  # Changed to GoogleGeminiClient
                client = GoogleGenAIClient(
                    api_key=api_key,
                    model_name=model_conf.get("model_name", model_id),
                    base_url=model_conf.get(
                        "base_url", "https://generativelanguage.googleapis.com/v1beta"
                    ),
                    **default_params,
                )
            elif client_class == OpenRouterClient:
                client = OpenRouterClient(
                    api_key=api_key,
                    model_name=model_conf.get("model_name", model_id),
                    base_url=model_conf.get("base_url", "https://openrouter.ai/api/v1"),
                    default_params=default_params,
                )
            else:
                logging.error(
                    f"Instantiating unknown client class for model {model_id}: {client_class.__name__}"
                )
                return None

            if client is None:
                logging.error(f"Failed to instantiate client for model {model_id}")
                return None

            logging.info(f"Client initialized: {model_id} (provider: {provider})")
            logging.debug(f"Capabilities: {client.get_capabilities()}")

            return client

        except ImportError as e:
            logging.error(
                f"Failed to import client for model {model_id} (provider {provider}): {e}"
            )
            return None
        except Exception as e:
            logging.error(
                f"Error initializing client for {model_id} (provider: {provider}): {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_client_for_model(model_id: str, models_config: dict[str, Any]):
        """Enhanced method with validation for ADE requirements."""
        return LLMClientFactory.create_client(model_id, models_config)

    @staticmethod
    def get_default_client(models_config: dict[str, Any]) -> BaseLLMClient | None:
        """Get the default LLM client (GPT-4.1-Nano for Kor'tana primary use)."""
        default_model_id = "gpt-4.1-nano"

        try:
            client = LLMClientFactory.create_client(default_model_id, models_config)
            if client:
                logger.info(
                    f"Default client created: {default_model_id} for primary Kor'tana conversation"
                )
            return client
        except Exception as e:
            logger.error(f"Failed to create default client {default_model_id}: {e}")
            return None

    @staticmethod
    def get_ade_client(
        models_config: dict[str, Any], task_type: str = "primary"
    ) -> BaseLLMClient | None:
        """Get appropriate client for ADE tasks based on task type."""
        task_model_mapping = {
            "primary": "gpt-4.1-nano",
            "analysis": "x-ai/grok-3-mini-beta",
            "reasoning": "gemini-2.5-flash",
            "memory": "meta-llama/llama-4-maverick",
            "longform": "qwen/qwen3-235b-a22b",
        }

        model_id = task_model_mapping.get(task_type, "gpt-4.1-nano")

        if model_id not in LLMClientFactory.MODEL_CLIENTS:
            logger.warning(
                f"ADE task type '{task_type}' mapped to unsupported model '{model_id}'. Falling back to default."
            )
            model_id = "gpt-4.1-nano"

        try:
            client = LLMClientFactory.create_client(model_id, models_config)
            if client:
                logger.info(
                    f"ADE client created: {model_id} for task type: {task_type}"
                )
            return client
        except Exception as e:
            logger.error(
                f"Failed to create ADE client for {task_type} (model {model_id}): {e}"
            )
            return LLMClientFactory.get_default_client(models_config)

    @staticmethod
    def validate_configuration(settings: KortanaConfig) -> bool:
        """Validate that essential models are properly configured."""
        # Load models from the enhanced configuration
        try:
            with open(settings.paths.models_config_file_path) as f:
                models_config = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load models configuration: {e}")
            return False  # Essential models for core functionality (prioritizing free models)
        essential_models = [
            "deepseek/deepseek-r1-0528:free",  # Free reasoning model
            "deepseek/deepseek-r1-0528-qwen3-8b:free",  # Free fast model
            "openai/gpt-4.1-nano",  # Premium general purpose
        ]

        # Recommended models for enhanced functionality
        recommended_models = [
            "google/gemini-2.5-flash-preview-05-20",  # Vision and long context
            "meta-llama/llama-4-maverick",  # Analysis tasks
            "google/gemini-2.0-flash-001",  # Fast vision
            "x-ai/grok-3-mini-beta",  # Creative and planning
        ]

        missing_essential = []
        missing_recommended = []

        # Check essential models
        for model_id in essential_models:
            if model_id not in LLMClientFactory.MODEL_CLIENTS:
                missing_essential.append(f"{model_id} (Not in MODEL_CLIENTS)")
                continue

            model_conf = models_config.get("models", {}).get(model_id)
            if not model_conf:
                missing_essential.append(f"{model_id} (Missing config)")
                continue

            api_key_env = model_conf.get("api_key_env", "")
            if not api_key_env:
                missing_essential.append(f"{model_id} (Missing api_key_env)")
                continue

            if not os.getenv(api_key_env):
                missing_essential.append(f"{model_id} (Missing {api_key_env} env var)")

        # Check recommended models
        for model_id in recommended_models:
            if model_id not in LLMClientFactory.MODEL_CLIENTS:
                missing_recommended.append(f"{model_id} (Not in MODEL_CLIENTS)")
                continue

            model_conf = models_config.get("models", {}).get(model_id)
            if not model_conf:
                missing_recommended.append(f"{model_id} (Missing config)")
                continue

            api_key_env = model_conf.get("api_key_env", "")
            if not api_key_env:
                missing_recommended.append(f"{model_id} (Missing api_key_env)")
                continue

            if not os.getenv(api_key_env):
                missing_recommended.append(
                    f"{model_id} (Missing {api_key_env} env var)"
                )

        # Report results
        if missing_essential:
            logger.error(f"Missing ESSENTIAL model configurations: {missing_essential}")
            logger.error("Kor'tana may not function properly without these models")
            return False

        if missing_recommended:
            logger.warning(
                f"Missing RECOMMENDED model configurations: {missing_recommended}"
            )
            logger.warning("Some advanced features may not be available")

        logger.info("Essential model configurations validated successfully")
        if not missing_recommended:
            logger.info(
                "All recommended models properly configured - full functionality available"
            )

        return True
