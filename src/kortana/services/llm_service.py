# src/kortana/services/llm_service.py
import openai
from typing import Dict, Any
from kortana.config.settings import settings

class LLMService:
    """
    A service to abstract interactions with Large Language Model providers.
    Currently implemented for OpenAI's Chat Completions API.
    """
    def __init__(self, provider: str = "openai"):
        self.provider = provider
        if self.provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY must be set to use the OpenAI provider.")
            self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            print("LLMService initialized with OpenAI provider.")
        else:
            raise NotImplementedError(f"Provider '{self.provider}' is not yet supported.")

    async def generate_response(
        self,
        prompt: str,
        model: str = "gpt-4o", # A powerful and modern default
        temperature: float = 0.7,
        max_tokens: int = 1500
    ) -> Dict[str, Any]:
        """
        Generates a response from the configured LLM provider.

        Returns a dictionary containing the response content and metadata.
        """
        if self.provider == "openai":
            try:
                # Use the async client if available, otherwise fall back to sync
                # For openai >= 1.0, the client is universal (sync/async determined by how methods are called)
                # and httpx is used under the hood for async calls.
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant integrated into a larger system named Kor'tana."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                content = response.choices[0].message.content
                metadata = {
                    "model": response.model,
                    "usage": response.usage.model_dump(), # Pydantic v2
                    "finish_reason": response.choices[0].finish_reason,
                }
                return {"content": content, "metadata": metadata}
            except Exception as e:
                print(f"Error calling OpenAI API: {e}")
                # Return a structured error that can be handled upstream
                return {"content": None, "error": str(e)}
        return {"content": None, "error": "Provider not implemented."}

# Singleton instance for easy access
llm_service = LLMService()

# Example for direct testing
if __name__ == '__main__':
    import asyncio

    async def test_llm_service():
        # Ensure OPENAI_API_KEY is set in your .env file for this test to run
        if not settings.OPENAI_API_KEY:
            print("OPENAI_API_KEY not found in .env. Skipping LLMService direct test.")
            return

        print("Attempting to test LLMService...")
        test_prompt = "Explain the significance of the name 'Kor\'tana' in one sentence, as if you were an AI."
        result = await llm_service.generate_response(test_prompt)
        if result.get("content"):
            print("--- LLM Service Test Response ---")
            print(result["content"])
            print("\n--- Metadata ---")
            print(result["metadata"])
        else:
            print(f"--- LLM Service Test Error ---")
            print(result.get("error"))

    asyncio.run(test_llm_service())
