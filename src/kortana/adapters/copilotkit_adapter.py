"""
CopilotKit Adapter for Kor'tana

This module provides an adapter between CopilotKit's frontend API expectations
and Kor'tana's backend API. It handles the transformation of requests and responses
between the two systems.
"""

import os
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.kortana.config import settings
from src.kortana.core.orchestrator import KorOrchestrator
from src.kortana.services.database import get_db_sync

router = APIRouter(
    prefix="/copilotkit",
    tags=["CopilotKit Integration"],
)


class CopilotMessage(BaseModel):
    """Represents a message in CopilotKit format."""

    role: str = Field(..., description="Message role (user/assistant/system)")
    content: str = Field(..., description="The message content")


class CopilotRequest(BaseModel):
    """Request format from CopilotKit."""

    messages: List[CopilotMessage] = Field(..., description="Conversation messages")
    context: Dict[str, Any] | None = Field(None, description="Additional context")
    stream: bool | None = Field(False, description="Whether to stream the response")


class CopilotResponse(BaseModel):
    """Response format expected by CopilotKit."""

    id: str = Field(..., description="Response ID")
    role: str = Field(default="assistant", description="Role of the response")
    content: str = Field(..., description="Response content")
    metadata: Dict[str, Any] | None = Field(None, description="Additional metadata")


def verify_api_key(authorization: str | None = Header(None)) -> bool:
    """Verify the API key from the request headers."""
    # For development, allow requests without auth
    # In production, you should enforce this
    if not authorization:
        # For now, allow without auth for easier development
        return True

    api_key_parts = authorization.split()
    if len(api_key_parts) != 2 or api_key_parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format",
        )
    
    # Get the API key from environment or settings
    api_key = os.environ.get(
        "KORTANA_API_KEY", getattr(settings, "KORTANA_API_KEY", None)
    )

    if api_key and api_key_parts[1] != api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return True


class CopilotKitAdapter:
    """Adapter for handling CopilotKit requests."""

    async def handle_copilotkit_request(
        self, request: CopilotRequest, db: Session
    ) -> CopilotResponse:
        """Handle a CopilotKit request and return a response."""
        # Extract the last user message
        user_messages = [msg for msg in request.messages if msg.role == "user"]
        if not user_messages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No user message found in the request",
            )

        user_query = user_messages[-1].content

        # Process the query through Kor'tana's orchestrator
        orchestrator = KorOrchestrator(db=db)
        orchestrator_response = await orchestrator.process_query(query=user_query)

        # Extract relevant metadata from the orchestrator response
        metadata = {
            "model_used": orchestrator_response.get("model_used"),
            "memory_context": orchestrator_response.get("memory_context"),
            "ethical_evaluation": orchestrator_response.get("ethical_evaluation"),
        }

        return CopilotResponse(
            id=str(uuid.uuid4()),
            role="assistant",
            content=orchestrator_response.get(
                "final_response", "I'm processing your request..."
            ),
            metadata=metadata,
        )


@router.post("", response_model=CopilotResponse)
async def process_copilotkit_chat(
    copilot_request: CopilotRequest,
    request: Request,
    db: Session = Depends(get_db_sync),
    _: bool = Depends(verify_api_key),
) -> CopilotResponse:
    """
    Process a chat message from CopilotKit and return a response.

    This endpoint adapts CopilotKit's API format to Kor'tana's internal format,
    processes the query, and then transforms the response back to CopilotKit's
    expected format.
    """
    try:
        adapter = CopilotKitAdapter()
        return await adapter.handle_copilotkit_request(
            request=copilot_request, db=db
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the error
        print(f"Error processing CopilotKit message: {e}")
        import traceback
        traceback.print_exc()

        # Return a friendly error message
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Kor'tana encountered an error processing your message: {str(e)}",
        ) from e


@router.get("/health")
async def copilotkit_health_check():
    """Health check endpoint for CopilotKit integration."""
    return {
        "status": "healthy",
        "service": "Kor'tana CopilotKit Adapter",
        "version": "1.0.0",
    }
