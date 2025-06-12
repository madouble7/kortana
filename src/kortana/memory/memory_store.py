"""
Abstract base class for memory storage systems.
This module defines the interface for memory storage backends.
"""

from abc import ABC, abstractmethod
from typing import Any


class MemoryStore(ABC):
    """
    Abstract base class for memory storage implementations.
    Defines the interface that all memory stores must implement.
    """

    @abstractmethod
    def add_memory(self, memory: dict[str, Any]) -> None:
        """
        Add a memory entry to the store.

        Args:
            memory: A dictionary containing the memory information
        """
        pass

    @abstractmethod
    def query_memories(
        self, query: str, top_k: int = 5, tags: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """
        Query memories based on a text query and optional tags.

        Args:
            query: The text query to search for
            top_k: Maximum number of results to return
            tags: Optional list of tags to filter by

        Returns:
            List of memory entries matching the query
        """
        pass

    @abstractmethod
    def delete_memory(self, memory_id: str) -> None:
        """
        Delete a memory entry by its ID.

        Args:
            memory_id: The unique identifier of the memory to delete
        """
        pass

    @abstractmethod
    def tag_memory(self, memory_id: str, tags: list[str]) -> None:
        """
        Add tags to an existing memory entry.

        Args:
            memory_id: The unique identifier of the memory to tag
            tags: The tags to add to the memory
        """
        pass
