"""Tests for memory caching functionality."""
import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from kortana.modules.memory_core import models, schemas, services


class TestMemoryCaching:
    """Test memory caching functionality."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def memory_service(self, mock_db):
        """Create a memory service instance."""
        return services.MemoryCoreService(mock_db)
    
    def test_cache_initialization(self, memory_service):
        """Test that cache is initialized correctly."""
        assert hasattr(memory_service, "_memory_cache")
        assert hasattr(memory_service, "_search_cache")
        assert isinstance(memory_service._memory_cache, dict)
        assert isinstance(memory_service._search_cache, dict)
        assert memory_service._cache_ttl == 300
    
    def test_get_memory_by_id_with_cache(self, memory_service, mock_db):
        """Test retrieving memory from cache."""
        # Setup mock memory
        mock_memory = Mock(spec=models.CoreMemory)
        mock_memory.id = 1
        mock_memory.content = "Test memory"
        
        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = mock_memory
        
        # First call should hit the database
        result1 = memory_service.get_memory_by_id(1, use_cache=True)
        assert result1 == mock_memory
        assert 1 in memory_service._memory_cache
        
        # Second call should hit the cache (no DB query)
        mock_db.query.reset_mock()
        result2 = memory_service.get_memory_by_id(1, use_cache=True)
        assert result2 == mock_memory
        assert not mock_db.query.called  # Should not call DB
    
    def test_get_memory_by_id_without_cache(self, memory_service, mock_db):
        """Test retrieving memory without cache."""
        mock_memory = Mock(spec=models.CoreMemory)
        mock_memory.id = 1
        
        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = mock_memory
        
        # Call without cache
        result = memory_service.get_memory_by_id(1, use_cache=False)
        assert result == mock_memory
        assert 1 not in memory_service._memory_cache
    
    def test_clear_cache(self, memory_service):
        """Test clearing the cache."""
        # Add some items to cache
        memory_service._memory_cache[1] = (Mock(), 0)
        memory_service._memory_cache[2] = (Mock(), 0)
        memory_service._search_cache["test"] = ([], 0)
        
        result = memory_service.clear_cache()
        
        assert result["memories_cleared"] == 2
        assert result["searches_cleared"] == 1
        assert len(memory_service._memory_cache) == 0
        assert len(memory_service._search_cache) == 0
    
    @patch('src.kortana.modules.memory_core.services.embedding_service')
    def test_search_with_cache(self, mock_embedding, memory_service, mock_db):
        """Test search with caching."""
        # Setup mock embedding
        mock_embedding.get_embedding_for_text.return_value = [0.1, 0.2, 0.3]
        
        # Setup mock memories
        mock_memory = Mock(spec=models.CoreMemory)
        mock_memory.embedding = [0.1, 0.2, 0.3]
        mock_memory.content = "Test"
        
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_memory]
        
        # First call
        result1 = memory_service.search_memories_semantic("test query", top_k=5, use_cache=True)
        assert len(memory_service._search_cache) == 1
        
        # Second call should use cache
        mock_db.query.reset_mock()
        result2 = memory_service.search_memories_semantic("test query", top_k=5, use_cache=True)
        assert not mock_db.query.called
    
    def test_search_relevance_ranking(self, memory_service, mock_db):
        """Test that search results include relevance ranking."""
        with patch('src.kortana.modules.memory_core.services.embedding_service') as mock_embedding:
            mock_embedding.get_embedding_for_text.return_value = [1.0, 0.0, 0.0]
            
            # Create mock memories with different similarities
            memories = []
            for i in range(3):
                mock_mem = Mock(spec=models.CoreMemory)
                mock_mem.embedding = [1.0 - i * 0.3, 0.0, 0.0]
                mock_mem.content = f"Memory {i}"
                memories.append(mock_mem)
            
            mock_db.query.return_value.filter.return_value.all.return_value = memories
            
            results = memory_service.search_memories_semantic("test", top_k=3, use_cache=False)
            
            # Check that relevance_rank is set
            for i, result in enumerate(results):
                assert result["relevance_rank"] == i + 1
