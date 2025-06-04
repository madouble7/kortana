"""
LLM Client Factory

Factory for creating LLM clients based on provider and model.
"""

import logging
from typing import Any

from kortana.config.schema import KortanaConfig

from .anthropic_client import AnthropicClient

# Import providers here (assuming these exist)
from .openai_client import OpenAIClient

# Add other provider imports as needed


logger = logging.getLogger(__name__)


class LLMClientFactory:
    """Factory for creating LLM clients based on provider and model."""

    def __init__(self, settings: KortanaConfig):
        """
        Initialize the LLM client factory.

        Args:
            settings: The application configuration.
        """
        self.settings = settings
        self.clients = {}

    def get_client(self, model_id: str) -> Any:
        """
        Get or create an LLM client for the specified model ID.

        Args:
            model_id: The model identifier (e.g., "gpt-4", "claude-2").

        Returns:
            An LLM client instance.
        """
        if model_id in self.clients:
            return self.clients[model_id]

        # Determine provider based on model_id prefix
        provider = self._get_provider_from_model_id(model_id)

        # Get API key from settings
        api_key = self.settings.get_api_key(provider)

        if not api_key:
            raise ValueError(f"No API key found for provider: {provider}")

        # Create client based on provider
        client = self._create_client(provider, model_id, api_key)

        # Cache the client
        self.clients[model_id] = client

        return client

    def _create_client(self, provider: str, model_id: str, api_key: str) -> Any:
        """Create a new LLM client for the specified provider and model."""
        if provider == "openai":
            return OpenAIClient(api_key=api_key, model=model_id)
        elif provider == "anthropic":
            return AnthropicClient(api_key=api_key, model=model_id)
        # Add other providers as needed
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def _get_provider_from_model_id(self, model_id: str) -> str:
        """
        Determine the provider based on the model ID.

        This is a simple implementation. You might want to enhance this with
        a more sophisticated mapping or pattern matching.
        """
        model_id_lower = model_id.lower()
        if model_id_lower.startswith("gpt-") or model_id_lower.startswith(
            "text-davinci-"
        ):
            return "openai"
        elif model_id_lower.startswith("claude-"):
            return "anthropic"
        # Add other model ID patterns as needed
        else:
            # Default to OpenAI
            return "openai"

    @staticmethod
    def validate_configuration(settings: KortanaConfig) -> bool:
        """
        Validate that the configuration contains all required LLM settings.

        Args:
            settings: The application configuration.

        Returns:
            True if the configuration is valid, False otherwise.
        """
        # Check if essential API keys are present
        if not settings.api_keys.openai:
            logger.warning("OpenAI API key is missing")
            return False

        # Add other validation as needed

        return True
