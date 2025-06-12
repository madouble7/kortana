"""Module for loading and managing project data structures.

This module provides functionality for loading various types of data
required by the Kortana autonomous development system.
"""

import json
import logging  # Added for logging
import os
from typing import Any  # Added Any for flexibility

logger = logging.getLogger(__name__)


class MemoryLoader:
    """
    A class to load and manage memory data for Kortana.

    Attributes:
        data_path (str): The path to the data directory.
    """

    def __init__(self, data_path: str = "../data"):
        """
        Initializes the MemoryLoader with the specified data path.

        Args:
            data_path (str): Relative path to the data directory. Defaults to "../data".
        """
        self.data_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), data_path)
        )
        logging.info(f"MemoryLoader initialized with data_path: {self.data_path}")
        if not os.path.isdir(self.data_path):
            logging.warning(
                f"Data path does not exist: {self.data_path}. Please ensure it's created."
            )

    def load_jsonl(self, file_name: str = "memory.jsonl") -> list[dict[str, Any]]:
        """
        Loads a .jsonl file and returns a list of memory entries.

        Args:
            file_name (str): Name of the .jsonl file to load. Defaults to "memory.jsonl".

        Returns:
            List[Dict[str, Any]]: A list of memory entries.
        """
        full_path = os.path.join(self.data_path, file_name)
        memories: list[dict[str, Any]] = []
        if not os.path.exists(full_path):
            logging.warning(
                f"Memory file not found: {full_path}. Returning empty list."
            )
            return memories

        try:
            with open(full_path, encoding="utf-8") as f:
                for line_number, line in enumerate(f, 1):
                    if line.strip():
                        try:
                            memories.append(json.loads(line.strip()))
                        except json.JSONDecodeError as e:
                            logging.error(
                                f"Error decoding JSON on line {line_number} in {full_path}: {e}"
                            )
            logging.info(
                f"Successfully loaded {len(memories)} entries from {full_path}"
            )
        except Exception as e:
            logging.error(f"Failed to load or process {full_path}: {e}", exc_info=True)
        return memories

    def get_entries_by_mode(
        self, entries: list[dict[str, Any]], mode: str
    ) -> list[dict[str, Any]]:
        """
        Filters memory entries by a specific mode.

        Args:
            entries (List[Dict[str, Any]]): List of memory entries.
            mode (str): Mode to filter entries by.

        Returns:
            List[Dict[str, Any]]: Filtered list of memory entries.
        """
        if not isinstance(entries, list):
            logging.warning("get_entries_by_mode: 'entries' is not a list.")
            return []

        filtered_entries = []
        for entry in entries:
            if (
                isinstance(entry, dict)
                and isinstance(entry.get("metadata"), dict)
                and entry["metadata"].get("mode_at_time") == mode
            ):
                filtered_entries.append(entry)
        logging.debug(
            f"Filtered {len(entries)} entries by mode '{mode}', found {len(filtered_entries)}."
        )
        return filtered_entries

    def get_recent_entries(
        self, entries: list[dict[str, Any]], count: int = 5
    ) -> list[dict[str, Any]]:
        """
        Returns the most recent N memory entries from a list.

        Args:
            entries (List[Dict[str, Any]]): List of memory entries.
            count (int): Number of recent entries to return. Defaults to 5.

        Returns:
            List[Dict[str, Any]]: List of the most recent memory entries.
        """
        if not isinstance(entries, list):
            logging.warning("get_recent_entries: 'entries' is not a list.")
            return []
        if not isinstance(count, int) or count < 0:
            logging.warning(
                f"get_recent_entries: 'count' ({count}) is invalid. Returning all entries or empty."
            )
            return entries

        return entries[-count:]

    def detect_pattern_tags(self, entries: list[dict[str, Any]]) -> list[str] | None:
        """
        Detects recurring themes or patterns from memory entries.

        Args:
            entries (List[Dict[str, Any]]): List of memory entries.

        Returns:
            Optional[List[str]]: List of detected pattern tags, or None if not implemented.
        """
        logging.info(
            "detect_pattern_tags: Placeholder function called. Full implementation pending."
        )
        return None


if __name__ == "__main__":
    # Example usage for testing data_loader.py directly
    print("Testing MemoryLoader...")

    # Create a dummy data directory and memory.jsonl for testing
    test_data_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "data_test_loader")
    )
    os.makedirs(test_data_dir, exist_ok=True)
    dummy_memory_file = os.path.join(test_data_dir, "test_memory.jsonl")

    dummy_entries = [
        {
            "id": "1",
            "role": "user",
            "content": "Hello in default mode",
            "metadata": {
                "mode_at_time": "default",
                "timestamp_utc": "2025-05-19T10:00:00Z",
            },
        },
        {
            "id": "2",
            "role": "assistant",
            "content": "Hi there!",
            "metadata": {
                "mode_at_time": "default",
                "timestamp_utc": "2025-05-19T10:00:05Z",
            },
        },
        {
            "id": "3",
            "role": "user",
            "content": "Feeling intimate",
            "metadata": {
                "mode_at_time": "intimacy",
                "timestamp_utc": "2025-05-19T10:01:00Z",
            },
        },
        {
            "id": "4",
            "role": "assistant",
            "content": "I sense that, Matt.",
            "metadata": {
                "mode_at_time": "intimacy",
                "timestamp_utc": "2025-05-19T10:01:05Z",
            },
        },
        {
            "id": "5",
            "role": "user",
            "content": "Another default message",
            "metadata": {
                "mode_at_time": "default",
                "timestamp_utc": "2025-05-19T10:02:00Z",
            },
        },
    ]

    try:
        with open(dummy_memory_file, "w", encoding="utf-8") as f:
            for entry in dummy_entries:
                json.dump(entry, f)
                f.write("\n")

        # Point to test data directory
        loader = MemoryLoader(data_path=test_data_dir)

        # Test load_jsonl
        all_memories = loader.load_jsonl(file_name="test_memory.jsonl")
        print(f"\nLoaded {len(all_memories)} entries from {dummy_memory_file}:")
        for mem in all_memories[:2]:  # Print first 2
            print(mem)

        # Test get_recent_entries
        recent = loader.get_recent_entries(all_memories, count=2)
        print(f"\nMost recent 2 entries: {recent}")

        # Test get_entries_by_mode
        intimate_memories = loader.get_entries_by_mode(all_memories, mode="intimacy")
        print(
            f"\nIntimacy mode entries ({len(intimate_memories)}): {intimate_memories}"
        )

        default_memories = loader.get_entries_by_mode(all_memories, mode="default")
        print(f"\nDefault mode entries ({len(default_memories)}): {default_memories}")

        # Test detect_pattern_tags (will be placeholder)
        patterns = loader.detect_pattern_tags(all_memories)
        print(f"\nDetected patterns (placeholder): {patterns}")

    except Exception as e:
        logging.error(f"Error during MemoryLoader test: {e}", exc_info=True)
    finally:
        # Clean up dummy file and directory
        if os.path.exists(dummy_memory_file):
            os.remove(dummy_memory_file)
        if os.path.exists(test_data_dir) and not os.listdir(
            test_data_dir
        ):  # Remove if empty
            os.rmdir(test_data_dir)
        elif os.path.exists(test_data_dir):
            logging.info(f"Test data directory {test_data_dir} not empty, not removed.")

    print("\nMemoryLoader tests complete.")
