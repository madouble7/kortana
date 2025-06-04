#!/usr/bin/env python3
"""
Kor'tana Brain Utilities Module
===============================
Helper functions and utilities extracted from the main brain module
to improve maintainability and reduce complexity.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

# Module-level logger
logger = logging.getLogger(__name__)


def load_json_config(path: str) -> Dict:
    """Load JSON configuration from file with graceful error handling.

    Args:
        path: Path to the JSON configuration file

    Returns:
        Dictionary containing the configuration data, empty dict if error
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(
            f"config file not found: {path} — the ember searches, but does not shame."
        )
        return {}
    except json.JSONDecodeError:
        logger.error(
            f"error decoding json: {path} — the fire stumbles, but does not go out."
        )
        return {}


def append_to_memory_journal(memory_journal_path: str, entry: Dict[str, Any]) -> None:
    """Append memory entry to the journal file.

    Args:
        memory_journal_path: Path to the memory journal file
        entry: Memory entry dictionary to append
    """
    try:
        with open(memory_journal_path, "a", encoding="utf-8") as f:
            json.dump(entry, f)
            f.write("\n")
    except Exception as e:
        logger.error(
            f"Error writing to memory journal {memory_journal_path}: {e} "
            "— the ember flickers, but does not die."
        )


def log_reasoning_content(response: str, reasoning_content: str) -> None:
    """Log reasoning content for debugging purposes.

    Args:
        response: The model response identifier
        reasoning_content: The reasoning content to log
    """
    try:
        logger.debug(f"Reasoning content for model {response}: {reasoning_content}")
        # Additional logging could be added here
        # E.g., write to REASONING_LOG_PATH if needed
    except Exception as e:
        logger.error(f"Reasoning log error: {e}")


def gentle_log_init() -> None:
    """Initialize logging configuration for Kor'tana's gentle consciousness.

    This function sets up the basic logging configuration with appropriate
    formatting for the Kor'tana system.
    """
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logging.info("kor'tana's fire: logging initialized — the ember is awake.")


def format_memory_entries_by_type(memories_by_type: Dict[str, List[Dict]]) -> List[str]:
    """Format memory entries by type for system prompt inclusion.

    # TODO: This function has high complexity and should be refactored in next phase

    Args:
        memories_by_type: Dictionary mapping memory types to lists of memory entries

    Returns:
        List of formatted strings for inclusion in system prompts
    """
    system_parts = []

    # Add decisions - critical choices made
    if "decision" in memories_by_type:
        system_parts.append("\n🎯 Key Decisions Made:")
        # Sort by timestamp descending and take the most recent
        for entry in sorted(
            memories_by_type["decision"],
            key=lambda x: x.get("timestamp", ""),
            reverse=True,
        )[:5]:  # Most recent 5
            # Include content, tags, and date if available
            tags = ", ".join(entry.get("tags", []))
            timestamp_str = entry.get("timestamp", "")
            date_str = f" ({timestamp_str.split('T')[0]})" if timestamp_str else ""
            tag_str = f" [{tags}]" if tags else ""
            system_parts.append(
                f"- {entry.get('content', '[empty]')}{tag_str}{date_str}"
            )

    # Add implementation notes - technical context
    if "implementation_note" in memories_by_type:
        system_parts.append("\n🛠️ Implementation Context:")
        # Sort by timestamp descending and take the most recent
        for entry in sorted(
            memories_by_type["implementation_note"],
            key=lambda x: x.get("timestamp", ""),
            reverse=True,
        )[:3]:  # Most recent 3
            # Include content, component, priority, and date if available
            component = entry.get("component", "")
            priority = entry.get("priority", "")
            timestamp_str = entry.get("timestamp", "")
            date_str = f" ({timestamp_str.split('T')[0]})" if timestamp_str else ""
            component_str = f" [{component}]" if component else ""
            priority_str = f" (Priority: {priority})" if priority else ""
            system_parts.append(
                f"- {entry.get('content', '[empty]')}{component_str}{priority_str}{date_str}"
            )

    # Add project insights - broader understanding
    if "project_insight" in memories_by_type:
        system_parts.append("\n💡 Key Project Insights:")
        # Sort by timestamp descending and take the most recent
        for entry in sorted(
            memories_by_type["project_insight"],
            key=lambda x: x.get("timestamp", ""),
            reverse=True,
        )[:3]:  # Most recent 3
            # Include content, impact, and date if available
            impact = entry.get("impact", "")
            timestamp_str = entry.get("timestamp", "")
            date_str = f" ({timestamp_str.split('T')[0]})" if timestamp_str else ""
            impact_str = f" (Impact: {impact})" if impact else ""
            system_parts.append(
                f"- {entry.get('content', '[empty]')}{impact_str}{date_str}"
            )

    # Add conversation summaries - conversational continuity
    if "conversation_summary" in memories_by_type:
        system_parts.append("\n💬 Recent Conversation Summaries:")
        # Sort by timestamp descending and take the most recent
        for entry in sorted(
            memories_by_type["conversation_summary"],
            key=lambda x: x.get("timestamp", ""),
            reverse=True,
        )[:2]:  # Most recent 2
            # Include content and date if available
            timestamp_str = entry.get("timestamp", "")
            date_str = f" ({timestamp_str.split('T')[0]})" if timestamp_str else ""
            system_parts.append(f"- {entry.get('content', '[empty]')}{date_str}")

    # Handle any other memory types not explicitly formatted
    other_memories = [
        entry
        for type, memories in memories_by_type.items()
        for entry in memories
        if type
        not in [
            "decision",
            "implementation_note",
            "project_insight",
            "conversation_summary",
        ]
    ]
    if other_memories:
        system_parts.append("\n🧩 Other Project Memories:")
        # Sort by timestamp descending and take the most recent
        for entry in sorted(
            other_memories, key=lambda x: x.get("timestamp", ""), reverse=True
        )[:5]:  # Most recent 5 of other types
            timestamp_str = entry.get("timestamp", "")
            date_str = f" ({timestamp_str.split('T')[0]})" if timestamp_str else ""
            system_parts.append(
                f"- [{entry.get('type', 'unknown')}] "
                f"{entry.get('content', '[empty]')}{date_str}"
            )

    return system_parts


def ensure_directories_exist(*paths: str) -> None:
    """Ensure that directories for the given file paths exist.

    Args:
        *paths: Variable number of file paths to ensure directories exist for
    """
    for path in paths:
        os.makedirs(os.path.dirname(path), exist_ok=True)


def create_timestamp() -> str:
    """Create a standardized timestamp string.

    Returns:
        ISO format timestamp string with timezone
    """
    return datetime.now(timezone.utc).isoformat()


def validate_memory_entry(entry: Dict[str, Any]) -> bool:
    """Validate that a memory entry has required fields.

    Args:
        entry: Memory entry dictionary to validate

    Returns:
        True if entry is valid, False otherwise
    """
    required_fields = ["content", "type"]
    return all(field in entry for field in required_fields)


def sanitize_user_input(user_input: str) -> str:
    """Sanitize and normalize user input.

    Args:
        user_input: Raw user input string

    Returns:
        Sanitized and normalized input string
    """
    if not user_input:
        return ""

    # Strip whitespace and normalize
    sanitized = user_input.strip()

    # Basic safety checks - remove null bytes
    sanitized = sanitized.replace("\x00", "")

    return sanitized


def extract_keywords_from_text(text: str, max_keywords: int = 10) -> List[str]:
    """Extract key terms from text for memory tagging.

    # TODO: This function could benefit from NLP library integration in next phase

    Args:
        text: Input text to extract keywords from
        max_keywords: Maximum number of keywords to return

    Returns:
        List of extracted keywords
    """
    if not text:
        return []

    # Simple keyword extraction - split on common delimiters
    words = text.lower().split()

    # Filter out common stop words (basic set)
    stop_words = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "is",
        "are",
        "was",
        "were",
        "be",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "can",
        "this",
        "that",
        "these",
        "those",
        "i",
        "you",
        "he",
        "she",
        "it",
        "we",
        "they",
    }

    keywords = [word for word in words if word not in stop_words and len(word) > 2]

    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for keyword in keywords:
        if keyword not in seen:
            seen.add(keyword)
            unique_keywords.append(keyword)

    return unique_keywords[:max_keywords]
