import hashlib
import time
from functools import lru_cache
from typing import Any

import numpy as np
from sqlalchemy.orm import Session, joinedload

from kortana.services.embedding_service import embedding_service

from . import models, schemas


# A simple cosine similarity function
def cosine_similarity(v1, v2):
    v1 = np.array(v1)
    v2 = np.array(v2)
    # Handle zero vectors to avoid division by zero
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return np.dot(v1, v2) / (norm_v1 * norm_v2)


# Smart cache for frequently accessed queries
@lru_cache(maxsize=256)
def _cached_query_hash(query: str) -> str:
    """Generate a hash for a query to use as cache key."""
    return hashlib.md5(query.encode()).hexdigest()


class MemoryCoreService:
    def __init__(self, db: Session):
        self.db = db
        # Cache for frequently accessed memories (memory_id -> (memory, timestamp))
        self._memory_cache: dict[int, tuple[models.CoreMemory, float]] = {}
        # Cache for search results (query_hash -> (results, timestamp))
        self._search_cache: dict[str, tuple[list[dict], float]] = {}
        # Cache expiry in seconds (5 minutes)
        self._cache_ttl = 300

    def create_memory(
        self, memory_create: schemas.CoreMemoryCreate
    ) -> models.CoreMemory:
        """
        Creates a new memory, generates its embedding, and stores it.
        """
        # Generate embedding for the memory's content
        text_to_embed = memory_create.content
        if memory_create.title:
            # Combining title and content can create a richer embedding
            text_to_embed = f"{memory_create.title}\n\n{memory_create.content}"

        generated_embedding = embedding_service.get_embedding_for_text(text_to_embed)

        db_memory_data = memory_create.model_dump(exclude={"sentiments"})
        db_memory = models.CoreMemory(
            **db_memory_data,
            embedding=generated_embedding,  # Add the embedding
        )

        # Handle sentiments
        if memory_create.sentiments:
            for sentiment_create in memory_create.sentiments:
                models.MemorySentiment(
                    **sentiment_create.model_dump(),
                    memory=db_memory,  # Sentiment added via relationship cascade
                )

        self.db.add(db_memory)
        self.db.commit()
        self.db.refresh(db_memory)
        return db_memory

    def get_memory_by_id(self, memory_id: int, use_cache: bool = True) -> models.CoreMemory | None:
        """
        Retrieves a specific memory by its ID, including its sentiments.
        Updates accessed_at timestamp via SQLAlchemy's onupdate.
        
        Args:
            memory_id: ID of the memory to retrieve
            use_cache: Whether to use the cache (default: True)
        """
        # Check cache first if enabled
        if use_cache and memory_id in self._memory_cache:
            cached_memory, cache_time = self._memory_cache[memory_id]
            if time.time() - cache_time < self._cache_ttl:
                return cached_memory
            else:
                # Cache expired, remove it
                del self._memory_cache[memory_id]
        
        memory = (
            self.db.query(models.CoreMemory)
            .options(joinedload(models.CoreMemory.sentiments))
            .filter(models.CoreMemory.id == memory_id)
            .first()
        )
        
        # Store in cache
        if memory and use_cache:
            self._memory_cache[memory_id] = (memory, time.time())
        
        return memory

    def get_all_memories(
        self, skip: int = 0, limit: int = 100
    ) -> list[models.CoreMemory]:
        """
        Retrieves a list of memories with pagination, including sentiments.
        """
        return (
            self.db.query(models.CoreMemory)
            .options(joinedload(models.CoreMemory.sentiments))
            .order_by(models.CoreMemory.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_memory(
        self, memory_id: int, memory_update: schemas.CoreMemoryUpdate
    ) -> models.CoreMemory | None:
        """
        Updates an existing memory.
        """
        db_memory = self.get_memory_by_id(memory_id)
        if not db_memory:
            return None
        update_data = memory_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_memory, key, value)
        self.db.commit()
        self.db.refresh(db_memory)
        return db_memory

    def delete_memory(self, memory_id: int) -> models.CoreMemory | None:
        """
        Deletes a memory by its ID.
        """
        db_memory = (
            self.db.query(models.CoreMemory)
            .filter(models.CoreMemory.id == memory_id)
            .first()
        )
        if not db_memory:
            return None
        self.db.delete(db_memory)
        self.db.commit()
        return db_memory

    def search_memories_semantic(
        self, query: str, top_k: int = 5, use_cache: bool = True
    ) -> list[dict]:
        """
        Performs a semantic search for memories based on a text query with caching.

        Args:
            query: Search query text
            top_k: Number of top results to return
            use_cache: Whether to use cached results (default: True)

        Returns:
            List of memory results with scores and relevance metadata
        """
        # Generate cache key
        cache_key = f"{_cached_query_hash(query)}_{top_k}"
        
        # Check cache first if enabled
        if use_cache and cache_key in self._search_cache:
            cached_results, cache_time = self._search_cache[cache_key]
            if time.time() - cache_time < self._cache_ttl:
                return cached_results
            else:
                # Cache expired, remove it
                del self._search_cache[cache_key]
        
        print(f"Performing semantic search for query: '{query}' (top_k={top_k})")
        start_time = time.time()
        
        query_embedding = embedding_service.get_embedding_for_text(query)
        if not query_embedding:
            return []

        # Fetch all memories with embeddings from the database
        # Ensure embeddings are not None
        all_memories = (
            self.db.query(models.CoreMemory)
            .filter(models.CoreMemory.embedding.isnot(None))
            .all()
        )

        if not all_memories:
            return []

        # Calculate similarity for each memory
        scored_memories = []
        for mem in all_memories:
            # Ensure mem.embedding is a list of floats before calculating similarity
            if (
                mem.embedding is not None
                and isinstance(mem.embedding, list)
                and all(isinstance(x, int | float) for x in mem.embedding)
            ):
                similarity = cosine_similarity(query_embedding, mem.embedding)
                scored_memories.append({
                    "memory": mem,
                    "score": similarity,
                    "relevance_rank": 0,  # Will be set after sorting
                })

        # Sort by similarity score in descending order and take the top_k
        sorted_memories = sorted(
            scored_memories, key=lambda x: x["score"], reverse=True
        )[:top_k]
        
        # Add relevance ranking
        for idx, mem_result in enumerate(sorted_memories):
            mem_result["relevance_rank"] = idx + 1
        
        search_time = time.time() - start_time
        print(f"Search completed in {search_time:.3f}s, found {len(sorted_memories)} results")
        
        # Cache results if enabled
        if use_cache:
            self._search_cache[cache_key] = (sorted_memories, time.time())
        
        return sorted_memories
    
    def clear_cache(self) -> dict[str, int]:
        """Clear all cached data and return counts."""
        memory_count = len(self._memory_cache)
        search_count = len(self._search_cache)
        self._memory_cache.clear()
        self._search_cache.clear()
        return {"memories_cleared": memory_count, "searches_cleared": search_count}
