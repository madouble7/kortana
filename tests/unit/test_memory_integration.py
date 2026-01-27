#!/usr/bin/env python3
"""
Unit Tests for Memory Integration in ChatEngine
==============================================
Tests for memory-related functions in the refactored ChatEngine.
"""

import unittest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

# Import modules for testing
from kortana.brain import ChatEngine


class TestMemoryIntegration(unittest.TestCase):
    """Test suite for memory integration in ChatEngine."""

    def setUp(self):
        """Set up test fixtures for each test."""
        # Create mock configurations
        self.mock_settings = MagicMock()
        self.mock_settings.default_llm_id = "mock-llm"
        self.mock_settings.paths.persona_file_path = "mock_persona.json"
        self.mock_settings.paths.identity_file_path = "mock_identity.json"

        # Mock dependencies
        self.patcher1 = patch("src.kortana.brain_fixed.LLMClientFactory")
        self.patcher2 = patch("src.kortana.brain_fixed.SacredModelRouter")
        self.patcher3 = patch("src.kortana.brain_fixed.MemoryManager")
        self.patcher4 = patch("src.kortana.brain_fixed.load_json_config")
        self.patcher5 = patch("src.kortana.brain_fixed.append_to_memory_journal")

        self.mock_llm_factory = self.patcher1.start()
        self.mock_router = self.patcher2.start()
        self.mock_memory_mgr_cls = self.patcher3.start()
        self.mock_load_config = self.patcher4.start()
        self.mock_append_journal = self.patcher5.start()

        # Set up mock return values
        self.mock_memory_mgr = MagicMock()
        self.mock_memory_mgr_cls.return_value = self.mock_memory_mgr
        self.mock_memory_mgr.pinecone_enabled = True
        self.mock_memory_mgr.memory_journal_path = "mock/journal.jsonl"

        self.mock_llm_client = MagicMock()
        self.mock_llm_client.complete = AsyncMock(
            return_value={"content": "Mock response"}
        )
        self.mock_llm_factory.return_value.get_client.return_value = (
            self.mock_llm_client
        )

        self.mock_load_config.return_value = {"base_persona": "I am a test persona."}

        # Create chat engine instance
        self.chat_engine = ChatEngine(self.mock_settings)

    def tearDown(self):
        """Clean up after tests."""
        self.patcher1.stop()
        self.patcher2.stop()
        self.patcher3.stop()
        self.patcher4.stop()
        self.patcher5.stop()

    def test_add_user_message(self):
        """Test adding a user message to history and memory."""
        # Mock necessary methods
        self.chat_engine._save_to_memory = MagicMock()

        # Add a test message
        self.chat_engine.add_user_message("Hello, Kor'tana!")

        # Check history and memory calls
        self.assertEqual(len(self.chat_engine.history), 1)
        self.assertEqual(self.chat_engine.history[0]["role"], "user")
        self.assertEqual(self.chat_engine.history[0]["content"], "Hello, Kor'tana!")
        self.chat_engine._save_to_memory.assert_called_once()

    def test_add_assistant_message(self):
        """Test adding an assistant message to history and memory."""
        # Mock necessary methods
        self.chat_engine._save_to_memory = MagicMock()

        # Add a test message
        self.chat_engine.add_assistant_message("I am here to assist you.")

        # Check history and memory calls
        self.assertEqual(len(self.chat_engine.history), 1)
        self.assertEqual(self.chat_engine.history[0]["role"], "assistant")
        self.assertEqual(
            self.chat_engine.history[0]["content"], "I am here to assist you."
        )
        self.chat_engine._save_to_memory.assert_called_once()

    def test_save_to_memory(self):
        """Test saving message to memory systems."""
        # Mock components
        self.chat_engine._save_to_journal = MagicMock()
        self.chat_engine._save_to_vector_storage = MagicMock()

        # Create test entry
        test_entry = {
            "role": "user",
            "content": "Test message",
            "timestamp": datetime.now().isoformat(),
        }

        # Call method
        self.chat_engine._save_to_memory(test_entry)

        # Verify calls
        self.chat_engine._save_to_journal.assert_called_once_with(test_entry)
        self.chat_engine._save_to_vector_storage.assert_called_once_with(test_entry)

    def test_save_to_journal(self):
        """Test saving entry to memory journal."""
        # Create test entry
        test_entry = {
            "role": "user",
            "content": "Test message",
            "timestamp": datetime.now().isoformat(),
        }

        # Call method
        self.chat_engine._save_to_journal(test_entry)

        # Verify append_to_memory_journal was called correctly
        self.mock_append_journal.assert_called_once_with(
            self.mock_memory_mgr.memory_journal_path, test_entry
        )

    @patch("src.kortana.brain_fixed.extract_keywords_from_text")
    def test_save_to_vector_storage(self, mock_extract_keywords):
        """Test saving entry to vector storage."""
        # Set up mock
        mock_extract_keywords.return_value = ["test", "message"]
        self.chat_engine.memory_manager.add_memory = MagicMock()

        # Create test entry
        test_entry = {
            "role": "user",
            "content": "Test message for vector storage",
            "timestamp": datetime.now().isoformat(),
        }

        # Call method
        self.chat_engine._save_to_vector_storage(test_entry)

        # Verify memory added to vector storage
        self.chat_engine.memory_manager.add_memory.assert_called_once()

    @patch("src.kortana.brain_fixed.generate_embedding")
    async def test_retrieve_semantic_memories(self, mock_generate_embedding):
        """Test retrieving semantic memories."""
        # Set up mocks
        mock_vector = [0.1, 0.2, 0.3]
        mock_generate_embedding.return_value = mock_vector
        mock_memories = [{"text": "Memory 1"}, {"text": "Memory 2"}]
        self.chat_engine.memory_manager.search_memory = MagicMock(
            return_value=mock_memories
        )

        # Call method
        result = await self.chat_engine._retrieve_semantic_memories("Test query")

        # Verify results
        self.assertEqual(result, mock_memories)
        mock_generate_embedding.assert_called_once_with("Test query")
        self.chat_engine.memory_manager.search_memory.assert_called_once_with(
            query_vector=mock_vector, top_k=5
        )

    async def test_get_memory_context_integration(self):
        """Test the integrated memory context retrieval."""
        # Mock component methods
        self.chat_engine._get_conversation_history_context = MagicMock(
            return_value="History context"
        )
        self.chat_engine._get_semantic_search_context = AsyncMock(
            return_value="Semantic context"
        )

        # Call the method
        context = await self.chat_engine._get_memory_context("Test message")

        # Verify the combined context
        self.assertEqual(context, "History context\nSemantic context")

    @patch("src.kortana.brain_fixed.generate_embedding")
    async def test_end_to_end_memory_integration(self, mock_generate_embedding):
        """Test end-to-end memory integration flow."""
        # Set up mock for embedding
        mock_vector = [0.1, 0.2, 0.3]
        mock_generate_embedding.return_value = mock_vector

        # Mock memory search results
        mock_memories = [
            {
                "text": "Previous conversation about testing",
                "source": "chat",
                "score": 0.85,
            }
        ]
        self.chat_engine.memory_manager.search_memory = MagicMock(
            return_value=mock_memories
        )

        # Add messages to history
        self.chat_engine._save_to_memory = MagicMock()  # Prevent actual saving
        self.chat_engine.add_user_message("Hello Kor'tana")
        self.chat_engine.add_assistant_message("Hello, how can I help?")

        # Test process_message with memory integration
        self.chat_engine._get_memory_context = AsyncMock(
            return_value="Relevant memory context"
        )

        # Mock the LLM response
        response = await self.chat_engine.process_message("Tell me about testing")

        # Verify flow and response
        self.assertEqual(response, "Mock response")
        self.chat_engine._get_memory_context.assert_called_once()
        self.mock_llm_client.complete.assert_called_once()


# Allow running tests directly
if __name__ == "__main__":
    unittest.main()
