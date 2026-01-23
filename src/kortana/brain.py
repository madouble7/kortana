"""
Kor'tana Core Brain with Memory Integration

This module implements the ChatEngine class that powers Kor'tana's conversational abilities
with integrated memory management following the Phase 3 blueprint.
"""

import logging
import os
import uuid
from datetime import UTC, datetime
from typing import Any

from kortana.config.schema import KortanaConfig

# Corrected imports for sanitize_user_input and extract_keywords_from_text
from kortana.brain_utils import (
    append_to_memory_journal,
    extract_keywords_from_text,
    load_json_config,
    sanitize_user_input,
)
from kortana.memory.memory import MemoryEntry
from kortana.memory.memory_manager import MemoryManager
from llm_clients.factory import LLMClientFactory
from model_router import SacredModelRouter

# Configure logging
logger = logging.getLogger(__name__)


class ChatEngine:
    """
    Core chat engine for Kor'tana with integrated memory management.

    This implementation focuses on memory integration following the blueprint:
    - Minimal memory interface for read/write operations
    - Integration with existing memory infrastructure
    - Incremental memory reintroduction to brain functionality
    """

    def __init__(self, settings: KortanaConfig, session_id: str | None = None):
        """
        Initialize the chat engine with memory integration.

        Args:
            settings: Application configuration.
            session_id: Optional session identifier.
        """
        self.settings = settings
        self.session_id = session_id or str(uuid.uuid4())
        self.mode = "default"
        self.history: list[dict[str, Any]] = []

        logger.info(f"Initializing ChatEngine with session ID {self.session_id}")

        # Initialize LLM clients
        self.llm_client_factory = LLMClientFactory(settings=self.settings)
        self.default_llm_client = self.llm_client_factory.get_client(
            self.settings.default_llm_id
        )

        # Initialize memory system - core focus of Phase 3
        self.memory_manager = MemoryManager(settings=self.settings)

        # Initialize model router
        self.router = SacredModelRouter(settings=self.settings)

        # Load persona and identity configurations
        self.persona_data = load_json_config(self.settings.paths.persona_file_path)
        self.identity_data = load_json_config(self.settings.paths.identity_file_path)

        # Load existing memories from journal
        self._load_existing_memories()

        logger.info("ChatEngine initialized with memory integration")

    def _load_existing_memories(self) -> None:
        """Load and format existing conversation memories for context-aware responses."""
        try:
            memories = self.memory_manager.load_project_memory()
            self.formatted_memories = memories
            logger.info(
                f"Loaded {len(memories)} existing memories. Formatting needs review."
            )
        except Exception as e:
            logger.error(f"Failed to load memories: {e}")

    def append_memory(self, interaction: dict[str, Any]) -> None:
        """Append a new memory entry to the journal."""
        try:
            memory_entry = MemoryEntry.from_interaction(interaction)
            self.memory_manager.append_to_memory_journal(memory_entry)
            logger.info("Memory appended successfully")
        except Exception as e:
            logger.error(f"Failed to append memory: {e}")

    def retrieve_context(self, query: str) -> list[dict[str, Any]]:
        """
        Retrieve relevant memories based on a text query.

        Args:
            query: Text query to find relevant memories

        Returns:
            List of relevant memory entries
        """
        try:
            from kortana.brain_utils import generate_embedding

            # Generate embedding vector for the query text
            query_vector = generate_embedding(query)

            # Search memory using the embedding vector
            results = self.memory_manager.search_memory(query_vector, top_k=5)

            logger.info(
                f"Retrieved {len(results)} memory entries for query: {query[:30]}..."
            )
            return results
        except Exception as e:
            logger.error(f"Failed to retrieve context: {e}")
            return []

    def add_user_message(self, message: str) -> None:
        """
        Add a user message to conversation history and memory.

        Args:
            message: User's message content
        """
        sanitized_message = sanitize_user_input(message)

        # Create message entry
        entry = self._create_message_entry("user", sanitized_message)
        # Add to history and save to memory
        self._add_message_to_history_and_memory(entry)

        logger.info(f"Added user message: {sanitized_message[:50]}...")

    def add_assistant_message(self, message: str) -> None:
        """
        Add an assistant message to conversation history and memory.

        Args:
            message: Assistant's message content
        """
        # Create message entry and add to history/memory
        entry = self._create_message_entry("assistant", message)
        self._add_message_to_history_and_memory(entry)

        logger.info(f"Added assistant message: {message[:50]}...")

    def _save_to_memory(self, entry: dict[str, Any]) -> None:
        """
        Save conversation entry to memory system.

        Args:
            entry: Conversation entry to save
        """
        try:
            # Save to journal file
            self._save_to_journal(entry)

            # Save to vector storage if enabled
            if self.memory_manager.pinecone_enabled:
                self._save_to_vector_storage(entry)

        except Exception as e:
            logger.error(f"Failed to save memory: {e}")

    def _save_to_journal(self, entry: dict[str, Any]) -> None:
        """Save an entry to the memory journal file.

        Args:
            entry: The entry to save to journal
        """
        journal_path = self.memory_manager.memory_journal_path
        append_to_memory_journal(journal_path, entry)

    def _save_to_vector_storage(self, entry: dict[str, Any]) -> None:
        """Save an entry to vector storage for semantic search.

        Args:
            entry: The entry to save to vector storage
        """
        keywords = extract_keywords_from_text(entry["content"])
        memory_entry = MemoryEntry(
            text=entry["content"],
            timestamp=datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00")),
            tags=["conversation", entry["role"]] + keywords,
            source="chat_engine",
        )
        self.memory_manager.add_memory(memory_entry)

    async def _get_memory_context(self, user_message: str, limit: int = 5) -> str:
        """
        Retrieve relevant memory context for the user message, combining
        recent conversation history and semantic search results.

        Args:
            user_message: Current user message
            limit: Maximum number of semantic memories to retrieve

        Returns:
            Formatted memory context string
        """
        try:
            # Get conversation history and semantic search results
            history_context = self._get_conversation_history_context()
            semantic_context = await self._get_semantic_search_context(
                user_message, limit
            )

            # Combine the contexts
            full_context = []
            if history_context:
                full_context.append(history_context)
            if semantic_context:
                full_context.append(semantic_context)

            return "\n".join(full_context)
        except Exception as e_main:
            logger.error(f"Error retrieving memory context: {e_main}")
            return ""

    def _get_conversation_history_context(self) -> str:
        """Get formatted context from recent conversation history."""
        context_lines: list[str] = []
        try:
            history_to_consider = self.history[-min(len(self.history), 10) :]
            if history_to_consider:
                context_lines.append("Recent conversation turns:")
                for entry in history_to_consider:
                    role = entry.get("role", "unknown")
                    content = entry.get("content", "")
                    context_lines.append(f"  {role}: {content}")

            return "\n".join(context_lines)
        except Exception as e:
            logger.error(f"Error getting conversation history context: {e}")
            return ""

    async def _get_semantic_search_context(
        self, user_message: str, limit: int = 5
    ) -> str:
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

    def _is_semantic_search_enabled(self) -> bool:
        """Check if semantic search functionality is enabled."""
        return bool(self.memory_manager and self.memory_manager.pinecone_enabled)

    async def _retrieve_semantic_memories(
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
            return self.memory_manager.search_memory(
                query_vector=query_vector, top_k=limit
            )
        except Exception as e:
            logger.error(f"Error retrieving semantic memories: {e}")
            return []

    def _format_semantic_context(self, memories: list[dict[str, Any]]) -> str:
        """Format semantic memory results into a context string.

        Args:
            memories: List of memory entries

        Returns:
            Formatted context string
        """
        context_lines = ["Relevant insights from memory:"]
        context_lines.extend(self._format_semantic_memories(memories))
        return "\n".join(context_lines)

    def _format_semantic_memories(self, memories: list[dict[str, Any]]) -> list[str]:
        """Format semantic memory results into human-readable strings."""
        formatted_lines = []
        for memory in memories:
            text = memory.get("text", "")
            source = memory.get("source", "unknown")
            score = memory.get("score")
            score_str = f"{score:.2f}" if isinstance(score, float) else str(score)
            formatted_lines.append(f"  - {text} (Source: {source}, Score: {score_str})")
        return formatted_lines

    async def process_message(
        self,
        user_message: str,
        user_id: str | None = None,
        user_name: str | None = None,
        channel: str = "default",
    ) -> str:
        """
        Process a user message and generate a response with memory integration.

        Args:
            user_message: The user's input message.
            user_id: Optional user identifier for personalization
            user_name: Optional user name for personalization
            channel: Source channel of the message

        Returns:
            Kor'tana's response.
        """
        logger.info(
            f"Processing message from {user_name or 'unknown'} via {channel}: {user_message[:50]}..."
        )

        # Step 1: Add the user's message to history
        self._add_message_to_history(user_message)

        # Step 2: Retrieve relevant memory context
        memory_context = await self._retrieve_memory_context(user_message)

        # Step 3: Generate response from LLM
        response_text = await self._generate_llm_response(
            user_message, memory_context, user_id, user_name, channel
        )

        return response_text

    def _add_message_to_history(self, message: str) -> None:
        """Add user message to history and memory."""
        self.add_user_message(message)

    async def _retrieve_memory_context(self, message: str) -> str:
        """Retrieve memory context relevant to the message."""
        return await self._get_memory_context(message)

    async def _generate_llm_response(
        self,
        user_message: str,
        memory_context: str,
        user_id: str | None = None,
        user_name: str | None = None,
        channel: str = "default",
    ) -> str:
        """Generate response using LLM with provided context."""
        try:
            # Build prompt with memory context and user information
            prompt = self._build_prompt_with_memory(
                user_message,
                memory_context,
                user_id=user_id,
                user_name=user_name,
                channel=channel,
            )

            # Get response from LLM
            response = await self.default_llm_client.complete(prompt)
            response_text = response.get(
                "content", "I'm here with you, though I'm still gathering my thoughts."
            )

            # Add the assistant's response to history
            self.add_assistant_message(response_text)

            return response_text
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            error_response = "I'm experiencing some difficulty right now, but I'm still here with you."
            self.add_assistant_message(error_response)
            return error_response

    def _build_prompt_with_memory(
        self,
        user_message: str,
        memory_context: str,
        user_id: str | None = None,
        user_name: str | None = None,
        channel: str = "default",
    ) -> dict[str, Any]:
        """
        Build a prompt with integrated memory context.

        Args:
            user_message: Current user message
            memory_context: Retrieved memory context
            user_id: Optional user identifier
            user_name: Optional user name
            channel: Source channel of the message

        Returns:
            Formatted prompt for LLM
        """
        # Build system prompt components from smaller functions
        system_prompt = self._get_base_persona_prompt()

        # Add channel information if provided
        if channel:
            system_prompt += self._format_channel_info(channel)

        # Add memory context if available
        if memory_context:
            system_prompt += self._format_memory_context(memory_context)

        # Add user information
        system_prompt += self._format_user_info(user_name, user_id)

        return {
            "model": self.settings.default_llm_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.7,
            "max_tokens": 1000,
        }

    def _get_base_persona_prompt(self) -> str:
        """Get the base persona prompt from configuration."""
        persona = self.persona_data.get(
            "base_persona", "I am Kor'tana, an AI assistant."
        )
        return f"{persona}\n\n"

    def _format_channel_info(self, channel: str) -> str:
        """Format channel information for prompt."""
        return f"Message received via {channel} channel.\n\n"

    def _format_memory_context(self, memory_context: str) -> str:
        """Format memory context for prompt."""
        return f"Recent conversation context:\n{memory_context}\n\n"

    def _format_user_info(
        self, user_name: str | None = None, user_id: str | None = None
    ) -> str:
        """Format user information for prompt."""
        # Get user name from environment or parameter
        actual_user_name = user_name or os.getenv("KORTANA_USER_NAME", "User")

        user_info = f"Current user: {actual_user_name}\n"

        if user_id:
            user_info += f"User ID: {user_id}\n"

        user_info += "Respond naturally and helpfully."

        return user_info

    def get_response(self, user_message: str, **kwargs) -> str:
        """
        Synchronous wrapper for process_message to maintain compatibility.

        Args:
            user_message: The user's input message
            **kwargs: Additional parameters (for compatibility)

        Returns:
            The processed response as a string
        """
        import asyncio

        # Simplified asyncio handling for calling async from sync
        try:
            return asyncio.run(self.process_message(user_message))
        except RuntimeError as e:
            logger.error(
                f"Error running async process_message from sync context: {e}. This might be due to a running event loop."
            )
            return "I'm facing a slight hiccup with my internal thoughts, but I'm still with you."
        except Exception as e:
            logger.error(f"Error in get_response: {e}")
            return "I'm here with you, though something went unexpectedly."

    def set_mode(self, mode: str) -> None:
        """
        Set the conversation mode.

        Args:
            mode: The conversation mode to set
        """
        self.mode = mode
        logger.info(f"Mode set to: {mode}")

    @property
    def current_mode(self) -> str:
        """Get the current conversation mode."""
        return self.mode

    def get_memory_stats(self) -> dict[str, Any]:
        """
        Get statistics about the current memory state.

        Returns:
            Dictionary containing memory statistics
        """
        try:
            # Get basic memory stats
            basic_stats = self._get_basic_memory_stats()

            # Get memory manager specific stats
            memory_manager_stats = self._get_memory_manager_stats()

            # Combine all stats
            return {**basic_stats, **memory_manager_stats}
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return {"error": str(e)}

    def _get_basic_memory_stats(self) -> dict[str, Any]:
        """Get basic memory statistics that don't rely on memory manager."""
        return {
            "conversation_history_length": len(self.history),
            "session_id": self.session_id,
        }

    def _get_memory_manager_stats(self) -> dict[str, Any]:
        """Get memory manager specific statistics."""
        try:
            memories = self.memory_manager.load_project_memory()
            return {
                "total_memories": len(memories),
                "pinecone_enabled": self.memory_manager.pinecone_enabled,
                "memory_journal_path": self.memory_manager.memory_journal_path,
            }
        except Exception as e:
            logger.error(f"Error in memory manager stats: {e}")
            return {"memory_manager_error": str(e)}

    def shutdown(self) -> None:
        """Perform cleanup operations."""
        logger.info("Shutting down ChatEngine...")

        # Save any pending memory operations
        self._save_pending_memory_operations()

        logger.info("ChatEngine shutdown complete")

    def _save_pending_memory_operations(self) -> None:
        """Save any pending memory operations during shutdown."""
        try:
            if hasattr(self.memory_manager, "save_project_memory"):
                memories = self.memory_manager.load_project_memory()
                self.memory_manager.save_project_memory(memories)
                logger.info("Successfully saved pending memory operations")
        except Exception as e:
            logger.error(f"Error saving pending memory operations: {e}")

    def _create_message_entry(self, role: str, content: str) -> dict[str, Any]:
        """
        Create a standardized message entry for conversation history.

        Args:
            role: The role of the message sender (user or assistant)
            content: The message content

        Returns:
            Dictionary with standardized message entry format
        """
        return {
            "role": role,
            "content": content,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def _add_message_to_history_and_memory(self, entry: dict[str, Any]) -> None:
        """
        Add a message entry to both conversation history and memory.

        Args:
            entry: The message entry to add
        """
        # Add to conversation history
        self.history.append(entry)

        # Save to memory journal
        self._save_to_memory(entry)
