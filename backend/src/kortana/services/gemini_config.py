"""
Gemini API Configuration with Auto-detection and Fallback
"""

import logging
import os

from src.kortana.model_lane_policy import describe_model_lane, model_allowed
from src.kortana.provider_model_defaults import (
    GEMINI_DEFAULT_MODEL,
    GEMINI_DISCOVERY_FALLBACK_MODELS,
)

logger = logging.getLogger(__name__)

DEFAULT_MODEL = GEMINI_DEFAULT_MODEL
FALLBACK_MODELS = GEMINI_DISCOVERY_FALLBACK_MODELS


def get_available_model() -> str:
    """
    Auto-detect available model for the configured API key.
    Falls back to DEFAULT_MODEL if detection fails.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.warning(f"GEMINI_API_KEY not set, using default: {DEFAULT_MODEL}")
        return DEFAULT_MODEL

    try:
        from google import genai

        logger.info("🔍 Detecting available Gemini models...")
        client = genai.Client(api_key=api_key)
        models = list(client.models.list())
        logger.info(f"📊 Found {len(models)} models available")

        if models:
            # Prefer known-safe fallback models first
            available = [m.name.replace("models/", "") for m in models if m and m.name]
            avail_set = set(available)

            for candidate in FALLBACK_MODELS:
                if candidate in avail_set and model_allowed(candidate):
                    logger.info(
                        "✅ Selected candidate model from fallback list: %s (%s lane)",
                        candidate,
                        describe_model_lane(candidate),
                    )
                    return candidate

            # Otherwise pick first model that appears to support generation
            for m in models:
                supported = getattr(m, "supported_generation_methods", None)
                name = m.name.replace("models/", "") if m and m.name else None
                if (
                    supported
                    and "generateContent" in supported
                    and name
                    and model_allowed(name)
                ):
                    logger.info(
                        "✅ Selected model supporting generateContent: %s (%s lane)",
                        name,
                        describe_model_lane(name),
                    )
                    return name

            # Fall back to the first model if none match heuristics
            for model_id in available:
                if model_allowed(model_id):
                    logger.info(
                        "✅ Selected first-discovered allowed model: %s (%s lane)",
                        model_id,
                        describe_model_lane(model_id),
                    )
                    return model_id

        logger.warning(f"No models found, using default: {DEFAULT_MODEL}")
        return DEFAULT_MODEL

    except ImportError:
        logger.error(f"google.genai not installed, using: {DEFAULT_MODEL}")
        return DEFAULT_MODEL
    except Exception as e:
        logger.error(f"Error detecting models: {str(e)}, using: {DEFAULT_MODEL}")
        return DEFAULT_MODEL


def get_model_name() -> str:
    """
    Get the configured model name with auto-detection and fallback.
    Checks GEMINI_MODEL env var first, then auto-detects.
    """
    model_from_env = os.getenv("GEMINI_MODEL")
    if model_from_env:
        if model_allowed(model_from_env):
            logger.info(
                "Using GEMINI_MODEL from env: %s (%s lane)",
                model_from_env,
                describe_model_lane(model_from_env),
            )
            return model_from_env
        logger.warning(
            "GEMINI_MODEL '%s' is unavailable under the active lane; "
            "falling back to an allowed Gemini model",
            model_from_env,
        )

    return get_available_model()


def get_preferred_model_name(preferred_model: str) -> str:
    """
    Return a preferred Gemini model when allowed, otherwise fall back
    to the active allowed Gemini selection strategy.
    """
    normalized = preferred_model.strip()
    if not normalized:
        return get_model_name()

    if model_allowed(normalized):
        logger.info(
            "Using preferred Gemini model: %s (%s lane)",
            normalized,
            describe_model_lane(normalized),
        )
        return normalized

    logger.warning(
        "Preferred Gemini model '%s' is unavailable under the active lane; "
        "falling back to an allowed Gemini model",
        normalized,
    )
    return get_model_name()
