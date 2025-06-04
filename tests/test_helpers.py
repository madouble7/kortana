"""Helper functions for testing."""

import os
import json
import tempfile
from typing import List, Dict, Any


def create_test_memory_file(memories: List[Dict[str, Any]]) -> str:
    """Create a temporary memory file with the given memories.

    Args:
        memories: List of memory entries to include

    Returns:
        Path to the temporary file
    """
    temp_file = tempfile.NamedTemporaryFile(mode="w+", delete=False)

    try:
        # Write each memory as a JSON line
        for memory in memories:
            json.dump(memory, temp_file)
            temp_file.write("\n")

        temp_file.close()
        return temp_file.name
    except Exception as e:
        # Clean up if something goes wrong
        temp_file.close()
        os.unlink(temp_file.name)
        raise e


def cleanup_test_file(file_path: str):
    """Remove a temporary test file."""
    try:
        os.unlink(file_path)
    except OSError:
        pass
