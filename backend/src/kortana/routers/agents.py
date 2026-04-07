import logging
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.kortana.circuit_breaker import create_circuit_breaker
from src.kortana.config import get_settings
from src.kortana.distributed_lock import create_task_lock_manager
from src.kortana.schemas import Agent, AgentCreate, AgentStatus

router = APIRouter(tags=["agents"])
logger = logging.getLogger("kortana.agents")
settings = get_settings()

# Optimization Suite Integration
_agent_breaker = create_circuit_breaker(settings.INTERNAL_REDIS_URL)
_agent_lock = create_task_lock_manager(settings.INTERNAL_REDIS_URL)

# Mock database for agents
_agents_db: List[dict] = []

# Legacy alias so tests can do ``agents_module.agents.clear()``
agents = _agents_db


class _LegacyCreatePayload(BaseModel):
    name: Optional[str] = "unnamed-agent"
    description: Optional[str] = None
    capabilities: Optional[List[str]] = None


class _LegacyExecPayload(BaseModel):
    task: str


@router.get("/", response_model=List[Agent])
async def list_agents():
    """List all created agents."""
    return [Agent.model_validate(a) for a in _agents_db]


# Legacy endpoint kept for backward-compatible tests
@router.get("/list")
async def list_agents_legacy():
    """Legacy list endpoint."""
    return {"agents": _agents_db}


@router.post("/", response_model=Agent)
async def create_agent(agent_in: AgentCreate):
    """Create a new agent with Distributed Locking."""
    lock_key = f"agent_create_{agent_in.name}"
    if not _agent_lock.acquire_for_task(lock_key, wait_time=10):
        raise HTTPException(status_code=409, detail="Agent creation in progress")
    try:
        for a in _agents_db:
            if a["name"] == agent_in.name:
                raise HTTPException(status_code=400, detail="Agent already exists")

        new_agent = {
            "id": str(uuid.uuid4()),
            "name": agent_in.name,
            "description": agent_in.description,
            "model": agent_in.model,
            "temperature": agent_in.temperature,
            "enabled": agent_in.enabled,
            "status": AgentStatus.IDLE,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        _agents_db.append(new_agent)
        return Agent.model_validate(new_agent)
    finally:
        _agent_lock.release_for_task(lock_key)


# Legacy endpoint kept for backward-compatible tests
@router.post("/create")
async def create_agent_legacy(payload: _LegacyCreatePayload):
    """Legacy create endpoint."""
    agent = {
        "id": str(uuid.uuid4()),
        "name": payload.name,
        "description": payload.description,
        "capabilities": payload.capabilities or [],
        "status": "created",
        "created_at": datetime.utcnow().isoformat(),
    }
    _agents_db.append(agent)
    return {"agent": agent}


@router.get("/{agent_id}", response_model=Agent)
async def get_agent(agent_id: str):
    """Get agent by ID."""
    for agent in _agents_db:
        if agent["id"] == agent_id:
            return Agent.model_validate(agent)
    raise HTTPException(status_code=404, detail="Agent not found")


@router.post("/{agent_id}/execute")
async def execute_agent_task(agent_id: str, task: str):
    """Execute an agent with Circuit Breaker protection."""
    agent_data = await get_agent(agent_id)
    task_key = f"agent_exec_{agent_id}"

    can_run, reason = _agent_breaker.can_execute(task_key)
    if not can_run:
        raise HTTPException(status_code=503, detail=f"Circuit open: {reason}")

    try:
        result = {"agent": agent_data.name, "task": task, "result": f"Executed: {task}"}
        _agent_breaker.record_success(task_key)
        return result
    except Exception as e:
        _agent_breaker.record_failure(task_key, str(e))
        logger.error(f"Agent execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Legacy execute by index
@router.post("/execute/{agent_idx}")
async def execute_agent_legacy(agent_idx: int, payload: _LegacyExecPayload):
    """Legacy execute endpoint using list index."""
    if agent_idx < 0 or agent_idx >= len(_agents_db):
        return {"error": f"Agent {agent_idx} not found"}
    agent = _agents_db[agent_idx]
    return {"result": f"Agent {agent.get('name', agent_idx)} executed: {payload.task}"}
