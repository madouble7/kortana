"""
Memory Manager (Pinecone)

This module provides a memory system for Kor'tana using Pinecone as the vector database.
"""

import json
import logging
import os
from functools import lru_cache
from typing import Any

# Modern Pinecone SDK import
try:
    from pinecone import Pinecone  # Main import for Pinecone client v3+

    PINECONE_SDK_AVAILABLE = True
except ImportError:
    try:
        import pinecone  # Fallback for older versions

        Pinecone = pinecone.Pinecone
        PINECONE_SDK_AVAILABLE = True
    except ImportError:
        Pinecone = None  # type: ignore  # Make linters aware Pinecone might be None
        PINECONE_SDK_AVAILABLE = False
        logging.getLogger(__name__).warning(
            "Pinecone SDK not found. Pinecone features will be disabled."
        )

from config.schema import KortanaConfig  # Assuming this path is now correct

from .memory import MemoryEntry

logger = logging.getLogger(__name__)


# Cache for the most recently used embeddings to avoid recomputing
@lru_cache(maxsize=128)
def _cached_embedding_lookup(text_hash: int) -> list[float] | None:
    """Cache lookup for text embeddings based on hash.

    Args:
        text_hash: Hash of the text to look up

    Returns:
        Cached embedding vector if available, None otherwise
    """
    # This is a placeholder - values are inserted by the embedding generation function
    return None


class MemoryManager:
    """Memory manager for Kor'tana using Pinecone as the vector database."""

    pinecone_enabled: bool = False
    pinecone_namespace: str | None = None
    index: Any = None  # For Pinecone Index object
    pc: Any | None = (
        None  # Pinecone client instance, type Any to avoid linter issues with conditional import
    )

    def __init__(self, settings: KortanaConfig):
        self.settings = settings
        logger.info(f"MemoryManager received settings of type: {type(settings)}")
        try:
            settings_json = settings.model_dump_json(indent=2)
            logger.debug(f"MemoryManager received settings (JSON):\n{settings_json}")
        except Exception as e:
            logger.error(f"Could not serialize settings to JSON in MemoryManager: {e}")
            logger.debug(f"MemoryManager received settings (raw): {settings}")

        self.user_name = os.getenv("KORTANA_USER_NAME", "default")

        data_dir = getattr(settings, "data_dir", "data")
        if not hasattr(settings, "data_dir"):
            logger.warning(
                "settings.data_dir not found, defaulting to 'data'. Check KortanaConfig initialization."
            )

        user_specific_data_path = os.path.join(data_dir, "users", self.user_name)
        self.memory_journal_path = os.path.join(
            user_specific_data_path, "memory_journal.jsonl"
        )
        self.heart_log_path = os.path.join(user_specific_data_path, "heart.log")
        self.soul_index_path = os.path.join(user_specific_data_path, "soul_index.json")
        self.lit_log_path = os.path.join(user_specific_data_path, "lit.log")
        self.project_memory_path = os.path.join(
            user_specific_data_path, "project_memory.jsonl"
        )

        paths_to_ensure = [
            self.memory_journal_path,
            self.heart_log_path,
            self.soul_index_path,
            self.lit_log_path,
            self.project_memory_path,
        ]
        for path_to_ensure in paths_to_ensure:
            os.makedirs(os.path.dirname(path_to_ensure), exist_ok=True)

        memory_settings = getattr(settings, "memory", None)
        if not memory_settings:
            logger.warning(
                "settings.memory not found. Pinecone will be disabled. Check KortanaConfig initialization."
            )
            self.pinecone_enabled = False
            return

        pinecone_api_key = getattr(memory_settings, "pinecone_api_key", None)
        pinecone_index_name = getattr(
            memory_settings, "pinecone_index_name", "kortana-memory"
        )

        if not pinecone_api_key:
            logger.warning(
                "Pinecone API key not found in settings.memory.pinecone_api_key. Pinecone features disabled."
            )
            self.pinecone_enabled = False
        elif (
            not PINECONE_SDK_AVAILABLE or Pinecone is None
        ):  # Check if Pinecone class itself is None
            logger.warning(
                "Pinecone SDK not available/installed correctly. Pinecone features disabled."
            )
            self.pinecone_enabled = False
        else:
            try:
                logger.info(
                    f"Initializing Pinecone client with API key ending: ...{pinecone_api_key[-4:]}"
                )
                self.pc = Pinecone(
                    api_key=pinecone_api_key
                )  # Initialize Pinecone client

                if self.pc:  # Ensure client was initialized
                    self.index = self.pc.Index(pinecone_index_name)
                    self.pinecone_namespace = f"kortana_user_{self.user_name}"
                    self.pinecone_enabled = True
                    logger.info(
                        f"Pinecone memory system initialized for index '{pinecone_index_name}', namespace '{self.pinecone_namespace}'."
                    )
                else:
                    logger.error(
                        "Pinecone client (self.pc) is None after initialization attempt."
                    )
                    self.pinecone_enabled = False

            except Exception as e:
                logger.error(f"Failed to initialize Pinecone (modern SDK): {e}")
                self.pinecone_enabled = False

    def load_project_memory(self) -> list[dict[str, Any]]:
        """
        Load project memory from the memory journal.

        Returns:
            List of memory entries.
        """
        try:
            with open(self.memory_journal_path) as f:
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

    def save_project_memory(self, memory_entries: list[dict[str, Any]]) -> bool:
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

            self.index.upsert(
                [(vector_id, vector, metadata)], namespace=self.pinecone_namespace
            )

            # Also add to journal for backup
            self._add_to_journal(memory_entry)

            return True
        except Exception as e:
            logger.error(f"Failed to add memory to Pinecone: {e}")
            return False

    def search_memory(
        self, query_vector: list[float], top_k: int = 5
    ) -> list[dict[str, Any]]:
        """Search for similar memories using Pinecone."""
        if not self.pinecone_enabled or not self.index:
            logger.warning("Pinecone is not enabled or index is not initialized.")
            return []

        try:
            results = self.index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True,
                namespace=self.pinecone_namespace,
            )

            return [
                {
                    "id": match["id"],
                    "score": match["score"],
                    "text": match["metadata"].get("text", ""),
                    "timestamp": match["metadata"].get("timestamp", ""),
                    "tags": match["metadata"].get("tags", []),
                    "source": match["metadata"].get("source", "unknown"),
                }
                for match in results.matches
            ]
        except Exception as e:
            logger.error(f"Failed to search Pinecone: {e}")
            return []

    def append_to_memory_journal(self, memory_entry: MemoryEntry) -> None:
        """Append a memory entry to the journal."""
        try:
            with open(self.memory_journal_path, "a") as journal:
                journal.write(json.dumps(memory_entry.to_dict()) + "\n")
            logger.info(f"Memory entry appended to journal: {self.memory_journal_path}")
        except Exception as e:
            logger.error(
                f"Failed to append memory entry to {self.memory_journal_path}: {e}"
            )

    def _add_to_journal(self, memory_entry: MemoryEntry) -> bool:
        """Add a memory entry to the journal file."""
        try:
            with open(self.memory_journal_path, "a") as f:
                f.write(json.dumps(memory_entry.to_dict()) + "\n")
            return True
        except Exception as e:
            logger.error(f"Failed to add memory to journal: {e}")
            return False
