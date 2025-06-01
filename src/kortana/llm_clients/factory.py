"""Factory for creating LLM clients based on configuration."""

import logging
import os
from typing import Any, Dict, Optional

from .base_client import BaseLLMClient
from .genai_client import GoogleGenAIClient
from .google_client import (
    GoogleGeminiClient,
)  # Changed to use the more robust GoogleGeminiClient
from .openai_client import OpenAIClient
from .openrouter_client import OpenRouterClient
from .xai_client import XAIClient

logger = logging.getLogger(__name__)


class LLMClientFactory:
    """Factory for creating appropriate LLM clients.

    Centralizes client creation logic and handles API key management.
    """

    MODEL_CLIENTS = {
        "anthropic/claude-3-haiku": OpenRouterClient,
        "gpt-4.1-nano": OpenAIClient,
        "gpt-4o-mini-openai": OpenAIClient,
        "gemini-2.5-flash": GoogleGeminiClient,  # Changed to GoogleGeminiClient
        "gemini-2.0-flash-lite": GoogleGeminiClient,  # Changed to GoogleGeminiClient
        "x-ai/grok-3-mini-beta": XAIClient,
        "deepseek/deepseek-chat-v3-0324": OpenRouterClient,
        "deepseek-chat-v3-openrouter": OpenRouterClient,
        "neversleep/noromaid-20b": OpenRouterClient,
        "meta-llama/llama-4-scout": OpenRouterClient,
        "meta-llama/llama-4-maverick": OpenRouterClient,
        "qwen/qwen3-235b-a22b": OpenRouterClient,
    }

    @staticmethod
    def create_client(
        model_id: str, models_config: Dict[str, Any]
    ) -> Optional[BaseLLMClient]:
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
    def get_client_for_model(model_id: str, models_config: Dict[str, Any]):
        """Enhanced method with validation for ADE requirements."""
        return LLMClientFactory.create_client(model_id, models_config)

    @staticmethod
    def get_default_client(models_config: Dict[str, Any]) -> Optional[BaseLLMClient]:
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
        models_config: Dict[str, Any], task_type: str = "primary"
    ) -> Optional[BaseLLMClient]:
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
    def validate_configuration(models_config: Dict[str, Any]) -> bool:
        """Validate that essential models are properly configured."""
        essential_models = ["gpt-4.1-nano", "x-ai/grok-3-mini-beta", "gemini-2.5-flash"]

        missing_models = []

        for model_id in essential_models:
            if model_id not in LLMClientFactory.MODEL_CLIENTS:
                missing_models.append(
                    f"{model_id} (Not in etched-in-stone MODEL_CLIENTS)"
                )
                continue

            model_conf = models_config.get("models", {}).get(model_id)
            if not model_conf:
                missing_models.append(
                    f"{model_id} (Missing config in models_config.json)"
                )
                continue

            api_key_env = model_conf.get("api_key_env", "")
            if not api_key_env:
                missing_models.append(f"{model_id} (Missing api_key_env in config)")
                continue

            if not os.getenv(api_key_env):
                missing_models.append(
                    f"{model_id} (Missing {api_key_env} environment variable)"
                )

        if missing_models:
            logger.error(
                f"Missing essential model configurations or API keys: {missing_models}"
            )
            return False

        logger.info("All essential models properly configured for Sacred Covenant")
        return True
