"""Phase 9 swarm control router."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.kortana.swarm.manager import get_swarm_manager

router = APIRouter(prefix="/api/swarm", tags=["swarm"])


class SwarmCommandRequest(BaseModel):
    command: str = Field(..., min_length=1, max_length=64)
    target: str | None = Field(default=None, max_length=64)
    payload: dict[str, Any] = Field(default_factory=dict)


@router.get("/status")
async def swarm_status() -> dict[str, Any]:
    return get_swarm_manager().get_status()


@router.get("/events")
async def swarm_events(limit: int = 25) -> dict[str, Any]:
    manager = get_swarm_manager()
    return {
        "events": manager.get_recent_events(limit),
        "count": min(max(limit, 1), 100),
    }


@router.post("/start")
async def swarm_start() -> dict[str, Any]:
    manager = get_swarm_manager()
    await manager.start()
    return {"status": "started", **manager.get_status()}


@router.post("/stop")
async def swarm_stop() -> dict[str, Any]:
    manager = get_swarm_manager()
    await manager.stop()
    return {"status": "stopped", **manager.get_status()}


@router.post("/command")
async def swarm_command(body: SwarmCommandRequest) -> dict[str, Any]:
    manager = get_swarm_manager()
    envelope = await manager.send_command(
        body.command, target=body.target, payload=body.payload
    )
    return {"status": "accepted", "command": envelope, "swarm": manager.get_status()}
