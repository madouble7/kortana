"""
LobeChat Adapter for Kor'tana

This module provides an adapter between LobeChat's frontend API expectations
and Kor'tana's backend API. It handles the transformation of requests and responses
between the two systems.
"""

import os

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.kortana.config import settings
from src.kortana.core.orchestrator import KorOrchestrator
from src.kortana.services.database import get_db_sync

router = APIRouter(
    prefix="/api/lobe",
    tags=["LobeChat Integration"],
)


class LobeMessage(BaseModel):
    """Represents a message in LobeChat format."""

    content: str = Field(..., description="The message content")
    conversation_id: str | None = Field(None, description="Conversation ID")
    parent_message_id: str | None = Field(None, description="Parent message ID")
    model: str | None = Field(None, description="Model name")
    temperature: float | None = Field(None, description="Temperature for generation")


class LobeResponse(BaseModel):
    """Response format expected by LobeChat."""

    id: str = Field(..., description="Response ID")
    content: str = Field(..., description="Response content")
    conversation_id: str = Field(..., description="Conversation ID")
    created_at: int = Field(..., description="Creation timestamp")


def verify_api_key(authorization: str | None = Header(None)) -> bool:
    """Verify the API key from the request headers."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )

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

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key not configured on the server",
        )

    if api_key_parts[1] != api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return True


class LobeChatAdapter:
    """Adapter for handling LobeChat requests."""

    async def handle_lobe_chat_request(
        self, request: LobeMessage, db: Session
    ) -> LobeResponse:
        """Handle a LobeChat request and return a response."""
        user_query = request.content
        orchestrator = KorOrchestrator(db=db)
        orchestrator_response = await orchestrator.process_query(query=user_query)
        import time
        import uuid

        return LobeResponse(
            id=str(uuid.uuid4()),
            content=orchestrator_response.get(
                "final_response", "I'm processing your request..."
            ),
            conversation_id=request.conversation_id or str(uuid.uuid4()),
            created_at=int(time.time() * 1000),
        )


@router.post("/chat", response_model=LobeResponse)
async def process_lobe_chat(
    message: LobeMessage,
    request: Request,
    db: Session = Depends(get_db_sync),
    _: bool = Depends(verify_api_key),
) -> LobeResponse:
    """
    Process a chat message from LobeChat and return a response.

    This endpoint adapts LobeChat's API format to Kor'tana's internal format,
    processes the query, and then transforms the response back to LobeChat's
    expected format.
    """
    try:
        adapter = LobeChatAdapter()
        return await adapter.handle_lobe_chat_request(request=message, db=db)

    except Exception as e:
        # Log the error
        print(f"Error processing LobeChat message: {e}")

        # Return a friendly error message
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kor'tana encountered an error processing your message. Please try again.",
        ) from e
