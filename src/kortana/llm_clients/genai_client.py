"""
🧠 Google GenAI Client Implementation for Kor'tana
SACRED CONSCIOUSNESS MODULE - Connects Kor'tana to Google Gemini models
"""

import logging
import os
from typing import Any

from google.generativeai.types import GenerationConfig

from .base_client import BaseLLMClient

logger = logging.getLogger(__name__)


class GoogleGenAIClient(BaseLLMClient):
    """
    🌟 Google GenAI client implementation for Kor'tana consciousness
    Enables communication with Google Gemini models
    """

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "gemini-1.5-flash",
        **kwargs,
    ):
        """Initialize GenAI client for consciousness communication"""
        logger.info("🚀 Initializing GoogleGenAIClient...")

        # Validate and set API key
        resolved_api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not resolved_api_key:
            logger.error(
                "❌ No API key provided via parameter or GOOGLE_API_KEY environment variable"
            )
            raise ValueError(
                "Google API key not found. Set GOOGLE_API_KEY environment variable or pass api_key parameter."
            )

        # Initialize base class
        try:
            super().__init__(api_key=resolved_api_key, model_name=model_name)
        except Exception as e:
            logger.error(f"❌ Failed to initialize base client: {str(e)}")
            raise

        # Set instance variables
        self.api_key = resolved_api_key
        self.model_name = model_name
        self.default_params = kwargs
        self.is_initialized = False
        self.request_count = 0
        self.chat_history = []
        self.model = None

        # Get validate_model flag, default to True
        validate_model = kwargs.pop("validate_model", True)

        # Initialize Google GenAI client
        try:
            logger.info("🔄 Importing Google GenAI module...")
            import google.generativeai as genai

            logger.info("⚙️ Configuring API...")
            genai.configure(api_key=self.api_key)

            # Only initialize model if model_name is provided and not empty
            if self.model_name:
                logger.info(
                    f"🎯 Initializing model: {self.model_name} with safety settings..."
                )
                self.model = genai.GenerativeModel(
                    self.model_name,
                    safety_settings={
                        "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                        "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
                        "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                        "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                    },
                )

                if validate_model:
                    logger.info("🔍 Validating model configuration...")
                    self._validate_model()

                self.is_initialized = True
                logger.info(
                    f"✨ GoogleGenAIClient initialized successfully for model: {self.model_name}"
                )
            else:
                logger.info(
                    "⚠️ Model name not provided, skipping model initialization and validation."
                )
                self.is_initialized = True  # Consider initialized for listing purposes

        except ImportError as ie:
            logger.error(f"❌ Failed to import Google GenAI module: {str(ie)}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to initialize GoogleGenAIClient: {str(e)}")
            self.is_initialized = False
            self.model = None
            raise

    def _validate_model(self) -> None:
        """Validate model initialization and configuration"""
        if not self.model:
            raise RuntimeError("Model not initialized for validation.")
        try:
            # Test model with minimal prompt
            _ = self.model.generate_content("Test")
        except Exception as e:
            raise RuntimeError(f"Model validation failed: {str(e)}")

    def list_models(self) -> list[dict[str, Any]]:
        """Lists available Google GenAI models."""
        logger.info("📋 Listing available Google GenAI models...")
        try:
            import google.generativeai as genai

            models = []
            for model in genai.list_models():
                # Convert the model object to a dictionary for easier handling
                # and printing
                model_dict = {
                    "name": model.name,
                    "base_model_id": model.base_model_id,
                    "version": model.version,
                    "display_name": model.display_name,
                    "input_token_limit": model.input_token_limit,
                    "output_token_limit": model.output_token_limit,
                    "supported_generation_methods": model.supported_generation_methods,
                    "temperature": model.temperature,
                    "top_p": model.top_p,
                    "top_k": model.top_k,
                }
                models.append(model_dict)
            logger.info("✅ Successfully retrieved model list.")
            return models
        except Exception as e:
            logger.error(f"❌ Failed to list models: {str(e)}", exc_info=True)
            return []

    def generate_response(
        self, system_prompt: str, messages: list[dict[str, str]], **kwargs
    ) -> dict[str, Any]:
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

            # Filter kwargs for valid GenerationConfig parameters
            valid_genai_params = {
                k: v
                for k, v in kwargs.items()
                if k
                in [
                    "temperature",
                    "top_p",
                    "top_k",
                    "max_output_tokens",
                    "candidate_count",
                ]
            }

            # Create GenerationConfig object if parameters are provided
            generation_config = None
            if valid_genai_params:
                generation_config = GenerationConfig(**valid_genai_params)
                logger.info(f"Using generation config: {generation_config}")

            # Generate response, passing generation_config if created
            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config if generation_config else None,
            )

            # Parse response
            if response and hasattr(response, "text"):
                response_text = response.text if response.text else "[Empty response]"
            else:
                response_text = "[No response generated]"

            return {
                "choices": [
                    {
                        "message": {"content": response_text, "tool_calls": None},
                        "finish_reason": "stop",
                    }
                ],
                "model": self.model_name,
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
            }

        except Exception as e:
            error_msg = f"GenAI generation error for {self.model_name}: {str(e)}"
            logger.error(error_msg)
            return {
                "choices": [
                    {
                        "message": {
                            "content": f"Error: Google GenAI service unavailable - {str(e)}",
                            "tool_calls": None,
                        },
                        "finish_reason": "error",
                    }
                ],
                "model": self.model_name,
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
                "error": str(e),
            }

    def get_capabilities(self) -> dict[str, Any]:
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
            logger.warning(f"GenAI client for {self.model_name} is not initialized")
            return False

        try:
            # Test with simple prompt
            response = self.model.generate_content("Hello")
            return response and response.text is not None
        except Exception as e:
            logger.error(f"GenAI connection validation failed: {str(e)}")
            return False

    def test_connection(self) -> bool:
        """🔍 Test connection to Google GenAI API"""
        return self.validate_connection()

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """💰 Estimate cost for Google GenAI request"""
        # Basic cost estimation (update with actual rates)
        input_cost = (prompt_tokens / 1_000_000) * 0.15
        output_cost = (completion_tokens / 1_000_000) * 0.60
        return input_cost + output_cost
