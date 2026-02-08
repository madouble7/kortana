"""Base client abstraction for all LLM providers used in Kor'tana."""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any


class BaseLLMClient(ABC):
    """Abstract base class defining the contract for all LLM clients.

    Kor'tana uses multiple LLM providers to create a rich, multi-faceted mind.
    This base class ensures all providers implement consistent interfaces.
    """

    def __init__(self, api_key: str, model_name: str, **kwargs):
        """Initialize the base LLM client.

        Args:
            api_key: API key for the LLM provider
            model_name: Name/identifier of the specific model
            **kwargs: Additional provider-specific configuration
        """
        self.api_key = api_key
        self.model_name = model_name
        self.config = kwargs

    @abstractmethod
    def generate_response(
        self, system_prompt: str, messages: list, **kwargs
    ) -> dict[str, Any]:
        """Generate a response from the LLM.

        Args:
            system_prompt: The system instructions for the LLM
            messages: List of conversation messages in standard format
            **kwargs: Additional parameters like temperature, max_tokens, etc.

        Returns:
            Dict containing:
                - content: The response text
                - reasoning_content: Optional reasoning/thought process
                - usage: Token usage statistics
                - error: Error message or None
                - model_id_used: Identifier of the model used
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> dict[str, Any]:
        """
        Get the capabilities of this LLM client

        Returns:
            Dictionary describing client capabilities
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test the connection to the LLM service

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Estimate the cost of a request

        Args:
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        pass

    def generate_response_with_retry(
        self,
        system_prompt: str,
        messages: list,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
    ) -> dict[str, Any]:
        """Generate response with automatic retry on transient failures.

        Implements exponential backoff strategy for resilience.
        """
        last_error = None
        for attempt in range(max_retries):
            try:
                return self.generate_response(system_prompt, messages)
            except Exception as e:
                last_error = e
                # Skip wait on last attempt
                if attempt < max_retries - 1:
                    backoff_time = backoff_factor**attempt
                    logging.warning(
                        f"LLM call failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {backoff_time}s..."
                    )
                    time.sleep(backoff_time)
                else:
                    logging.error(f"All {max_retries} LLM call attempts failed: {e}")

        # If we reached here, all retries failed
        return {
            "content": f"I seem to be experiencing difficulty connecting to my thought engine. {last_error}",
            "reasoning_content": None,
            "usage": {},
            "error": str(last_error),
            "model_id_used": getattr(self, "model_name", "unknown"),
        }

    # Optional methods with default implementations
    def supports_function_calling(self) -> bool:
        """Check if the client supports function calling"""
        return False

    def supports_streaming(self) -> bool:
        """Check if the client supports streaming responses"""
        return False

    def get_model_info(self) -> dict[str, Any]:
        """Get information about the current model"""
        return {"name": self.model_name, "provider": "unknown"}

    def complete(self, prompt: dict[str, Any]) -> dict[str, Any]:
        """Compatibility wrapper used by ChatEngine.

        Accepts OpenAI-style prompt payloads:
        {
          "messages": [{"role": "system"|"user"|..., "content": "..."}],
          "temperature": 0.7,
          "max_tokens": 1000,
        }

        Returns a normalized shape:
        {"content": "...", "raw": <provider_response>}
        """
        messages = prompt.get("messages", []) if isinstance(prompt, dict) else []
        system_prompt = ""
        chat_messages: list[dict[str, str]] = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system" and not system_prompt:
                system_prompt = content
            else:
                chat_messages.append({"role": role, "content": content})

        raw = self.generate_response(
            system_prompt=system_prompt,
            messages=chat_messages,
            temperature=prompt.get("temperature", 0.7),
            max_tokens=prompt.get("max_tokens", 1000),
        )

        content = ""
        if isinstance(raw, dict):
            if "content" in raw and isinstance(raw.get("content"), str):
                content = raw["content"]
            else:
                try:
                    content = raw["choices"][0]["message"].get("content", "")
                except Exception:
                    content = ""

        return {"content": content, "raw": raw}
