"""
Functions to replace in brain.py to fix syntax errors and continue refactoring.
"""

import logging
from typing import Any

# Configure logger
logger = logging.getLogger(__name__)


# New implementations of refactored memory context functions
async def get_semantic_search_context(self, user_message: str, limit: int = 5) -> str:
    """Get formatted context from semantic search results."""
    if not self._is_semantic_search_enabled():
        return ""

    try:
        # Get vector memories relevant to the query
        memories = await self._retrieve_semantic_memories(user_message, limit)

        # Format memories if found
        if not memories:
            return ""

        return self._format_semantic_context(memories)
    except Exception as e:
        logger.error(f"Error during semantic search: {e}")
        return ""


def is_semantic_search_enabled(self) -> bool:
    """Check if semantic search functionality is enabled."""
    return bool(self.memory_manager and self.memory_manager.pinecone_enabled)


async def retrieve_semantic_memories(
    self, user_message: str, limit: int = 5
) -> list[dict[str, Any]]:
    """Retrieve semantic memories related to the query text.

    Args:
        user_message: The query text
        limit: Maximum number of memories to retrieve

    Returns:
        List of memory entries
    """
    try:
        from kortana.brain_utils import generate_embedding

        # Generate embedding vector for the query using our optimized utility function
        query_vector = generate_embedding(user_message)

        # Search for relevant memories
        return self.memory_manager.search_memory(query_vector=query_vector, top_k=limit)
    except Exception as e:
        logger.error(f"Error retrieving semantic memories: {e}")
        return []


def format_semantic_context(self, memories: list[dict[str, Any]]) -> str:
    """Format semantic memory results into a context string.

    Args:
        memories: List of memory entries

    Returns:
        Formatted context string
    """
    context_lines = ["Relevant insights from memory:"]
    context_lines.extend(self._format_semantic_memories(memories))
    return "\n".join(context_lines)


# Fix for the get_conversation_history_context function
def get_conversation_history_context(self) -> str:
    """Get formatted context from recent conversation history."""
    context_lines: list[str] = []
    try:
        # Get the most recent history entries (up to 10)
        if len(self.history) > 0:
            history_to_consider = self.history[-min(len(self.history), 10) :]
            context_lines.append("Recent conversation turns:")
            for entry in history_to_consider:
                role = entry.get("role", "unknown")
                content = entry.get("content", "")
                context_lines.append(f"  {role}: {content}")
        return "\n".join(context_lines)
    except Exception as e:
        logger.error(f"Error getting conversation history context: {e}")
        return ""
