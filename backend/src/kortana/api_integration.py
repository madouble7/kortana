"""
KOR'TANA API Integration Layer

Bridges the cost-optimized model router to actual API providers.
Handles real API calls with fallback chains and cost tracking.
"""

from __future__ import annotations

import asyncio
import os

from src.kortana.cost_optimized_model_router import (
    CostOptimizedModelRouter,
    ModelProvider,
    TaskType,
)
from src.kortana.logger import get_logger

logger = get_logger(__name__)


class GroqAPIClient:
    """Groq API client (free, unlimited, fast)"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.groq.com/openai/v1"
        self.model = "mixtral-8x7b-32768"

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> tuple[str, int, int]:
        """
        Generate text using Groq API.

        Returns: (text, input_tokens, output_tokens)
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data["choices"][0]["message"]["content"]
                        usage = data["usage"]
                        return (
                            content,
                            usage["prompt_tokens"],
                            usage["completion_tokens"],
                        )
                    else:
                        error_text = await response.text()
                        raise Exception(
                            f"Groq API error {response.status}: {error_text}"
                        )
        except asyncio.TimeoutError:
            raise Exception("Groq API request timeout")
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise


class GeminiAPIClient:
    """Gemini API client (free, quota-limited)"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "gemini-3.1-flash-lite-preview"

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> tuple[str, int, int]:
        """
        Generate text using Gemini API.

        Returns: (text, input_tokens, output_tokens)
        """
        try:
            # Use Google's generative AI client
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model)

            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=temperature,
                ),
                stream=False,
            )

            content = response.text
            # Estimate tokens (Gemini doesn't always return exact counts)
            input_tokens = len(prompt.split()) * 1.3
            output_tokens = len(content.split()) * 1.3

            return content, int(input_tokens), int(output_tokens)

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise


class ClaudeAPIClient:
    """Claude API client (premium, for critical decisions)"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.anthropic.com/v1"
        self.model = "claude-3-5-sonnet-20241022"

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> tuple[str, int, int]:
        """
        Generate text using Claude API.

        Returns: (text, input_tokens, output_tokens)
        """
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/messages",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data["content"][0]["text"]
                        usage = data["usage"]
                        return (
                            content,
                            usage["input_tokens"],
                            usage["output_tokens"],
                        )
                    else:
                        error_text = await response.text()
                        raise Exception(
                            f"Claude API error {response.status}: {error_text}"
                        )
        except asyncio.TimeoutError:
            raise Exception("Claude API request timeout")
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise


class OpenAIAPIClient:
    """OpenAI API client (expensive, fallback)"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "gpt-4o-mini"

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> tuple[str, int, int]:
        """
        Generate text using OpenAI API.

        Returns: (text, input_tokens, output_tokens)
        """
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self.api_key)

            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )

            content = response.choices[0].message.content
            usage = response.usage
            return (
                content,
                usage.prompt_tokens,
                usage.completion_tokens,
            )

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise


class UnifiedAPIClient:
    """
    Unified client that coordinates across all API providers.
    Automatically selects optimal provider and handles fallback chains.
    """

    def __init__(self):
        self.router = CostOptimizedModelRouter()
        self.clients: dict[ModelProvider, object] = {}
        self._init_clients()

    def _init_clients(self) -> None:
        """Initialize all available API clients"""
        if os.getenv("GROQ_API_KEY"):
            self.clients[ModelProvider.GROQ] = GroqAPIClient(os.getenv("GROQ_API_KEY"))

        if os.getenv("GEMINI_API_KEY"):
            self.clients[ModelProvider.GEMINI] = GeminiAPIClient(
                os.getenv("GEMINI_API_KEY")
            )

        if os.getenv("ANTHROPIC_API_KEY"):
            self.clients[ModelProvider.CLAUDE] = ClaudeAPIClient(
                os.getenv("ANTHROPIC_API_KEY")
            )

        if os.getenv("OPENAI_API_KEY"):
            self.clients[ModelProvider.OPENAI] = OpenAIAPIClient(
                os.getenv("OPENAI_API_KEY")
            )

    async def generate(
        self,
        prompt: str,
        task_type: TaskType,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        budget_limit: float = 0.01,
    ) -> tuple[str, ModelProvider, float]:
        """
        Generate text with automatic provider selection and fallback.

        Returns: (content, provider_used, cost)
        """
        # Get optimal provider chain
        providers = self.router.select_for_task(task_type, budget_limit)

        for provider in providers:
            client = self.clients.get(provider)
            if not client:
                continue

            try:
                logger.info(f"Attempting {provider.value} for {task_type.value}")

                content, input_tokens, output_tokens = await client.generate(
                    prompt, max_tokens, temperature
                )

                # Record usage and calculate cost
                cost = self.router.estimate_cost(
                    provider, task_type, input_tokens, output_tokens
                )
                self.router.record_usage(
                    provider, task_type, input_tokens, output_tokens
                )

                logger.info(
                    f"✅ Success with {provider.value} "
                    f"(${cost:.4f}, {len(content)} chars)"
                )
                return content, provider, cost

            except Exception as e:
                logger.warning(
                    f"Provider {provider.value} failed: {e}. " f"Trying next..."
                )
                continue

        # All providers failed
        raise Exception(f"All providers exhausted for {task_type.value}")

    def get_cost_report(self) -> dict:
        """Get current cost tracking"""
        return self.router.get_cost_report()

    def get_routing_info(self) -> dict:
        """Get routing strategy info"""
        return self.router.get_routing_strategy()
