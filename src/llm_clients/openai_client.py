"""
OpenAI Client

Client for interacting with OpenAI models.
"""

import logging
from typing import Any

from openai import AsyncOpenAI, OpenAI

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Client for interacting with OpenAI models."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        Initialize the OpenAI client.

        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-4o-mini)
        """
        self.api_key = api_key
        self.model = model
        self.client = OpenAI(api_key=api_key)
        self.async_client = AsyncOpenAI(api_key=api_key)
        logger.info(f"Initialized OpenAI client with model {model}")

    async def generate_text(
        self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7
    ) -> str:
        """
        Generate text using the OpenAI model.

        Args:
            prompt: The prompt to send to the model
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for text generation

        Returns:
            Generated text
        """
        try:
            logger.debug(f"Sending prompt to OpenAI ({len(prompt)} chars)")
            response = await self.async_client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"Error generating text with OpenAI: {str(e)}")
            return f"Error generating text: {str(e)}"

    async def chat(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> dict[str, Any]:
        """
        Chat with the OpenAI model.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for text generation

        Returns:
            Response from the model
        """
        try:
            logger.debug(f"Sending {len(messages)} messages to OpenAI")
            response = await self.async_client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages,
            )

            return {
                "message": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            }
        except Exception as e:
            logger.error(f"Error in OpenAI chat: {str(e)}")
            return {"error": str(e)}
