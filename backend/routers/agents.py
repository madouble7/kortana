from fastapi import APIRouter
from typing import Any

router = APIRouter()

# Placeholder for agents - in production, use persistent storage
agents: list[Any] = []

@router.get("/list")
async def list_agents():
    """List all created agents."""
    return {"agents": agents}

@router.post("/create")
async def create_agent(payload: dict):
    """Create a new agent."""
    name = payload.get("name", "")
    description = payload.get("description", "")
    capabilities = payload.get("capabilities", [])
    agent = {
        "id": len(agents),
        "name": name,
        "description": description,
        "capabilities": capabilities,
        "status": "created"
    }
    agents.append(agent)
    return {"message": "Agent created", "agent": agent}

@router.post("/execute/{agent_id}")
async def execute_agent(agent_id: int, payload: dict):
    """Execute an agent with given input."""
    if agent_id >= len(agents):
        return {"error": "Agent not found"}
    agent = agents[agent_id]
    task = payload.get("task", "")
    # Placeholder execution - implement actual agent logic
    result = f"Agent {agent['name']} executed task: {task}"
    return {"agent": agent["name"], "task": task, "result": result}
