"""
Memory Manager (Pinecone)

This module provides a memory system for Kor'tana using Pinecone as the vector database.
"""

import json
import logging
from typing import Any, Dict, List

# Assuming these imports exist
import pinecone

from kortana.config.schema import KortanaConfig

from .memory import MemoryEntry

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Memory manager for Kor'tana using Pinecone as the vector database.
    Also handles the memory journal for persistent storage.
    """

    def __init__(self, settings: KortanaConfig):
        """
        Initialize the memory manager.

        Args:
            settings: The application configuration.
        """
        self.settings = settings
        self.memory_journal_path = self.settings.paths.memory_journal_path

        # Initialize Pinecone
        pinecone_api_key = self.settings.get_api_key("pinecone")
        if not pinecone_api_key:
            logger.warning(
                "Pinecone API key not found. Memory system will operate in limited mode."
            )
            self.pinecone_enabled = False
        else:
            try:
                pinecone.init(
                    api_key=pinecone_api_key,
                    environment=self.settings.pinecone.environment,
                )

                # Check if index exists, if not create it
                if self.settings.pinecone.index_name not in pinecone.list_indexes():
                    logger.info(
                        f"Creating Pinecone index: {self.settings.pinecone.index_name}"
                    )
                    pinecone.create_index(
                        name=self.settings.pinecone.index_name,
                        dimension=1536,  # OpenAI embedding dimension
                        metric="cosine",
                    )

                self.index = pinecone.Index(self.settings.pinecone.index_name)
                self.pinecone_enabled = True
                logger.info("Pinecone memory system initialized successfully")

            except Exception as e:
                logger.error(f"Failed to initialize Pinecone: {e}")
                self.pinecone_enabled = False

    def load_project_memory(self) -> List[Dict[str, Any]]:
        """
        Load project memory from the memory journal.

        Returns:
            List of memory entries.
        """
        try:
            with open(self.memory_journal_path, "r") as f:
                memory_entries = [json.loads(line) for line in f.readlines()]
            logger.info(
                f"Loaded {len(memory_entries)} memory entries from {self.memory_journal_path}"
            )
            return memory_entries
        except FileNotFoundError:
            logger.warning(
                f"Memory journal not found: {self.memory_journal_path}. Starting with empty memory."
            )
            return []
        except Exception as e:
            logger.error(f"Failed to load memory journal: {e}")
            return []

    def save_project_memory(self, memory_entries: List[Dict[str, Any]]) -> bool:
        """
        Save project memory to the memory journal.

        Args:
            memory_entries: List of memory entries.

        Returns:
            True if successful, False otherwise.
        """
        try:
            with open(self.memory_journal_path, "w") as f:
                for entry in memory_entries:
                    f.write(json.dumps(entry) + "\n")
            logger.info(
                f"Saved {len(memory_entries)} memory entries to {self.memory_journal_path}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to save memory journal: {e}")
            return False

    def add_memory(self, memory_entry: MemoryEntry) -> bool:
        """
        Add a memory entry to the system.

        Args:
            memory_entry: The memory entry to add.

        Returns:
            True if successful, False otherwise.
        """
        if not self.pinecone_enabled:
            logger.warning(
                "Pinecone not enabled. Memory will only be saved to journal."
            )
            return self._add_to_journal(memory_entry)

        try:
            # Add to Pinecone
            vector_id = memory_entry.id
            vector = memory_entry.embedding
            metadata = {
                "text": memory_entry.text,
                "timestamp": str(memory_entry.timestamp),
                "tags": memory_entry.tags,
                "source": memory_entry.source,
            }

            self.index.upsert([(vector_id, vector, metadata)])

            # Also add to journal for backup
            self._add_to_journal(memory_entry)

            return True
        except Exception as e:
            logger.error(f"Failed to add memory to Pinecone: {e}")
            return False

    def search_memory(
        self, query_vector: List[float], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar memories.

        Args:
            query_vector: The query vector.
            top_k: Number of results to return.

        Returns:
            List of matching memory entries.
        """
        if not self.pinecone_enabled:
            logger.warning("Pinecone not enabled. Cannot perform vector search.")
            return []

        try:
            results = self.index.query(
                vector=query_vector, top_k=top_k, include_metadata=True
            )

            return [
                {
                    "id": match["id"],
                    "score": match["score"],
                    "text": match["metadata"]["text"],
                    "timestamp": match["metadata"]["timestamp"],
                    "tags": match["metadata"].get("tags", []),
                    "source": match["metadata"].get("source", "unknown"),
                }
                for match in results.matches
            ]
        except Exception as e:
            logger.error(f"Failed to search Pinecone: {e}")
            return []

    def _add_to_journal(self, memory_entry: MemoryEntry) -> bool:
        """Add a memory entry to the journal file."""
        try:
            with open(self.memory_journal_path, "a") as f:
                f.write(json.dumps(memory_entry.to_dict()) + "\n")
            return True
        except Exception as e:
            logger.error(f"Failed to add memory to journal: {e}")
            return False
            return False
