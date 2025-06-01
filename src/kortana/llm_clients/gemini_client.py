"""Fixed Gemini client implementation for Kor'tana."""

import logging
import os
import time
from typing import Any, Dict, List, Tuple

try:
    import google.generativeai as genai  # type: ignore

    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None  # type: ignore

from .base_client import BaseLLMClient

logger = logging.getLogger(__name__)


class GoogleGenAIClient(BaseLLMClient):
    """
    Google Gemini client using the google.generativeai library.
    Handles multi-turn conversations and system prompts for Kor'tana.
    """

    def __init__(
        self,
        model_id: str,
        api_key_env: str = "GOOGLE_API_KEY",
        model_name: str = "gemini-pro",
        **kwargs,
    ):
        # Get API key first
        api_key = os.getenv(api_key_env)
        if not api_key:
            logger.error(
                f"API key environment variable {api_key_env} not found for GoogleGenAIClient."
            )
            raise ValueError(
                f"API key for {model_id} not found in environment variable {api_key_env}"
            )

        # Initialize base class
        super().__init__(api_key, model_name, **kwargs)

        self.model_name_for_api = (
            model_name  # e.g., "gemini-1.5-flash-latest", "gemini-pro"
        )
        self.model_id = model_id

        if not GENAI_AVAILABLE or genai is None:
            logger.error(
                "google.generativeai library not available. Install with: pip install google-generativeai"
            )
            raise ImportError(
                "google.generativeai library required for GoogleGenAIClient"
            )

        try:
            # Configure the library with API key
            genai.configure(api_key=self.api_key)  # type: ignore

            # Initialize the model
            self.model = genai.GenerativeModel(self.model_name_for_api)  # type: ignore

            logger.info(
                f"GoogleGenAIClient for model '{self.model_name_for_api}' initialized successfully."
            )

        except Exception as e:
            logger.error(
                f"Failed to initialize GoogleGenAIClient for model '{self.model_name_for_api}': {e}"
            )
            raise

    def get_capabilities(self) -> Dict[str, Any]:
        """Return capabilities of the Google Gemini client."""
        return {
            "supports_system_prompt": True,
            "supports_function_calling": False,  # Update based on model capabilities
            "supports_streaming": True,
            "max_context_length": (
                1048576 if "flash" in self.model_name_for_api else 32768
            ),
            "supports_multimodal": True,
        }

    def generate_response(
        self, system_prompt: str, messages: List[Dict[str, str]], **kwargs
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate response using Google Gemini API.

        Args:
            system_prompt: System instructions for the model
            messages: List of conversation messages with 'role' and 'content'
            **kwargs: Additional parameters like temperature, max_tokens

        Returns:
            Tuple of (response_text, usage_data)
        """
        try:
            # Prepare messages for Google API format
            formatted_messages = []

            # Handle system prompt by prepending to first user message or
            # adding as instruction
            if system_prompt:
                if messages and messages[0]["role"] == "user":
                    # Prepend system prompt to first user message
                    messages[0]["content"] = (
                        system_prompt + "\n\n" + messages[0]["content"]
                    )
                else:
                    # Add system prompt as initial user message with model
                    # acknowledgment
                    formatted_messages.append(
                        {"role": "user", "parts": [{"text": system_prompt}]}
                    )
                    formatted_messages.append(
                        {
                            "role": "model",
                            "parts": [
                                {
                                    "text": "I understand. I'll follow these instructions."
                                }
                            ],
                        }
                    )

            # Convert messages to Google API format
            for msg in messages:
                role = msg["role"]
                content = msg["content"]

                # Map roles: 'assistant' -> 'model', 'user' -> 'user'
                api_role = "model" if role == "assistant" else "user"
                formatted_messages.append(
                    {"role": api_role, "parts": [{"text": content}]}
                )

            # Extract generation parameters with proper typing
            generation_config: Dict[str, Any] = {}
            if "temperature" in kwargs:
                generation_config["temperature"] = kwargs["temperature"]
            if "max_tokens" in kwargs:
                generation_config["max_output_tokens"] = kwargs["max_tokens"]
            if "top_p" in kwargs:
                generation_config["top_p"] = kwargs["top_p"]

            # Make the API call
            start_time = time.time()

            if formatted_messages:
                # Multi-turn conversation
                api_response = self.model.generate_content(  # type: ignore
                    formatted_messages,
                    generation_config=generation_config or None,  # type: ignore
                )
            else:
                # Single prompt (fallback)
                api_response = self.model.generate_content(  # type: ignore
                    system_prompt or "Hello",
                    generation_config=generation_config or None,  # type: ignore
                )

            end_time = time.time()

            # Extract response text
            response_text = (
                api_response.text  # type: ignore
                if hasattr(api_response, "text")
                else str(api_response)
            )

            # Extract usage data (Google API might have different structure)
            usage_data = {
                "prompt_tokens": getattr(api_response, "prompt_token_count", 0),
                "completion_tokens": (
                    getattr(api_response, "candidates_token_count", 0)
                    if hasattr(api_response, "candidates_token_count")
                    else len(response_text.split())
                ),
                "total_tokens": getattr(api_response, "total_token_count", 0),
                "latency_sec": end_time - start_time,
            }

            logger.debug(
                f"Google Gemini response generated successfully. Length: {len(response_text)} chars"
            )
            return response_text, usage_data

        except Exception as e:
            logger.error(
                f"Error in GoogleGenAIClient.generate_response for model {self.model_name_for_api}: {e}"
            )
            error_response = (
                f"I encountered an issue while processing your request: {str(e)}"
            )
            error_usage = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "latency_sec": 0.0,
            }
            return error_response, error_usage

    def test_connection(self) -> bool:
        """Test if the client can connect to Google's API."""
        try:
            # Make a simple test call
            self.model.generate_content("Hello")  # type: ignore
            return True
        except Exception as e:
            logger.error(f"Google Gemini connection test failed: {e}")
            return False

    def stream_response(
        self, system_prompt: str, messages: List[Dict[str, str]], **kwargs
    ) -> Any:
        """
        Stream response from Google Gemini API.

        Args:
            system_prompt: System instructions for the model
            messages: List of conversation messages with 'role' and 'content'
            **kwargs: Additional parameters

        Yields:
            Response chunks from the streaming API
        """
        try:
            # Prepare messages (similar to generate_response)
            formatted_messages = []

            if system_prompt:
                if messages and messages[0]["role"] == "user":
                    messages[0]["content"] = (
                        system_prompt + "\n\n" + messages[0]["content"]
                    )
                else:
                    formatted_messages.append(
                        {"role": "user", "parts": [{"text": system_prompt}]}
                    )

            for msg in messages:
                role = msg["role"]
                content = msg["content"]
                api_role = "model" if role == "assistant" else "user"
                formatted_messages.append(
                    {"role": api_role, "parts": [{"text": content}]}
                )

            # Extract generation config
            generation_config: Dict[str, Any] = {}
            if "temperature" in kwargs:
                generation_config["temperature"] = kwargs["temperature"]
            if "max_tokens" in kwargs:
                generation_config["max_output_tokens"] = kwargs["max_tokens"]

            # Stream the response
            if formatted_messages:
                response_stream = self.model.generate_content(  # type: ignore
                    formatted_messages,
                    generation_config=generation_config or None,  # type: ignore
                    stream=True,  # type: ignore
                )
            else:
                response_stream = self.model.generate_content(  # type: ignore
                    system_prompt or "Hello",
                    generation_config=generation_config or None,  # type: ignore
                    stream=True,  # type: ignore
                )

            for chunk in response_stream:  # type: ignore
                if hasattr(chunk, "text"):
                    yield chunk.text  # type: ignore
                else:
                    yield str(chunk)

        except Exception as e:
            logger.error(f"Error in streaming response: {e}")
            yield f"Error: {str(e)}"

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        return {
            "model_id": self.model_id,
            "model_name": self.model_name_for_api,
            "provider": "google",
            "capabilities": self.get_capabilities(),
        }
