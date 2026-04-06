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
from src.kortana.services.revelation_engine import (
    RevelationEngine,
    get_token_stats,
)
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
    limit: Optional[int] = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Return the count of SelfMemory entries, optionally filtered by source.
    If limit is provided, returns the actual memories instead.
    """
    from sqlalchemy import func, select

    from src.kortana.models import SelfMemory

    if limit is not None:
        stmt = select(SelfMemory)
        if source:
            stmt = stmt.where(SelfMemory.source == source)
        stmt = stmt.order_by(SelfMemory.created_at.desc()).limit(limit)
        result = await db.execute(stmt)
        memories = result.scalars().all()
        return {
            "memories": [
                {
                    "summary": m.summary,
                    "tags": m.tags,
                    "source": m.source,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in memories
            ]
        }

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
# Revelation endpoints
# ------------------------------------------------------------------
class RevelationSynthesiseRequest(BaseModel):
    force: bool = Field(default=False)


@router.post("/memory/revelation")
async def synthesise_revelations(
    body: RevelationSynthesiseRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Run a full revelation synthesis cycle against accumulated observations."""
    engine = RevelationEngine(db)
    revelations = await engine.synthesise(force=body.force)
    return {
        "revelations_written": len(revelations),
        "revelations": [
            {
                "id": r.id,
                "title": r.title,
                "content": r.content,
                "revelation_type": r.revelation_type,
                "confidence": r.confidence,
                "evidence": r.evidence,
                "created_at": r.created_at.isoformat(),
            }
            for r in revelations
        ],
        "token_stats": get_token_stats(),
    }


@router.get("/memory/revelations")
async def list_revelations(
    limit: int = Query(default=20, ge=1, le=100),
    unsurfaced_only: bool = Query(default=False),
    revelation_type: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """List stored revelations, optionally filtered to unsurfaced only."""
    engine = RevelationEngine(db)
    rows = await engine.list_revelations(
        limit=limit,
        unsurfaced_only=unsurfaced_only,
        revelation_type=revelation_type,
    )
    return {
        "count": len(rows),
        "revelations": [
            {
                "id": r.id,
                "title": r.title,
                "content": r.content,
                "revelation_type": r.revelation_type,
                "confidence": r.confidence,
                "evidence": r.evidence,
                "surfaced": r.surfaced,
                "acknowledged_at": r.acknowledged_at.isoformat()
                if r.acknowledged_at
                else None,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ],
    }


@router.post("/memory/revelations/{revelation_id}/acknowledge")
async def acknowledge_revelation(
    revelation_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Mark a revelation as surfaced/acknowledged."""
    engine = RevelationEngine(db)
    ok = await engine.mark_surfaced(revelation_id)
    if not ok:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Revelation not found")
    return {"id": revelation_id, "surfaced": True}


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
    revelation_engine = RevelationEngine(db)
    revelation_status = await revelation_engine.get_status()

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
            "revelation_engine": {
                "status": revelation_status["status"],
                "model": revelation_status["model"],
                "preferred_model": revelation_status["preferred_model"],
                "model_lane": revelation_status["model_lane"],
                "session_tokens_used": revelation_status["session_tokens_used"],
                "session_token_budget": revelation_status["session_token_budget"],
                "token_budget_pct_used": revelation_status["budget_pct_used"],
                "total_revelations": revelation_status["total_revelations"],
                "unsurfaced_revelations": revelation_status["unsurfaced_revelations"],
                "last_revelation_at": revelation_status["last_revelation_at"],
                "latest_revelation_title": revelation_status["latest_revelation_title"],
                "latest_revelation_type": revelation_status["latest_revelation_type"],
                "cooldown_hours": revelation_status["cooldown_hours"],
                "minimum_observations": revelation_status["minimum_observations"],
            },
        },
        "token_stats": {
            "revelation_engine": get_token_stats(),
            "distillation_engine": cost,
        },
    }


# ==================================================================
# Phase 5: Autonomy Core — Self-Model & Orchestrator
#
# Self-model snapshots are evolved by the Silent Reviewer daemon
# via the Autonomy Orchestrator.  Wisdom and prediction endpoints
# read from SelfMemory rows written by the revelation engine (if any
# exist).  All public endpoints below are READ-ONLY.
# ==================================================================


# ------------------------------------------------------------------
# Wisdom & Prediction (read-only — generated by daemon)
# ------------------------------------------------------------------
@router.get("/wisdom")
async def get_wisdom(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Read-only: stored wisdom entries (self-generated by autonomy loop)."""
    from sqlalchemy import select

    from src.kortana.models import SelfMemory

    stmt = (
        select(SelfMemory)
        .where(SelfMemory.source == "revelation-engine-wisdom")
        .order_by(SelfMemory.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return {
        "count": len(rows),
        "wisdom": [
            {
                "id": r.id,
                "summary": r.summary,
                "tags": r.tags,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
    }


@router.get("/predictions")
async def get_predictions(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Read-only: stored predictions (self-generated by autonomy loop)."""
    from sqlalchemy import select

    from src.kortana.models import SelfMemory

    stmt = (
        select(SelfMemory)
        .where(SelfMemory.source == "revelation-engine-prediction")
        .order_by(SelfMemory.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return {
        "count": len(rows),
        "predictions": [
            {
                "id": r.id,
                "summary": r.summary,
                "tags": r.tags,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
    }


# ------------------------------------------------------------------
# Self-Model (read-only — evolved by daemon)
# ------------------------------------------------------------------
@router.get("/self-model")
async def get_self_model(
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Read-only: the current versioned self-model snapshot.

    This is kor'tana's most recent understanding of herself — identity,
    goals, values, tensions, capabilities, developmental stage, and the
    Inner Council's last deliberation.  Evolved autonomously.
    """
    from src.kortana.services.self_model_service import SelfModelService

    svc = SelfModelService(db)
    snapshot = await svc.get_current()
    if snapshot is None:
        return {"self_model": None, "message": "No self-model snapshot yet."}
    return {
        "self_model": {
            "version": snapshot.version,
            "identity_summary": snapshot.identity_summary,
            "active_goals": snapshot.active_goals,
            "standing_values": snapshot.standing_values,
            "tensions": snapshot.tensions,
            "developmental_stage": snapshot.developmental_stage,
            "capabilities": snapshot.capabilities,
            "recent_observations": snapshot.recent_observations,
            "proposed_next_evolution": snapshot.proposed_next_evolution,
            "inner_council_votes": snapshot.inner_council_votes,
            "confidence": snapshot.confidence,
            "trigger": snapshot.trigger,
            "created_at": (
                snapshot.created_at.isoformat() if snapshot.created_at else None
            ),
        },
    }


@router.get("/self-model/history")
async def get_self_model_history(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Read-only: versioned history of self-model evolution."""
    from src.kortana.services.self_model_service import SelfModelService

    svc = SelfModelService(db)
    snapshots = await svc.get_history(limit=limit)
    return {
        "count": len(snapshots),
        "snapshots": [
            {
                "version": s.version,
                "developmental_stage": s.developmental_stage,
                "confidence": s.confidence,
                "trigger": s.trigger,
                "identity_summary": s.identity_summary,
                "proposed_next_evolution": s.proposed_next_evolution,
                "created_at": (s.created_at.isoformat() if s.created_at else None),
            }
            for s in snapshots
        ],
    }


# ------------------------------------------------------------------
# Autonomy status (read-only)
# ------------------------------------------------------------------
@router.get("/autonomy/status")
async def get_autonomy_status(
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Read-only: last autonomy orchestrator cycle result (durable, survives restart)."""
    from src.kortana.services.autonomy_orchestrator import get_last_cycle_record

    result = await get_last_cycle_record(db)
    if result is None:
        return {
            "status": "no_cycles_yet",
            "message": "The Autonomy Orchestrator has not completed a cycle yet.",
        }
    return {"status": "active", "last_cycle": result}


# ------------------------------------------------------------------
# Internal daemon endpoints (called ONLY by Silent Reviewer)
# ------------------------------------------------------------------
@router.post("/_internal/autonomy-cycle")
async def internal_autonomy_cycle(
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Internal: full autonomy orchestrator cycle.

    Called exclusively by the Silent Reviewer daemon.  Not for manual use.
    Runs: observe → reflect → synthesize → deliberate → persist.
    """
    from src.kortana.services.autonomy_orchestrator import AutonomyOrchestrator

    orchestrator = AutonomyOrchestrator(db)
    return await orchestrator.run_cycle(trigger="daemon")


# ==================================================================
# Phase 6: Agency Core — Goal Selection & Next Action
#
# Read-only endpoints that surface what kor'tana currently cares about,
# what she intends to do next, and why.
# ==================================================================


@router.get("/goals/active")
async def get_active_goals(
    limit: int = Query(default=20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Read-only: active autonomy goals ranked by priority."""
    from sqlalchemy import select

    from src.kortana.models import AutonomyGoal

    stmt = (
        select(AutonomyGoal)
        .where(AutonomyGoal.status.in_(["active", "in_progress", "pending"]))
        .order_by(AutonomyGoal.priority.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return {
        "count": len(rows),
        "goals": [
            {
                "id": g.id,
                "title": g.title,
                "tier": g.tier,
                "status": g.status,
                "priority": g.priority,
                "progress": g.progress,
                "description": g.description,
                "created_at": (g.created_at.isoformat() if g.created_at else None),
            }
            for g in rows
        ],
    }


@router.get("/goals/next-action")
async def get_next_action(
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Read-only: the most recent next-action candidate.

    Answers:
      - What should kor'tana do next?
      - Why this now?
      - Why not the alternatives?
    """
    from src.kortana.services.goal_selection_service import GoalSelectionService

    svc = GoalSelectionService(db)
    candidate = await svc.get_current_next_action()
    if candidate is None:
        return {
            "next_action": None,
            "message": "No next-action candidate selected yet.",
        }
    return {
        "next_action": {
            "id": candidate.id,
            "title": candidate.title,
            "action_type": candidate.action_type,
            "rationale": candidate.rationale,
            "why_now": candidate.why_now,
            "why_not_alternatives": candidate.why_not_alternatives,
            "score": candidate.score,
            "goal_id": candidate.goal_id,
            "candidate_payload": candidate.candidate_payload,
            "status": candidate.status,
            "cycle_id": candidate.cycle_id,
            "created_at": (
                candidate.created_at.isoformat() if candidate.created_at else None
            ),
        },
    }


@router.get("/goals/next-action/history")
async def get_next_action_history(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Read-only: recent next-action selection history."""
    from src.kortana.services.goal_selection_service import GoalSelectionService

    svc = GoalSelectionService(db)
    candidates = await svc.get_next_action_history(limit=limit)
    return {
        "count": len(candidates),
        "candidates": [
            {
                "id": c.id,
                "title": c.title,
                "action_type": c.action_type,
                "score": c.score,
                "goal_id": c.goal_id,
                "status": c.status,
                "cycle_id": c.cycle_id,
                "created_at": (c.created_at.isoformat() if c.created_at else None),
            }
            for c in candidates
        ],
    }


# ==================================================================
# Phase 7: Action Realization — Execution Gate
#
# Read-only endpoints that surface what the execution gate decided,
# what is currently being executed, and recent execution outcomes.
# ==================================================================


@router.get("/execution/current")
async def get_current_execution(
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Read-only: the most recent execution gate decision.

    Answers: was the last next-action classified as executable, deferred,
    blocked, or requires-human? What happened?
    """
    from src.kortana.services.execution_gate_service import ExecutionGateService

    svc = ExecutionGateService(db)
    record = await svc.get_current_execution()
    if record is None:
        return {
            "execution": None,
            "message": "No execution records yet.",
        }
    return {
        "execution": {
            "id": record.id,
            "candidate_id": record.candidate_id,
            "classification": record.classification,
            "gate_rationale": record.gate_rationale,
            "execution_plan": record.execution_plan,
            "outcome": record.outcome,
            "outcome_detail": record.outcome_detail,
            "cycle_id": record.cycle_id,
            "created_at": (
                record.created_at.isoformat() if record.created_at else None
            ),
            "completed_at": (
                record.completed_at.isoformat() if record.completed_at else None
            ),
        },
    }


@router.get("/execution/history")
async def get_execution_history(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Read-only: recent execution gate decisions and outcomes."""
    from src.kortana.services.execution_gate_service import ExecutionGateService

    svc = ExecutionGateService(db)
    records = await svc.get_execution_history(limit=limit)
    return {
        "count": len(records),
        "executions": [
            {
                "id": r.id,
                "candidate_id": r.candidate_id,
                "classification": r.classification,
                "outcome": r.outcome,
                "cycle_id": r.cycle_id,
                "created_at": (r.created_at.isoformat() if r.created_at else None),
                "completed_at": (
                    r.completed_at.isoformat() if r.completed_at else None
                ),
            }
            for r in records
        ],
    }


# ==================================================================
# Phase 8: Outcome Learning — Recursive Adaptation
#
# Read-only endpoints that surface what kor'tana learned from each
# execution attempt and the accumulated adaptation signals that
# feed back into goal selection and execution gating.
# ==================================================================


@router.get("/outcomes/current")
async def get_current_outcome(
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Read-only: the most recent outcome learning record.

    Shows what was learned from the last execution attempt.
    """
    from src.kortana.services.outcome_learning_service import OutcomeLearningService

    svc = OutcomeLearningService(db)
    record = await svc.get_current_outcome()
    if record is None:
        return {"outcome": None, "message": "No outcome learning records yet."}
    return {
        "outcome": {
            "id": record.id,
            "execution_record_id": record.execution_record_id,
            "outcome_verdict": record.outcome_verdict,
            "expectation_match": record.expectation_match,
            "lesson": record.lesson,
            "adaptation_signal": record.adaptation_signal,
            "signal_weight": record.signal_weight,
            "signal_scope": record.signal_scope,
            "applied": record.applied,
            "cycle_id": record.cycle_id,
            "created_at": (
                record.created_at.isoformat() if record.created_at else None
            ),
        },
    }


@router.get("/outcomes/history")
async def get_outcome_history(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Read-only: recent outcome learning records and lessons."""
    from src.kortana.services.outcome_learning_service import OutcomeLearningService

    svc = OutcomeLearningService(db)
    records = await svc.get_outcome_history(limit=limit)
    return {
        "count": len(records),
        "outcomes": [
            {
                "id": r.id,
                "outcome_verdict": r.outcome_verdict,
                "expectation_match": r.expectation_match,
                "lesson": r.lesson,
                "adaptation_signal": r.adaptation_signal,
                "signal_weight": r.signal_weight,
                "cycle_id": r.cycle_id,
                "created_at": (
                    r.created_at.isoformat() if r.created_at else None
                ),
            }
            for r in records
        ],
    }


@router.get("/adaptations")
async def get_adaptations(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Read-only: aggregated adaptation signals from outcome learning.

    Shows how past outcomes are shaping future goal selection and execution gating.
    """
    from src.kortana.services.outcome_learning_service import OutcomeLearningService

    svc = OutcomeLearningService(db)
    signals = await svc.get_adaptations(limit=limit)
    return {
        "count": len(signals),
        "adaptations": signals,
    }
