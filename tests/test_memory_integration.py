"""
Integration tests for Kor'tana's memory system.

These tests validate the end-to-end flow of the memory system, including:
- Creation and retrieval of different memory types
- Memory integration in system prompts
"""

import json
import os
import shutil
import sys
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

# Add the src directory to the path so we can import modules
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

# Import the modules we want to test
from kortana.core.memory import (
    get_memory_by_type,
    load_memory,
    save_decision,
    save_implementation_note,
    save_memory,
    save_project_insight,
)
from kortana.core.brain import ChatEngine

# Constants for testing
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "test_data")
TEST_MEMORY_PATH = os.path.join(TEST_DATA_DIR, "test_project_memory.jsonl")


class TestMemoryIntegration:
    """Test the end-to-end memory system."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for tests."""
        # Create test directories
        os.makedirs(TEST_DATA_DIR, exist_ok=True)

        # Patch memory path for testing
        self.patcher = patch("core.memory.PROJECT_MEMORY_PATH", TEST_MEMORY_PATH)
        self.patcher.start()

        # Clear any existing test memory file
        if os.path.exists(TEST_MEMORY_PATH):
            os.remove(TEST_MEMORY_PATH)

        yield

        # Teardown
        self.patcher.stop()

        # Clean up test data
        if os.path.exists(TEST_DATA_DIR):
            shutil.rmtree(TEST_DATA_DIR)

    def test_save_and_load_decision(self):
        """Test saving and loading a decision memory."""
        # Create a decision
        decision_content = "Use automatic summarization with threshold of 20 messages"
        tags = ["memory", "summarization"]

        # Save the decision
        success = save_decision(decision_content, tags)
        assert success, "Failed to save decision"

        # Load all memories
        memories = load_memory()
        assert len(memories) == 1, "Expected 1 memory entry"

        # Check the saved memory
        memory = memories[0]
        assert memory["type"] == "decision", "Wrong memory type"
        assert memory["content"] == decision_content, "Wrong memory content"
        assert memory["tags"] == tags, "Wrong memory tags"
        assert "timestamp" in memory, "Missing timestamp"

    def test_save_multiple_memory_types(self):
        """Test saving multiple types of memories."""
        # Save different types of memories
        save_decision(
            "Use Sacred Model Router for model selection", ["router", "architecture"]
        )
        save_implementation_note(
            "Added automatic summarization trigger", "memory_system", "high"
        )
        save_project_insight("Memory organization improves context retention", "high")

        # Load all memories
        memories = load_memory()
        assert len(memories) == 3, "Expected 3 memory entries"

        # Check memory types
        memory_types = [memory["type"] for memory in memories]
        assert "decision" in memory_types, "Missing decision memory"
        assert "implementation_note" in memory_types, (
            "Missing implementation note memory"
        )
        assert "project_insight" in memory_types, "Missing project insight memory"

        # Test retrieving by type
        decisions = get_memory_by_type("decision")
        assert len(decisions) == 1, "Expected 1 decision memory"
        assert (
            decisions[0]["content"] == "Use Sacred Model Router for model selection"
        ), "Wrong decision content"

    def test_memory_timestamp_ordering(self):
        """Test that memories can be ordered by timestamp."""
        # Save memories with different timestamps
        # Using the save_memory function directly to control timestamps
        save_memory(
            {
                "type": "decision",
                "content": "First decision",
                "timestamp": (
                    datetime.now(UTC) - timedelta(days=3)
                ).isoformat(),
                "tags": [],
            }
        )

        save_memory(
            {
                "type": "decision",
                "content": "Second decision",
                "timestamp": (
                    datetime.now(UTC) - timedelta(days=2)
                ).isoformat(),
                "tags": [],
            }
        )

        save_memory(
            {
                "type": "decision",
                "content": "Latest decision",
                "timestamp": datetime.now(UTC).isoformat(),
                "tags": [],
            }
        )

        # Load memories
        memories = load_memory()
        assert len(memories) == 3, "Expected 3 memory entries"

        # Sort by timestamp (most recent first)
        sorted_memories = sorted(
            memories, key=lambda x: x.get("timestamp", ""), reverse=True
        )

        # Check sorting
        assert sorted_memories[0]["content"] == "Latest decision", (
            "Wrong order - expected latest decision first"
        )
        assert sorted_memories[-1]["content"] == "First decision", (
            "Wrong order - expected first decision last"
        )

    @patch("brain.ChatEngine._get_llm_client_for_model")
    @patch("brain.ChatEngine.add_assistant_message")
    def test_automatic_summarization_trigger(
        self, mock_add_assistant, mock_get_llm_client
    ):
        """Test automatic summarization is triggered at the right threshold."""
        # Configure mock LLM client
        mock_llm_client = MagicMock()
        mock_llm_client.send_message.return_value = {
            "content": "This is a summary of the conversation."
        }
        mock_get_llm_client.return_value = mock_llm_client

        # Create ChatEngine instance
        engine = ChatEngine(session_id="test_session")

        # Override SUMMARY_THRESHOLD for testing
        engine.SUMMARY_THRESHOLD = 5

        # Add messages until we hit the threshold
        for i in range(5):
            engine.add_user_message(f"User message {i}")
            # Add assistant message without triggering summarization
            engine.history.append(
                {"role": "assistant", "content": f"Assistant message {i}"}
            )

        # This should trigger summarization
        engine.add_assistant_message("Final assistant message")

        # Check if summarization was triggered
        (
            mock_get_llm_client.assert_called(),
            "LLM client should be called for summarization",
        )
        (
            mock_llm_client.send_message.assert_called_once(),
            "send_message should be called once for summarization",
        )

    @patch("brain.load_memory")
    def test_memory_integration_in_system_prompt(self, mock_load_memory):
        """Test that memories are properly integrated into system prompts."""
        # Mock memory data
        mock_memories = [
            {
                "type": "decision",
                "content": "Use automatic summarization",
                "timestamp": datetime.now(UTC).isoformat(),
                "tags": ["memory"],
            },
            {
                "type": "implementation_note",
                "content": "Added memory helper functions",
                "timestamp": datetime.now(UTC).isoformat(),
                "component": "memory_system",
                "priority": "high",
            },
            {
                "type": "project_insight",
                "content": "Memory organization is crucial",
                "timestamp": datetime.now(UTC).isoformat(),
                "impact": "high",
            },
        ]
        mock_load_memory.return_value = mock_memories

        # Create ChatEngine instance
        engine = ChatEngine(session_id="test_session")

        # Generate system prompt
        system_prompt = engine.build_system_prompt()

        # Check if memories are included in the prompt
        assert "Key Project Decisions" in system_prompt, (
            "Missing decision section in prompt"
        )
        assert "Implementation Context" in system_prompt, (
            "Missing implementation note section in prompt"
        )
        assert "Key Project Insights" in system_prompt, (
            "Missing project insight section in prompt"
        )
        assert "Use automatic summarization" in system_prompt, (
            "Missing decision content in prompt"
        )
        assert "Added memory helper functions" in system_prompt, (
            "Missing implementation note content in prompt"
        )
        assert "Memory organization is crucial" in system_prompt, (
            "Missing project insight content in prompt"
        )

    @patch("brain.ChatEngine._get_llm_client_for_model")
    def test_function_calls_for_memory(self, mock_get_llm_client):
        """Test function calls for saving memories."""
        # Configure mock LLM client
        mock_llm_client = MagicMock()
        mock_get_llm_client.return_value = mock_llm_client

        # Create ChatEngine instance
        engine = ChatEngine(session_id="test_session")

        # Create tool call for save_decision
        tool_call = {
            "function": {
                "name": "save_decision",
                "arguments": json.dumps(
                    {
                        "content": "Decision via function call",
                        "tags": ["function_call", "test"],
                    }
                ),
            }
        }

        # Process the function call
        result = engine._handle_function_calls([tool_call], "Initial response")

        # Check if decision was saved
        assert "Decision saved" in result, "Missing confirmation in response"

        # Verify memory was actually saved
        with patch("core.memory.PROJECT_MEMORY_PATH", TEST_MEMORY_PATH):
            memories = load_memory()
            decision_memories = [m for m in memories if m["type"] == "decision"]
            assert len(decision_memories) > 0, "No decision memories found"
            assert any(
                m["content"] == "Decision via function call" for m in decision_memories
            ), "Decision not saved correctly"

    def test_memory_retrieval_by_type_and_recency(self):
        """Test retrieving memories by type and recency."""
        # Save multiple memories of the same type with different timestamps
        save_memory(
            {
                "type": "implementation_note",
                "content": "Old implementation note",
                "timestamp": (
                    datetime.now(UTC) - timedelta(days=10)
                ).isoformat(),
                "component": "old_component",
                "priority": "low",
            }
        )

        save_memory(
            {
                "type": "implementation_note",
                "content": "Recent implementation note",
                "timestamp": datetime.now(UTC).isoformat(),
                "component": "current_component",
                "priority": "high",
            }
        )

        # Get recent memories of this type
        from kortana.core.memory import get_recent_memories_by_type

        recent_notes = get_recent_memories_by_type("implementation_note", limit=1)

        # Check if we got the most recent one
        assert len(recent_notes) == 1, "Expected exactly 1 recent memory"
        assert recent_notes[0]["content"] == "Recent implementation note", (
            "Wrong content in recent memory"
        )
        assert recent_notes[0]["component"] == "current_component", (
            "Wrong component in recent memory"
        )

    def test_enhanced_memory_organization_in_system_prompt(self):
        """Test that different memory types are properly organized in the system prompt."""
        # Create a diverse set of test memories
        memories = [
            {
                "type": "decision",
                "content": "Use automatic summarization with threshold of 20",
                "timestamp": "2023-07-15T14:30:00Z",
                "tags": ["memory", "architecture"],
            },
            {
                "type": "decision",
                "content": "Implement memory helper functions",
                "timestamp": "2023-07-16T10:15:00Z",
                "tags": ["memory", "code"],
            },
            {
                "type": "implementation_note",
                "content": "Memory helper functions in core/memory.py",
                "timestamp": "2023-07-16T15:45:00Z",
                "component": "memory_system",
                "priority": "high",
            },
            {
                "type": "project_insight",
                "content": "Organizing memories by type improves retrieval",
                "timestamp": "2023-07-17T09:30:00Z",
                "impact": "high",
            },
            {
                "type": "conversation_summary",
                "content": "Discussed memory integration approaches",
                "timestamp": "2023-07-17T16:20:00Z",
                "message_range": "45-65",
            },
        ]

        # Mock loading these memories
        with patch("brain.load_memory", return_value=memories):
            engine = ChatEngine(session_id="test_session")
            system_prompt = engine.build_system_prompt()

            # Check for section headers with emojis (enhanced format)
            assert "🔍 Key Project Decisions:" in system_prompt
            assert "🛠️ Implementation Context:" in system_prompt
            assert "💡 Key Project Insights:" in system_prompt
            assert "💬 Recent Conversation Summaries:" in system_prompt

            # Check that memory content is included
            assert "Use automatic summarization with threshold of 20" in system_prompt
            assert "Memory helper functions in core/memory.py" in system_prompt
            assert "Organizing memories by type improves retrieval" in system_prompt
            assert "Discussed memory integration approaches" in system_prompt

            # Check for metadata inclusion
            assert (
                "[memory, architecture]" in system_prompt
                or "(2023-07-15)" in system_prompt
            )
            assert (
                "Priority: high" in system_prompt or "[memory_system]" in system_prompt
            )
            assert "Impact: high" in system_prompt

    def test_memory_helper_command_parsing(self):
        """Test memory helper commands from user messages."""
        # Create a mock chat engine with function calling enabled
        engine = ChatEngine(session_id="test_session")

        # Mock the save_decision method
        with patch.object(engine, "save_decision") as mock_save_decision:
            # Create mock tool call for save_decision
            tool_call = {
                "function": {
                    "name": "save_decision",
                    "arguments": json.dumps(
                        {
                            "content": "Use memory helpers for command-line style memory saving",
                            "tags": ["usability", "interface"],
                        }
                    ),
                }
            }

            # Call the function handler
            result = engine._handle_function_calls([tool_call], "Initial response")

            # Verify the function was called with expected arguments
            mock_save_decision.assert_called_once_with(
                "Use memory helpers for command-line style memory saving",
                ["usability", "interface"],
            )

            # Verify response includes confirmation
            assert "Decision saved" in result

    def test_summarization_threshold_behavior(self):
        """Test that summarization triggers exactly at the threshold and not before."""
        # Create a ChatEngine with summarization mocked
        engine = ChatEngine(session_id="test_session")

        # Override SUMMARY_THRESHOLD for testing
        original_threshold = engine.SUMMARY_THRESHOLD
        engine.SUMMARY_THRESHOLD = 5

        # Mock the summarize_context method
        with patch.object(engine, "summarize_context") as mock_summarize:
            # Add messages just below the threshold (4 pairs = 8 messages)
            for i in range(4):
                engine.add_user_message(f"Test message {i}")
                engine.add_assistant_message(f"Test response {i}")

            # Verify summarize_context was not called yet
            mock_summarize.assert_not_called()

            # Add one more pair to reach the threshold
            engine.add_user_message("Threshold message")

            # This should trigger summarization
            engine.add_assistant_message("Threshold response")

            # Verify summarize_context was called exactly once
            mock_summarize.assert_called_once()

        # Restore original threshold
        engine.SUMMARY_THRESHOLD = original_threshold


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
