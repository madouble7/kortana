"""
Anthropic Client

Client for interacting with Anthropic API.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class AnthropicClient:
    """Client for Anthropic API."""

    def __init__(self, api_key: str, model: str = "claude-2"):
        """
        Initialize the Anthropic client.

        Args:
            api_key: API key for Anthropic.
            model: Model name to use.
        """
        self.api_key = api_key
        self.model = model
        logger.info(f"Initialized Anthropic client with model {model}")

    async def complete(self, prompt: str) -> Dict[str, Any]:
        """
        Generate a completion for the given prompt.

        Args:
            prompt: The prompt to generate a completion for.

        Returns:
            A dictionary containing the completion response.
        """
        logger.info(f"Generating completion with model {self.model}")

        # This is a stub implementation for testing
        # In a real implementation, this would call the Anthropic API

        return {
            "content": f"This is a simulated response from {self.model}. The prompt was: '{prompt[:20]}...'",
            "model": self.model,
            "finish_reason": "stop",
        }
