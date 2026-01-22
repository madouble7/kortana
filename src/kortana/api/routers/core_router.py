import time
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.kortana.core.orchestrator import KorOrchestrator
from src.kortana.services.database import get_db_sync

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
    language: str | None = Field(
        None,
        description="ISO 639-1 language code for the response (e.g., 'en', 'es', 'fr')",
        min_length=2,
        max_length=2,
    )


@router.post("/query", response_model=dict[str, Any])
async def process_user_query(request: QueryRequest, db: Session = Depends(get_db_sync)):
    """
    Main endpoint for interacting with Kor'tana's core logic.
    Supports multilingual responses via the optional 'language' parameter.
    """
    orchestrator = KorOrchestrator(db=db)
    return await orchestrator.process_query(query=request.query, language=request.language)


# --- New OpenAI-Compatible Adapter Endpoint ---


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str | None = None
    messages: list[ChatMessage]
    language: str | None = Field(
        None,
        description="ISO 639-1 language code for the response (e.g., 'en', 'es', 'fr')",
    )


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


@openai_adapter_router.post("/chat/completions", response_model=ChatCompletionResponse)
async def openai_chat_completions_adapter(
    request: ChatCompletionRequest, db: Session = Depends(get_db_sync)
):
    """
    OpenAI-compatible chat completions endpoint for LobeChat integration.
    Supports multilingual responses via the optional 'language' parameter.
    """
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
    kortana_response_data = await orchestrator.process_query(
        query=user_query, language=request.language
    )

    response_text: str
    if isinstance(kortana_response_data, dict):
        response_text = kortana_response_data.get(
            "response",
            kortana_response_data.get("content", "Sorry, I could not process that."),
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
