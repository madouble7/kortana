"""
KOR'TANA Memory Router — persistent semantic memory via MemoryEngine.
Uses real Gemini embeddings + SQLite-backed vector search.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.kortana.database import get_db
from src.kortana.services.memory_engine import MemoryEngine

logger = logging.getLogger(__name__)

router = APIRouter()

_MAX_TITLE_LEN = 500
_MAX_CONTENT_LEN = 51_200  # 50 KB


class DocumentIn(BaseModel):
    title: str = Field("", max_length=_MAX_TITLE_LEN)
    content: str = Field("", max_length=_MAX_CONTENT_LEN)


class MemoryStoreIn(BaseModel):
    content: str = Field(..., min_length=1, max_length=_MAX_CONTENT_LEN)
    memory_type: str = Field(default="long_term", max_length=50)
    agent_id: str = Field(default="kortana-system", max_length=100)


@router.get("/documents")
async def get_documents(
    limit: int = Query(default=20, ge=1, le=100),
    memory_type: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Retrieve stored memories."""
    engine = MemoryEngine(db)
    stats = await engine.stats()
    # Use search with a broad query to list recent memories
    results = await engine.search(query="*", limit=limit, memory_type=memory_type, threshold=0.0)
    return {
        "documents": [
            {
                "id": str(m.id),
                "content": str(m.content)[:500],
                "memory_type": str(m.memory_type),
                "embedded": m.embedding is not None,
            }
            for m, _ in results
        ],
        "stats": stats,
    }


@router.post("/add_document")
async def add_document(
    payload: DocumentIn,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Store a document as a persistent memory with vector embedding."""
    content = payload.content
    if payload.title:
        content = f"{payload.title}\n\n{payload.content}"

    engine = MemoryEngine(db)
    mem = await engine.store(content=content, memory_type="document")
    return {
        "message": "Document stored",
        "document": {
            "id": mem.id,
            "memory_type": mem.memory_type,
            "embedded": mem.embedding is not None,
        },
    }


@router.post("/store")
async def store_memory(
    payload: MemoryStoreIn,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Store a memory with real vector embedding."""
    engine = MemoryEngine(db)
    mem = await engine.store(
        content=payload.content,
        memory_type=payload.memory_type,
        agent_id=payload.agent_id,
    )
    return {
        "id": mem.id,
        "memory_type": mem.memory_type,
        "embedded": mem.embedding is not None,
        "status": "stored",
    }


@router.get("/search")
async def search_documents_get(
    query: str = Query(..., min_length=1, max_length=500),
    limit: int = Query(default=5, ge=1, le=50),
    memory_type: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Semantic search across stored memories via GET."""
    engine = MemoryEngine(db)
    results = await engine.search(query=query, limit=limit, memory_type=memory_type)
    return {
        "query": query,
        "count": len(results),
        "results": [
            {
                "id": str(m.id),
                "content": str(m.content)[:500],
                "memory_type": str(m.memory_type),
                "similarity": round(score, 4),
            }
            for m, score in results
        ],
    }


@router.post("/search")
async def search_documents(
    payload: dict,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Semantic search across stored memories via POST."""
    query = str(payload.get("query", ""))[:500]
    if not query:
        raise HTTPException(status_code=422, detail="Query is required")
    limit = min(int(payload.get("limit", 5)), 50)
    memory_type = payload.get("memory_type")

    engine = MemoryEngine(db)
    results = await engine.search(
        query=query, limit=limit, memory_type=memory_type
    )
    return {
        "query": query,
        "count": len(results),
        "results": [
            {
                "id": str(m.id),
                "content": str(m.content)[:500],
                "memory_type": str(m.memory_type),
                "similarity": round(score, 4),
            }
            for m, score in results
        ],
    }


@router.get("/stats")
async def memory_stats(
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Return memory system statistics."""
    engine = MemoryEngine(db)
    return await engine.stats()
