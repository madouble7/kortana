"""
Tests for memory caching functionality
"""

import pytest
from datetime import datetime
from kortana.memory.memory_manager import MemoryCache


class TestMemoryCache:
    """Test cases for the MemoryCache class."""
    
    def test_cache_initialization(self):
        """Test cache initialization with default and custom sizes."""
        cache = MemoryCache()
        assert cache.max_size == 100
        assert len(cache.cache) == 0
        
        cache_custom = MemoryCache(max_size=50)
        assert cache_custom.max_size == 50
    
    def test_cache_put_and_get(self):
        """Test putting and getting items from cache."""
        cache = MemoryCache(max_size=5)
        
        test_data = {"id": "test1", "text": "Test memory", "score": 0.95}
        cache.put("key1", test_data)
        
        retrieved = cache.get("key1")
        assert retrieved is not None
        assert retrieved["id"] == "test1"
        assert retrieved["text"] == "Test memory"
    
    def test_cache_miss(self):
        """Test cache miss returns None."""
        cache = MemoryCache()
        
        result = cache.get("nonexistent_key")
        assert result is None
    
    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = MemoryCache(max_size=3)
        
        # Fill the cache
        cache.put("key1", {"data": "value1"})
        cache.put("key2", {"data": "value2"})
        cache.put("key3", {"data": "value3"})
        
        # Add one more item, should evict key1
        cache.put("key4", {"data": "value4"})
        
        assert cache.get("key1") is None  # Evicted
        assert cache.get("key2") is not None
        assert cache.get("key3") is not None
        assert cache.get("key4") is not None
    
    def test_cache_access_count(self):
        """Test that access counts are tracked correctly."""
        cache = MemoryCache()
        
        cache.put("key1", {"data": "value1"})
        
        # Access the item multiple times
        cache.get("key1")
        cache.get("key1")
        cache.get("key1")
        
        stats = cache.get_stats()
        assert stats["size"] == 1
        # Access count should be at least 3 (from gets) + 1 (from put)
        assert cache.access_counts["key1"] >= 4
    
    def test_cache_clear(self):
        """Test clearing the cache."""
        cache = MemoryCache()
        
        cache.put("key1", {"data": "value1"})
        cache.put("key2", {"data": "value2"})
        
        assert len(cache.cache) == 2
        
        cache.clear()
        
        assert len(cache.cache) == 0
        assert len(cache.access_counts) == 0
        assert len(cache.last_accessed) == 0
    
    def test_cache_stats(self):
        """Test cache statistics."""
        cache = MemoryCache(max_size=10)
        
        # Add some items
        cache.put("key1", {"data": "value1"})
        cache.put("key2", {"data": "value2"})
        
        # Access them
        cache.get("key1")
        cache.get("key1")
        cache.get("key2")
        
        stats = cache.get_stats()
        
        assert stats["size"] == 2
        assert stats["max_size"] == 10
        assert stats["total_accesses"] > 0
        assert stats["most_accessed"] is not None
        assert stats["most_accessed"][0] == "key1"  # key1 accessed more
    
    def test_cache_updates_existing_key(self):
        """Test updating an existing key in cache."""
        cache = MemoryCache()
        
        cache.put("key1", {"data": "value1"})
        cache.put("key1", {"data": "value1_updated"})
        
        retrieved = cache.get("key1")
        assert retrieved["data"] == "value1_updated"
        assert len(cache.cache) == 1  # Should not duplicate
