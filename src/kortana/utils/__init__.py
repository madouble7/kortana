# src/utils/__init__.py
"""
Utilities Package

Contains various utility functions and modules used throughout the Kor'tana system.
"""

from .text_analysis import (
    analyze_sentiment,
    count_tokens,
    detect_emphasis_all_caps,
    detect_keywords,
    ensure_dir_exists,
    extract_keywords,
    format_timestamp,
    identify_important_message_for_context,
    load_all_configs,
    load_json_file,
    safe_write_jsonl,
    summarize_text,
    validate_config,
)
from .text_encoding import (
    decode_base64_to_text,
    encode_file_to_base64,
    encode_text_to_base64,
)

# Temporarily simplified to troubleshoot import issues.
from .timestamp_utils import get_iso_timestamp

pass


# Explicitly list exports for clarity
__all__ = [
    "get_iso_timestamp",
    # from text_encoding.py
    "encode_text_to_base64",
    "decode_base64_to_text",
    "encode_file_to_base64",
    # from text_analysis.py
    "analyze_sentiment",
    "detect_emphasis_all_caps",
    "detect_keywords",
    "identify_important_message_for_context",
    "format_timestamp",
    "validate_config",
    "ensure_dir_exists",
    "load_json_file",
    "safe_write_jsonl",
    "load_all_configs",
    "count_tokens",
    "summarize_text",
    "extract_keywords",
]

# This file makes the utils directory a Python package.
