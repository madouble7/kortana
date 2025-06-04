"""
Unit tests for Kor'tana's memory helper functions.

These tests focus on the individual memory helper functions in memory.py,
ensuring they work correctly in isolation.
"""

import os
import sys
import pytest
import json
import tempfile
from unittest.mock import patch, mock_open

# Add the src directory to the path so we can import modules
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

# Import memory helpers
from kortana.core.memory import (
    save_memory,
    load_memory,
    save_decision,
    save_implementation_note,
    save_project_insight,
    get_memory_by_type,
    get_recent_memories_by_type,
)


class TestMemoryHelpers:
    """Test the memory helper functions."""

    @pytest.fixture
    def mock_memory_file(self):
        """Create a temporary memory file for testing."""
        # Use a temporary file as the memory file
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp:
            temp.write(
                '{"type": "decision", "content": "Test decision", "timestamp": "2023-06-15T12:00:00Z", "tags": ["test"]}\n'
            )
            temp.write(
                '{"type": "implementation_note", "content": "Test note", "timestamp": "2023-06-16T12:00:00Z", "component": "test", "priority": "high"}\n'
            )
            temp_name = temp.name

        # Patch the PROJECT_MEMORY_PATH to use our temp file
        with patch("core.memory.PROJECT_MEMORY_PATH", temp_name):
            yield temp_name

        # Clean up
        os.unlink(temp_name)

    def test_load_memory(self, mock_memory_file):
        """Test loading memory from file."""
        # Load memories from the mocked file
        memories = load_memory()

        # Check the loaded memories
        assert len(memories) == 2, "Expected 2 memory entries"
        assert memories[0]["type"] == "decision", "Wrong type for first memory"
        assert memories[0]["content"] == "Test decision", (
            "Wrong content for first memory"
        )
        assert memories[1]["type"] == "implementation_note", (
            "Wrong type for second memory"
        )
        assert memories[1]["content"] == "Test note", "Wrong content for second memory"

    def test_save_memory(self):
        """Test saving memory to file."""
        # Create a mock memory entry
        memory = {
            "type": "test_type",
            "content": "Test content",
            "timestamp": "2023-06-15T12:00:00Z",
        }

        # Use mock_open to test file writing
        m = mock_open()
        with patch("builtins.open", m):
            with patch("os.makedirs"):
                # Call save_memory with our test memory
                result = save_memory(memory)

                # Check the result
                assert result, "save_memory should return True on success"

                # Check that the file was opened for appending
                m.assert_called_once()
                handle = m()

                # Check that memory was written to the file
                handle.write.assert_called()

                # Check the content that was written
                write_args = handle.write.call_args_list
                written_content = "".join(args[0][0] for args in write_args)
                assert json.dumps(memory) in written_content, (
                    "Memory entry should be written to file"
                )

    def test_save_decision(self):
        """Test the save_decision helper function."""
        # Use a patch to prevent actual file writing
        with patch("core.memory.save_memory") as mock_save:
            mock_save.return_value = True

            # Call save_decision
            result = save_decision("Test decision", ["tag1", "tag2"])

            # Check the result
            assert result, "save_decision should return True on success"

            # Check that save_memory was called with the right arguments
            mock_save.assert_called_once()
            call_args = mock_save.call_args[0][0]
            assert call_args["type"] == "decision", "Wrong type in saved memory"
            assert call_args["content"] == "Test decision", (
                "Wrong content in saved memory"
            )
            assert call_args["tags"] == ["tag1", "tag2"], "Wrong tags in saved memory"
            assert "timestamp" in call_args, "Missing timestamp in saved memory"

    def test_save_implementation_note(self):
        """Test the save_implementation_note helper function."""
        # Use a patch to prevent actual file writing
        with patch("core.memory.save_memory") as mock_save:
            mock_save.return_value = True

            # Call save_implementation_note
            result = save_implementation_note("Test note", "test_component", "high")

            # Check the result
            assert result, "save_implementation_note should return True on success"

            # Check that save_memory was called with the right arguments
            mock_save.assert_called_once()
            call_args = mock_save.call_args[0][0]
            assert call_args["type"] == "implementation_note", (
                "Wrong type in saved memory"
            )
            assert call_args["content"] == "Test note", "Wrong content in saved memory"
            assert call_args["component"] == "test_component", (
                "Wrong component in saved memory"
            )
            assert call_args["priority"] == "high", "Wrong priority in saved memory"
            assert "timestamp" in call_args, "Missing timestamp in saved memory"

    def test_save_project_insight(self):
        """Test the save_project_insight helper function."""
        # Use a patch to prevent actual file writing
        with patch("core.memory.save_memory") as mock_save:
            mock_save.return_value = True

            # Call save_project_insight
            result = save_project_insight("Test insight", "medium")

            # Check the result
            assert result, "save_project_insight should return True on success"

            # Check that save_memory was called with the right arguments
            mock_save.assert_called_once()
            call_args = mock_save.call_args[0][0]
            assert call_args["type"] == "project_insight", "Wrong type in saved memory"
            assert call_args["content"] == "Test insight", (
                "Wrong content in saved memory"
            )
            assert call_args["impact"] == "medium", "Wrong impact in saved memory"
            assert "timestamp" in call_args, "Missing timestamp in saved memory"

    def test_get_memory_by_type(self, mock_memory_file):
        """Test getting memories by type."""
        # Get memories of type 'decision'
        decision_memories = get_memory_by_type("decision")

        # Check the results
        assert len(decision_memories) == 1, "Expected 1 decision memory"
        assert decision_memories[0]["content"] == "Test decision", (
            "Wrong content in decision memory"
        )

        # Get memories of type 'implementation_note'
        note_memories = get_memory_by_type("implementation_note")

        # Check the results
        assert len(note_memories) == 1, "Expected 1 implementation note memory"
        assert note_memories[0]["content"] == "Test note", (
            "Wrong content in implementation note memory"
        )

        # Get memories of a non-existent type
        nonexistent_memories = get_memory_by_type("nonexistent")

        # Check the results
        assert len(nonexistent_memories) == 0, "Expected 0 nonexistent memories"

    def test_get_recent_memories_by_type(self, mock_memory_file):
        """Test getting recent memories by type."""
        # Get recent decision memories
        recent_decisions = get_recent_memories_by_type("decision", limit=1)

        # Check the results
        assert len(recent_decisions) == 1, "Expected 1 recent decision memory"
        assert recent_decisions[0]["content"] == "Test decision", (
            "Wrong content in recent decision memory"
        )

        # Try getting more memories than exist
        all_decisions = get_recent_memories_by_type("decision", limit=10)

        # Check the results
        assert len(all_decisions) == 1, "Expected all decision memories (1)"

        # Try getting memories of a non-existent type
        recent_nonexistent = get_recent_memories_by_type("nonexistent", limit=1)

        # Check the results
        assert len(recent_nonexistent) == 0, "Expected 0 nonexistent memories"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
