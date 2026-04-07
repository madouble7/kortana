"""
AutoGen-Compatible Frontend Adapter
Provides multi-agent workflow compatibility for AutoGen-based frontends
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class AgentMessage(BaseModel):
    """Message from an agent in the conversation"""

    role: str
    content: str
    name: str | None = None


class AgentConversationRequest(BaseModel):
    """Request to initiate an agent conversation"""

    task: str
    agents: list[str] | None = None
    max_rounds: int = 10
    initial_message: str | None = None


class AgentConversationResponse(BaseModel):
    """Response from agent conversation"""

    messages: list[AgentMessage]
    status: str
    summary: str | None = None


@router.post("/conversation", response_model=AgentConversationResponse)
async def start_agent_conversation(request: AgentConversationRequest) -> dict[str, Any]:
    """
    Start a multi-agent conversation workflow.
    Compatible with AutoGen's conversation patterns.

    Args:
        request: Conversation configuration including task and agent list

    Returns:
        Conversation messages and status
    """
    try:
        # Use Kortana's existing AI services for agent simulation
        from src.kortana.services.multi_model_ai import ai_service

        if ai_service is None:
            raise HTTPException(
                status_code=503,
                detail="AI service not available. Check API key configuration.",
            )

        # Simulate multi-agent workflow
        messages: list[AgentMessage] = []

        # Add initial user message
        messages.append(
            AgentMessage(
                role="user",
                content=request.initial_message or request.task,
                name="User",
            )
        )

        # Process through AI service
        response = await ai_service.analyze_text(
            f"Task: {request.task}\n\nProvide a structured response as if from multiple agents working together."
        )

        # Add assistant response
        messages.append(
            AgentMessage(
                role="assistant",
                content=response,
                name="KortanaAgent",
            )
        )

        return {
            "messages": messages,
            "status": "completed",
            "summary": f"Processed task with {len(messages)} messages",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversation failed: {str(e)}")


@router.post("/agent/create")
async def create_agent(agent_config: dict[str, Any]) -> dict[str, Any]:
    """
    Create a new agent with specified capabilities.

    Args:
        agent_config: Agent configuration including name, role, and capabilities

    Returns:
        Created agent information
    """
    name = agent_config.get("name", "Agent")
    role = agent_config.get("role", "assistant")
    system_message = agent_config.get("system_message", "")

    return {
        "agent_id": f"agent_{name.lower()}",
        "name": name,
        "role": role,
        "system_message": system_message,
        "status": "created",
    }


@router.get("/agents/list")
async def list_agents() -> dict[str, Any]:
    """
    List available agents in the system.

    Returns:
        List of available agents
    """
    return {
        "agents": [
            {
                "agent_id": "kortana_assistant",
                "name": "Kortana Assistant",
                "role": "assistant",
                "capabilities": ["text_analysis", "code_generation", "multimodal"],
            },
            {
                "agent_id": "kortana_coder",
                "name": "Kortana Coder",
                "role": "coder",
                "capabilities": ["code_generation", "code_review", "testing"],
            },
        ]
    }


@router.post("/group-chat")
async def group_chat(chat_config: dict[str, Any]) -> dict[str, Any]:
    """
    Initiate a group chat with multiple agents.

    Args:
        chat_config: Configuration for the group chat

    Returns:
        Group chat session information
    """
    agents = chat_config.get("agents", [])
    task = chat_config.get("task", "")

    return {
        "session_id": "group_chat_session",
        "agents": agents,
        "task": task,
        "status": "initialized",
        "message": "Group chat session created",
    }
