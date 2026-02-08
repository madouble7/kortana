# src/kortana/services/llm_service.py
"""
LLM Service with Enhanced Error Handling and Lazy Loading

Provides abstraction for LLM provider interactions with:
- Lazy client initialization to prevent circular imports
- Comprehensive error handling
- Performance metrics
- Async support
"""

import logging
import time
from typing import Any, Optional

from ..config.settings import settings
from ..utils import ServiceError, TimeoutError

logger = logging.getLogger(__name__)


class LLMService:
    """
    A service to abstract interactions with Large Language Model providers.
    Currently implemented for OpenAI's Chat Completions API.

    Features:
    - Lazy client initialization (prevents circular imports)
    - Error handling with recovery strategies
    - Response timing and metrics
    - Type-safe responses
    """

    def __init__(self, provider: str = "openai"):
        """
        Initialize LLM service.

        Args:
            provider: LLM provider name (currently: 'openai')

        Raises:
            ServiceError: If provider is invalid or API key missing
        """
        self.provider = provider
        self._client = None  # Lazy initialization
        self._initialized = False

        logger.info(f"LLMService instantiated with provider: {provider}")

    def _ensure_initialized(self) -> None:
        """Lazy initialization of the client."""
        if self._initialized:
            return

        if self.provider == "openai":
            try:
                import openai

                if not settings.OPENAI_API_KEY:
                    raise ServiceError(
                        "OPENAI_API_KEY must be set to use the OpenAI provider",
                        service_name="openai"
                    )

                self._client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
                self._initialized = True
                logger.info("OpenAI client initialized successfully")
            except ImportError:
                raise ServiceError(
                    "OpenAI library not installed. Install with: pip install openai",
                    service_name="openai"
                )
            except Exception as e:
                raise ServiceError(
                    f"Failed to initialize OpenAI client: {e}",
                    service_name="openai"
                )
        else:
            raise ServiceError(
                f"Provider '{self.provider}' is not yet supported",
                service_name=provider
            )

    @property
    def client(self):
        """Lazy-loaded client property."""
        self._ensure_initialized()
        return self._client

    async def generate_response(
        self,
        prompt: str,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 1500,
        timeout: Optional[float] = 30.0,
    ) -> dict[str, Any]:
        """
        Generate a response from the configured LLM provider.

        Args:
            prompt: User prompt/message
            model: Model identifier
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum response tokens
            timeout: Request timeout in seconds

        Returns:
            Dictionary with 'content', 'metadata', and optional 'error' keys

        Example:
            result = await llm_service.generate_response("Hello!")
            if "error" not in result:
                print(result["content"])
        """
        start_time = time.perf_counter()

        try:
            self._ensure_initialized()

            if self.provider == "openai":
                try:
                    import asyncio

                    # Use sync API in async context (OpenAI handles this)
                    response = await asyncio.to_thread(
                        self.client.chat.completions.create,
                        model=model,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are Kor'tana, an autonomous AI assistant integrated into a larger system.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )

                    content = response.choices[0].message.content
                    metadata = {
                        "model": response.model,
                        "usage": response.usage.model_dump() if hasattr(response.usage, 'model_dump') else {},
                        "finish_reason": response.choices[0].finish_reason,
                        "processing_time_ms": (time.perf_counter() - start_time) * 1000,
                    }

                    logger.info(f"LLM request successful. Time: {metadata['processing_time_ms']:.1f}ms")
                    return {"content": content, "metadata": metadata}

                except asyncio.TimeoutError:
                    raise TimeoutError(
                        "LLM request exceeded timeout",
                        operation="llm_generate",
                        timeout_seconds=timeout
                    )
                except Exception as e:
                    raise ServiceError(
                        f"OpenAI API error: {e}",
                        service_name="openai",
                        http_status=getattr(e, 'status_code', None)
                    )

            return {"content": None, "error": "Provider not implemented"}

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"LLM generation failed after {elapsed_ms:.1f}ms: {e}")
            return {
                "content": None,
                "error": str(e),
                "processing_time_ms": elapsed_ms,
            }


# Singleton instance for easy access with lazy initialization
_llm_service: Optional[LLMService] = None


def get_llm_service(provider: str = "openai") -> LLMService:
    """
    Get or create LLM service singleton.

    Args:
        provider: LLM provider to use

    Returns:
        LLMService instance
    """
    global _llm_service

    if _llm_service is None:
        _llm_service = LLMService(provider=provider)
        logger.info("Created new LLMService singleton")

    return _llm_service


# Example for direct testing
if __name__ == "__main__":
    import asyncio
    import time

    async def test_llm_service():
        """Test LLMService functionality."""
        logger.basicConfig(level=logging.INFO)

        if not settings.OPENAI_API_KEY:
            print("OPENAI_API_KEY not found in .env. Skipping LLMService direct test.")
            return

        print("Testing LLMService...")
        test_prompt = "Explain the significance of the name 'Kor'tana' in one sentence."

        service = get_llm_service()
        result = await service.generate_response(test_prompt)

        if "error" not in result:
            print("--- LLM Service Test Response ---")
            print(result["content"])
            print("\n--- Metadata ---")
            print(result["metadata"])
        else:
            print(f"Error: {result['error']}")

            print(result["metadata"])
        else:
            print("--- LLM Service Test Error ---")
            print(result.get("error"))

    asyncio.run(test_llm_service())
