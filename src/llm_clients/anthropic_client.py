"""
Anthropic Client

Client for interacting with Anthropic's Claude models.
"""

import logging
from typing import Any

import anthropic

logger = logging.getLogger(__name__)


class AnthropicClient:
    """Client for interacting with Anthropic's Claude models."""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20240620"):
        """
        Initialize the Anthropic client.

        Args:
            api_key: Anthropic API key
            model: Model to use (default: claude-3-5-sonnet-20240620)
        """
        self.api_key = api_key
        self.model = model
        self.client = anthropic.Anthropic(api_key=api_key)
        logger.info(f"Initialized Anthropic client with model {model}")

    async def generate_text(
        self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7
    ) -> str:
        """
        Generate text using the Anthropic model.

        Args:
            prompt: The prompt to send to the model
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for text generation

        Returns:
            Generated text
        """
        try:
            logger.debug(f"Sending prompt to Anthropic ({len(prompt)} chars)")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Error generating text with Anthropic: {str(e)}")
            return f"Error generating text: {str(e)}"

    async def chat(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> dict[str, Any]:
        """
        Chat with the Anthropic model.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for text generation

        Returns:
            Response from the model
        """
        try:
            # Convert messages to Anthropic format if needed
            anthropic_messages = []
            for msg in messages:
                role = msg["role"]
                # Anthropic uses "user" and "assistant" roles
                if role == "system":
                    # Handle system messages as special user messages
                    anthropic_messages.append({
                        "role": "user",
                        "content": f"System instruction: {msg['content']}"
                    })
                else:
                    anthropic_messages.append({
                        "role": role,
                        "content": msg["content"]
                    })

            logger.debug(f"Sending {len(messages)} messages to Anthropic")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=anthropic_messages
            )

            return {
                "message": response.content[0].text,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            }
        except Exception as e:
            logger.error(f"Error in Anthropic chat: {str(e)}")
            return {"error": str(e)}
