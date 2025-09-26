"""Base client abstraction for all LLM providers used in Kor'tana."""

import asyncio
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

    async def complete(self, prompt: Any, **kwargs) -> dict[str, Any]:
        """Unified async interface used across the Kor'tana codebase.

        This adapter accepts either a raw string prompt or the OpenAI-style
        payload produced by the chat engine (containing ``messages`` and
        optional generation parameters). The underlying client implementation
        remains synchronous, so the work is dispatched to a background thread
        to avoid blocking the event loop.
        """

        system_prompt = ""
        message_payload: list[dict[str, Any]] = []
        generation_kwargs = dict(kwargs)

        if isinstance(prompt, dict):
            # Support both explicit ``system_prompt`` keys and a system role
            # inside the messages collection.
            system_prompt = prompt.get("system_prompt", "") or ""
            prompt_messages = prompt.get("messages", [])
            if not system_prompt:
                for message in prompt_messages:
                    if (
                        isinstance(message, dict)
                        and message.get("role") == "system"
                        and isinstance(message.get("content"), str)
                    ):
                        system_prompt = message.get("content", "")
                        break

            for message in prompt_messages:
                if not isinstance(message, dict):
                    continue
                if message.get("role") == "system":
                    continue
                message_payload.append(message)

            # Carry through common generation parameters when they are
            # provided on the prompt object.
            for key in (
                "temperature",
                "max_tokens",
                "top_p",
                "frequency_penalty",
                "presence_penalty",
            ):
                if key in prompt and key not in generation_kwargs:
                    generation_kwargs[key] = prompt[key]
        elif isinstance(prompt, str):
            message_payload.append({"role": "user", "content": prompt})
        else:
            raise TypeError(
                f"Unsupported prompt type for complete: {type(prompt)!r}"
            )

        try:
            raw_response = await asyncio.to_thread(
                self.generate_response_with_retry,
                system_prompt,
                message_payload,
                **generation_kwargs,
            )
        except RuntimeError:
            # If no running loop is available (e.g., called from sync code),
            # fall back to a direct call so that the client still functions.
            raw_response = self.generate_response_with_retry(
                system_prompt, message_payload, **generation_kwargs
            )

        return self._normalize_response(raw_response)

    def _normalize_response(self, raw_response: Any) -> dict[str, Any]:
        """Standardise heterogeneous client responses."""

        if isinstance(raw_response, dict):
            normalized: dict[str, Any] = dict(raw_response)
        else:
            normalized = {"content": str(raw_response) if raw_response else ""}

        if not isinstance(normalized.get("usage"), dict):
            normalized["usage"] = {}

        if "error" not in normalized:
            normalized["error"] = None

        if "model_id_used" not in normalized:
            normalized["model_id_used"] = getattr(self, "model_name", "unknown")

        if "reasoning_content" not in normalized:
            normalized["reasoning_content"] = None

        if not normalized.get("content"):
            normalized["content"] = self._extract_content_from_choices(normalized) or ""

        # Preserve the original response for debugging while ensuring we do
        # not introduce self-referential structures when the response was a
        # dictionary.
        if "_raw_response" not in normalized:
            normalized["_raw_response"] = raw_response

        return normalized

    @staticmethod
    def _extract_content_from_choices(response: dict[str, Any]) -> str | None:
        """Extract assistant text from OpenAI-style response payloads."""

        choices = response.get("choices")
        if not isinstance(choices, list):
            return None

        for choice in choices:
            if not isinstance(choice, dict):
                continue
            message = choice.get("message")
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str):
                    return content
            content = choice.get("content")
            if isinstance(content, str):
                return content

        return None
