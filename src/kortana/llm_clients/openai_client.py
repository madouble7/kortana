# C:\kortana\src\llm_clients\openai_client.py
# Purpose: Implements a client for direct OpenAI API calls.
# Role: Enables Kor'tana to use OpenAI models (e.g., for tactical or fire
# modes).

"""
Official OpenAI SDK-compatible client implementation for Kor'tana
Uses standard client.chat.completions.create() pattern for full compatibility
Optimized for GPT-4.1-Nano and autonomous development
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from openai import OpenAI
from openai.types.chat import ChatCompletionUserMessageParam

from .base_client import BaseLLMClient

logger = logging.getLogger(__name__)


class OpenAIClient(BaseLLMClient):
    """
    Official OpenAI SDK-compatible client implementation
    Provides both direct SDK calls and ADE compatibility
    """

    def __init__(
        self, api_key: Optional[str] = None, model_name: str = "gpt-4.1-nano", **kwargs
    ):
        """
        Initialize OpenAI client using official SDK structure

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
                        model_name: Model to use (defaults to gpt-4.1-nano)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model_name
        self.default_params = kwargs
        self.base_url = kwargs.get("base_url", "https://api.openai.com/v1")

        # ✅ Initialize official OpenAI client
        self.client = OpenAI(api_key=self.api_key)

        # ✅ Add chat attribute for ADE compatibility
        self.chat = ChatNamespace(self.client)

        logger.info(f"OpenAIClient initialized for model: {model_name}")

    # Standardize the return format to match OpenAI-like structure
    # This is a nested dictionary that mimics the expected attributes
    def _standardize_response(
        self,
        content: str,
        model_id: str,
        usage: Dict[str, int],
        function_call: Optional[Dict] = None,
        finish_reason: str = "stop",
    ) -> Dict[str, Any]:
        message = {"content": content}
        if function_call:  # Ensure function_call is a list of tool_calls as expected
            # by ChatEngine. The OpenAI SDK returns a list of ToolCall objects
            # We need to convert this to a list of dicts if function_call here
            # is the raw SDK object. Assuming function_call passed here is
            # already processed into a dict if needed
            message["tool_calls"] = [
                {
                    "function": {
                        "name": function_call.get("name"),
                        "arguments": json.dumps(
                            function_call.get("arguments", {})
                        ),  # Arguments should be a JSON string
                    }
                }
            ]

        return {
            "choices": [{"message": message, "finish_reason": finish_reason}],
            "model": model_id,  # Include model ID at the top level as well
            "usage": usage,
        }

    def generate_response(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        enable_function_calling: bool = False,
        functions: Optional[List[Dict]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Generate response using official OpenAI SDK structure"""
        try:
            # Prepare messages with system prompt
            full_messages = []
            if system_prompt:
                full_messages.append({"role": "system", "content": system_prompt})
            full_messages.extend(messages)

            # Prepare arguments for chat completion
            completion_args = {
                "model": self.model_name,
                "messages": full_messages,
                "max_tokens": kwargs.get("max_tokens", 500),
                "temperature": kwargs.get("temperature", 0.7),
                "stream": kwargs.get("stream", False),
            }

            # Add function calling if enabled and functions are provided
            if enable_function_calling and functions:
                # The underlying OpenAI client expects 'tools' and
                # 'tool_choice'
                completion_args["tools"] = [
                    {"type": "function", "function": func} for func in functions
                ]
                completion_args["tool_choice"] = kwargs.get("tool_choice", "auto")

            # ✅ Use official OpenAI SDK structure
            response = self.client.chat.completions.create(**completion_args)

            # Extract response content and standardize the return format
            if response.choices and len(response.choices) > 0:
                choice = response.choices[0]
                content = choice.message.content or ""

                # Handle function calls - extract from message if present
                tool_calls_from_response = None
                if hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
                    # The OpenAI SDK returns ToolCall objects, convert to dicts
                    tool_calls_from_response = [
                        {
                            "name": tc.function.name,
                            "arguments": json.loads(
                                tc.function.arguments
                            ),  # Arguments are usually a JSON string
                        }
                        for tc in choice.message.tool_calls
                    ]

                usage = {
                    "prompt_tokens": (
                        response.usage.prompt_tokens if response.usage else 0
                    ),
                    "completion_tokens": (
                        response.usage.completion_tokens if response.usage else 0
                    ),
                    "total_tokens": (
                        response.usage.total_tokens if response.usage else 0
                    ),
                }

                # Return standardized successful response
                return self._standardize_response(
                    content=content,
                    model_id=self.model_name,
                    usage=usage,
                    function_call=(
                        tool_calls_from_response[0]
                        if tool_calls_from_response
                        else None
                    ),  # Pass first tool call if any
                    finish_reason=choice.finish_reason,
                )
            else:
                # Return standardized response for no choices returned
                return self._standardize_response(
                    content="No response choices returned",
                    model_id=self.model_name,
                    usage={},
                    finish_reason="error",
                )

        except Exception as e:
            logger.error(
                f"OpenAI API error: {e}", exc_info=True
            )  # Log exception details
            # Return standardized error response
            return self._standardize_response(
                content=f"Error with OpenAI API: {e}",
                model_id=self.model_name,
                usage={},
                finish_reason="error",
            )

    def get_capabilities(self) -> Dict[str, Any]:
        """Return client capabilities"""
        return {
            "name": self.model_name,
            "provider": "openai",
            "supports_function_calling": True,
            "supports_streaming": True,
            "context_window": 4096,  # GPT-4.1-Nano context window
            "supports_reasoning": False,
            "optimal_for": [
                "conversation",
                "autonomous_development",
                "function_calling",
            ],
        }

    def validate_connection(self) -> bool:
        """Validate OpenAI API connection"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=1,
            )
            return bool(response.choices)
        except Exception as e:
            logger.error(f"Connection validation failed: {e}")
            return False

    def get_completion(self, messages: List[Dict[str, str]], **kwargs) -> Any:
        """Get completion from OpenAI API"""
        try:
            # Set default parameters
            params = {
                "model": self.model_name,
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 1000),
                "top_p": kwargs.get("top_p", 1.0),
                "frequency_penalty": kwargs.get("frequency_penalty", 0),
                "presence_penalty": kwargs.get("presence_penalty", 0),
            }

            # Add function calling support if provided
            if "functions" in kwargs:
                params["functions"] = kwargs["functions"]
            if "function_call" in kwargs:
                params["function_call"] = kwargs["function_call"]
            if "tools" in kwargs:
                params["tools"] = kwargs["tools"]
            if "tool_choice" in kwargs:
                params["tool_choice"] = kwargs["tool_choice"]

            response = self.client.chat.completions.create(**params)
            logger.debug(f"OpenAI API call successful for model: {self.model_name}")
            return response

        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost based on token usage"""
        # OpenAI pricing (approximate, update with current rates)
        pricing = {
            "gpt-4o": {"input": 2.50, "output": 10.00},
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "gpt-4-turbo": {"input": 10.00, "output": 30.00},
            "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
            # Estimated pricing
            "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
        }
        # Default pricing if model not found
        model_pricing = pricing.get(self.model_name, {"input": 1.00, "output": 3.00})

        input_cost = (prompt_tokens / 1_000_000) * model_pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * model_pricing["output"]
        total_cost = input_cost + output_cost

        logger.debug(f"Estimated cost for {self.model_name}: ${total_cost:.6f}")
        return total_cost

    def test_connection(self) -> bool:
        """Test connection to OpenAI API"""
        try:
            # Simple test with minimal tokens
            test_messages: List[ChatCompletionUserMessageParam] = [
                {"role": "user", "content": "Hello"}
            ]
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=test_messages,
                max_tokens=5,
                temperature=0,
            )

            if response and response.choices:
                logger.info(f"OpenAI connection test successful for {self.model_name}")
                return True
            else:
                logger.error("OpenAI connection test failed: No response")
                return False

        except Exception as e:
            logger.error(f"OpenAI connection test failed: {e}")
            return False

    def supports_streaming(self) -> bool:
        """Check if client supports streaming"""
        return True

    def get_model_info(self) -> Dict[str, Any]:
        """Get detailed model information"""
        return {
            "model_name": self.model_name,
            "provider": "openai",
            "capabilities": self.get_capabilities(),
            "base_url": self.base_url,
            "api_key_configured": bool(self.api_key),
        }


class ChatNamespace:
    """
    Chat namespace that provides ADE compatibility
    Routes calls to the official OpenAI client
    """

    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client
        self.completions = ChatCompletions(openai_client)


class ChatCompletions:
    """
    Chat completions handler that matches OpenAI SDK structure
    Provides full compatibility with ADE calling patterns
    """

    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client

    def create(self, **kwargs) -> Any:
        """
        Create chat completion - matches openai.chat.completions.create() signature
        ✅ This enables: client.chat.completions.create() calls from ADE
        """
        return self.openai_client.chat.completions.create(**kwargs)
