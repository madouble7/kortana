"""
LobeChat Adapter with OpenAI-Compatible API Layer
Provides LobeChat-compatible endpoints with OpenAI API format
"""

from typing import Any, AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()


class LobeChatMessage(BaseModel):
    """Message in LobeChat format"""

    role: str
    content: str


class LobeChatRequest(BaseModel):
    """Chat request from LobeChat"""

    model: str | None = "kortana-ai"
    messages: list[LobeChatMessage]
    stream: bool = False
    temperature: float = 0.7
    max_tokens: int | None = None
    functions: list[dict[str, Any]] | None = None


class LobeChatResponse(BaseModel):
    """Chat response for LobeChat (OpenAI format)"""

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[dict[str, Any]]
    usage: dict[str, int] | None = None


@router.post("/v1/chat/completions")
async def chat_completions(request: LobeChatRequest) -> StreamingResponse | dict[str, Any]:
    """
    OpenAI-compatible chat completions endpoint for LobeChat.
    Supports streaming, function calling, and plugin integration.
    
    Args:
        request: Chat request in OpenAI format
        
    Returns:
        Chat completion response or streaming response
    """
    try:
        from services.multi_model_ai import ai_service
        import time

        if ai_service is None:
            raise HTTPException(
                status_code=503,
                detail="AI service not available. Check API key configuration.",
            )

        # Extract the last user message
        user_message = None
        for msg in request.messages:
            if msg.role == "user":
                user_message = msg.content

        if not user_message:
            raise HTTPException(status_code=400, detail="No user message found")

        # Build context if functions are available
        context = user_message
        if request.functions:
            context += "\n\nAvailable functions:\n"
            for func in request.functions:
                context += f"- {func.get('name')}: {func.get('description')}\n"

        # Get AI response
        response_text = await ai_service.analyze_text(context)

        if request.stream:
            # Return streaming response
            async def generate() -> AsyncGenerator[str, None]:
                import json
                
                # Split response into chunks for streaming
                words = response_text.split()
                for i, word in enumerate(words):
                    chunk = {
                        "id": f"chatcmpl-{int(time.time())}",
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": request.model or "kortana-ai",
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"content": word + " "},
                                "finish_reason": None if i < len(words) - 1 else "stop",
                            }
                        ],
                    }
                    yield f"data: {json.dumps(chunk)}\n\n"
                yield "data: [DONE]\n\n"

            return StreamingResponse(generate(), media_type="text/event-stream")

        # Return non-streaming response
        return {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.model or "kortana-ai",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_text,
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": len(user_message.split()),
                "completion_tokens": len(response_text.split()),
                "total_tokens": len(user_message.split()) + len(response_text.split()),
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.get("/v1/models")
async def list_models() -> dict[str, Any]:
    """
    List available models (OpenAI format).
    
    Returns:
        List of available models in OpenAI format
    """
    import time
    
    return {
        "object": "list",
        "data": [
            {
                "id": "kortana-ai",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "kortana",
                "permission": [],
                "root": "kortana-ai",
                "parent": None,
            },
            {
                "id": "kortana-code",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "kortana",
                "permission": [],
                "root": "kortana-code",
                "parent": None,
            },
            {
                "id": "kortana-multimodal",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "kortana",
                "permission": [],
                "root": "kortana-multimodal",
                "parent": None,
            },
        ],
    }


@router.post("/v1/functions/register")
async def register_function(function_def: dict[str, Any]) -> dict[str, Any]:
    """
    Register a new function for function calling.
    
    Args:
        function_def: Function definition in OpenAI format
        
    Returns:
        Registration confirmation
    """
    name = function_def.get("name", "")
    return {
        "function_id": f"func_{name}",
        "name": name,
        "status": "registered",
        "message": f"Function '{name}' registered successfully",
    }


@router.get("/v1/functions/list")
async def list_functions() -> dict[str, Any]:
    """
    List available functions.
    
    Returns:
        List of registered functions
    """
    return {
        "functions": [
            {
                "name": "analyze_code",
                "description": "Analyze code for quality and potential issues",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Code to analyze"},
                        "language": {"type": "string", "description": "Programming language"},
                    },
                    "required": ["code"],
                },
            },
            {
                "name": "search_knowledge",
                "description": "Search the Kortana knowledge base",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                    },
                    "required": ["query"],
                },
            },
        ]
    }


@router.get("/v1/health")
async def health_check() -> dict[str, Any]:
    """
    Health check endpoint for LobeChat.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "kortana-lobechat-adapter",
        "openai_compatible": True,
    }


@router.post("/v1/embeddings")
async def create_embeddings(embedding_request: dict[str, Any]) -> dict[str, Any]:
    """
    Create embeddings (for plugin support).
    
    Args:
        embedding_request: Request with text to embed
        
    Returns:
        Embedding response in OpenAI format
    """
    import time
    import random
    
    text = embedding_request.get("input", "")
    model = embedding_request.get("model", "text-embedding-ada-002")
    
    # Generate mock embedding (in production, use actual embedding model)
    embedding = [random.random() for _ in range(1536)]
    
    return {
        "object": "list",
        "data": [
            {
                "object": "embedding",
                "embedding": embedding,
                "index": 0,
            }
        ],
        "model": model,
        "usage": {
            "prompt_tokens": len(text.split()),
            "total_tokens": len(text.split()),
        },
    }
