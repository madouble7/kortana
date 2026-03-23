import logging
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException

from src.kortana.circuit_breaker import create_circuit_breaker
from src.kortana.config import get_settings
from src.kortana.distributed_lock import create_task_lock_manager
from src.kortana.schemas import Agent, AgentCreate, AgentStatus

router = APIRouter(prefix="/api/agents", tags=["agents"])
logger = logging.getLogger("kortana.agents")
settings = get_settings()

# Optimization Suite Integration
_agent_breaker = create_circuit_breaker(settings.INTERNAL_REDIS_URL)
_agent_lock = create_task_lock_manager(settings.INTERNAL_REDIS_URL)

# Mock database for agents
_agents_db: List[dict] = []


@router.get("/", response_model=List[Agent])
async def list_agents():
    """List all created agents."""
    return [Agent.model_validate(a) for a in _agents_db]


@router.post("/", response_model=Agent)
async def create_agent(agent_in: AgentCreate):
    """Create a new agent with Distributed Locking."""
    async with _agent_lock.lock(f"agent_create_{agent_in.name}", timeout=10.0):
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


@router.get("/{agent_id}", response_model=Agent)
async def get_agent(agent_id: str):
    """Get agent by ID."""
    for agent in _agents_db:
        if agent["id"] == agent_id:
            return Agent.model_validate(agent)
    raise HTTPException(status_code=404, detail="Agent not found")


@router.post("/{agent_id}/execute")
async def execute_agent_task(agent_id: str, task: str):
    """Execute an agent with Circuit Breaker."""
    agent_data = await get_agent(agent_id)

    async def _run_agent_inference():
        # Actual agent implementation would call Gemini here
        return {"agent": agent_data.name, "task": task, "result": f"Executed: {task}"}

    try:
        return await _agent_breaker.call_async(
            f"agent_exec_{agent_id}", _run_agent_inference
        )
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
