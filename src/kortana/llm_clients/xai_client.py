"""
XAI (Grok) Client Implementation for Kor'tana
Specialized for autonomous development and reasoning tasks
"""

import json
import logging
import os
from typing import Any

from .base_client import BaseLLMClient

logger = logging.getLogger(__name__)


class XAIClient(BaseLLMClient):
    """
    XAI (Grok) client implementation
    Optimized for autonomous development and reasoning
    """    def __init__(
        self, api_key: str | None = None, model_name: str = "grok-3-mini", **kwargs
    ):
        """
        Initialize XAI client
        
        Args:
            api_key: XAI API key (defaults to XAI_API_KEY env var)
            model_name: Model to use (defaults to grok-3-mini)
        """
        self.api_key = api_key or os.getenv("XAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "XAI API key is required. Set XAI_API_KEY environment variable or pass api_key parameter."
            )
        self.model_name = model_name
        self.base_url = "https://api.x.ai/v1"
        self.default_params = kwargs

        # Initialize XAI client
        try:
            # Use OpenAI-compatible client for XAI API
            from openai import OpenAI

            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            self.available = True
            logger.info(f"XAI client initialized for model: {model_name}")
        except ImportError:
            logger.error(
                "OpenAI library required for XAI client. Install with: pip install openai"
            )
            self.client = None
            self.available = False
        except Exception as e:
            logger.error(f"Failed to initialize XAI client: {e}")
            self.client = None
            self.available = False

    # Standardize the return format to match OpenAI-like structure
    # This is a nested dictionary that mimics the expected attributes
    def _standardize_response(
        self,
        content: str,
        model_id: str,
        usage: dict[str, int],
        function_call: dict | None = None,
        finish_reason: str = "stop",
    ) -> dict[str, Any]:
        # Add logging for arguments received by standardize_response
        logger.debug(
            f"_standardize_response received: content='{content[:50]}...', model_id={model_id}, usage={usage}, function_call={function_call}, finish_reason={finish_reason}"
        )

        message = {"content": content}
        if function_call:
            # Assuming the ChatEngine expects a 'tool_calls' structure for function calls
            # Adjust this if ChatEngine's handling is different
            message["tool_calls"] = [
                {
                    "function": {
                        "name": function_call["name"],
                        "arguments": json.dumps(function_call["arguments"]),
                    }
                }
            ]

        standardized_response = {
            "choices": [{"message": message, "finish_reason": finish_reason}],
            "model": model_id,  # Include model ID at the top level as well
            "usage": usage,
        }
        # Add logging for the standardized response being returned
        logger.debug(f"_standardize_response returning: {standardized_response}")
        return standardized_response

    def generate_response(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        enable_function_calling: bool = False,
        functions: list[dict] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Generate response using XAI Grok API
        Optimized for autonomous development tasks
        """
        if not self.available or not self.client:
            # Return standardized error response
            return self._standardize_response(
                content="XAI client not available.",
                model_id=self.model_name,
                usage={},
                finish_reason="error",
            )

        try:
            # Prepare messages with system prompt
            full_messages = []
            if system_prompt:
                full_messages.append({"role": "system", "content": system_prompt})
            full_messages.extend(messages)  # Add existing messages

            # Prepare completion arguments optimized for reasoning
            completion_args = {
                "model": self.model_name,
                "messages": full_messages,
                "max_tokens": kwargs.get("max_tokens", 2048),
                "temperature": kwargs.get(
                    "temperature", 0.5
                ),  # Lower temp for reasoning
                "top_p": kwargs.get("top_p", 0.8),
                "stream": kwargs.get("stream", False),
            }

            # Add function calling if enabled and functions are provided
            if enable_function_calling and functions:
                # The underlying OpenAI client expects 'tools' and
                # 'tool_choice'
                completion_args["tools"] = [
                    {"type": "function", "function": func} for func in functions
                ]
                completion_args["tool_choice"] = kwargs.get(
                    "tool_choice", "auto"
                )  # Use 'tool_choice' not 'function_call'

            # Generate response using XAI API
            response = self.client.chat.completions.create(**completion_args)

            # Add logging for raw response from XAI API
            logger.debug(f"Raw response from XAI API: {response}")

            # Extract data and standardize the return format
            if response.choices and len(response.choices) > 0:
                choice = response.choices[0]
                content = choice.message.content or ""

                # Handle function calls - extract from message if present
                tool_calls_from_response = None
                if hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
                    # Assuming tool_calls is a list of objects with 'function'
                    # attribute
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
                logger.warning("XAI API returned no choices.")
                return self._standardize_response(
                    content="No response choices returned",
                    model_id=self.model_name,
                    usage={},
                    finish_reason="error",
                )

        except Exception as e:
            logger.error(f"XAI API error: {e}", exc_info=True)  # Log exception details
            # Ensure standardized error response is always returned
            # Add logging for error before standardizing
            logger.debug(f"Error details before standardizing: {e}")
            return self._standardize_response(
                content=f"Error with XAI API: {e}",
                model_id=self.model_name,
                usage={},
                finish_reason="error",
            )

    def get_capabilities(self) -> dict[str, Any]:
        """Return XAI client capabilities"""
        return {
            "name": self.model_name,
            "provider": "xai",
            "supports_function_calling": True,
            "supports_streaming": True,
            "context_window": 128000,  # Grok-3 Mini context window
            "supports_reasoning": True,
            "optimal_for": [
                "autonomous_development",
                "code_generation",
                "reasoning",
                "self_improvement",
            ],
        }

    def validate_connection(self) -> bool:
        """Validate XAI API connection"""
        if not self.available:
            return False

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=1,
            )
            return bool(response.choices)
        except Exception as e:
            logger.error(f"XAI connection validation failed: {e}")
            return False

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Estimate the cost of a request for Grok-3-mini-beta.
        Pricing: Input $0.30 / 1M tokens, Output $0.50 / 1M tokens (based on OpenRouter).
        """
        # Prices are per 1 million tokens
        input_cost_per_token = 0.30 / 1_000_000
        output_cost_per_token = 0.50 / 1_000_000

        estimated_cost = (prompt_tokens * input_cost_per_token) + (
            completion_tokens * output_cost_per_token
        )
        return estimated_cost

    def test_connection(self) -> bool:
        """
        Test the connection to the XAI API using the validate_connection logic.
        """
        logger.info(f"Testing connection for model: {self.model_name}")
        return self.validate_connection()
