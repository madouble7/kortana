"""
Memory Management

This module provides memory management functionality for Kor'tana,
including JSON-based logging and the memory journal system.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from kortana.config.schema import KortanaConfig

logger = logging.getLogger(__name__)


class MemoryEntry:
    """Represents a single memory entry."""

    def __init__(
        self,
        text: str,
        timestamp: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        source: str = "conversation",
        embedding: Optional[List[float]] = None,
        id: Optional[str] = None,
    ):
        self.text = text
        self.timestamp = timestamp or datetime.now()
        self.tags = tags or []
        self.source = source
        self.embedding = embedding or []
        self.id = id or f"{source}-{self.timestamp.isoformat()}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert the memory entry to a dictionary."""
        return {
            "id": self.id,
            "text": self.text,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
            "source": self.source,
            "embedding": self.embedding,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        """Create a memory entry from a dictionary."""
        timestamp = (
            datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else None
        )
        return cls(
            text=data["text"],
            timestamp=timestamp,
            tags=data.get("tags", []),
            source=data.get("source", "conversation"),
            embedding=data.get("embedding", []),
            id=data.get("id"),
        )


class MemoryManager:
    """
    Memory manager for Kor'tana using JSON logs.
    Handles heart.log, soul.index.jsonl, and lit.log.jsonl.
    """

    def __init__(self, settings: KortanaConfig):
        """
        Initialize the memory manager.

        Args:
            settings: The application configuration.
        """
        self.settings = settings

        # Set paths from settings
        self.heart_log_path = self.settings.paths.heart_log_path
        self.soul_index_path = self.settings.paths.soul_index_path
        self.lit_log_path = self.settings.paths.lit_log_path
        self.project_memory_path = self.settings.paths.project_memory_file_path

        # Ensure directories exist
        for path in [
            self.heart_log_path,
            self.soul_index_path,
            self.lit_log_path,
            self.project_memory_path,
        ]:
            os.makedirs(os.path.dirname(path), exist_ok=True)

    def add_heart_memory(self, text: str, tags: Optional[List[str]] = None) -> bool:
        """
        Add a memory to the heart log.

        Args:
            text: The memory text.
            tags: Optional list of tags.

        Returns:
            True if successful, False otherwise.
        """
        try:
            entry = MemoryEntry(text=text, tags=tags or ["heart"], source="heart")

            with open(self.heart_log_path, "a") as f:
                f.write(json.dumps(entry.to_dict()) + "\n")

            logger.info(f"Added heart memory: {text[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to add heart memory: {e}")
            return False

    def add_soul_memory(
        self, text: str, pattern: str, tags: Optional[List[str]] = None
    ) -> bool:
        """
        Add a memory to the soul index.

        Args:
            text: The memory text.
            pattern: The pattern this memory represents.
            tags: Optional list of tags.

        Returns:
            True if successful, False otherwise.
        """
        try:
            entry = MemoryEntry(
                text=text,
                tags=(tags or []) + ["soul", f"pattern:{pattern}"],
                source="soul",
            )

            with open(self.soul_index_path, "a") as f:
                f.write(json.dumps(entry.to_dict()) + "\n")

            logger.info(f"Added soul memory for pattern '{pattern}': {text[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to add soul memory: {e}")
            return False

    def add_lit_memory(
        self, text: str, ritual: str, tags: Optional[List[str]] = None
    ) -> bool:
        """
        Add a memory to the lit log.

        Args:
            text: The memory text.
            ritual: The ritual associated with this memory.
            tags: Optional list of tags.

        Returns:
            True if successful, False otherwise.
        """
        try:
            entry = MemoryEntry(
                text=text, tags=(tags or []) + ["lit", f"ritual:{ritual}"], source="lit"
            )

            with open(self.lit_log_path, "a") as f:
                f.write(json.dumps(entry.to_dict()) + "\n")

            logger.info(f"Added lit memory for ritual '{ritual}': {text[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to add lit memory: {e}")
            return False

    def get_heart_memories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get memories from the heart log.

        Args:
            limit: Maximum number of memories to return.

        Returns:
            List of memory entries.
        """
        try:
            memories = []
            if os.path.exists(self.heart_log_path):
                with open(self.heart_log_path, "r") as f:
                    for line in f:
                        if line.strip():
                            memories.append(json.loads(line))
                            if len(memories) >= limit:
                                break
            return memories
        except Exception as e:
            logger.error(f"Failed to get heart memories: {e}")
            return []

    def get_soul_memories(
        self, pattern: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get memories from the soul index.

        Args:
            pattern: Optional pattern to filter by.
            limit: Maximum number of memories to return.

        Returns:
            List of memory entries.
        """
        try:
            memories = []
            if os.path.exists(self.soul_index_path):
                with open(self.soul_index_path, "r") as f:
                    for line in f:
                        if line.strip():
                            entry = json.loads(line)
                            if pattern is None or f"pattern:{pattern}" in entry.get(
                                "tags", []
                            ):
                                memories.append(entry)
                                if len(memories) >= limit:
                                    break
            return memories
        except Exception as e:
            logger.error(f"Failed to get soul memories: {e}")
            return []

    def get_lit_memories(
        self, ritual: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get memories from the lit log.

        Args:
            ritual: Optional ritual to filter by.
            limit: Maximum number of memories to return.

        Returns:
            List of memory entries.
        """
        try:
            memories = []
            if os.path.exists(self.lit_log_path):
                with open(self.lit_log_path, "r") as f:
                    for line in f:
                        if line.strip():
                            entry = json.loads(line)
                            if ritual is None or f"ritual:{ritual}" in entry.get(
                                "tags", []
                            ):
                                memories.append(entry)
                                if len(memories) >= limit:
                                    break
            return memories
        except Exception as e:
            logger.error(f"Failed to get lit memories: {e}")
            return []


def load_memory(file_path: str) -> List[Dict[str, Any]]:
    """
    Load memory from a JSONL file.

    Args:
        file_path: Path to the memory file.

    Returns:
        List of memory entries.
    """
    memories = []
    try:
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                for line in f:
                    if line.strip():
                        memories.append(json.loads(line))
        logger.info(f"Loaded {len(memories)} memories from {file_path}")
        return memories
    except Exception as e:
        logger.error(f"Failed to load memory from {file_path}: {e}")
        return []


def save_memory(memories: List[Dict[str, Any]], file_path: str) -> bool:
    """
    Save memory to a JSONL file.

    Args:
        memories: List of memory entries.
        file_path: Path to the memory file.

    Returns:
        True if successful, False otherwise.
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w") as f:
            for memory in memories:
                f.write(json.dumps(memory) + "\n")

        logger.info(f"Saved {len(memories)} memories to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save memory to {file_path}: {e}")
        return False


class JsonMemoryStore:
    """Memory store using JSON files."""

    def __init__(self, file_path: str):
        """Initialize the memory store."""
        self.file_path = file_path
        self.memories = load_memory(file_path)

    def add(self, memory: Dict[str, Any]) -> bool:
        """Add a memory entry."""
        self.memories.append(memory)
        return save_memory(self.memories, self.file_path)

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all memory entries."""
        return self.memories

    def save(self) -> bool:
        """Save all memories to file."""
        return save_memory(self.memories, self.file_path)
