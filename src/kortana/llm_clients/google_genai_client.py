"""
Google Generative AI client for Kortana.
This module provides integration with Google's Gemini models through the generativeai SDK.
"""

import logging
import os
from typing import Any

from .base_client import LLMClient

logger = logging.getLogger(__name__)


class GenAIClient(LLMClient):
    """
    Google GenAI client implementation with fixed parameter structure
    Implements all required abstract methods from LLMClient base class
    """

    def __init__(
        self, model_name: str = "gemini-2.5-flash", api_key: str | None = None
    ):
        super().__init__(model_name)
        import google.generativeai as genai

        # Configure API key
        api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "Google API key not found. Set GOOGLE_API_KEY environment variable."
            )

        genai.configure(api_key=api_key)

        try:
            self.model = genai.GenerativeModel(model_name)
            logger.info(f"✅ Google GenAI client initialized with model: {model_name}")
        except Exception as e:
            logger.error(
                f"❌ Failed to initialize Google GenAI model {model_name}: {e}"
            )
            raise

    def generate_response(
        self, messages: list[dict[str, str]], **kwargs
    ) -> dict[str, Any]:
        """
        Generate response using Google GenAI - REQUIRED ABSTRACT METHOD IMPLEMENTATION

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional parameters like temperature, max_tokens, etc.

        Returns:
            Dictionary with response data including content, usage, etc.
        """
        try:
            # Convert messages to Google GenAI format
            prompt = self._convert_messages_to_prompt(messages)

            # Extract parameters with defaults
            temperature = kwargs.get("temperature", 0.7)
            max_tokens = kwargs.get("max_tokens", 4096)
            top_p = kwargs.get("top_p", 0.9)

            # Configure generation parameters
            generation_config = genai.GenerationConfig(
                temperature=temperature, max_output_tokens=max_tokens, top_p=top_p
            )

            # Generate response
            response = self.model.generate_content(
                prompt, generation_config=generation_config
            )

            # Extract response content
            content = response.text if response.text else ""

            # Create standardized response format
            return {
                "content": content,
                "model": self.model_name,
                "usage": {
                    "prompt_tokens": (
                        response.usage_metadata.prompt_token_count
                        if hasattr(response, "usage_metadata")
                        else 0
                    ),
                    "completion_tokens": (
                        response.usage_metadata.candidates_token_count
                        if hasattr(response, "usage_metadata")
                        else 0
                    ),
                    "total_tokens": (
                        response.usage_metadata.total_token_count
                        if hasattr(response, "usage_metadata")
                        else 0
                    ),
                },
                "choices": [{"message": {"content": content, "role": "assistant"}}],
            }

        except Exception as e:
            logger.error(f"Google GenAI generation error: {e}")
            return {
                "content": f"Error: {str(e)}",
                "model": self.model_name,
                "error": str(e),
            }

    def get_completion(self, messages: list[dict[str, str]], **kwargs) -> Any:
        """
        Get completion using Google GenAI - COMPATIBILITY METHOD

        This method provides compatibility with the existing ChatEngine interface
        Returns a response object that mimics OpenAI's structure
        """
        response_dict = self.generate_response(messages, **kwargs)

        # Create mock response object with choices attribute
        class MockResponse:
            def __init__(self, response_data):
                self.choices = [MockChoice(response_data)]
                self.usage = MockUsage(response_data.get("usage", {}))
                self.model = response_data.get("model", "unknown")

        class MockChoice:
            def __init__(self, response_data):
                self.message = MockMessage(response_data)

        class MockMessage:
            def __init__(self, response_data):
                self.content = response_data.get("content", "")
                self.role = "assistant"

        class MockUsage:
            def __init__(self, usage_data):
                self.prompt_tokens = usage_data.get("prompt_tokens", 0)
                self.completion_tokens = usage_data.get("completion_tokens", 0)
                self.total_tokens = usage_data.get("total_tokens", 0)

        return MockResponse(response_dict)

    def _convert_messages_to_prompt(self, messages: list[dict[str, str]]) -> str:
        """
        Convert OpenAI-style messages to Google GenAI prompt format

        Args:
            messages: List of message dictionaries

        Returns:
            Formatted prompt string
        """
        prompt_parts = []

        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")

            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")

        return "\n\n".join(prompt_parts)

    def get_capabilities(self) -> dict[str, Any]:
        """
        Get client capabilities - REQUIRED ABSTRACT METHOD IMPLEMENTATION

        Returns:
            Dictionary of client capabilities
        """
        return {
            # Google GenAI has function calling but not implemented yet
            "supports_function_calling": False,
            "supports_streaming": True,
            "supports_system_messages": True,
            "max_context_length": 1048576,  # Gemini 2.5 Flash context window
            "supports_multimodal": True,
            "model_name": self.model_name,
            "provider": "google",
        }

    def test_connection(self) -> bool:
        """
        Test the connection to Google GenAI - REQUIRED ABSTRACT METHOD IMPLEMENTATION

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Test with a simple prompt
            test_response = self.generate_response(
                [
                    {
                        "role": "user",
                        "content": "Hello, respond with 'OK' if you can hear me.",
                    }
                ]
            )

            success = "OK" in test_response.get("content", "").upper()
            if success:
                logger.info("✅ Google GenAI connection test successful")
            else:
                logger.warning(
                    "⚠️ Google GenAI connection test returned unexpected response"
                )

            return success

        except Exception as e:
            logger.error(f"❌ Google GenAI connection test failed: {e}")
            return False

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Estimate cost for Google GenAI usage - REQUIRED ABSTRACT METHOD IMPLEMENTATION

        Args:
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        # Gemini 2.5 Flash pricing (as of latest update)
        input_cost_per_1m = 0.15  # $0.15 per 1M input tokens
        output_cost_per_1m = 0.60  # $0.60 per 1M output tokens

        input_cost = (prompt_tokens / 1_000_000) * input_cost_per_1m
        output_cost = (completion_tokens / 1_000_000) * output_cost_per_1m

        return input_cost + output_cost

    def supports_function_calling(self) -> bool:
        """Check if the client supports function calling"""
        return False  # Not implemented yet, but Google GenAI does support it

    def supports_streaming(self) -> bool:
        """Check if the client supports streaming responses"""
        return True

    def get_model_info(self) -> dict[str, Any]:
        """Get information about the current model"""
        return {
            "name": self.model_name,
            "provider": "google",
            "context_window": 1048576,  # 1M+ tokens for Gemini 2.5 Flash
            "supports_multimodal": True,
            "supports_function_calling": False,  # Not implemented yet
            "cost_per_1m_input": 0.15,
            "cost_per_1m_output": 0.60,
        }
