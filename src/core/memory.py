import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List

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


def load_memory() -> List[Dict[str, Any]]:
    """Loads memory entries from the project memory file."""
    memory_entries: List[Dict[str, Any]] = []
    # Construct the absolute path to the memory file
    abs_memory_path = os.path.abspath(PROJECT_MEMORY_PATH)

    if not os.path.exists(abs_memory_path):  # pragma: no cover
        # print(f"Project memory file not found: {abs_memory_path}") # Avoid
        # printing in library function
        return memory_entries

    try:
        with open(abs_memory_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                try:
                    entry = json.loads(line)
                    memory_entries.append(entry)
                except json.JSONDecodeError as e:
                    print(
                        f"Error decoding JSON in {abs_memory_path}: {e} - Line: {line[:100]}..."
                    )  # Keep error printing for file issues
                    # Decide how to handle errors - skip line, log, etc. #
                    # pragma: no cover
                    pass  # For now, just skip the problematic line # pragma: no cover
    except IOError as e:  # pragma: no cover
        print(f"Error reading project memory file {abs_memory_path}: {e}")

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
    except IOError as e:
        print(
            f"Error writing to project memory file {abs_memory_path}: {e}"
        )  # Keep error printing for file issues
        return False


# --- Helper functions for specific memory types ---


def save_decision(content: str) -> None:
    """Saves a project decision to memory."""
    entry = {
        "type": "decision",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "content": content,
    }
    save_memory(entry)


def save_context_summary(content: str) -> None:
    """Saves a context summary to memory."""
    entry = {
        "type": "context_summary",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "content": content,
    }
    save_memory(entry)


def save_implementation_note(content: str) -> None:
    """Saves an implementation note to memory."""
    entry = {
        "type": "implementation_note",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "content": content,
    }
    save_memory(entry)


def save_project_insight(content: str) -> None:
    """Saves a project insight to memory."""
    entry = {
        "type": "project_insight",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "content": content,
    }
    save_memory(entry)


# --- Retrieval helper functions ---


def get_memory_by_type(memory_type: str) -> List[Dict[str, Any]]:
    """Retrieves all memory entries of a specific type."""
    all_memories = load_memory()
    # Filter by type and return a new list
    return [entry for entry in all_memories if entry.get(
        "type") == memory_type]


def get_recent_memories_by_type(
    memory_type: str, limit: int = 5
) -> List[Dict[str, Any]]:
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
