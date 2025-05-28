# C:\kortana\src\utils.py
# Purpose: Shared utility functions for Kor'tana project.
# Role: Reduces code duplication and provides common helpers for
#       timestamp formatting, configuration validation, file operations, etc.

from datetime import datetime, timezone # Added timezone for consistency
import os
import json
import logging # Added for logging within utils
from typing import Optional, List, Dict, Any
import re
from textblob import TextBlob

logger = logging.getLogger(__name__)

def format_timestamp(compact: bool = False, dt_object: Optional[datetime] = None) -> str:
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
        dt_object = datetime.now(timezone.utc)
    elif dt_object.tzinfo is None: # If naive, assume UTC
        dt_object = dt_object.replace(tzinfo=timezone.utc)

    if compact:
        return dt_object.strftime("%Y%m%d_%H%M%S")
    else:
        return dt_object.strftime("%Y-%m-%d %H:%M") # Standard readable format

def validate_config(config: dict, required_keys: Optional[List[str]] = None) -> bool:
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
        logger.warning(f"Config validation failed. Missing keys: {', '.join(missing_keys)}")
        return False
    
    # Example: Check for nested structure in persona.json if that's the target
    if "persona" in required_keys and not isinstance(config.get("persona"), dict):
        logger.warning("Config validation failed: 'persona' key does not map to a dictionary.")
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
        dir_to_check = os.path.dirname(path) if '.' in os.path.basename(path) else path
        if dir_to_check: # Ensure dirname is not empty (e.g. if path is just "file.txt")
            os.makedirs(dir_to_check, exist_ok=True)
            # logging.debug(f"Ensured directory exists: {dir_to_check}") # Can be noisy
    except Exception as e:
        logger.error(f"Error ensuring directory exists for path '{path}': {e}")

def load_json_file(path: str) -> Dict[Any, Any]: # Changed to Dict[Any, Any] for more flexibility
    """
    Loads JSON from a file, returns empty dict on failure.
    Ensures directory exists before trying to read (though less critical for read).

    Args:
        path (str): The path to the JSON file.

    Returns:
        dict: The loaded JSON data as a dictionary, or an empty dictionary if loading fails.
    """
    # ensure_dir_exists(path) # Not strictly necessary for reading, but good if creating default configs
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # logging.debug(f"Successfully loaded JSON from: {path}")
            return data
    except FileNotFoundError:
        logger.warning(f"JSON file not found at: {path}. Returning empty dictionary.")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from file: {path}. Returning empty dictionary.")
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
        with open(path, 'a', encoding='utf-8') as f:
            json.dump(data, f)
            f.write("\n")
        # logging.debug(f"Safely wrote JSON line to: {path}") # Can be noisy
    except Exception as e:
        logger.error(f"Error safely writing JSON line to {path}: {e}")

def analyze_sentiment(text: str) -> Dict[str, float]:
    """Analyze sentiment of text input using TextBlob.

    Args:
        text: Text to analyze

    Returns:
        Dict with polarity (-1 to 1) and subjectivity (0 to 1)
    """
    if not text:
        return {"polarity": 0.0, "subjectivity": 0.0}
    try:
        blob = TextBlob(text)
        return {
            "polarity": blob.sentiment.polarity,
            "subjectivity": blob.sentiment.subjectivity
        }
    except Exception as e:
        logging.error(f"TextBlob sentiment analysis failed: {e}", exc_info=True)
        return {"polarity": 0.0, "subjectivity": 0.0}

def detect_emphasis_all_caps(text: str, threshold_ratio: float = 0.6, min_length: int = 5) -> bool:
    """Detect if text contains significant emphasis (ALL CAPS)."""
    if len(text) < min_length:
        return False
    alpha_chars = [char for char in text if char.isalpha()]
    if not alpha_chars:
        return False
    caps_count = sum(1 for char in alpha_chars if char.isupper())
    caps_ratio = caps_count / len(alpha_chars)
    return caps_ratio >= threshold_ratio

def detect_keywords(text: str, keyword_sets: Dict[str, List[str]]) -> List[str]:
    """Detect presence of keywords from predefined sets."""
    text_lower = text.lower()
    found_categories = []
    for category, keywords in keyword_sets.items():
        if any(re.search(r'\\b' + re.escape(keyword.lower()) + r'\\b', text_lower) for keyword in keywords):
            found_categories.append(category)
    return found_categories

def identify_important_message_for_context(content: str, important_markers: Optional[List[str]] = None) -> bool:
    """Determine if a message is important for context preservation based on markers."""
    if important_markers is None:
        important_markers = [
            r'\\bremember this\\b', r'\\bimportant to recall\\b', r'\\bnote this down\\b',
            r'\\bkey point\\b', r'\\bcrucial detail\\b', r'\\balways keep in mind\\b',
            r'\\bmy core belief\\b', r'\\ba sacred moment for me was\\b',
            r'significant event'
        ]
    return any(re.search(pattern, content.lower()) for pattern in important_markers)

if __name__ == "__main__":
    # Example usage for testing utils.py directly
    print("Testing utils.py...")
    
    # Test format_timestamp
    print(f"Formatted Timestamp (default): {format_timestamp()}")
    print(f"Formatted Timestamp (compact): {format_timestamp(compact=True)}")
    specific_time = datetime(2025, 1, 1, 10, 30, 0, tzinfo=timezone.utc)
    print(f"Formatted Timestamp (specific): {format_timestamp(dt_object=specific_time)}")

    # Test validate_config
    valid_persona_config = {"persona": {}, "core_prompt": "test", "modes": {}, "default_mode": "default"}
    invalid_persona_config = {"core_prompt": "test"}
    print(f"Validating good persona config: {validate_config(valid_persona_config)}")
    print(f"Validating bad persona config: {validate_config(invalid_persona_config)}")

    # Test ensure_dir_exists and safe_write_jsonl
    test_log_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'test_logs')
    test_log_file = os.path.join(test_log_dir, 'util_test.jsonl')
    
    print(f"Attempting to ensure directory for: {test_log_file}")
    ensure_dir_exists(test_log_file) # Should create data/test_logs if not exists
    
    test_data_entry = {"event": "util_test", "timestamp": format_timestamp(compact=True), "message": "Testing safe_write_jsonl"}
    print(f"Attempting to write to: {test_log_file}")
    safe_write_jsonl(test_log_file, test_data_entry)
    
    # Test load_json_file (example with a dummy config it might create)
    # This part is more for illustration as we'd typically load existing configs
    dummy_config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'dummy_test_config.json')
    # ensure_dir_exists(dummy_config_path) # ensure config dir exists
    # with open(dummy_config_path, 'w') as f_dummy:
    #     json.dump({"sample_key": "sample_value"}, f_dummy)
    # loaded_dummy_config = load_json_file(dummy_config_path)
    # print(f"Loaded dummy config: {loaded_dummy_config}")
    # if os.path.exists(dummy_config_path): os.remove(dummy_config_path) # Clean up

    print("utils.py tests complete. Check data/test_logs/ for util_test.jsonl.")

