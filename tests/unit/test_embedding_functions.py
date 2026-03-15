#!/usr/bin/env python3
"""
Unit Tests for Embedding Functions in brain_utils Module
=======================================================
Tests for the recently added embedding generation functionality.
"""

import unittest
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.kortana.brain_utils import (
    _hash_text_for_cache,
    generate_embedding,
    get_embedding_model,
)


class TestEmbeddingFunctions(unittest.TestCase):
    """Test suite for embedding-related functions in brain_utils."""

    def test_hash_text_for_cache(self):
        """Test that text hashing produces consistent, expected results."""
        # Test with simple string
        text = "Hello, world!"
        hash1 = _hash_text_for_cache(text)
        hash2 = _hash_text_for_cache(text)

        # Hashes should be consistent for the same input
        self.assertEqual(hash1, hash2)

        # Hash should be a valid MD5 hexadecimal string (32 characters)
        self.assertEqual(len(hash1), 32)

        # Different inputs should produce different hashes
        another_text = "Different text"
        another_hash = _hash_text_for_cache(another_text)
        self.assertNotEqual(hash1, another_hash)

    @patch('src.kortana.brain_utils.SentenceTransformer', autospec=True)
    def test_get_embedding_model_singleton(self, mock_sentence_transformer):
        """Test that get_embedding_model implements singleton pattern correctly."""
        # Set up the mock
        mock_instance = MagicMock()
        mock_sentence_transformer.return_value = mock_instance

        # First call should create the model
        model1 = get_embedding_model()
        mock_sentence_transformer.assert_called_once_with("all-MiniLM-L6-v2")

        # Reset mock to verify it's not called again
        mock_sentence_transformer.reset_mock()

        # Second call should reuse the existing model
        model2 = get_embedding_model()
        mock_sentence_transformer.assert_not_called()

        # Both calls should return the same instance
        self.assertEqual(model1, model2)

    @patch('src.kortana.brain_utils.get_embedding_model')
    def test_generate_embedding_with_text(self, mock_get_model):
        """Test generating embeddings from text."""
        # Set up the mock model
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([0.1, 0.2, 0.3])
        mock_get_model.return_value = mock_model

        # Generate embedding
        result = generate_embedding("Test text")

        # Verify the model was called correctly
        mock_model.encode.assert_called_once()

        # Verify the result is a list of floats
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)
        self.assertEqual(result, [0.1, 0.2, 0.3])

    @patch('src.kortana.brain_utils.get_embedding_model')
    def test_generate_embedding_with_empty_text(self, mock_get_model):
        """Test generating embeddings with empty text."""
        # Generate embedding with empty text
        result = generate_embedding("")

        # Should not call the model for empty text
        mock_get_model.assert_not_called()

        # Should return default zero vector with correct dimensions
        self.assertEqual(len(result), 384)
        self.assertEqual(sum(result), 0.0)

    @patch('src.kortana.brain_utils.get_embedding_model')
    def test_generate_embedding_caching(self, mock_get_model):
        """Test that embedding generation uses caching for repeated inputs."""
        # Set up the mock model
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([0.5, 0.5, 0.5])
        mock_get_model.return_value = mock_model

        # Generate embedding for the same text twice
        text = "Cache test"
        result1 = generate_embedding(text)
        result2 = generate_embedding(text)

        # Model should only be called once (for the first call)
        mock_model.encode.assert_called_once()

        # Both results should be identical
        self.assertEqual(result1, result2)

    @patch('src.kortana.brain_utils.logger')
    @patch('src.kortana.brain_utils.get_embedding_model')
    def test_generate_embedding_error_handling(self, mock_get_model, mock_logger):
        """Test error handling during embedding generation."""
        # Set up the mock model to raise an exception
        mock_model = MagicMock()
        mock_model.encode.side_effect = Exception("Test error")
        mock_get_model.return_value = mock_model

        # Generate embedding
        result = generate_embedding("Test text")

        # Should log the error
        mock_logger.error.assert_called_once()

        # Should return default zero vector as fallback
        self.assertEqual(len(result), 384)
        self.assertEqual(sum(result), 0.0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
