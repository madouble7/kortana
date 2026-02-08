"""
Text analysis utilities for Kortana.
This module provides functions for text processing, analysis, and manipulation
to support Kor'tana's natural language understanding capabilities.
"""

import json
import logging
import os
import re
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


def format_timestamp(
    compact: bool = False, dt_object: datetime | None = None
) -> str:
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


def analyze_sentiment(text: str) -> str:
    """
    Simple sentiment analysis of text.

    Args:
        text: The text to analyze.

    Returns:
        Sentiment assessment ("positive", "negative", or "neutral").
    """
    # This is a simplistic implementation
    positive_words = [
        "good",
        "great",
        "excellent",
        "happy",
        "joy",
        "love",
        "like",
        "thanks",
    ]
    negative_words = [
        "bad",
        "awful",
        "terrible",
        "sad",
        "hate",
        "dislike",
        "angry",
        "annoyed",
    ]

    text_lower = text.lower()

    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)

    if positive_count > negative_count:
        return "positive"
    elif negative_count > positive_count:
        return "negative"
    else:
        return "neutral"


def detect_emphasis_all_caps(text: str) -> list[str]:
    """
    Detect words in ALL CAPS which indicate emphasis.

    Args:
        text: The text to analyze.

    Returns:
        List of words in all caps.
    """
    # Find words of 3+ characters in all caps
    caps_words = re.findall(r"\b[A-Z]{3,}\b", text)
    return caps_words


def detect_keywords(text: str) -> list[str]:
    """
    Extract potential keywords from text.

    Args:
        text: The text to analyze.

    Returns:
        List of potential keywords.
    """
    # This is a simplistic implementation
    # In a real system, this would use NLP techniques like TF-IDF
    stop_words = [
        "the",
        "and",
        "a",
        "in",
        "to",
        "of",
        "is",
        "for",
        "on",
        "that",
        "this",
    ]

    words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    keywords = [word for word in words if word not in stop_words]

    # Return unique keywords
    return list(set(keywords))


def identify_important_message_for_context(text: str) -> bool:
    """
    Determine if a message is important to remember for future context.

    Args:
        text: The text to analyze.

    Returns:
        True if the message is deemed important, False otherwise.
    """
    # This is a simplistic implementation
    # In a real system, this would use more sophisticated analysis
    important_indicators = [
        "remember this",
        "important",
        "critical",
        "key point",
        "don't forget",
        "note this",
    ]

    text_lower = text.lower()

    # Check for indicators
    for indicator in important_indicators:
        if indicator in text_lower:
            return True

    # Length-based heuristic (longer messages might be more important)
    if len(text) > 200:
        return True

    # Consider question-like messages somewhat important
    if "?" in text:
        return True

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
    Count approximate tokens in text using a simple heuristic.
    
    This uses a simple word-based approximation since tiktoken may not be available.
    For more accurate counting, integrate tiktoken library when available.

    Args:
        text (str): The input text string.

    Returns:
        int: The approximate number of tokens.
    """
    # Use a simple heuristic: ~1.3 tokens per word on average for English text
    # This is a reasonable approximation for most use cases
    words = text.split()
    
    # Count punctuation and special characters as additional tokens
    punctuation_count = sum(1 for char in text if char in ".,!?;:()[]{}\"'")
    
    # Approximate token count: words + 30% + punctuation/2
    approximate_tokens = int(len(words) * 1.3 + punctuation_count * 0.5)
    
    return approximate_tokens


def summarize_text(text: str, max_tokens: int) -> str:
    """
    Summarize text by truncating to approximate token limit with sentence boundaries.

    Args:
        text (str): The input text string.
        max_tokens (int): The maximum number of tokens for the summary.

    Returns:
        str: The summarized text.
    """
    # If text is already short enough, return as-is
    current_tokens = count_tokens(text)
    if current_tokens <= max_tokens:
        return text
    
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # Build summary by adding sentences until we reach the limit
    summary_parts = []
    token_count = 0
    
    for sentence in sentences:
        sentence_tokens = count_tokens(sentence)
        if token_count + sentence_tokens <= max_tokens:
            summary_parts.append(sentence)
            token_count += sentence_tokens
        else:
            # If we haven't added any sentences yet, truncate the first sentence
            if not summary_parts:
                words = sentence.split()
                # Estimate words per token (~0.77 words per token)
                target_words = int(max_tokens * 0.77)
                summary_parts.append(' '.join(words[:target_words]) + '...')
            break
    
    summary = ' '.join(summary_parts)
    
    # Add ellipsis if we truncated
    if summary != text and not summary.endswith('...'):
        summary += '...'
    
    return summary


def extract_keywords(text: str, max_keywords: int = 10) -> list[str]:
    """
    Extract keywords from text using frequency analysis with stop word filtering.

    Args:
        text (str): The input text string.
        max_keywords (int): Maximum number of keywords to return.

    Returns:
        List[str]: A list of extracted keywords.
    """
    # Expanded stop words list for better filtering
    stop_words = {
        "the", "and", "a", "an", "in", "to", "of", "is", "for", "on", "that", 
        "this", "with", "at", "from", "by", "as", "be", "are", "was", "were",
        "been", "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "can", "or", "but", "if",
        "then", "else", "when", "where", "who", "which", "what", "how", "why",
        "there", "their", "they", "them", "these", "those", "it", "its", "he",
        "she", "him", "her", "his", "your", "you", "we", "us", "our", "my",
        "me", "i", "am"
    }
    
    # Extract words (alphanumeric, 3+ characters)
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    # Filter out stop words
    meaningful_words = [word for word in words if word not in stop_words]
    
    # Count frequency
    from collections import Counter
    word_freq = Counter(meaningful_words)
    
    # Get most common keywords
    keywords = [word for word, _ in word_freq.most_common(max_keywords)]
    
    return keywords
