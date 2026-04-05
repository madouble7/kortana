"""
KOR'TANA Consciousness Router — Phase 8 API
Endpoints for semantic memory, self-diagnostics, and experience distillation.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.kortana.database import get_db
from src.kortana.services.experience_distiller import (
    ExperienceDistiller,
    get_distillation_model_info,
)
from src.kortana.services.memory_engine import MemoryEngine
from src.kortana.services.self_diagnostic import (
    SelfDiagnostic,
    get_analysis_model_info,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/consciousness", tags=["consciousness"])


# ------------------------------------------------------------------
# Request / Response schemas
# ------------------------------------------------------------------
class MemoryStoreRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    memory_type: str = Field(default="long_term")
    agent_id: str = Field(default="kortana-system")


class SelfMemoryWriteRequest(BaseModel):
    """Write directly to SelfMemory — the table injected into every chat prompt."""

    summary: str = Field(..., min_length=1, max_length=3000)
    tags: Optional[list] = Field(default=None)
    source: str = Field(default="voice")


class MemorySearchResponse(BaseModel):
    id: str
    content: str
    memory_type: str
    similarity: float


class DiagnosticAnalyzeRequest(BaseModel):
    error_type: str = Field(..., min_length=1, max_length=200)
    error_message: str = Field(..., min_length=1, max_length=2000)
    context: Optional[Dict[str, Any]] = None


class DistilRequest(BaseModel):
    age_hours: int = Field(default=24, ge=1, le=720)
    batch_size: int = Field(default=30, ge=1, le=100)


# ------------------------------------------------------------------
# Memory endpoints
# ------------------------------------------------------------------
@router.post("/memory/store")
async def store_memory(
    body: MemoryStoreRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Store a memory with real vector embedding."""
    engine = MemoryEngine(db)
    mem = await engine.store(
        content=body.content,
        memory_type=body.memory_type,
        agent_id=body.agent_id,
    )
    return {
        "id": mem.id,
        "memory_type": mem.memory_type,
        "embedded": mem.embedding is not None,
        "status": "stored",
    }


@router.get("/memory/search")
async def search_memory(
    q: str = Query(..., min_length=1, max_length=500),
    limit: int = Query(default=5, ge=1, le=50),
    memory_type: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Semantic search across stored memories."""
    engine = MemoryEngine(db)
    results = await engine.search(query=q, limit=limit, memory_type=memory_type)
    return {
        "query": q,
        "count": len(results),
        "results": [
            MemorySearchResponse(
                id=str(m.id),
                content=str(m.content)[:500],
                memory_type=str(m.memory_type),
                similarity=round(score, 4),
            ).model_dump()
            for m, score in results
        ],
    }


@router.get("/memory/stats")
async def memory_stats(
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Return memory system statistics."""
    engine = MemoryEngine(db)
    return await engine.stats()


@router.get("/memory/self")
async def count_self_memories(
    source: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Return the count of SelfMemory entries, optionally filtered by source."""
    from sqlalchemy import func, select

    from src.kortana.models import SelfMemory

    stmt = select(func.count()).select_from(SelfMemory)
    if source:
        stmt = stmt.where(SelfMemory.source == source)
    result = await db.execute(stmt)
    count = result.scalar() or 0
    return {"count": count, "source_filter": source}


@router.post("/memory/self")
async def write_self_memory(
    body: SelfMemoryWriteRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Write an entry directly to SelfMemory.

    SelfMemory rows are injected into every chat system prompt via
    MemoryPolicyService.build_context(), giving kor'tana continuity of self.
    No agent FK required — this is kor'tana's own introspective memory.
    """
    from src.kortana.models import SelfMemory

    entry = SelfMemory(
        cycle_number=0,  # 0 = externally written (not from autonomy cycle)
        summary=body.summary,
        tags=body.tags or [],
        source=body.source,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return {"id": entry.id, "source": entry.source, "status": "stored"}


@router.post("/memory/backfill")
async def backfill_embeddings(
    batch_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Generate embeddings for memories that lack them."""
    engine = MemoryEngine(db)
    filled = await engine.backfill_embeddings(batch_size=batch_size)
    return {"backfilled": filled}


# ------------------------------------------------------------------
# Diagnostics endpoints
# ------------------------------------------------------------------
@router.post("/diagnostics/analyze")
async def analyze_error(
    body: DiagnosticAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Analyze a failure using Gemini for root cause and fix suggestion."""
    diag = SelfDiagnostic(db)
    result = await diag.analyze_error_string(
        error_type=body.error_type,
        error_message=body.error_message,
        context=body.context,
    )
    return result.to_dict()


@router.get("/diagnostics/history")
async def diagnostic_history(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Return recent diagnostic history."""
    diag = SelfDiagnostic(db)
    await diag.load_history(limit=limit)
    return {
        "count": len(diag.get_history(limit=limit)),
        "history": diag.get_history(limit=limit),
    }


@router.get("/diagnostics/patterns")
async def diagnostic_patterns(
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Return known failure patterns."""
    diag = SelfDiagnostic(db)
    await diag.load_history()
    patterns = diag.get_known_patterns()
    return {"count": len(patterns), "patterns": patterns}


# ------------------------------------------------------------------
# Experience distillation endpoints
# ------------------------------------------------------------------
@router.post("/experience/distil")
async def distil_experience(
    body: DistilRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Distil old memories into experience capsules."""
    distiller = ExperienceDistiller(db)
    capsules = await distiller.distil(
        age_hours=body.age_hours,
        batch_size=body.batch_size,
    )
    return {
        "capsules_created": len(capsules),
        "capsules": [c.to_dict() for c in capsules],
        "cost": distiller.get_cost_stats(),
    }


@router.get("/experience/capsules")
async def get_capsules(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Return experience capsules (from current session)."""
    distiller = ExperienceDistiller(db)
    return {"capsules": distiller.get_capsules(limit=limit)}


@router.get("/experience/cost")
async def get_cost_stats(
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Return API cost/token usage statistics."""
    distiller = ExperienceDistiller(db)
    return distiller.get_cost_stats()


@router.post("/experience/distil-diagnostics")
async def distil_diagnostics(
    age_hours: int = Query(default=48, ge=1, le=720),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Distil old diagnostic records into an experience capsule."""
    distiller = ExperienceDistiller(db)
    capsule = await distiller.distil_diagnostics(age_hours=age_hours)
    if capsule:
        return {"capsule": capsule.to_dict(), "cost": distiller.get_cost_stats()}
    return {"capsule": None, "message": "No diagnostics old enough to distil"}


# ------------------------------------------------------------------
# Phase 8 overview endpoint
# ------------------------------------------------------------------
@router.get("/status")
async def consciousness_status(
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Return overall Phase 8 consciousness system status."""
    engine = MemoryEngine(db)
    mem_stats = await engine.stats()

    diagnostic_model = get_analysis_model_info()
    distiller = ExperienceDistiller(db)
    cost = distiller.get_cost_stats()
    distillation_model = get_distillation_model_info()

    return {
        "phase": 8,
        "codename": "Consciousness Persistence & Self-Repair",
        "systems": {
            "memory_engine": {
                "status": "active",
                "total_memories": mem_stats["total_memories"],
                "embedded": mem_stats["embedded"],
            },
            "self_diagnostic": {
                "status": "active",
                "model": diagnostic_model["model"],
                "preferred_model": diagnostic_model["preferred_model"],
                "model_lane": diagnostic_model["model_lane"],
            },
            "experience_distiller": {
                "status": "active",
                "model": distillation_model["model"],
                "preferred_model": distillation_model["preferred_model"],
                "model_lane": distillation_model["model_lane"],
                "capsules_created": cost["capsules_created"],
                "token_budget_pct_used": cost["budget_pct_used"],
            },
        },
    }
