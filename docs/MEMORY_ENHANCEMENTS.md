# Memory Optimization and Conversation History Enhancements

This document describes the enhancements made to Kor'tana's memory system and conversation history management.

## 1. Memory Caching Layer

### Overview
Added an LRU (Least Recently Used) cache to improve performance when accessing frequently used memories.

### Features
- **Configurable cache size**: Default 100 items, customizable per instance
- **Automatic eviction**: Removes least recently used items when cache is full
- **Access tracking**: Tracks how many times each memory is accessed
- **Timestamp tracking**: Records when each memory was last accessed
- **Statistics**: Provides insights into cache usage and performance

### Usage Example

```python
from kortana.memory.memory_manager import MemoryManager
from config.schema import KortanaConfig

# Initialize with custom cache size
settings = KortanaConfig()
memory_manager = MemoryManager(settings, cache_size=200)

# Search operations will now use caching
results = memory_manager.search_memory(query_vector, top_k=5)

# Get cache statistics
stats = memory_manager.get_cache_stats()
print(f"Cache size: {stats['size']}/{stats['max_size']}")
print(f"Total accesses: {stats['total_accesses']}")

# Clear cache if needed
memory_manager.clear_cache()
```

### Performance Benefits
- Reduces Pinecone API calls for repeated queries
- Faster response times for frequently accessed memories
- Reduced latency for common search patterns

## 2. Conversation History Archiving

### Overview
Implemented a comprehensive archiving system for managing conversation history over time.

### Features
- **Automatic archiving**: Archives conversations older than a configurable threshold (default: 30 days)
- **Compression**: Optional gzip compression to save storage space
- **Organized storage**: Archives organized by year-month for easy management
- **Retrieval**: Fast retrieval of archived conversations by ID
- **Pruning**: Automated pruning of old conversations from active memory
- **Statistics**: Detailed statistics about archived conversations

### Usage Example

```python
from kortana.memory.conversation_archive import ConversationArchive

# Initialize archive manager
archive = ConversationArchive(
    archive_dir="data/archives",
    max_active_conversations=100,
    archive_after_days=30,
    compress_archives=True
)

# Check if a conversation should be archived
from datetime import datetime, timedelta
old_date = datetime.now() - timedelta(days=60)
should_archive = archive.should_archive(old_date)

# Archive a conversation
conversation_data = {
    "timestamp": old_date.isoformat(),
    "messages": [...],
    "metadata": {...}
}
archive.archive_conversation("conv_123", conversation_data)

# Retrieve an archived conversation
retrieved = archive.retrieve_archived_conversation("conv_123")

# Prune old conversations from active list
active_conversations = [...]  # List of active conversations
remaining, archived_count = archive.prune_old_conversations(active_conversations)
print(f"Archived {archived_count} conversations")

# Get archive statistics
stats = archive.get_archive_statistics()
print(f"Total archived: {stats['total_archived_conversations']}")
print(f"Total size: {stats['total_size_mb']} MB")
```

### Storage Structure
```
data/archives/
├── 2024-01/
│   ├── conv_123.json.gz
│   ├── conv_456.json.gz
│   └── ...
├── 2024-02/
│   └── ...
└── 2024-03/
    └── ...
```

## 3. Enhanced Metadata Tracking

### Overview
Extended the MemoryEntry class with comprehensive metadata tracking for better traceability.

### Features
- **Creation timestamp**: Records when each memory was created
- **Access tracking**: Tracks last access time and access count
- **Custom metadata**: Supports arbitrary metadata fields
- **Persistence**: Metadata is preserved across save/load operations

### Usage Example

```python
from kortana.memory.memory import MemoryEntry

# Create a memory entry with custom metadata
entry = MemoryEntry(
    text="Important conversation point",
    tags=["important", "project"],
    metadata={
        "user_id": "user_123",
        "session_id": "session_456",
        "importance": "high",
        "category": "work"
    }
)

# Access the memory (updates metadata)
entry.update_access_metadata()

# Check metadata
print(f"Created: {entry.metadata['created_at']}")
print(f"Last accessed: {entry.metadata['last_accessed']}")
print(f"Access count: {entry.metadata['access_count']}")
print(f"User ID: {entry.metadata['user_id']}")

# Metadata is preserved in dict conversion
data = entry.to_dict()
restored = MemoryEntry.from_dict(data)
```

### Default Metadata Fields
- `created_at`: ISO format timestamp of creation
- `last_accessed`: ISO format timestamp of last access
- `access_count`: Number of times the memory has been accessed

### Custom Metadata
You can add any custom metadata fields to track additional information:
- User identification
- Session information
- Importance/priority levels
- Categories or classifications
- Source information
- Context data

## 4. Configuration

### Memory Manager Configuration

```python
from config.schema import KortanaConfig

settings = KortanaConfig()

# Initialize with custom cache size
memory_manager = MemoryManager(
    settings=settings,
    cache_size=100  # Adjust based on memory availability
)
```

### Archive Configuration

```python
archive = ConversationArchive(
    archive_dir="data/archives",           # Where to store archives
    max_active_conversations=100,          # Max before pruning
    archive_after_days=30,                 # Age threshold for archiving
    compress_archives=True                 # Enable compression
)
```

## 5. Testing

### Running Tests

The implementation includes comprehensive tests for all new features:

```bash
# Test memory cache
pytest tests/test_memory_cache.py -v

# Test conversation archiving
pytest tests/test_conversation_archive.py -v

# Test metadata tracking
pytest tests/test_memory_metadata.py -v
```

### Test Coverage
- Cache initialization and operations
- LRU eviction behavior
- Access tracking
- Archive creation and retrieval
- Conversation pruning
- Metadata persistence
- Statistics generation

## 6. Migration Guide

### Existing Code Compatibility

The changes are backward compatible. Existing code will continue to work without modifications.

### Enabling New Features

To enable caching:
```python
# Old code (still works)
memory_manager = MemoryManager(settings)

# New code with caching
memory_manager = MemoryManager(settings, cache_size=100)
```

To enable archiving:
```python
from kortana.memory.conversation_archive import ConversationArchive

# Add to your initialization code
archive = ConversationArchive(
    archive_dir="data/archives",
    archive_after_days=30
)

# Periodically prune old conversations
remaining, count = archive.prune_old_conversations(active_conversations)
```

## 7. Performance Considerations

### Cache Size
- Larger cache = better hit rate but more memory usage
- Recommended: 100-500 for typical usage
- Monitor cache statistics to optimize size

### Archive Compression
- Compression saves ~70-80% storage space
- Slight CPU overhead during archive/retrieve
- Recommended for production use

### Pruning Frequency
- Run pruning daily or weekly depending on volume
- Consider running during off-peak hours
- Monitor archive growth rate

## 8. Future Enhancements

Potential future improvements:
- [ ] Cache warming on startup
- [ ] Tiered archiving (hot/warm/cold storage)
- [ ] Async archiving operations
- [ ] Archive search and indexing
- [ ] Metadata-based querying
- [ ] Export/import functionality
