#!/usr/bin/env python3
"""
Unit Tests for ChatEngine Memory Integration and Refactored Functions
====================================================================
Tests for the brain.py module's refactored functions and memory integration.
"""

import unittest
from unittest.mock import MagicMock, patch

import pytest

from src.kortana.brain import ChatEngine


class TestChatEngineRefactoring(unittest.TestCase):
    """Test suite for the refactored ChatEngine class."""

    def setUp(self):
        """Set up test fixtures for each test."""
        # Create a mock for settings
        self.mock_settings = MagicMock()
        self.mock_settings.default_llm_id = "test_llm"
        self.mock_settings.paths.persona_file_path = "test_persona_path"
        self.mock_settings.paths.identity_file_path = "test_identity_path"

        # Patch required dependencies
        self.patcher1 = patch('src.kortana.brain.LLMClientFactory')
        self.patcher2 = patch('src.kortana.brain.SacredModelRouter')
        self.patcher3 = patch('src.kortana.brain.MemoryManager')
        self.patcher4 = patch('src.kortana.brain.load_json_config')

        self.mock_factory = self.patcher1.start()
        self.mock_router = self.patcher2.start()
        self.mock_memory_manager = self.patcher3.start()
        self.mock_load_config = self.patcher4.start()

        # Set up return values
        self.mock_llm_client = MagicMock()
        self.mock_factory.return_value.get_client.return_value = self.mock_llm_client
        self.mock_load_config.return_value = {"base_persona": "I am a test persona"}

        # Create the chat engine instance
        self.chat_engine = ChatEngine(self.mock_settings)

    def tearDown(self):
        """Tear down test fixtures after each test."""
        self.patcher1.stop()
        self.patcher2.stop()
        self.patcher3.stop()
        self.patcher4.stop()

    def test_get_base_persona_prompt(self):
        """Test the _get_base_persona_prompt function."""
        # Test with default persona
        result = self.chat_engine._get_base_persona_prompt()
        self.assertEqual(result, "I am a test persona\n\n")

        # Test with custom persona
        self.chat_engine.persona_data = {"base_persona": "Custom persona"}
        result = self.chat_engine._get_base_persona_prompt()
        self.assertEqual(result, "Custom persona\n\n")

    def test_format_channel_info(self):
        """Test the _format_channel_info function."""
        result = self.chat_engine._format_channel_info("discord")
        self.assertEqual(result, "Message received via discord channel.\n\n")

    def test_format_memory_context(self):
        """Test the _format_memory_context function."""
        test_context = "Test memory\nAnother memory"
        result = self.chat_engine._format_memory_context(test_context)
        self.assertEqual(result, "Recent conversation context:\nTest memory\nAnother memory\n\n")

    def test_format_user_info(self):
        """Test the _format_user_info function."""
        # Test with default user
        result = self.chat_engine._format_user_info()
        self.assertEqual(result, "Current user: User\nRespond naturally and helpfully.")

        # Test with custom user
        result = self.chat_engine._format_user_info(user_name="TestUser")
        self.assertEqual(result, "Current user: TestUser\nRespond naturally and helpfully.")

        # Test with user ID
        result = self.chat_engine._format_user_info(user_name="TestUser", user_id="123")
        self.assertEqual(result, "Current user: TestUser\nUser ID: 123\nRespond naturally and helpfully.")

    def test_build_prompt_with_memory_integration(self):
        """Test the _build_prompt_with_memory function fully integrated."""
        # Mock the component methods
        self.chat_engine._get_base_persona_prompt = MagicMock(return_value="Base persona\n\n")
        self.chat_engine._format_channel_info = MagicMock(return_value="Channel info\n\n")
        self.chat_engine._format_memory_context = MagicMock(return_value="Memory context\n\n")
        self.chat_engine._format_user_info = MagicMock(return_value="User info")

        # Call the method
        result = self.chat_engine._build_prompt_with_memory(
            user_message="Test message",
            memory_context="Test memory",
            user_name="TestUser",
            channel="discord"
        )

        # Check the result
        self.assertEqual(result["model"], "test_llm")
        self.assertEqual(len(result["messages"]), 2)
        self.assertEqual(result["messages"][0]["role"], "system")
        self.assertEqual(result["messages"][1]["role"], "user")
        self.assertEqual(result["messages"][1]["content"], "Test message")

        # Verify the full system prompt was constructed correctly
        expected_system_content = "Base persona\n\nChannel info\n\nMemory context\n\nUser info"
        self.assertEqual(result["messages"][0]["content"], expected_system_content)

        # Verify component methods were called with correct parameters
        self.chat_engine._format_channel_info.assert_called_once_with("discord")
        self.chat_engine._format_memory_context.assert_called_once_with("Test memory")
        self.chat_engine._format_user_info.assert_called_once_with("TestUser", None)

    def test_get_basic_memory_stats(self):
        """Test the _get_basic_memory_stats function."""
        # Set up test data
        self.chat_engine.history = [{"test": "entry"}, {"test": "entry2"}]
        self.chat_engine.session_id = "test_session"

        # Get stats
        result = self.chat_engine._get_basic_memory_stats()

        # Check results
        self.assertEqual(result["conversation_history_length"], 2)
        self.assertEqual(result["session_id"], "test_session")

    def test_get_memory_manager_stats(self):
        """Test the _get_memory_manager_stats function."""
        # Set up mock memory manager
        self.chat_engine.memory_manager.load_project_memory.return_value = [
            {"id": 1}, {"id": 2}, {"id": 3}
        ]
        self.chat_engine.memory_manager.pinecone_enabled = True
        self.chat_engine.memory_manager.memory_journal_path = "test/path.jsonl"

        # Get stats
        result = self.chat_engine._get_memory_manager_stats()

        # Check results
        self.assertEqual(result["total_memories"], 3)
        self.assertEqual(result["pinecone_enabled"], True)
        self.assertEqual(result["memory_journal_path"], "test/path.jsonl")

    def test_get_memory_stats_integration(self):
        """Test the get_memory_stats function integrated with its components."""
        # Mock the component methods
        self.chat_engine._get_basic_memory_stats = MagicMock(return_value={
            "basic_stat1": "value1",
            "basic_stat2": "value2"
        })
        self.chat_engine._get_memory_manager_stats = MagicMock(return_value={
            "mm_stat1": "value3",
            "mm_stat2": "value4"
        })

        # Get combined stats
        result = self.chat_engine.get_memory_stats()

        # Check results
        self.assertEqual(result["basic_stat1"], "value1")
        self.assertEqual(result["basic_stat2"], "value2")
        self.assertEqual(result["mm_stat1"], "value3")
        self.assertEqual(result["mm_stat2"], "value4")

    def test_get_memory_stats_error_handling(self):
        """Test error handling in get_memory_stats."""
        # Make the component method raise an exception
        self.chat_engine._get_basic_memory_stats = MagicMock(side_effect=Exception("Test error"))

        # Get stats with error
        result = self.chat_engine.get_memory_stats()

        # Check it returned an error dictionary
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Test error")

    def test_save_pending_memory_operations(self):
        """Test the _save_pending_memory_operations function."""
        # Set up mock memory manager
        self.chat_engine.memory_manager.load_project_memory.return_value = [{"test": "data"}]

        # Call the method
        self.chat_engine._save_pending_memory_operations()

        # Verify the memory manager methods were called
        self.chat_engine.memory_manager.load_project_memory.assert_called_once()
        self.chat_engine.memory_manager.save_project_memory.assert_called_once_with([{"test": "data"}])

    def test_shutdown_integration(self):
        """Test the shutdown function integrated with its components."""
        # Mock the component method
        self.chat_engine._save_pending_memory_operations = MagicMock()

        # Call shutdown
        self.chat_engine.shutdown()

        # Verify the component method was called
        self.chat_engine._save_pending_memory_operations.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
