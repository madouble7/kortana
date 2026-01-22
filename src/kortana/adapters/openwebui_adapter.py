"""
Open WebUI Adapter for Kor'tana

This module provides an OpenAI-compatible API adapter for Open WebUI integration.
It translates Open WebUI's OpenAI-formatted requests to Kor'tana's internal format
and returns OpenAI-compatible responses.
"""

import os
import time
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.kortana.config import settings
from src.kortana.core.orchestrator import KorOrchestrator
from src.kortana.services.database import get_db_sync

router = APIRouter(
    prefix="/api/openai/v1",
    tags=["Open WebUI Integration - OpenAI Compatible API"],
)


# OpenAI-compatible Models
class OpenAIMessage(BaseModel):
    """OpenAI message format."""

    role: str = Field(..., description="Role: system, user, or assistant")
    content: str = Field(..., description="Message content")
    name: Optional[str] = Field(None, description="Optional name")


class OpenAIChatRequest(BaseModel):
    """OpenAI chat completion request format."""

    model: str = Field(default="gpt-4", description="Model identifier")
    messages: List[OpenAIMessage] = Field(..., description="Chat messages")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    stream: bool = Field(default=False, description="Enable streaming responses")
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    user: Optional[str] = Field(None, description="User identifier")


class OpenAIChoice(BaseModel):
    """OpenAI response choice."""

    index: int
    message: OpenAIMessage
    finish_reason: str = "stop"


class OpenAIUsage(BaseModel):
    """Token usage information."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class OpenAIChatResponse(BaseModel):
    """OpenAI chat completion response format."""

    id: str = Field(..., description="Unique response ID")
    object: str = Field(default="chat.completion", description="Object type")
    created: int = Field(..., description="Unix timestamp")
    model: str = Field(..., description="Model used")
    choices: List[OpenAIChoice] = Field(..., description="Response choices")
    usage: OpenAIUsage = Field(..., description="Token usage")


class OpenAIModel(BaseModel):
    """OpenAI model information."""

    id: str
    object: str = "model"
    created: int
    owned_by: str = "kortana"


class OpenAIModelList(BaseModel):
    """List of available models."""

    object: str = "list"
    data: List[OpenAIModel]


def verify_api_key(authorization: Optional[str] = Header(None)) -> bool:
    """Verify the API key from the request headers."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected: Bearer <token>",
        )

    api_key = os.environ.get(
        "KORTANA_API_KEY", getattr(settings, "KORTANA_API_KEY", "kortana-default-key")
    )

    if parts[1] != api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return True


class OpenWebUIAdapter:
    """Adapter for handling Open WebUI OpenAI-compatible requests."""

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Rough estimation of token count (approximately 4 characters per token)."""
        return len(text) // 4

    async def process_chat_completion(
        self, request: OpenAIChatRequest, db: Session
    ) -> OpenAIChatResponse:
        """Process a chat completion request."""
        # Extract the last user message as the query
        user_messages = [msg for msg in request.messages if msg.role == "user"]
        if not user_messages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No user messages found in request",
            )

        user_query = user_messages[-1].content

        # Build context from previous messages
        context_messages = []
        for msg in request.messages[:-1]:
            context_messages.append(f"{msg.role}: {msg.content}")

        # Process through Kor'tana's orchestrator
        orchestrator = KorOrchestrator(db=db)
        response_data = await orchestrator.process_query(
            query=user_query,
            context="\n".join(context_messages) if context_messages else None,
        )

        # Extract the response
        assistant_message = response_data.get(
            "final_response", "I'm processing your request..."
        )

        # Calculate token usage (rough estimation)
        prompt_text = " ".join([msg.content for msg in request.messages])
        prompt_tokens = self._estimate_tokens(prompt_text)
        completion_tokens = self._estimate_tokens(assistant_message)

        # Build OpenAI-compatible response
        response_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
        timestamp = int(time.time())

        return OpenAIChatResponse(
            id=response_id,
            created=timestamp,
            model=request.model,
            choices=[
                OpenAIChoice(
                    index=0,
                    message=OpenAIMessage(role="assistant", content=assistant_message),
                    finish_reason="stop",
                )
            ],
            usage=OpenAIUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
        )

    async def stream_chat_completion(
        self, request: OpenAIChatRequest, db: Session
    ) -> AsyncGenerator[str, None]:
        """Stream a chat completion response in OpenAI format."""
        # For now, return a non-streaming response formatted as SSE
        # TODO: Implement actual streaming when Kor'tana orchestrator supports it
        response = await self.process_chat_completion(request, db)

        # Stream the response in OpenAI's server-sent events format
        response_id = response.id
        timestamp = response.created

        # Stream the message content
        content = response.choices[0].message.content
        
        # Send the complete chunk
        chunk = {
            "id": response_id,
            "object": "chat.completion.chunk",
            "created": timestamp,
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "delta": {"role": "assistant", "content": content},
                    "finish_reason": None,
                }
            ],
        }
        yield f"data: {chunk}\n\n"

        # Send the final chunk
        final_chunk = {
            "id": response_id,
            "object": "chat.completion.chunk",
            "created": timestamp,
            "model": request.model,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
        }
        yield f"data: {final_chunk}\n\n"
        yield "data: [DONE]\n\n"


# API Endpoints
@router.get("/models", response_model=OpenAIModelList)
async def list_models(_: bool = Depends(verify_api_key)) -> OpenAIModelList:
    """
    List available models in OpenAI format.
    
    This endpoint returns a list of models that Kor'tana can use,
    formatted according to OpenAI's API specification.
    """
    models = [
        OpenAIModel(
            id="gpt-4",
            created=int(time.time()),
            owned_by="kortana",
        ),
        OpenAIModel(
            id="gpt-3.5-turbo",
            created=int(time.time()),
            owned_by="kortana",
        ),
        OpenAIModel(
            id="claude-3-opus",
            created=int(time.time()),
            owned_by="kortana",
        ),
        OpenAIModel(
            id="claude-3-sonnet",
            created=int(time.time()),
            owned_by="kortana",
        ),
    ]

    return OpenAIModelList(data=models)


@router.post("/chat/completions")
async def create_chat_completion(
    request: OpenAIChatRequest,
    db: Session = Depends(get_db_sync),
    _: bool = Depends(verify_api_key),
):
    """
    Create a chat completion using OpenAI-compatible format.
    
    This endpoint accepts OpenAI-formatted requests from Open WebUI
    and returns responses in OpenAI format. Supports both streaming
    and non-streaming responses.
    """
    try:
        adapter = OpenWebUIAdapter()

        if request.stream:
            # Return streaming response
            return StreamingResponse(
                adapter.stream_chat_completion(request, db),
                media_type="text/event-stream",
            )
        else:
            # Return regular response
            return await adapter.process_chat_completion(request, db)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in chat completion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat completion: {str(e)}",
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for Open WebUI integration."""
    return {
        "status": "healthy",
        "service": "Kor'tana OpenAI-Compatible API",
        "version": "1.0.0",
    }
