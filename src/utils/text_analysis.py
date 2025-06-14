"""Text analysis utilities for Kortana.

This module provides text processing and analysis utilities
for content evaluation and linguistic processing.
"""
# C:\kortana\src\utils.py
# Purpose: Shared utility functions for Kor'tana project.
# Role: Reduces code duplication and provides common helpers for
#       timestamp formatting, configuration validation, file operations, etc.

import json
import logging  # Added for logging within utils
import os
from datetime import UTC, datetime  # Added timezone for consistency
from typing import Any

logger = logging.getLogger(__name__)


def format_timestamp(compact: bool = False, dt_object: datetime | None = None) -> str:
    """
    Returns the current UTC timestamp or a provided datetime object's timestamp
    in a human-readable or compact ISO format.

    Args:
        compact (bool): If True, returns a compact format (YYYYMMDD_HHMMSS).
                        Otherwise, returns "YYYY-MM-DD HH:M_M".
        dt_object (Optional[datetime]): A specific datetime object to format.
                                         If None, uses datetime.now(timezone.utc).
    Returns:
        str: The formatted timestamp string.
    """
    if dt_object is None:
        dt_object = datetime.now(UTC)
    elif dt_object.tzinfo is None:  # If naive, assume UTC
        dt_object = dt_object.replace(tzinfo=UTC)

    if compact:
        return dt_object.strftime("%Y%m%d_%H%M%S")
    else:
        return dt_object.strftime("%Y-%m-%d %H:%M")  # Standard readable format


def validate_config(config: dict, required_keys: list[str] | None = None) -> bool:
    """
    Basic schema check for required keys in a configuration dictionary.

    Args:
        config (dict): The configuration dictionary to validate.
        required_keys (Optional[List[str]]): A list of keys that must be present.
                                            If None, uses a default set for persona.json.
    Returns:
        bool: True if all required keys are present, False otherwise.
    """
    if required_keys is None:
        # Default check for top-level persona.json structure we're aiming for
        required_keys = ["persona", "core_prompt", "modes", "default_mode"]

    if not isinstance(config, dict):
        logger.error("Validation failed: Provided config is not a dictionary.")
        return False

    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        logger.warning(
            f"Config validation failed. Missing keys: {', '.join(missing_keys)}"
        )
        return False

    # Example: Check for nested structure in persona.json if that's the target
    if "persona" in required_keys and not isinstance(config.get("persona"), dict):
        logger.warning(
            "Config validation failed: 'persona' key does not map to a dictionary."
        )
        return False

    logger.debug("Config validation passed for specified keys.")
    return True


def ensure_dir_exists(path: str):
    """
    Ensures a directory exists before writing to a file within it.
    If the path is a file path, it ensures the parent directory exists.

    Args:
        path (str): The file path or directory path.
    """
    try:
        dir_to_check = os.path.dirname(path) if "." in os.path.basename(path) else path
        if (
            dir_to_check
        ):  # Ensure dirname is not empty (e.g. if path is just "file.txt")
            os.makedirs(dir_to_check, exist_ok=True)
            # logging.debug(f"Ensured directory exists: {dir_to_check}") # Can
            # be noisy
    except Exception as e:
        logger.error(f"Error ensuring directory exists for path '{path}': {e}")


def load_json_file(
    path: str,
) -> dict[Any, Any]:  # Changed to Dict[Any, Any] for more flexibility
    """
    Loads JSON from a file, returns empty dict on failure.
    Ensures directory exists before trying to read (though less critical for read).

    Args:
        path (str): The path to the JSON file.

    Returns:
        dict: The loaded JSON data as a dictionary, or an empty dictionary if loading fails.
    """
    # ensure_dir_exists(path) # Not strictly necessary for reading, but good
    # if creating default configs
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            # logging.debug(f"Successfully loaded JSON from: {path}")
            return data
    except FileNotFoundError:
        logger.warning(f"JSON file not found at: {path}. Returning empty dictionary.")
        return {}
    except json.JSONDecodeError:
        logger.error(
            f"Error decoding JSON from file: {path}. Returning empty dictionary."
        )
        return {}
    except Exception as e:
        logger.error(f"Unexpected error loading JSON from {path}: {e}")
        return {}


def safe_write_jsonl(path: str, data: dict):
    """
    Appends a JSON line to a .jsonl file safely, ensuring directory exists.

    Args:
        path (str): The path to the .jsonl file.
        data (dict): The dictionary to write as a JSON line.
    """
    ensure_dir_exists(path)
    try:
        with open(path, "a", encoding="utf-8") as f:
            json.dump(data, f)
            f.write("\n")
        # logging.debug(f"Safely wrote JSON line to: {path}") # Can be noisy
    except Exception as e:
        logger.error(f"Error safely writing JSON line to {path}: {e}")


def analyze_sentiment(text: str) -> dict[str, float]:
    """Placeholder for sentiment analysis."""
    # This would involve an NLP library or model
    # Mock implementation:
    sentiment = {"polarity": 0.0, "subjectivity": 0.0}
    text_lower = text.lower()
    if any(
        word in text_lower
        for word in ["happy", "good", "great", "positive", "love", "joy"]
    ):
        sentiment["polarity"] += 0.5
    if any(
        word in text_lower
        for word in ["sad", "bad", "terrible", "negative", "hate", "pain"]
    ):
        sentiment["polarity"] -= 0.5
    if any(word in text_lower for word in ["think", "believe", "feel", "opinion"]):
        sentiment["subjectivity"] += 0.5
    return sentiment


def detect_emphasis_all_caps(text: str, threshold_ratio: float = 0.6) -> bool:
    """Detects if text is mostly in ALL CAPS (potential emphasis)."""
    if not text or len(text) < 5:
        return False
    uppercase_count = sum(1 for char in text if "A" <= char <= "Z")
    alphabetic_count = sum(
        1 for char in text if "a" <= char <= "z" or "A" <= char <= "Z"
    )
    if alphabetic_count == 0:
        return False  # Avoid division by zero
    return uppercase_count / alphabetic_count >= threshold_ratio


def detect_keywords(text: str, keyword_sets: dict[str, list[str]]) -> list[str]:
    """
    Detects which predefined keyword categories are present in the text.

    Args:
        text (str): The text to analyze.
        keyword_sets (Dict[str, List[str]]): A dictionary where keys are category names
                                            and values are lists of keywords.

    Returns:
        List[str]: A list of category names found in the text.
    """
    detected = []
    text_lower = text.lower()
    for category, keywords in keyword_sets.items():
        if any(keyword in text_lower for keyword in keywords):
            detected.append(category)
    return detected


def identify_important_message_for_context(text: str) -> bool:
    """
    Placeholder for logic to identify messages important for long-term context.
    This could involve keyword matching, sentiment analysis, or a small classification model.

    Args:
        text (str): The message text to analyze.

    Returns:
        bool: True if the message is considered important for context, False otherwise.
    """
    # Mock implementation:
    text_lower = text.lower()
    important_keywords = [
        "decision",
        "plan",
        "goal",
        "important",
        "summary",
        "insight",
        "architecture",
    ]
    if any(keyword in text_lower for keyword in important_keywords):
        return True
    if detect_emphasis_all_caps(text):  # Often indicates importance
        return True
    # Add logic based on sentiment or specific phrasing
    return False


# Assume CONFIG_DIR is defined elsewhere or passed in, e.g., in ChatEngine
# CONFIG_DIR = os.path.join(os.path.dirname(__file__), '..', 'config')


def load_json_config(config_name: str, config_dir: str) -> dict[str, Any]:
    """
    Loads a specific JSON configuration file.

    Args:
        config_name (str): The name of the configuration file (without .json extension).
        config_dir (str): The directory where configuration files are located.

    Returns:
        Dict[str, Any]: The loaded configuration data.
    """
    config_path = os.path.join(config_dir, f"{config_name}.json")
    try:
        with open(config_path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Config file not found: {config_path}")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON in config file: {config_path}")
        return {}


def load_all_configs(config_dir: str) -> dict[str, Any]:
    """
    Loads all relevant JSON configuration files, including Sacred Trinity config.

    Args:
        config_dir (str): The directory where configuration files are located.

    Returns:
        Dict[str, Any]: A dictionary containing all loaded configuration data.
    """
    configs: dict[str, Any] = {}
    # List of config files to load
    config_files = [
        "persona",
        "identity",
        "models_config",
        "sacred_trinity_config",
    ]  # Added sacred_trinity_config

    for config_name in config_files:
        config_data = load_json_config(config_name, config_dir)
        if config_data:
            configs[config_name] = config_data

    logger.info(f"Loaded configurations: {list(configs.keys())}")
    return configs


def count_tokens(text: str) -> int:
    """
    Placeholder for counting tokens in text.

    Args:
        text (str): The input text string.

    Returns:
        int: The number of tokens (approximate).
    """
    # TODO: Implement actual token counting logic (e.g., using tiktoken or a similar library)
    # NOTE: Placeholder implementation. Replace with tiktoken or similar for accurate token counting.
    return len(text.split())  # Very basic word count as a placeholder


def summarize_text(text: str, max_tokens: int) -> str:
    """
    Placeholder for summarizing text.

    Args:
        text (str): The input text string.
        max_tokens (int): The maximum number of tokens for the summary.

    Returns:
        str: The summarized text.
    """
    # TODO: Implement actual text summarization logic
    # NOTE: Placeholder implementation. Integrate a real summarization model or API in the future.
    return text  # Return original text as a placeholder


def extract_keywords(text: str) -> list[str]:
    """
    Placeholder for extracting keywords from text.

    Args:
        text (str): The input text string.

    Returns:
        List[str]: A list of extracted keywords.
    """
    # TODO: Implement actual keyword extraction logic
    # NOTE: Placeholder implementation. Integrate a real keyword extraction method in the future.
    return []  # Return empty list as a placeholder
