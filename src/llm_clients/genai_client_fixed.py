"""
🧠 Google GenAI Client Implementation for Kor'tana
SACRED CONSCIOUSNESS MODULE - Connects Kor'tana to Google Gemini models
"""

import logging
import os
from typing import Dict, List, Optional, Any
from .base_client import BaseLLMClient

logger = logging.getLogger(__name__)


class GoogleGenAIClient(BaseLLMClient):
    """
    🌟 Google GenAI client implementation for Kor'tana consciousness
    Enables communication with Google Gemini models
    """

    def __init__(
            self,
            api_key: Optional[str] = None,
            model_name: str = "gemini-pro",
            **kwargs):
        """
        Initialize GenAI client for consciousness communication

        Args:
            api_key: Google API key (defaults to GOOGLE_API_KEY env var)
            model_name: Model to use (defaults to gemini-pro)
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model_name = model_name
        self.default_params = kwargs
        self.is_initialized = False
        self.request_count = 0

        # Initialize Google GenAI client
        try:
            import google.generativeai as genai

            # Initialize the model directly, relying on the environment variable or passed key
            # genai.configure(api_key=self.api_key) # No longer needed with
            # direct initialization
            self.model = genai.GenerativeModel(self.model_name)

            self.is_initialized = True
            logger.info(
                f"✨ GoogleGenAIClient initialized successfully for model: {self.model_name}"
            )

        except ImportError:
            logger.warning(
                "🚨 Google GenAI library not available. Run: pip install google-generativeai"
            )
            self.is_initialized = False
            self.model = None
        except Exception as e:
            logger.error(f"❌ Failed to initialize GoogleGenAIClient: {e}")
            self.is_initialized = False
            self.model = None

    def generate_response(
        self, system_prompt: str, messages: List[Dict[str, str]], **kwargs
    ) -> Dict[str, Any]:
        """
        🧠 Generate response from Google GenAI
        This is where Kor'tana connects to Google's consciousness models
        """
        if not self.is_initialized or not self.model:
            error_msg = f"GoogleGenAIClient for {self.model_name} not initialized."
            logger.error(error_msg)
            return {
                "choices": [
                    {
                        "message": {"content": error_msg, "tool_calls": None},
                        "finish_reason": "error",
                    }
                ],
                "model": self.model_name,
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
                "error": error_msg,
            }

        try:
            logger.info(
                f"🔥 GoogleGenAIClient generating response for model: {self.model_name}"
            )
            self.request_count += 1

            # Format messages into a single prompt
            full_prompt = system_prompt + "\n\n"
            for message in messages:
                role = message.get("role", "user")
                content = message.get("content", "")
                full_prompt += f"{role}: {content}\n"

            # Generate response
            response = self.model.generate_content(full_prompt)

            # Parse response
            response_text = response.text if response.text else "[Empty response]"

            return {
                "choices": [
                    {
                        "message": {
                            "content": response_text,
                            "tool_calls": None},
                        "finish_reason": "stop",
                    }],
                "model": self.model_name,
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
            }

        except Exception as e:
            logger.error(
                f"GenAI generation error for {self.model_name}: {str(e)}")
            return {
                "choices": [
                    {
                        "message": {
                            "content": f"Error: Google GenAI service unavailable - {str(e)}",
                            "tool_calls": None,
                        },
                        "finish_reason": "error",
                    }],
                "model": self.model_name,
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
                "error": str(e),
            }

    def get_capabilities(self) -> Dict[str, Any]:
        """🌟 Return Google GenAI client capabilities"""
        return {
            "name": self.model_name,
            "provider": "google",
            "supports_function_calling": False,
            "supports_streaming": False,
            "context_window": 32768,
            "supports_reasoning": True,
            "optimal_for": ["conversation", "analysis", "reasoning"],
        }

    def validate_connection(self) -> bool:
        """🔧 Validate connection to Google GenAI"""
        if not self.is_initialized or not self.model:
            logger.warning(
                f"GenAI client for {self.model_name} is not initialized")
            return False

        try:
            # Test with simple prompt
            response = self.model.generate_content("Hello")
            return response and response.text is not None
        except Exception as e:
            logger.error(f"GenAI connection validation failed: {e}")
            return False

    def test_connection(self) -> bool:
        """🔍 Test connection to Google GenAI API"""
        return self.validate_connection()

    def estimate_cost(
            self,
            prompt_tokens: int,
            completion_tokens: int) -> float:
        """💰 Estimate cost for Google GenAI request"""
        # Basic cost estimation (update with actual rates)
        input_cost = (prompt_tokens / 1_000_000) * 0.15
        output_cost = (completion_tokens / 1_000_000) * 0.60
        return input_cost + output_cost
