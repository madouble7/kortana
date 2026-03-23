"""
Gemini API Configuration with Auto-detection and Fallback
"""

import logging
import os

logger = logging.getLogger(__name__)

# Primary model. Google currently exposes 3.1 Flash-Lite via a preview ID.
DEFAULT_MODEL = "gemini-3.1-flash-lite-preview"

# Fallback models
FALLBACK_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-3.1-flash-lite-preview",
    "gemini-flash-lite-latest",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]


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
                if candidate in avail_set:
                    logger.info(
                        f"✅ Selected candidate model from fallback list: {candidate}"
                    )
                    return candidate

            # Otherwise pick first model that appears to support generation
            for m in models:
                supported = getattr(m, "supported_generation_methods", None)
                name = m.name.replace("models/", "") if m and m.name else None
                if supported and "generateContent" in supported and name:
                    logger.info(f"✅ Selected model supporting generateContent: {name}")
                    return name

            # Fall back to the first model if none match heuristics
            model_id = available[0]
            logger.info(f"✅ Selected first-discovered model: {model_id}")

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
        logger.info(f"Using GEMINI_MODEL from env: {model_from_env}")
        return model_from_env

    return get_available_model()
