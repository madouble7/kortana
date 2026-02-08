import time
import uuid
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from kortana.core.orchestrator import KorOrchestrator
from kortana.services.database import get_db_sync

# Existing router for /core/query
router = APIRouter(
    prefix="/core",
    tags=["Core Logic"],
)


class QueryRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        examples=["What do you remember about our first conversation?"],
    )


@router.post("/query", response_model=dict[str, Any])
async def process_user_query(request: QueryRequest, db: Session = Depends(get_db_sync)):
    """
    Main endpoint for interacting with Kor'tana's core logic.
    """
    orchestrator = KorOrchestrator(db=db)
    return await orchestrator.process_query(query=request.query)


# --- New OpenAI-Compatible Adapter Endpoint ---


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str | None = None
    messages: list[ChatMessage]
    stream: bool = False  # Add support for streaming


class ChatCompletionChoice(BaseModel):
    index: int = 0
    message: ChatMessage
    finish_reason: str = "stop"


class UsageInfo(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex}")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str | None = "kortana-custom"
    choices: list[ChatCompletionChoice]
    usage: UsageInfo | None = Field(default_factory=UsageInfo)


openai_adapter_router = APIRouter(
    prefix="/v1",
    tags=["OpenAI Adapter"],
)


async def stream_chat_response(
    request: ChatCompletionRequest, db: Session
) -> AsyncIterator[str]:
    """
    Stream chat completion responses in SSE format.

    This simulates streaming by breaking the response into chunks.
    In a production system, this would stream tokens as they're generated from the LLM.
    """
    import json

    # Extract user query
    user_query: str | None = None
    if request.messages:
        for msg in reversed(request.messages):
            if msg.role == "user":
                user_query = msg.content
                break

    if not user_query:
        # Send error as stream
        error_chunk = {
            "id": f"chatcmpl-{uuid.uuid4().hex}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": request.model or "kortana-custom",
            "choices": [{
                "index": 0,
                "delta": {"content": "Error: No user message found"},
                "finish_reason": "stop"
            }]
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"
        yield "data: [DONE]\n\n"
        return

    # Process query
    orchestrator = KorOrchestrator(db=db)
    kortana_response_data = await orchestrator.process_query(query=user_query)

    # Extract response text
    response_text: str
    if isinstance(kortana_response_data, dict):
        response_text = kortana_response_data.get(
            "final_kortana_response",
            kortana_response_data.get(
                "response",
                kortana_response_data.get("content", "Sorry, I could not process that."),
            )
        )
    elif isinstance(kortana_response_data, str):
        response_text = kortana_response_data
    else:
        response_text = "Sorry, I received an unexpected response format."

    # Stream the response in chunks
    chunk_id = f"chatcmpl-{uuid.uuid4().hex}"
    created_time = int(time.time())
    model_name = request.model or "kortana-custom"

    # Split response into words for streaming simulation
    words = response_text.split()

    for i, word in enumerate(words):
        chunk_content = word + (" " if i < len(words) - 1 else "")

        chunk = {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": created_time,
            "model": model_name,
            "choices": [{
                "index": 0,
                "delta": {"content": chunk_content},
                "finish_reason": None
            }]
        }

        yield f"data: {json.dumps(chunk)}\n\n"

    # Send final chunk with finish_reason
    final_chunk = {
        "id": chunk_id,
        "object": "chat.completion.chunk",
        "created": created_time,
        "model": model_name,
        "choices": [{
            "index": 0,
            "delta": {},
            "finish_reason": "stop"
        }]
    }
    yield f"data: {json.dumps(final_chunk)}\n\n"
    yield "data: [DONE]\n\n"


@openai_adapter_router.post("/chat/completions")
async def openai_chat_completions_adapter(
    request: ChatCompletionRequest, db: Session = Depends(get_db_sync)
):
    """
    OpenAI-compatible chat completions endpoint for LobeChat integration.

    Supports both streaming and non-streaming responses via the 'stream' parameter.
    """
    # Check if streaming is requested
    if request.stream:
        # Return streaming response
        return StreamingResponse(
            stream_chat_response(request, db),
            media_type="text/event-stream"
        )

    # Non-streaming response (original logic)
    user_query: str | None = None
    if request.messages:
        for msg in reversed(request.messages):
            if msg.role == "user":
                user_query = msg.content
                break

    if not user_query:
        raise HTTPException(
            status_code=400,
            detail="No user message found in request or messages list is empty.",
        )

    orchestrator = KorOrchestrator(db=db)
    kortana_response_data = await orchestrator.process_query(query=user_query)

    response_text: str
    if isinstance(kortana_response_data, dict):
        response_text = kortana_response_data.get(
            "final_kortana_response",
            kortana_response_data.get(
                "response",
                kortana_response_data.get("content", "Sorry, I could not process that."),
            )
        )
    elif isinstance(kortana_response_data, str):
        response_text = kortana_response_data
    else:
        response_text = (
            "Sorry, I received an unexpected response format from the orchestrator."
        )

    assistant_message = ChatMessage(role="assistant", content=response_text)
    choice = ChatCompletionChoice(message=assistant_message)

    response_model_name = request.model or "kortana-custom"

    return ChatCompletionResponse(model=response_model_name, choices=[choice])
