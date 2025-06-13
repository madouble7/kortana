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
    """

    def __init__(
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

    def _standardize_response(
        self,
        content: str,
        model_id: str,
        usage: dict[str, int],
        function_call: dict | None = None,
        finish_reason: str = "stop",
    ) -> dict[str, Any]:
        logger.debug(
            f"_standardize_response received: content='{content[:50]}...', model_id={model_id}, usage={usage}, function_call={function_call}, finish_reason={finish_reason}"
        )
        message = {"content": content}
        if function_call:
            # If downstream expects a string, use json.dumps; else, pass as list
            message["tool_calls"] = [
                {
                    "function": {
                        "name": function_call["name"],
                        "arguments": function_call["arguments"],
                    }
                }
            ]
        standardized_response = {
            "choices": [{"message": message, "finish_reason": finish_reason}],
            "model": model_id,
            "usage": usage,
        }
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
            return self._standardize_response(
                content="XAI client not available.",
                model_id=self.model_name,
                usage={},
                finish_reason="error",
            )
        try:
            full_messages = []
            if system_prompt:
                full_messages.append({"role": "system", "content": system_prompt})
            full_messages.extend(messages)
            completion_args = {
                "model": self.model_name,
                "messages": full_messages,
                "max_tokens": kwargs.get("max_tokens", 2048),
                "temperature": kwargs.get("temperature", 0.5),
                "top_p": kwargs.get("top_p", 0.8),
                "stream": kwargs.get("stream", False),
            }
            if enable_function_calling and functions:
                completion_args["tools"] = [
                    {"type": "function", "function": func} for func in functions
                ]
                completion_args["tool_choice"] = kwargs.get("tool_choice", "auto")
            response = self.client.chat.completions.create(**completion_args)
            logger.debug(f"Raw response from XAI API: {response}")
            if response.choices and len(response.choices) > 0:
                choice = response.choices[0]
                content = choice.message.content or ""
                tool_calls_from_response = None
                if hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
                    tool_calls_from_response = [
                        {
                            "name": tc.function.name,
                            "arguments": json.loads(tc.function.arguments),
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
                return self._standardize_response(
                    content=content,
                    model_id=self.model_name,
                    usage=usage,
                    function_call=(
                        tool_calls_from_response[0]
                        if tool_calls_from_response
                        else None
                    ),
                    finish_reason=choice.finish_reason,
                )
            else:
                logger.warning("XAI API returned no choices.")
                return self._standardize_response(
                    content="No response choices returned",
                    model_id=self.model_name,
                    usage={},
                    finish_reason="error",
                )
        except Exception as e:
            logger.error(f"XAI API error: {e}", exc_info=True)
            logger.debug(f"Error details before standardizing: {e}")
            return self._standardize_response(
                content=f"Error with XAI API: {e}",
                model_id=self.model_name,
                usage={},
                finish_reason="error",
            )

    def get_capabilities(self) -> dict[str, Any]:
        return {
            "name": self.model_name,
            "provider": "xai",
            "supports_function_calling": True,
            "supports_streaming": True,
            "context_window": 128000,
            "supports_reasoning": True,
            "optimal_for": [
                "autonomous_development",
                "code_generation",
                "reasoning",
                "self_improvement",
            ],
        }

    def validate_connection(self) -> bool:
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
        input_cost_per_token = 0.30 / 1_000_000
        output_cost_per_token = 0.50 / 1_000_000
        return (prompt_tokens * input_cost_per_token) + (
            completion_tokens * output_cost_per_token
        )

    def test_connection(self) -> bool:
        logger.info(f"Testing connection for model: {self.model_name}")
        return self.validate_connection()
