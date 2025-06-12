"""
Core memory system for Kortana.
This module provides functionality for loading, saving, and managing memory entries
stored in JSONL format for long-term retention of important information.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import UTC, datetime
from typing import Any

# Ensure src is in sys.path for imports if this script is run standalone
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Adjust the MEMORY_FILE path to be relative to the project root
# assuming this file is in src/core/
PROJECT_MEMORY_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "data",
    "project_memory.jsonl",  # Corrected path
)


def load_memory() -> list[dict[str, Any]]:
    """Loads memory entries from the project memory file."""
    memory_entries: list[dict[str, Any]] = []
    # Construct the absolute path to the memory file
    abs_memory_path = os.path.abspath(PROJECT_MEMORY_PATH)

    print(f"[DEBUG] Attempting to load memory from: {abs_memory_path}")

    if not os.path.exists(abs_memory_path):  # pragma: no cover
        print(
            f"[DEBUG] Memory file not found at {abs_memory_path}. Returning empty list."
        )
        # print(f"Project memory file not found: {abs_memory_path}") # Avoid
        # printing in library function
        return memory_entries

    print(f"[DEBUG] Memory file found at {abs_memory_path}. Attempting to read.")

    try:
        with open(abs_memory_path, encoding="utf-8") as f:
            print("[DEBUG] File opened successfully. Reading line by line...")
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                print(f"[DEBUG] Reading line {line_num}: {line[:50]}...")
                try:
                    entry = json.loads(line)
                    memory_entries.append(entry)
                    print(f"[DEBUG] Successfully parsed line {line_num}.")
                except json.JSONDecodeError as e:
                    print(
                        f"[ERROR] JSON decoding error in {abs_memory_path} at line {line_num}: {e} - Line: {line[:100]}..."
                    )  # Keep error printing for file issues
                    # Decide how to handle errors - skip line, log, etc. #
                    # pragma: no cover
                    pass  # For now, just skip the problematic line # pragma: no cover
            print("[DEBUG] Finished reading file.")
    except OSError as e:  # pragma: no cover
        print(f"[ERROR] IO Error reading project memory file {abs_memory_path}: {e}")
        print("[DEBUG] Returning empty list due to IO Error.")

    print(f"[DEBUG] load_memory finished. Loaded {len(memory_entries)} entries.")
    return memory_entries


def save_memory(entry: dict) -> bool:
    """Appends a new entry to the project memory file (project_memory.jsonl)."""
    abs_memory_path = os.path.abspath(PROJECT_MEMORY_PATH)

    try:
        # Ensure the directory exists before writing
        os.makedirs(os.path.dirname(abs_memory_path), exist_ok=True)
        with open(abs_memory_path, "a", encoding="utf-8") as f:
            json.dump(entry, f)
            f.write("\n")
        return True  # pragma: no cover
    except OSError as e:
        print(
            f"Error writing to project memory file {abs_memory_path}: {e}"
        )  # Keep error printing for file issues
        return False


# --- Helper functions for specific memory types ---


def save_decision(content: str) -> None:
    """Saves a project decision to memory."""
    entry = {
        "type": "decision",
        "timestamp": datetime.now(UTC).isoformat(),
        "content": content,
    }
    save_memory(entry)


def save_context_summary(content: str) -> None:
    """Saves a context summary to memory."""
    entry = {
        "type": "context_summary",
        "timestamp": datetime.now(UTC).isoformat(),
        "content": content,
    }
    save_memory(entry)


def save_implementation_note(content: str) -> None:
    """Saves an implementation note to memory."""
    entry = {
        "type": "implementation_note",
        "timestamp": datetime.now(UTC).isoformat(),
        "content": content,
    }
    save_memory(entry)


def save_project_insight(content: str) -> None:
    """Saves a project insight to memory."""
    entry = {
        "type": "project_insight",
        "timestamp": datetime.now(UTC).isoformat(),
        "content": content,
    }
    save_memory(entry)


# --- Retrieval helper functions ---


def get_memory_by_type(memory_type: str) -> list[dict[str, Any]]:
    """Retrieves all memory entries of a specific type."""
    all_memories = load_memory()
    # Filter by type and return a new list
    return [entry for entry in all_memories if entry.get("type") == memory_type]


def get_recent_memories_by_type(
    memory_type: str, limit: int = 5
) -> list[dict[str, Any]]:
    """Retrieves the most recent memory entries of a specific type."""
    memories_of_type = get_memory_by_type(memory_type)
    # Return the last 'limit' entries (most recent)
    return memories_of_type[-limit:]


# Example usage (for testing):
# if __name__ == "__main__":
#     # Add a sample entry
#     # save_decision("Decided to use project_memory.jsonl for project state.")

#     # Load and print memories
#     # decisions = get_memory_by_type("decision")
#     # print("Decisions:", decisions)

#     # recent_summaries = get_recent_memories_by_type("context_summary", limit=2)
#     # print("Recent Summaries:", recent_summaries)


class MemoryManager:
    """
    Dummy MemoryManager to unblock GoalManager.
    Replace with actual implementation later.
    """
    def __init__(self, db_session = None): # db_session is a placeholder if needed by a real one
        self.entries: list[dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)
        self.logger.info("Dummy MemoryManager initialized.")

    async def store_entry(self, entry: dict[str, Any]) -> None:
        self.logger.info(f"Dummy MemoryManager: Storing entry: {entry.get('role', 'N/A')}")
        self.entries.append(entry)
        # In a real scenario, this would interact with a database or file store.
        await asyncio.sleep(0) # Simulate async operation

    async def search_entries(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        self.logger.info(f"Dummy MemoryManager: Searching entries with query: {query}, limit: {limit}")
        # This is a very naive search, replace with actual search logic.
        results = [e for e in self.entries if query.lower() in str(e).lower()]
        await asyncio.sleep(0) # Simulate async operation
        return results[:limit]

    async def delete_entries(self, query: str) -> None:
        self.logger.info(f"Dummy MemoryManager: Deleting entries with query: {query}")
        # This is a very naive delete, replace with actual delete logic.
        self.entries = [e for e in self.entries if query.lower() not in str(e).lower()]
        await asyncio.sleep(0) # Simulate async operation

    async def get_all_entries(self) -> list[dict[str, Any]]:
        self.logger.info("Dummy MemoryManager: Getting all entries")
        await asyncio.sleep(0) # Simulate async operation
        return self.entries
