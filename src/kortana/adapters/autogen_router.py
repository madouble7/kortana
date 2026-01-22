# src/kortana/adapters/autogen_router.py
"""
API Router for AutoGen adapter integration.

Provides endpoints for:
- Single and multi-agent conversations
- Multi-agent collaboration
- Agent status and configuration
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.kortana.services.database import get_db_sync

from .autogen_adapter import AutoGenAdapter


# Pydantic models for AutoGen interaction
class AutoGenMessage(BaseModel):
    """Message in AutoGen conversation format."""

    role: str = Field(..., examples=["user", "assistant", "system"])
    content: str = Field(..., examples=["Hello, how can you help me?"])
    name: str | None = Field(None, examples=["user", "assistant_agent"])


class AutoGenRequest(BaseModel):
    """Request format for AutoGen chat endpoint."""

    messages: list[AutoGenMessage] = Field(
        ..., description="List of messages in the conversation"
    )
    conversation_id: str | None = Field(
        None, description="Optional conversation ID for tracking"
    )
    agent_config: dict[str, Any] | None = Field(
        None, description="Optional agent configuration"
    )


class AutoGenResponse(BaseModel):
    """Response format for AutoGen chat endpoint."""

    agent_responses: list[dict[str, Any]]
    conversation_id: str
    status: str
    debug_info: dict[str, Any] | None = None


class MultiAgentRequest(BaseModel):
    """Request format for multi-agent collaboration."""

    task: str = Field(
        ...,
        examples=[
            "Analyze this code and suggest improvements with proper testing strategy"
        ],
    )
    agent_config: dict[str, Any] | None = Field(
        None, description="Configuration for participating agents"
    )
    max_rounds: int | None = Field(
        10, description="Maximum conversation rounds between agents"
    )


class MultiAgentResponse(BaseModel):
    """Response format for multi-agent collaboration."""

    collaboration_result: str
    agents_involved: list[str]
    task: str
    status: str
    agent_contributions: list[dict[str, Any]]
    debug_info: dict[str, Any] | None = None


class AgentStatusResponse(BaseModel):
    """Response format for agent status endpoint."""

    available_agents: list[str]
    agent_details: dict[str, Any]
    framework: str
    status: str


# Create router
router = APIRouter(
    prefix="/adapters/autogen",
    tags=["AutoGen Adapter"],
)

# Instantiate the adapter
autogen_adapter = AutoGenAdapter()


@router.post("/chat", response_model=AutoGenResponse)
async def handle_autogen_chat(
    request: AutoGenRequest, db: Session = Depends(get_db_sync)
):
    """
    Endpoint to receive messages from AutoGen frontend and respond via Kor'tana.
    
    This endpoint enables single-agent or multi-agent conversations using
    the AutoGen framework integrated with Kor'tana's orchestrator.
    """
    try:
        # Pass the database session to the adapter method
        response_data = await autogen_adapter.handle_autogen_request(
            request.model_dump(), db
        )
        # Ensure the response matches the AutoGenResponse model
        return AutoGenResponse(**response_data)
    except HTTPException as e:
        # Re-raise HTTPException to let FastAPI handle it
        raise e
    except Exception as e:
        # Catch any other unexpected errors
        print(f"Error in AutoGen adapter endpoint: {e}")
        # Return structured error response
        return AutoGenResponse(
            agent_responses=[
                {
                    "agent": "error_handler",
                    "role": "assistant",
                    "content": "An unexpected error occurred while processing your request.",
                    "metadata": {"error": True},
                }
            ],
            conversation_id=request.conversation_id or "error",
            status="error",
            debug_info={"error": str(e)},
        )


@router.post("/collaborate", response_model=MultiAgentResponse)
async def handle_multi_agent_collaboration(
    request: MultiAgentRequest, db: Session = Depends(get_db_sync)
):
    """
    Endpoint for multi-agent collaboration using AutoGen.
    
    This endpoint enables multiple agents to work together on complex tasks,
    coordinating their efforts to produce comprehensive results.
    """
    try:
        response_data = await autogen_adapter.handle_multi_agent_collaboration(
            request.model_dump(), db
        )
        return MultiAgentResponse(**response_data)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error in multi-agent collaboration endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Multi-agent collaboration failed: {str(e)}",
        )


@router.get("/status", response_model=AgentStatusResponse)
async def get_agent_status():
    """
    Get status and configuration of available AutoGen agents.
    
    This endpoint provides information about all configured agents,
    their capabilities, and current operational status.
    """
    try:
        status_data = autogen_adapter.get_agent_status()
        return AgentStatusResponse(**status_data)
    except Exception as e:
        print(f"Error getting agent status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve agent status: {str(e)}"
        )


@router.get("/health")
async def autogen_health_check():
    """
    Health check endpoint for AutoGen adapter.
    
    Returns basic health status of the AutoGen integration.
    """
    return {
        "status": "healthy",
        "adapter": "AutoGen",
        "framework": "Microsoft AutoGen",
        "message": "AutoGen adapter is operational",
    }
