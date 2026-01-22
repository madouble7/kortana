"""
MCP (Model Context Protocol) Router for Kor'tana

This module provides MCP endpoints that extend LLM functionality
by exposing Kor'tana's internal tools and services.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.kortana.services.database import get_db_sync
from src.kortana.modules.memory_core.services import MemoryService
import os

router = APIRouter(
    prefix="/api/mcp",
    tags=["MCP - Model Context Protocol"],
)


def verify_mcp_token(authorization: Optional[str] = Header(None)) -> bool:
    """Verify MCP authentication token."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format",
        )

    api_key = os.environ.get("KORTANA_API_KEY", "kortana-default-key")
    if parts[1] != api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    return True


# MCP Request/Response Models
class MCPToolRequest(BaseModel):
    """MCP tool invocation request."""

    tool_name: str = Field(..., description="Name of the tool to invoke")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Tool parameters"
    )


class MCPToolResponse(BaseModel):
    """MCP tool invocation response."""

    success: bool = Field(..., description="Whether the tool executed successfully")
    result: Any = Field(None, description="Tool execution result")
    error: Optional[str] = Field(None, description="Error message if failed")


# Memory MCP Endpoints
@router.post("/memory/search", response_model=MCPToolResponse)
async def mcp_search_memory(
    request: MCPToolRequest,
    db: Session = Depends(get_db_sync),
    _: bool = Depends(verify_mcp_token),
):
    """
    MCP endpoint to search Kor'tana's memory system.
    
    Parameters:
    - query: Search query string
    - limit: Maximum number of results (default: 5)
    """
    try:
        query = request.parameters.get("query", "")
        limit = request.parameters.get("limit", 5)

        if not query:
            return MCPToolResponse(
                success=False, error="Query parameter is required", result=None
            )

        memory_service = MemoryService(db=db)
        results = await memory_service.search_memories(query=query, limit=limit)

        return MCPToolResponse(
            success=True,
            result={
                "memories": [
                    {
                        "id": memory.id,
                        "content": memory.content,
                        "relevance_score": memory.relevance_score,
                        "created_at": memory.created_at.isoformat()
                        if hasattr(memory, "created_at")
                        else None,
                    }
                    for memory in results
                ],
                "count": len(results),
            },
        )

    except Exception as e:
        return MCPToolResponse(success=False, error=str(e), result=None)


@router.post("/memory/store", response_model=MCPToolResponse)
async def mcp_store_memory(
    request: MCPToolRequest,
    db: Session = Depends(get_db_sync),
    _: bool = Depends(verify_mcp_token),
):
    """
    MCP endpoint to store information in Kor'tana's memory.
    
    Parameters:
    - content: Content to store
    - tags: Optional tags for categorization
    """
    try:
        content = request.parameters.get("content", "")
        tags = request.parameters.get("tags", [])

        if not content:
            return MCPToolResponse(
                success=False, error="Content parameter is required", result=None
            )

        memory_service = MemoryService(db=db)
        memory = await memory_service.store_memory(content=content, tags=tags)

        return MCPToolResponse(
            success=True,
            result={
                "id": memory.id,
                "content": memory.content,
                "tags": tags,
                "created": True,
            },
        )

    except Exception as e:
        return MCPToolResponse(success=False, error=str(e), result=None)


# Goal MCP Endpoints
@router.post("/goals/list", response_model=MCPToolResponse)
async def mcp_list_goals(
    request: MCPToolRequest,
    db: Session = Depends(get_db_sync),
    _: bool = Depends(verify_mcp_token),
):
    """
    MCP endpoint to list Kor'tana's goals.
    
    Parameters:
    - status: Filter by status (pending, active, completed)
    """
    try:
        # Import here to avoid circular dependencies
        from src.kortana.core.services.goal_service import GoalService

        status_filter = request.parameters.get("status", None)
        goal_service = GoalService(db=db)

        goals = await goal_service.get_goals(status=status_filter)

        return MCPToolResponse(
            success=True,
            result={
                "goals": [
                    {
                        "id": goal.id,
                        "title": goal.title,
                        "description": goal.description,
                        "status": goal.status,
                        "priority": getattr(goal, "priority", None),
                    }
                    for goal in goals
                ],
                "count": len(goals),
            },
        )

    except Exception as e:
        return MCPToolResponse(success=False, error=str(e), result=None)


@router.post("/goals/create", response_model=MCPToolResponse)
async def mcp_create_goal(
    request: MCPToolRequest,
    db: Session = Depends(get_db_sync),
    _: bool = Depends(verify_mcp_token),
):
    """
    MCP endpoint to create a new goal for Kor'tana.
    
    Parameters:
    - title: Goal title
    - description: Detailed description
    - priority: Priority level (1-10)
    """
    try:
        from src.kortana.core.services.goal_service import GoalService

        title = request.parameters.get("title", "")
        description = request.parameters.get("description", "")
        priority = request.parameters.get("priority", 5)

        if not title:
            return MCPToolResponse(
                success=False, error="Title parameter is required", result=None
            )

        goal_service = GoalService(db=db)
        goal = await goal_service.create_goal(
            title=title, description=description, priority=priority
        )

        return MCPToolResponse(
            success=True,
            result={
                "id": goal.id,
                "title": goal.title,
                "description": goal.description,
                "priority": priority,
                "created": True,
            },
        )

    except Exception as e:
        return MCPToolResponse(success=False, error=str(e), result=None)


# Context MCP Endpoints
@router.post("/context/gather", response_model=MCPToolResponse)
async def mcp_gather_context(
    request: MCPToolRequest,
    db: Session = Depends(get_db_sync),
    _: bool = Depends(verify_mcp_token),
):
    """
    MCP endpoint to gather contextual information.
    
    Parameters:
    - query: Query to gather context for
    - sources: List of sources to use (memory, files, web)
    """
    try:
        query = request.parameters.get("query", "")
        sources = request.parameters.get("sources", ["memory"])

        if not query:
            return MCPToolResponse(
                success=False, error="Query parameter is required", result=None
            )

        context_data = {"query": query, "sources": [], "total_results": 0}

        # Gather from memory if requested
        if "memory" in sources:
            memory_service = MemoryService(db=db)
            memories = await memory_service.search_memories(query=query, limit=5)
            context_data["sources"].append(
                {
                    "type": "memory",
                    "count": len(memories),
                    "items": [
                        {"content": m.content, "relevance": getattr(m, "relevance_score", 0)}
                        for m in memories
                    ],
                }
            )
            context_data["total_results"] += len(memories)

        # TODO: Implement file and web sources when available

        return MCPToolResponse(success=True, result=context_data)

    except Exception as e:
        return MCPToolResponse(success=False, error=str(e), result=None)


# MCP Discovery Endpoint
@router.get("/discover")
async def mcp_discover_tools(_: bool = Depends(verify_mcp_token)):
    """
    Discover available MCP tools and their capabilities.
    
    This endpoint returns metadata about all available MCP tools
    that can be used to extend LLM functionality.
    """
    return {
        "protocol": "MCP",
        "version": "1.0",
        "server": "Kor'tana MCP Server",
        "tools": [
            {
                "name": "search_memory",
                "endpoint": "/api/mcp/memory/search",
                "description": "Search Kor'tana's memory for relevant context",
                "parameters": ["query", "limit"],
            },
            {
                "name": "store_memory",
                "endpoint": "/api/mcp/memory/store",
                "description": "Store information in Kor'tana's memory",
                "parameters": ["content", "tags"],
            },
            {
                "name": "list_goals",
                "endpoint": "/api/mcp/goals/list",
                "description": "List Kor'tana's goals",
                "parameters": ["status"],
            },
            {
                "name": "create_goal",
                "endpoint": "/api/mcp/goals/create",
                "description": "Create a new goal",
                "parameters": ["title", "description", "priority"],
            },
            {
                "name": "gather_context",
                "endpoint": "/api/mcp/context/gather",
                "description": "Gather contextual information",
                "parameters": ["query", "sources"],
            },
        ],
    }
