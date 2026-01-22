"""
OpenAI-Compatible LobeChat Adapter for Kor'tana

This adapter implements the OpenAI Chat Completions API format to enable
seamless integration with LobeChat frontend, which expects OpenAI-compatible endpoints.

LobeChat can connect to custom backends that implement the OpenAI API format.
"""

import os
import time
import uuid
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.kortana.core.orchestrator import KorOrchestrator
from src.kortana.services.database import get_db_sync

router = APIRouter(
    prefix="/v1",
    tags=["OpenAI-Compatible API for LobeChat"],
)


# OpenAI-compatible Pydantic models
class Message(BaseModel):
    """Represents a message in the conversation."""
    role: Literal["system", "user", "assistant"] = Field(
        ..., description="The role of the message author"
    )
    content: str = Field(..., description="The content of the message")
    name: Optional[str] = Field(None, description="Optional name of the message author")


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible chat completion request format."""
    model: str = Field(default="kortana-default", description="Model to use for completion")
    messages: List[Message] = Field(..., description="List of messages in the conversation")
    temperature: Optional[float] = Field(default=0.7, ge=0, le=2, description="Sampling temperature")
    top_p: Optional[float] = Field(default=1.0, ge=0, le=1, description="Nucleus sampling parameter")
    n: Optional[int] = Field(default=1, description="Number of completions to generate")
    stream: Optional[bool] = Field(default=False, description="Whether to stream responses")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    presence_penalty: Optional[float] = Field(default=0, ge=-2, le=2)
    frequency_penalty: Optional[float] = Field(default=0, ge=-2, le=2)
    user: Optional[str] = Field(None, description="Unique identifier for the end-user")


class ChatCompletionChoice(BaseModel):
    """Represents a single completion choice."""
    index: int = Field(..., description="Index of this choice")
    message: Message = Field(..., description="The generated message")
    finish_reason: str = Field(..., description="Reason for completion finishing")


class Usage(BaseModel):
    """Token usage information."""
    prompt_tokens: int = Field(..., description="Tokens in the prompt")
    completion_tokens: int = Field(..., description="Tokens in the completion")
    total_tokens: int = Field(..., description="Total tokens used")


class ChatCompletionResponse(BaseModel):
    """OpenAI-compatible chat completion response format."""
    id: str = Field(..., description="Unique identifier for this completion")
    object: str = Field(default="chat.completion", description="Object type")
    created: int = Field(..., description="Unix timestamp of creation")
    model: str = Field(..., description="Model used for completion")
    choices: List[ChatCompletionChoice] = Field(..., description="List of completion choices")
    usage: Usage = Field(..., description="Token usage information")


class ModelInfo(BaseModel):
    """Information about a model."""
    id: str
    object: str = "model"
    created: int
    owned_by: str = "kortana"


class ModelListResponse(BaseModel):
    """List of available models."""
    object: str = "list"
    data: List[ModelInfo]


def verify_api_key(authorization: Optional[str] = Header(None)) -> bool:
    """
    Verify the API key from the request headers.
    
    Supports both:
    - Authorization: Bearer <token>
    - x-api-key: <token> (for compatibility)
    """
    api_key = os.environ.get("KORTANA_API_KEY")
    
    if not api_key:
        # Log warning about open access in development mode
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            "KORTANA_API_KEY not configured - API is accessible without authentication. "
            "This is acceptable for development but should NEVER be used in production. "
            "Set KORTANA_API_KEY in your .env file to enable authentication."
        )
        return True
    
    # Check Authorization header
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            if parts[1] == api_key:
                return True
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.get("/models", response_model=ModelListResponse)
async def list_models(_: bool = Depends(verify_api_key)):
    """
    List available models (OpenAI-compatible endpoint).
    
    LobeChat uses this endpoint to discover available models.
    """
    return ModelListResponse(
        object="list",
        data=[
            ModelInfo(
                id="kortana-default",
                object="model",
                created=int(time.time()),
                owned_by="kortana"
            ),
            ModelInfo(
                id="gpt-4o-mini-openai",
                object="model", 
                created=int(time.time()),
                owned_by="kortana"
            ),
            ModelInfo(
                id="gemini-2.0-flash-lite",
                object="model",
                created=int(time.time()),
                owned_by="kortana"
            ),
        ]
    )


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    request: ChatCompletionRequest,
    db: Session = Depends(get_db_sync),
    _: bool = Depends(verify_api_key),
) -> ChatCompletionResponse:
    """
    Create a chat completion (OpenAI-compatible endpoint).
    
    This is the main endpoint that LobeChat uses for chat interactions.
    It processes messages through Kor'tana's orchestrator and returns
    responses in OpenAI-compatible format.
    """
    try:
        # Extract the user's latest message
        if not request.messages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No messages provided"
            )
        
        # Get the last user message
        user_messages = [msg for msg in request.messages if msg.role == "user"]
        if not user_messages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No user messages found"
            )
        
        user_query = user_messages[-1].content
        
        # Build context from conversation history
        conversation_context = []
        for msg in request.messages[:-1]:  # Exclude the current message
            if msg.role in ["system", "user", "assistant"]:
                conversation_context.append(f"{msg.role}: {msg.content}")
        
        # Process through Kor'tana's orchestrator
        orchestrator = KorOrchestrator(db=db)
        
        # Add conversation context to the query if available
        if conversation_context:
            enhanced_query = f"Conversation context:\n" + "\n".join(conversation_context[-5:]) + f"\n\nCurrent query: {user_query}"
        else:
            enhanced_query = user_query
        
        orchestrator_response = await orchestrator.process_query(query=enhanced_query)
        
        # Extract the response content
        response_content = orchestrator_response.get(
            "final_response",
            orchestrator_response.get(
                "final_kortana_response",
                "I'm processing your request..."
            )
        )
        
        # Create OpenAI-compatible response
        completion_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
        
        # Estimate token counts (simplified approximation)
        # NOTE: This is a rough approximation using word count * 1.3
        # For accurate token counting, consider using tiktoken library
        # Real token count may vary depending on the model's tokenizer
        prompt_tokens = int(sum(len(msg.content.split()) for msg in request.messages) * 1.3)
        completion_tokens = int(len(response_content.split()) * 1.3)
        
        return ChatCompletionResponse(
            id=completion_id,
            object="chat.completion",
            created=int(time.time()),
            model=request.model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=Message(
                        role="assistant",
                        content=response_content
                    ),
                    finish_reason="stop"
                )
            ],
            usage=Usage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in chat completion: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat completion: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for the OpenAI-compatible API."""
    return {
        "status": "healthy",
        "api": "OpenAI-compatible API for Kor'tana",
        "version": "1.0.0"
    }
