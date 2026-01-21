"""
Example integration demonstrating the memory optimization and conversation archiving features.

This script shows how to use the new caching, archiving, and metadata tracking features together.
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Note: This example requires proper configuration setup
# For testing purposes, we'll use mock data


def example_memory_caching():
    """Demonstrate memory caching functionality."""
    print("=" * 60)
    print("Example 1: Memory Caching")
    print("=" * 60)
    
    # Simulate the cache behavior without full initialization
    from collections import OrderedDict
    
    class SimpleMemoryCache:
        def __init__(self, max_size=100):
            self.max_size = max_size
            self.cache = OrderedDict()
            self.access_counts = {}
        
        def get(self, key):
            if key in self.cache:
                self.cache.move_to_end(key)
                self.access_counts[key] = self.access_counts.get(key, 0) + 1
                return self.cache[key]
            return None
        
        def put(self, key, value):
            if key in self.cache:
                self.cache.move_to_end(key)
            else:
                if len(self.cache) >= self.max_size:
                    removed_key, _ = self.cache.popitem(last=False)
                    self.access_counts.pop(removed_key, None)
                    print(f"  Cache full, evicted: {removed_key}")
            
            self.cache[key] = value
            self.access_counts[key] = self.access_counts.get(key, 0) + 1
    
    # Create a cache
    cache = SimpleMemoryCache(max_size=3)
    
    # Add some memories
    print("\n1. Adding memories to cache:")
    cache.put("memory_1", {"text": "First memory", "score": 0.95})
    print("   Added memory_1")
    cache.put("memory_2", {"text": "Second memory", "score": 0.88})
    print("   Added memory_2")
    cache.put("memory_3", {"text": "Third memory", "score": 0.92})
    print("   Added memory_3")
    
    # Access a memory
    print("\n2. Accessing cached memory:")
    result = cache.get("memory_1")
    print(f"   Retrieved: {result}")
    
    # Add another memory (will evict least recently used)
    print("\n3. Adding memory when cache is full:")
    cache.put("memory_4", {"text": "Fourth memory", "score": 0.87})
    
    # Try to get the evicted memory
    print("\n4. Attempting to access evicted memory:")
    result = cache.get("memory_2")
    print(f"   Result: {result} (was evicted)")
    
    print("\n5. Current cache contents:")
    for key in cache.cache.keys():
        print(f"   - {key} (accessed {cache.access_counts[key]} times)")


def example_conversation_archiving():
    """Demonstrate conversation archiving functionality."""
    print("\n\n" + "=" * 60)
    print("Example 2: Conversation Archiving")
    print("=" * 60)
    
    # Create example conversations with different ages
    print("\n1. Creating example conversations:")
    
    conversations = [
        {
            "id": "conv_001",
            "timestamp": (datetime.now() - timedelta(days=45)).isoformat(),
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ],
            "age_days": 45
        },
        {
            "id": "conv_002",
            "timestamp": (datetime.now() - timedelta(days=60)).isoformat(),
            "messages": [
                {"role": "user", "content": "How are you?"},
                {"role": "assistant", "content": "I'm doing well!"}
            ],
            "age_days": 60
        },
        {
            "id": "conv_003",
            "timestamp": (datetime.now() - timedelta(days=5)).isoformat(),
            "messages": [
                {"role": "user", "content": "Recent conversation"},
                {"role": "assistant", "content": "Yes, very recent!"}
            ],
            "age_days": 5
        },
    ]
    
    for conv in conversations:
        print(f"   {conv['id']}: {conv['age_days']} days old")
    
    # Determine which should be archived (> 30 days)
    print("\n2. Determining which conversations to archive (> 30 days):")
    archive_threshold = 30
    
    to_archive = []
    to_keep = []
    
    for conv in conversations:
        if conv["age_days"] > archive_threshold:
            to_archive.append(conv)
            print(f"   ✓ Archive: {conv['id']} ({conv['age_days']} days)")
        else:
            to_keep.append(conv)
            print(f"   ✗ Keep active: {conv['id']} ({conv['age_days']} days)")
    
    print(f"\n3. Summary:")
    print(f"   Total conversations: {len(conversations)}")
    print(f"   To archive: {len(to_archive)}")
    print(f"   Remain active: {len(to_keep)}")
    
    # Show archive structure
    print(f"\n4. Archive structure (year-month organization):")
    for conv in to_archive:
        timestamp = datetime.fromisoformat(conv["timestamp"])
        year_month = timestamp.strftime("%Y-%m")
        print(f"   data/archives/{year_month}/{conv['id']}.json.gz")


def example_metadata_tracking():
    """Demonstrate metadata tracking functionality."""
    print("\n\n" + "=" * 60)
    print("Example 3: Enhanced Metadata Tracking")
    print("=" * 60)
    
    # Simulate a memory entry
    class MemoryWithMetadata:
        def __init__(self, text, tags=None, metadata=None):
            self.text = text
            self.tags = tags or []
            self.metadata = metadata or {}
            
            # Add default metadata
            if "created_at" not in self.metadata:
                self.metadata["created_at"] = datetime.now().isoformat()
            if "last_accessed" not in self.metadata:
                self.metadata["last_accessed"] = datetime.now().isoformat()
            if "access_count" not in self.metadata:
                self.metadata["access_count"] = 0
        
        def update_access_metadata(self):
            self.metadata["last_accessed"] = datetime.now().isoformat()
            self.metadata["access_count"] += 1
    
    print("\n1. Creating a memory with custom metadata:")
    memory = MemoryWithMetadata(
        text="Important project discussion",
        tags=["project", "important"],
        metadata={
            "user_id": "user_123",
            "session_id": "session_456",
            "importance": "high",
            "category": "work"
        }
    )
    
    print(f"   Text: {memory.text}")
    print(f"   Tags: {memory.tags}")
    print(f"   Custom metadata:")
    print(f"     - User ID: {memory.metadata['user_id']}")
    print(f"     - Session ID: {memory.metadata['session_id']}")
    print(f"     - Importance: {memory.metadata['importance']}")
    print(f"     - Category: {memory.metadata['category']}")
    
    print("\n2. Automatic metadata tracking:")
    print(f"   Created at: {memory.metadata['created_at']}")
    print(f"   Last accessed: {memory.metadata['last_accessed']}")
    print(f"   Access count: {memory.metadata['access_count']}")
    
    print("\n3. Simulating memory accesses:")
    for i in range(3):
        memory.update_access_metadata()
        print(f"   Access #{i+1} - Count: {memory.metadata['access_count']}")
    
    print(f"\n4. Final metadata state:")
    print(f"   Total accesses: {memory.metadata['access_count']}")
    print(f"   Last accessed: {memory.metadata['last_accessed']}")


def example_integrated_usage():
    """Demonstrate integrated usage of all features."""
    print("\n\n" + "=" * 60)
    print("Example 4: Integrated Usage Scenario")
    print("=" * 60)
    
    print("\nScenario: Managing a conversation history with memory optimization")
    
    print("\n1. User starts a conversation:")
    print("   - System creates new conversation with metadata")
    print("   - Tracks session ID, user ID, timestamp")
    
    print("\n2. User searches for relevant memories:")
    print("   - System checks cache first (fast)")
    print("   - Cache miss -> queries Pinecone")
    print("   - Results cached for future queries")
    print("   - Access metadata updated")
    
    print("\n3. Conversation continues over time:")
    print("   - Each message stored with full metadata")
    print("   - Frequently accessed memories remain in cache")
    print("   - Less used memories naturally evicted")
    
    print("\n4. Daily archival process:")
    print("   - Scan conversations older than 30 days")
    print("   - Archive to compressed year-month folders")
    print("   - Remove from active memory")
    print("   - Keep cache for recent hot data")
    
    print("\n5. Benefits:")
    print("   ✓ Fast access to frequent queries (cache)")
    print("   ✓ Reduced storage for old data (compression)")
    print("   ✓ Full traceability (metadata)")
    print("   ✓ Scalable as data grows (archiving)")


def main():
    """Run all examples."""
    print("\n")
    print("*" * 60)
    print("MEMORY OPTIMIZATION & CONVERSATION HISTORY")
    print("Feature Demonstration")
    print("*" * 60)
    
    example_memory_caching()
    example_conversation_archiving()
    example_metadata_tracking()
    example_integrated_usage()
    
    print("\n" + "=" * 60)
    print("Examples completed successfully!")
    print("=" * 60)
    print("\nFor full documentation, see: docs/MEMORY_ENHANCEMENTS.md")
    print()


if __name__ == "__main__":
    main()
