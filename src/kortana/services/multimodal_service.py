"""
Multimodal service for orchestrating multimodal prompt processing.

This service coordinates between prompt generation, LLM clients, and memory
to provide comprehensive multimodal AI capabilities.
"""

import logging
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from ..core.multimodal import (
    MultimodalPrompt,
    MultimodalPromptGenerator,
    MultimodalProcessor,
    MultimodalResponse,
)
from ..core.multimodal.models import ContentType
from ..llm_clients.factory import LLMClientFactory
from ..memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class MultimodalService:
    """
    Service for processing multimodal prompts.

    This service integrates multimodal prompt generation with LLM processing
    and memory management to provide comprehensive multimodal AI capabilities.
    """

    def __init__(self, db: Session):
        """
        Initialize the multimodal service.

        Args:
            db: Database session for memory operations
        """
        self.db = db
        self.generator = MultimodalPromptGenerator()
        self.processor = MultimodalProcessor()
        self.memory_manager = None  # Will be initialized when needed

    def _get_memory_manager(self) -> MemoryManager:
        """Get or create memory manager instance."""
        if self.memory_manager is None:
            try:
                self.memory_manager = MemoryManager(self.db)
            except Exception as e:
                logger.warning(f"Could not initialize memory manager: {e}")
                self.memory_manager = None
        return self.memory_manager

    async def process_prompt(
        self, prompt: MultimodalPrompt, use_memory: bool = True
    ) -> MultimodalResponse:
        """
        Process a multimodal prompt and generate a response.

        Args:
            prompt: The multimodal prompt to process
            use_memory: Whether to use memory context

        Returns:
            Multimodal response
        """
        try:
            # Validate prompt
            if not self.generator.validate_prompt(prompt):
                return MultimodalResponse(
                    prompt_id=prompt.prompt_id,
                    content="Invalid prompt structure",
                    success=False,
                    error_message="Prompt validation failed",
                )

            # Enhance prompt with memory context if enabled
            if use_memory:
                prompt = await self._enhance_with_memory(prompt)

            # Process prompt to LLM format
            processed_prompt = self.processor.process_prompt(prompt)

            # Get appropriate LLM client based on content type
            client = await self._get_llm_client(prompt.primary_content_type)
            if not client:
                return MultimodalResponse(
                    prompt_id=prompt.prompt_id,
                    content="No suitable LLM client available",
                    success=False,
                    error_message="Failed to obtain LLM client",
                )

            # Generate response
            llm_response = await self._generate_response(client, processed_prompt)

            # Store in memory if enabled
            if use_memory and llm_response.get("content"):
                await self._store_in_memory(prompt, llm_response)

            # Create response object
            response = MultimodalResponse(
                prompt_id=prompt.prompt_id,
                content=llm_response.get("content", "No response generated"),
                content_type=ContentType.TEXT,
                processing_info={
                    "model_used": llm_response.get("model_id_used", "unknown"),
                    "usage": llm_response.get("usage", {}),
                    "primary_content_type": prompt.primary_content_type.value,
                },
                success=llm_response.get("error") is None,
                error_message=llm_response.get("error"),
            )

            return response

        except Exception as e:
            logger.error(f"Error processing multimodal prompt: {e}")
            return MultimodalResponse(
                prompt_id=prompt.prompt_id,
                content=f"Error processing prompt: {str(e)}",
                success=False,
                error_message=str(e),
            )

    async def _enhance_with_memory(
        self, prompt: MultimodalPrompt
    ) -> MultimodalPrompt:
        """
        Enhance prompt with memory context.

        Args:
            prompt: Original prompt

        Returns:
            Enhanced prompt with memory context
        """
        try:
            memory_manager = self._get_memory_manager()
            if not memory_manager:
                return prompt

            # Extract text content for memory search
            text_contents = prompt.get_contents_by_type(ContentType.TEXT)
            if text_contents:
                search_text = " ".join([c.data for c in text_contents if isinstance(c.data, str)])

                # Search for relevant memories
                memories = memory_manager.search_memories(search_text, top_k=3)
                if memories:
                    prompt = self.generator.enhance_prompt_with_context(
                        prompt, memory_context=memories
                    )

        except Exception as e:
            logger.warning(f"Could not enhance prompt with memory: {e}")

        return prompt

    async def _get_llm_client(self, content_type: ContentType):
        """
        Get appropriate LLM client based on content type.

        Args:
            content_type: Primary content type

        Returns:
            LLM client instance
        """
        try:
            # Load models config
            import json
            import os
            from pathlib import Path

            # Try environment variable first, fallback to default path
            config_path_str = os.getenv("MODELS_CONFIG_PATH", "config/models_config.json")
            config_path = Path(config_path_str)
            
            if not config_path.exists():
                logger.error(f"Models config not found at {config_path}")
                return None

            with open(config_path) as f:
                models_config = json.load(f)

            # Get multimodal client for vision/image content
            if content_type in [ContentType.IMAGE, ContentType.VIDEO]:
                return LLMClientFactory.get_multimodal_client(models_config)

            # Get default client for other content types
            return LLMClientFactory.get_default_client(models_config)

        except Exception as e:
            logger.error(f"Error getting LLM client: {e}")
            return None

    async def _generate_response(
        self, client, processed_prompt: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate response using LLM client.

        Args:
            client: LLM client
            processed_prompt: Processed prompt data

        Returns:
            Response dictionary
        """
        try:
            # Extract instruction and build messages
            instruction = processed_prompt.get("instruction") or "You are a helpful AI assistant."
            messages = []

            # Build messages from contents
            for content in processed_prompt.get("contents", []):
                if content.get("type") == "text":
                    messages.append({"role": "user", "content": content.get("text", "")})

            # Check if client supports multimodal
            if hasattr(client, "supports_multimodal") and client.supports_multimodal():
                return client.generate_multimodal_response(
                    system_prompt=instruction,
                    messages=messages,
                    multimodal_content=processed_prompt,
                )
            else:
                # Fall back to text-only processing
                return client.generate_response(
                    system_prompt=instruction, messages=messages
                )

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "content": f"Error generating response: {str(e)}",
                "error": str(e),
                "model_id_used": "unknown",
                "usage": {},
            }

    async def _store_in_memory(
        self, prompt: MultimodalPrompt, llm_response: Dict[str, Any]
    ) -> None:
        """
        Store prompt and response in memory.

        Args:
            prompt: Original prompt
            llm_response: LLM response
        """
        try:
            memory_manager = self._get_memory_manager()
            if not memory_manager:
                return

            # Extract text for storage
            text_contents = prompt.get_contents_by_type(ContentType.TEXT)
            if text_contents:
                user_text = " ".join([c.data for c in text_contents if isinstance(c.data, str)])
                response_text = llm_response.get("content", "")

                # Store as conversation memory
                memory_manager.store_memory(
                    content=f"User: {user_text}\nAssistant: {response_text}",
                    metadata={
                        "type": "multimodal_conversation",
                        "content_type": prompt.primary_content_type.value,
                        "prompt_id": prompt.prompt_id,
                    },
                )

        except Exception as e:
            logger.warning(f"Could not store in memory: {e}")
