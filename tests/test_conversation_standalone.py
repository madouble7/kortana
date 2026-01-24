"""
Standalone test for conversation history functionality without complex dependencies.
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Direct import of conversation history (no kortana services __init__)
from kortana.services.conversation_history import (
    ConversationHistoryService,
)


def test_conversation_creation():
    """Test creating a conversation."""
    print("Test 1: Creating conversation...")
    service = ConversationHistoryService("/tmp/test_conversations_standalone")
    
    conv = service.create_conversation(user_id="test_user", tags=["python", "ai"])
    assert conv.id is not None
    assert conv.user_id == "test_user"
    assert "python" in conv.tags
    print(f"✓ Created conversation {conv.id} with tags {conv.tags}")


def test_message_handling():
    """Test adding messages."""
    print("\nTest 2: Adding messages...")
    service = ConversationHistoryService("/tmp/test_conversations_standalone")
    
    conv = service.create_conversation()
    conv.add_message("user", "Hello, Kor'tana!")
    conv.add_message("assistant", "Hello! How can I help?")
    service.save_conversation(conv)
    
    # Retrieve and verify
    retrieved = service.get_conversation(conv.id)
    assert len(retrieved.messages) == 2
    assert retrieved.messages[0].content == "Hello, Kor'tana!"
    print(f"✓ Added and retrieved {len(retrieved.messages)} messages")


def test_tag_management():
    """Test tag operations."""
    print("\nTest 3: Managing tags...")
    service = ConversationHistoryService("/tmp/test_conversations_standalone")
    
    conv = service.create_conversation(tags=["initial"])
    service.add_tags(conv.id, ["new1", "new2"])
    
    updated = service.get_conversation(conv.id)
    assert "new1" in updated.tags
    assert "new2" in updated.tags
    print(f"✓ Tags after adding: {updated.tags}")
    
    service.remove_tags(conv.id, ["new1"])
    updated = service.get_conversation(conv.id)
    assert "new1" not in updated.tags
    print(f"✓ Tags after removing: {updated.tags}")


def test_filtering_by_tags():
    """Test filtering conversations by tags."""
    print("\nTest 4: Filtering by tags...")
    service = ConversationHistoryService("/tmp/test_conversations_standalone_filter")
    
    conv1 = service.create_conversation(tags=["python", "ai"])
    conv2 = service.create_conversation(tags=["javascript", "web"])
    conv3 = service.create_conversation(tags=["python", "web"])
    
    # Filter by python tag
    results = service.list_conversations(tags=["python"])
    assert len(results) == 2
    print(f"✓ Found {len(results)} conversations with 'python' tag")


def test_keyword_search():
    """Test keyword filtering."""
    print("\nTest 5: Keyword search...")
    service = ConversationHistoryService("/tmp/test_conversations_standalone_search")
    
    conv1 = service.create_conversation()
    conv1.add_message("user", "Tell me about machine learning algorithms")
    service.save_conversation(conv1)
    
    conv2 = service.create_conversation()
    conv2.add_message("user", "What is the weather forecast?")
    service.save_conversation(conv2)
    
    # Search for "machine"
    results = service.list_conversations(keywords=["machine"])
    assert len(results) == 1
    print(f"✓ Found {len(results)} conversations with 'machine' keyword")


def test_engagement_rank():
    """Test engagement rank calculation."""
    print("\nTest 6: Engagement rank...")
    service = ConversationHistoryService("/tmp/test_conversations_standalone_engagement")
    
    conv = service.create_conversation()
    assert conv.engagement_rank == 0.0
    
    # Add messages to increase engagement
    for i in range(10):
        conv.add_message("user", f"This is a detailed message about topic {i} with many words")
    
    assert conv.engagement_rank > 0.0
    print(f"✓ Engagement rank after 10 messages: {conv.engagement_rank:.3f}")


def test_user_timestamp_search():
    """Test user-based timestamp search."""
    print("\nTest 7: User timestamp search...")
    service = ConversationHistoryService("/tmp/test_conversations_standalone_timestamp")
    
    user_id = "timestamp_test_user"
    
    # Create older conversation
    conv1 = service.create_conversation(user_id=user_id)
    conv1.created_at = datetime.utcnow() - timedelta(days=5)
    service.save_conversation(conv1)
    
    # Create recent conversation
    conv2 = service.create_conversation(user_id=user_id)
    conv2.created_at = datetime.utcnow()
    service.save_conversation(conv2)
    
    # Search for conversations from last 2 days
    start_time = datetime.utcnow() - timedelta(days=2)
    results = service.search_by_user_timestamp(
        user_id=user_id,
        start_timestamp=start_time,
    )
    
    assert len(results) == 1
    print(f"✓ Found {len(results)} recent conversations for user")


def test_statistics():
    """Test statistics generation."""
    print("\nTest 8: Statistics...")
    service = ConversationHistoryService("/tmp/test_conversations_standalone_stats")
    
    # Create test data
    for i in range(3):
        conv = service.create_conversation(
            user_id=f"user{i}",
            tags=[f"tag{i}", "common"],
        )
        conv.add_message("user", f"Message {i}")
        service.save_conversation(conv)
    
    stats = service.get_statistics()
    assert stats["total_conversations"] == 3
    assert stats["total_messages"] == 3
    assert "common" in stats["unique_tags"]
    print(f"✓ Statistics: {stats}")


def run_all_tests():
    """Run all standalone tests."""
    print("="*60)
    print("CONVERSATION HISTORY FUNCTIONALITY TESTS")
    print("="*60)
    
    test_conversation_creation()
    test_message_handling()
    test_tag_management()
    test_filtering_by_tags()
    test_keyword_search()
    test_engagement_rank()
    test_user_timestamp_search()
    test_statistics()
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED")
    print("="*60)


if __name__ == "__main__":
    run_all_tests()
