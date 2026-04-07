"""
KOR'TANA Memory Engine — Phase 8 Cycle #1: Consciousness Persistence
Real vector embeddings via Gemini + SQLite-backed semantic search.
Replaces all mocked embeddings with production-grade memory recall.
"""

import logging
import math
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, cast

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.kortana.models import Memory
from src.kortana.provider_model_defaults import MEMORY_ENGINE_EMBEDDING_MODEL

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = MEMORY_ENGINE_EMBEDDING_MODEL
EMBEDDING_DIM = 768
SYSTEM_AGENT_ID = "kortana-system"


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


async def generate_embedding(text: str) -> Optional[List[float]]:
    """Generate a vector embedding using Gemini free-tier API."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("No Gemini API key — embedding skipped")
        return None
    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        result = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text[:2048],  # Gemini limit guard
        )
        embeddings = result.embeddings
        if not embeddings:
            return None
        values = embeddings[0].values
        if not values:
            return None
        return [float(value) for value in values]
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        return None


class MemoryEngine:
    """Persistent memory with semantic search over SQLite-stored embeddings."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Store
    # ------------------------------------------------------------------
    async def store(
        self,
        content: str,
        memory_type: str = "long_term",
        agent_id: str = SYSTEM_AGENT_ID,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Memory:
        """Persist a memory with a real vector embedding."""
        embedding = await generate_embedding(content)

        mem = Memory(
            agent_id=agent_id,
            memory_type=memory_type,
            content=content,
            embedding=embedding,
        )
        self.db.add(mem)
        await self.db.commit()
        await self.db.refresh(mem)
        logger.info(
            f"Stored {memory_type} memory {mem.id} "
            f"(embedding={'yes' if embedding else 'no'})"
        )
        return mem

    # ------------------------------------------------------------------
    # Semantic search
    # ------------------------------------------------------------------
    async def search(
        self,
        query: str,
        limit: int = 5,
        memory_type: Optional[str] = None,
        threshold: float = 0.35,
    ) -> List[Tuple[Memory, float]]:
        """Return the top-k memories ranked by cosine similarity."""
        query_embedding = await generate_embedding(query)

        stmt = select(Memory).where(Memory.embedding.isnot(None))
        if memory_type:
            stmt = stmt.where(Memory.memory_type == memory_type)
        result = await self.db.execute(stmt)
        candidates = result.scalars().all()

        if not candidates:
            return []

        if query_embedding:
            scored = []
            for m in candidates:
                embedding = cast(list[float] | None, m.embedding)
                if not embedding:
                    continue
                scored.append((m, _cosine_similarity(query_embedding, embedding)))
            scored.sort(key=lambda x: x[1], reverse=True)
            hits = [(m, s) for m, s in scored if s >= threshold][:limit]
        else:
            # Fallback: keyword match
            q_lower = query.lower()
            hits = [
                (m, 1.0)
                for m in candidates
                if q_lower in cast(str, m.content or "").lower()
            ][:limit]

        # Touch accessed_at for retrieved memories
        now = datetime.utcnow()
        for mem, _ in hits:
            await self.db.execute(
                update(Memory).where(Memory.id == mem.id).values(accessed_at=now)
            )
        if hits:
            await self.db.commit()

        return hits

    # ------------------------------------------------------------------
    # Recall (convenience wrapper for single best match)
    # ------------------------------------------------------------------
    async def recall(self, query: str) -> Optional[str]:
        """Return the single most relevant memory's content, or None."""
        results = await self.search(query, limit=1)
        if results:
            return cast(str | None, results[0][0].content)
        return None

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------
    async def stats(self) -> Dict[str, Any]:
        """Return memory statistics."""
        result = await self.db.execute(select(Memory))
        all_mems = result.scalars().all()

        by_type: Dict[str, int] = {}
        embedded = 0
        for m in all_mems:
            memory_type = cast(str, m.memory_type)
            by_type[memory_type] = by_type.get(memory_type, 0) + 1
            if cast(list[float] | None, m.embedding):
                embedded += 1

        return {
            "total_memories": len(all_mems),
            "embedded": embedded,
            "unembedded": len(all_mems) - embedded,
            "by_type": by_type,
            "embedding_model": EMBEDDING_MODEL,
            "embedding_dim": EMBEDDING_DIM,
        }

    # ------------------------------------------------------------------
    # Backfill embeddings for legacy memories
    # ------------------------------------------------------------------
    async def backfill_embeddings(self, batch_size: int = 20) -> int:
        """Generate embeddings for memories that lack them."""
        stmt = select(Memory).where(Memory.embedding.is_(None)).limit(batch_size)
        result = await self.db.execute(stmt)
        memories = result.scalars().all()

        filled = 0
        for mem in memories:
            emb = await generate_embedding(cast(str, mem.content))
            if emb:
                await self.db.execute(
                    update(Memory).where(Memory.id == mem.id).values(embedding=emb)
                )
                filled += 1

        if filled:
            await self.db.commit()
            logger.info(f"Backfilled {filled}/{len(memories)} embeddings")
        return filled
