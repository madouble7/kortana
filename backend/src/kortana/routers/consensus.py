"""
Consensus Engine API Router

Exposes multi-provider AI consensus to HTTP clients.
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter

from src.kortana.services.ai_consensus import ConsensusMode, get_consensus_engine

router = APIRouter(prefix="/api/consensus", tags=["consensus"])


class QueryRequest(BaseModel):
    prompt: str
    mode: str = Field(default="fastest", description="fastest | best | consensus")
    system: str | None = None
    max_tokens: int = 1024


class QueryResponse(BaseModel):
    answer: str
    provider_used: str | list[str]
    providers_queried: int
    providers_succeeded: int
    latency: float
    mode: str


@router.post("", response_model=QueryResponse)
async def consensus_query(req: QueryRequest) -> QueryResponse:
    """Query multiple AI providers and return a consensus answer."""
    engine = get_consensus_engine()
    result = await engine.query(
        prompt=req.prompt,
        mode=ConsensusMode(req.mode),
        system=req.system,
        max_tokens=req.max_tokens,
    )
    return QueryResponse(
        answer=result.answer,
        provider_used=result.provider_used,
        providers_queried=result.providers_queried,
        providers_succeeded=result.providers_succeeded,
        latency=result.latency,
        mode=req.mode,
    )


@router.get("/status")
async def consensus_status() -> dict:
    """Return provider rankings and stats."""
    engine = get_consensus_engine()
    return engine.get_status()
