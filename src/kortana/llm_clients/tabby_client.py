"""
Tabby LLM Client - Ghost Protocol Phase 2 Integration

This client connects to a local Tabby ML server to provide local inference.
Part of the Kor'tana Autonomous Development Engine (ADE).
"""

import logging
import time
from typing import Any

import requests

from .base_client import BaseLLMClient

logger = logging.getLogger(__name__)


class TabbyClient(BaseLLMClient):
    """
    Client for local Tabby ML inference server.
    Implements the BaseLLMClient contract for Kor'tana integration.
    """

    def __init__(
        self,
        api_key: str = "local-tabby-key",
        model_name: str = "StarCoder2-7B",
        **kwargs,
    ):
        """
        Initialize Tabby client.

        Args:
            api_key: Optional API key (not used by default local Tabby)
            model_name: Model identifier used by Tabby
            **kwargs: Configuration including 'base_url' (default: http://localhost:8080)
        """
        super().__init__(api_key, model_name, **kwargs)
        self.base_url = kwargs.get("base_url", "http://localhost:8080")
        self.timeout = kwargs.get("timeout", 60)

        logger.info(
            f"TabbyClient initialized for model: {model_name} at {self.base_url}"
        )

    def generate_response(
        self, system_prompt: str, messages: list[dict[str, str]], **kwargs
    ) -> dict[str, Any]:
        """
        Generate response using Tabby's OpenAI-compatible chat completions endpoint.
        """
        endpoint = f"{self.base_url}/v1/chat/completions"

        # Prepare messages
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        payload = {
            "model": self.model_name,
            "messages": full_messages,
            "temperature": kwargs.get("temperature", 0.1),
            "max_tokens": kwargs.get("max_tokens", 2048),
            "top_p": kwargs.get("top_p", 1.0),
            "stream": False,
        }

        try:
            start_time = time.time()
            response = requests.post(
                endpoint,
                json=payload,
                timeout=self.timeout,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            response.raise_for_status()
            data = response.json()
            latency = time.time() - start_time

            # Extract content
            content = data["choices"][0]["message"]["content"]
            usage = data.get(
                "usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            )

            return {
                "content": content,
                "usage": usage,
                "model_id_used": self.model_name,
                "latency": latency,
                "error": None,
            }

        except Exception as e:
            logger.error(f"Tabby inference failed: {str(e)}")
            return {
                "content": "",
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
                "model_id_used": self.model_name,
                "error": str(e),
            }

    def get_capabilities(self) -> dict[str, Any]:
        """Returns the capabilities of the local StarCoder model."""
        return {
            "local_inference": True,
            "code_specialized": True,
            "context_window": 8192,
            "provider": "tabby",
        }

    def test_connection(self) -> bool:
        """Tests if the Tabby server is reachable."""
        try:
            response = requests.get(f"{self.base_url}/v1/model", timeout=5)
            return response.status_code == 200
        except:
            return False

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Local inference has zero financial cost."""
        return 0.0
