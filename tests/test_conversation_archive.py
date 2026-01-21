"""
Tests for conversation archive functionality
"""

import json
import gzip
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from kortana.memory.conversation_archive import ConversationArchive


class TestConversationArchive:
    """Test cases for the ConversationArchive class."""
    
    @pytest.fixture
    def temp_archive_dir(self, tmp_path):
        """Create a temporary archive directory."""
        archive_dir = tmp_path / "conversation_archives"
        archive_dir.mkdir()
        return str(archive_dir)
    
    @pytest.fixture
    def archive_manager(self, temp_archive_dir):
        """Create a ConversationArchive instance for testing."""
        return ConversationArchive(
            archive_dir=temp_archive_dir,
            max_active_conversations=10,
            archive_after_days=7,
            compress_archives=True,
        )
    
    def test_archive_initialization(self, archive_manager, temp_archive_dir):
        """Test archive manager initialization."""
        assert archive_manager.archive_dir == Path(temp_archive_dir)
        assert archive_manager.max_active_conversations == 10
        assert archive_manager.archive_after_days == 7
        assert archive_manager.compress_archives is True
    
    def test_should_archive_old_conversation(self, archive_manager):
        """Test that old conversations should be archived."""
        old_timestamp = datetime.now() - timedelta(days=30)
        assert archive_manager.should_archive(old_timestamp) is True
    
    def test_should_not_archive_recent_conversation(self, archive_manager):
        """Test that recent conversations should not be archived."""
        recent_timestamp = datetime.now() - timedelta(days=3)
        assert archive_manager.should_archive(recent_timestamp) is False
    
    def test_archive_conversation_compressed(self, archive_manager):
        """Test archiving a conversation with compression."""
        conversation_id = "test_conv_123"
        conversation_data = {
            "timestamp": datetime.now().isoformat(),
            "role": "user",
            "content": "Test conversation content",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ],
        }
        metadata = {"tags": ["test"], "session_id": "session_456"}
        
        result = archive_manager.archive_conversation(
            conversation_id, conversation_data, metadata
        )
        
        assert result is True
        
        # Verify the file was created
        year_month = datetime.now().strftime("%Y-%m")
        archive_path = archive_manager.archive_dir / year_month / f"{conversation_id}.json.gz"
        assert archive_path.exists()
        
        # Verify the content
        with gzip.open(archive_path, "rt", encoding="utf-8") as f:
            archived_data = json.load(f)
        
        assert archived_data["conversation_id"] == conversation_id
        assert "archived_at" in archived_data
        assert archived_data["metadata"] == metadata
        assert archived_data["conversation"]["content"] == "Test conversation content"
    
    def test_archive_conversation_uncompressed(self, temp_archive_dir):
        """Test archiving a conversation without compression."""
        archive_manager = ConversationArchive(
            archive_dir=temp_archive_dir,
            compress_archives=False,
        )
        
        conversation_id = "test_conv_456"
        conversation_data = {
            "timestamp": datetime.now().isoformat(),
            "content": "Uncompressed conversation",
        }
        
        result = archive_manager.archive_conversation(conversation_id, conversation_data)
        assert result is True
        
        # Verify the file was created (uncompressed)
        year_month = datetime.now().strftime("%Y-%m")
        archive_path = archive_manager.archive_dir / year_month / f"{conversation_id}.json"
        assert archive_path.exists()
    
    def test_retrieve_archived_conversation(self, archive_manager):
        """Test retrieving an archived conversation."""
        conversation_id = "test_conv_789"
        conversation_data = {
            "timestamp": datetime.now().isoformat(),
            "content": "Retrievable conversation",
        }
        
        # Archive the conversation
        archive_manager.archive_conversation(conversation_id, conversation_data)
        
        # Retrieve it
        retrieved = archive_manager.retrieve_archived_conversation(conversation_id)
        
        assert retrieved is not None
        assert retrieved["conversation_id"] == conversation_id
        assert retrieved["conversation"]["content"] == "Retrievable conversation"
    
    def test_retrieve_nonexistent_conversation(self, archive_manager):
        """Test retrieving a conversation that doesn't exist."""
        retrieved = archive_manager.retrieve_archived_conversation("nonexistent_id")
        assert retrieved is None
    
    def test_prune_old_conversations(self, archive_manager):
        """Test pruning old conversations."""
        # Create test conversations with different ages
        old_timestamp = (datetime.now() - timedelta(days=30)).isoformat()
        recent_timestamp = (datetime.now() - timedelta(days=2)).isoformat()
        
        active_conversations = [
            {"id": "old_conv_1", "timestamp": old_timestamp, "content": "Old 1"},
            {"id": "old_conv_2", "timestamp": old_timestamp, "content": "Old 2"},
            {"id": "recent_conv_1", "timestamp": recent_timestamp, "content": "Recent 1"},
            {"id": "recent_conv_2", "timestamp": recent_timestamp, "content": "Recent 2"},
        ]
        
        remaining, archived_count = archive_manager.prune_old_conversations(
            active_conversations
        )
        
        assert archived_count == 2
        assert len(remaining) == 2
        assert all(conv["id"].startswith("recent") for conv in remaining)
    
    def test_archive_statistics(self, archive_manager):
        """Test getting archive statistics."""
        # Archive some conversations
        for i in range(3):
            conversation_id = f"test_conv_{i}"
            conversation_data = {
                "timestamp": datetime.now().isoformat(),
                "content": f"Test content {i}",
            }
            archive_manager.archive_conversation(conversation_id, conversation_data)
        
        stats = archive_manager.get_archive_statistics()
        
        assert stats["total_archived_conversations"] == 3
        assert "total_size_mb" in stats
        assert "archives_by_month" in stats
        assert len(stats["archives_by_month"]) > 0
    
    def test_empty_archive_statistics(self, archive_manager):
        """Test statistics for empty archive."""
        stats = archive_manager.get_archive_statistics()
        
        assert stats["total_archived_conversations"] == 0
        assert stats["total_size_mb"] == 0
        assert len(stats["archives_by_month"]) == 0
