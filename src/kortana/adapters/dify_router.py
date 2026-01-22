# src/kortana/adapters/dify_router.py
"""
API Router for Dify platform integration.

Provides endpoints for:
- Chat applications
- Workflow automation
- Text completion
- Agent-based interactions
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.kortana.services.database import get_db_sync

from .dify_adapter import DifyAdapter


# Pydantic models for Dify interaction
class DifyChatRequest(BaseModel):
    """Request model for Dify chat endpoint."""
    query: str = Field(..., description="User's message or question")
    conversation_id: str | None = Field(None, description="Optional conversation identifier")
    user: str | None = Field(None, description="Optional user identifier")
    inputs: dict[str, Any] = Field(default_factory=dict, description="Optional variables for prompt templates")
    response_mode: str = Field(default="blocking", description="Response mode: 'blocking' or 'streaming'", pattern="^(blocking|streaming)$")


class DifyWorkflowRequest(BaseModel):
    """Request model for Dify workflow endpoint."""
    workflow_id: str = Field(..., description="Workflow identifier")
    inputs: dict[str, Any] = Field(..., description="Input variables for the workflow")
    user: str | None = Field(None, description="Optional user identifier")


class DifyCompletionRequest(BaseModel):
    """Request model for Dify completion endpoint."""
    prompt: str = Field(..., description="The prompt for text completion")
    inputs: dict[str, Any] = Field(default_factory=dict, description="Optional variables for prompt templates")
    user: str | None = Field(None, description="Optional user identifier")


class DifyChatResponse(BaseModel):
    """Response model for Dify chat endpoint."""
    answer: str = Field(..., description="The assistant's response")
    conversation_id: str = Field(..., description="Conversation identifier")
    metadata: dict[str, Any] | None = Field(None, description="Additional response metadata")


class DifyWorkflowResponse(BaseModel):
    """Response model for Dify workflow endpoint."""
    workflow_id: str = Field(..., description="Workflow identifier")
    status: str = Field(..., description="Workflow execution status")
    outputs: dict[str, Any] | None = Field(None, description="Workflow output results")
    error: str | None = Field(None, description="Error message if workflow failed")


class DifyCompletionResponse(BaseModel):
    """Response model for Dify completion endpoint."""
    completion: str = Field(..., description="The completion result")
    metadata: dict[str, Any] | None = Field(None, description="Additional completion metadata")
    error: str | None = Field(None, description="Error message if completion failed")


class DifyAdapterInfo(BaseModel):
    """Response model for adapter information."""
    name: str
    version: str
    supported_features: list[str]
    security: dict[str, Any]
    capabilities: dict[str, Any]


router = APIRouter(
    prefix="/adapters/dify",
    tags=["Dify Adapter"],
    responses={
        400: {"description": "Bad Request - Invalid input"},
        401: {"description": "Unauthorized - Invalid API key"},
        500: {"description": "Internal Server Error"},
    },
)

# Instantiate the Dify adapter
dify_adapter_instance = DifyAdapter()


def verify_dify_api_key(authorization: str | None = Header(None)) -> bool:
    """
    Verify Dify API key from Authorization header.
    
    In production, this validates against configured API keys.
    Can be disabled by setting DIFY_REQUIRE_AUTH=false in environment.
    
    Args:
        authorization: Authorization header value
        
    Returns:
        True if valid, raises HTTPException otherwise
    """
    import os
    
    # Check if authentication is required
    require_auth = os.getenv("DIFY_REQUIRE_AUTH", "false").lower() == "true"
    
    if not require_auth:
        # Authentication disabled (development mode)
        return True
    
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header. Include 'Bearer <api-key>' in request headers."
        )
    
    # Extract the token from "Bearer <token>" format
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format. Use 'Bearer <api-key>'."
        )
    
    token = authorization.replace("Bearer ", "").strip()
    
    # Validate against configured API key
    expected_key = os.getenv("DIFY_API_KEY")
    
    if not expected_key:
        # No API key configured - allow access but log warning
        print("WARNING: DIFY_API_KEY not configured. All requests will be accepted.")
        return True
    
    if token != expected_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key."
        )
    
    return True


@router.post("/chat", response_model=DifyChatResponse)
async def handle_dify_chat(
    request: DifyChatRequest,
    db: Session = Depends(get_db_sync),
    _authorized: bool = Depends(verify_dify_api_key)
):
    """
    Handle chat messages from Dify applications.
    
    This endpoint processes chat requests and returns context-aware responses
    powered by Kor'tana's memory and reasoning systems.
    
    Example request:
    ```json
    {
        "query": "What is the meaning of life?",
        "conversation_id": "conv_123",
        "user": "user_456",
        "inputs": {"context": "philosophical"}
    }
    ```
    """
    try:
        response_data = await dify_adapter_instance.handle_chat_request(
            request.model_dump(), db
        )
        return DifyChatResponse(**response_data)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in Dify chat endpoint: {e}")
        return DifyChatResponse(
            answer="An unexpected error occurred while processing your request.",
            conversation_id=request.conversation_id or "default",
            metadata={"error": str(e), "error_type": type(e).__name__},
        )


@router.post("/workflows/run", response_model=DifyWorkflowResponse)
async def handle_dify_workflow(
    request: DifyWorkflowRequest,
    db: Session = Depends(get_db_sync),
    _authorized: bool = Depends(verify_dify_api_key)
):
    """
    Execute Dify workflows with Kor'tana backend processing.
    
    This endpoint supports Dify's workflow automation features,
    allowing complex multi-step AI operations.
    
    Example request:
    ```json
    {
        "workflow_id": "wf_789",
        "inputs": {
            "query": "Analyze customer feedback",
            "data_source": "recent_reviews"
        },
        "user": "analyst_123"
    }
    ```
    """
    try:
        response_data = await dify_adapter_instance.handle_workflow_request(
            request.model_dump(), db
        )
        return DifyWorkflowResponse(**response_data)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in Dify workflow endpoint: {e}")
        return DifyWorkflowResponse(
            workflow_id=request.workflow_id,
            status="failed",
            error=str(e),
        )


@router.post("/completion", response_model=DifyCompletionResponse)
async def handle_dify_completion(
    request: DifyCompletionRequest,
    db: Session = Depends(get_db_sync),
    _authorized: bool = Depends(verify_dify_api_key)
):
    """
    Handle text completion requests from Dify.
    
    This endpoint provides text completion capabilities for
    non-chat Dify applications.
    
    Example request:
    ```json
    {
        "prompt": "Write a function that calculates fibonacci numbers",
        "inputs": {"language": "python"},
        "user": "dev_001"
    }
    ```
    """
    try:
        response_data = await dify_adapter_instance.handle_completion_request(
            request.model_dump(), db
        )
        return DifyCompletionResponse(**response_data)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in Dify completion endpoint: {e}")
        return DifyCompletionResponse(
            completion="",
            error=str(e),
        )


@router.get("/info", response_model=DifyAdapterInfo)
async def get_dify_adapter_info():
    """
    Get information about the Dify adapter capabilities.
    
    Returns metadata about supported features, security measures,
    and integration capabilities.
    """
    try:
        info = dify_adapter_instance.get_adapter_info()
        return DifyAdapterInfo(**info)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving adapter info: {str(e)}"
        )


@router.get("/health")
async def dify_adapter_health():
    """
    Health check endpoint for Dify integration.
    
    Returns the operational status of the Dify adapter.
    """
    return {
        "status": "healthy",
        "adapter": "Dify",
        "version": "1.0.0",
        "message": "Dify adapter is operational and ready to process requests",
    }
