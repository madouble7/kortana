"""
Tests for enhanced metadata tracking in memory entries
"""

import pytest
from datetime import datetime
from kortana.memory.memory import MemoryEntry


class TestMemoryEntryMetadata:
    """Test cases for enhanced metadata tracking in MemoryEntry."""
    
    def test_memory_entry_with_metadata(self):
        """Test creating a memory entry with custom metadata."""
        custom_metadata = {
            "user_id": "user123",
            "session_id": "session456",
            "importance": "high",
        }
        
        entry = MemoryEntry(
            text="Test memory with metadata",
            tags=["test"],
            metadata=custom_metadata,
        )
        
        assert entry.metadata["user_id"] == "user123"
        assert entry.metadata["session_id"] == "session456"
        assert entry.metadata["importance"] == "high"
        assert "created_at" in entry.metadata
        assert "last_accessed" in entry.metadata
        assert "access_count" in entry.metadata
    
    def test_memory_entry_default_metadata(self):
        """Test that default metadata is created when not provided."""
        entry = MemoryEntry(text="Test memory")
        
        assert "created_at" in entry.metadata
        assert "last_accessed" in entry.metadata
        assert entry.metadata["access_count"] == 0
    
    def test_update_access_metadata(self):
        """Test updating access metadata."""
        entry = MemoryEntry(text="Test memory")
        
        # Record initial values
        initial_access_time = entry.metadata["last_accessed"]
        initial_count = entry.metadata["access_count"]
        
        # Update access metadata
        entry.update_access_metadata()
        
        assert entry.metadata["access_count"] == initial_count + 1
        assert entry.metadata["last_accessed"] != initial_access_time
    
    def test_multiple_access_updates(self):
        """Test multiple access metadata updates."""
        entry = MemoryEntry(text="Test memory")
        
        assert entry.metadata["access_count"] == 0
        
        for i in range(5):
            entry.update_access_metadata()
        
        assert entry.metadata["access_count"] == 5
    
    def test_memory_entry_to_dict_includes_metadata(self):
        """Test that to_dict includes metadata."""
        custom_metadata = {"custom_field": "custom_value"}
        entry = MemoryEntry(
            text="Test memory",
            tags=["test"],
            metadata=custom_metadata,
        )
        
        data_dict = entry.to_dict()
        
        assert "metadata" in data_dict
        assert data_dict["metadata"]["custom_field"] == "custom_value"
        assert "created_at" in data_dict["metadata"]
    
    def test_memory_entry_from_dict_with_metadata(self):
        """Test creating memory entry from dict with metadata."""
        data = {
            "id": "test-id",
            "text": "Test memory",
            "timestamp": datetime.now().isoformat(),
            "tags": ["test"],
            "source": "test_source",
            "embedding": [0.1, 0.2, 0.3],
            "metadata": {
                "custom_field": "custom_value",
                "created_at": datetime.now().isoformat(),
                "last_accessed": datetime.now().isoformat(),
                "access_count": 5,
            },
        }
        
        entry = MemoryEntry.from_dict(data)
        
        assert entry.metadata["custom_field"] == "custom_value"
        assert entry.metadata["access_count"] == 5
    
    def test_memory_entry_from_interaction_with_metadata(self):
        """Test creating memory entry from interaction with metadata."""
        interaction = {
            "text": "User message",
            "tags": ["conversation"],
            "source": "chat",
            "metadata": {
                "session_id": "session789",
                "user_id": "user456",
            },
        }
        
        entry = MemoryEntry.from_interaction(interaction)
        
        assert entry.text == "User message"
        assert entry.metadata["session_id"] == "session789"
        assert entry.metadata["user_id"] == "user456"
    
    def test_metadata_persistence_in_dict_conversion(self):
        """Test that metadata persists through dict conversion."""
        original_metadata = {
            "importance": "high",
            "category": "work",
        }
        
        entry = MemoryEntry(text="Test memory", metadata=original_metadata)
        entry.update_access_metadata()
        entry.update_access_metadata()
        
        # Convert to dict and back
        data_dict = entry.to_dict()
        restored_entry = MemoryEntry.from_dict(data_dict)
        
        assert restored_entry.metadata["importance"] == "high"
        assert restored_entry.metadata["category"] == "work"
        assert restored_entry.metadata["access_count"] == 2
