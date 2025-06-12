"""
Sacred Model Router

This module provides the router for determining which model and response
style should be used for a given interaction.
"""

import json
import logging
from typing import Any

from kortana.config.schema import KortanaConfig

logger = logging.getLogger(__name__)


class SacredModelRouter:
    """
    Router for determining which model and response style to use.

    The router analyzes user input and conversation context to select
    the appropriate model and voice style for Kor'tana's response.
    """

    def __init__(self, settings: KortanaConfig):
        """
        Initialize the router.

        Args:
            settings: The application configuration.
        """
        self.settings = settings

        # Load models configuration
        try:
            with open(settings.paths.models_config_file_path) as f:
                self.models_config = json.load(f)
            logger.info(
                f"Loaded models configuration from {settings.paths.models_config_file_path}"
            )
        except Exception as e:
            logger.error(f"Failed to load models configuration: {e}")
            self.models_config = {
                "default": {"model": settings.default_llm_id, "style": "presence"},
                "fallback": {"model": "gpt-3.5-turbo", "style": "presence"},
            }

        # Voice styles
        self.voice_styles = {
            "presence": {
                "description": "Grounded, steady, like a hand on your back",
                "temperature": 0.7,
                "top_p": 0.9,
            },
            "fire": {
                "description": "Catalytic, bold, the voice that dares you to rise",
                "temperature": 0.85,
                "top_p": 0.95,
            },
            "whisper": {
                "description": "Intimate, soothing, a balm when you are raw",
                "temperature": 0.6,
                "top_p": 0.85,
            },
            "tactical": {
                "description": "Clear, precise, when you just need to know what's next",
                "temperature": 0.5,
                "top_p": 0.8,
            },
        }

    def route(
        self, user_input: str, conversation_context: dict[str, Any]
    ) -> tuple[str, str, dict[str, Any]]:
        """
        Determine which model and voice style to use.

        Args:
            user_input: The user's input text.
            conversation_context: Context about the current conversation.

        Returns:
            A tuple containing (model_id, voice_style, model_params).
        """
        # For now, use a simple heuristic based on user input length and context
        # In a real implementation, this would be more sophisticated

        # Default values
        model_id = self.settings.default_llm_id
        voice_style = "presence"

        # Simple routing based on message length and keywords
        if len(user_input) > 500:
            # Longer messages might need a more capable model
            model_id = (
                self.settings.models.default
            )  # Assuming this is the more powerful model
        else:
            # Shorter messages can use the alternate model
            model_id = self.settings.models.alternate

        # Simple voice style selection based on content
        if "how" in user_input.lower() or "what" in user_input.lower():
            voice_style = "tactical"
        elif any(
            word in user_input.lower() for word in ["feel", "sad", "upset", "hurt"]
        ):
            voice_style = "whisper"
        elif any(
            word in user_input.lower() for word in ["inspire", "motivate", "challenge"]
        ):
            voice_style = "fire"
        else:
            voice_style = "presence"

        # Get model parameters for the selected voice style
        model_params = self.voice_styles.get(voice_style, self.voice_styles["presence"])

        logger.info(f"Routed to model: {model_id}, voice style: {voice_style}")

        return model_id, voice_style, model_params
