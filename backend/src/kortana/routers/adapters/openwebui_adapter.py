"""
Open WebUI Adapter with MCP Protocol Support
Provides Open WebUI compatible endpoints with Model Context Protocol integration
"""

from typing import Any, AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()


class MCPTool(BaseModel):
    """MCP tool definition"""

    name: str
    description: str
    input_schema: dict[str, Any]


class OpenWebUIChatRequest(BaseModel):
    """Chat request from Open WebUI"""

    model: str
    messages: list[dict[str, str]]
    stream: bool = False
    tools: list[MCPTool] | None = None


class OpenWebUIChatResponse(BaseModel):
    """Chat response for Open WebUI"""

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[dict[str, Any]]


@router.post("/chat/completions", response_model=None)
async def chat_completions(
    request: OpenWebUIChatRequest,
) -> StreamingResponse | dict[str, Any]:
    """
    OpenAI-compatible chat completions endpoint for Open WebUI.
    Supports streaming and MCP tool integration.

    Args:
        request: Chat request with messages and optional tools

    Returns:
        Chat completion response or streaming response
    """
    try:
        import time

        from src.kortana.services.multi_model_ai import ai_service

        if ai_service is None:
            raise HTTPException(
                status_code=503,
                detail="AI service not available. Check API key configuration.",
            )

        # Extract the last user message
        user_message = None
        for msg in reversed(request.messages):
            if msg.get("role") == "user":
                user_message = msg.get("content")
                break

        if not user_message:
            raise HTTPException(status_code=400, detail="No user message found")

        # Get AI response
        response_text = await ai_service.analyze_text(user_message)

        if request.stream:
            # Return streaming response
            async def generate() -> AsyncGenerator[str, None]:
                # Split response into chunks for streaming
                words = response_text.split()
                for i, word in enumerate(words):
                    chunk = {
                        "id": f"chatcmpl-{int(time.time())}",
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": request.model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"content": word + " "},
                                "finish_reason": None if i < len(words) - 1 else "stop",
                            }
                        ],
                    }
                    yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"

            return StreamingResponse(generate(), media_type="text/event-stream")

        # Return non-streaming response
        return {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.model,
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
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.get("/models")
async def list_models() -> dict[str, Any]:
    """
    List available models (Open WebUI compatible).

    Returns:
        List of available models
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
            },
            {
                "id": "kortana-multimodal",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "kortana",
            },
        ],
    }


@router.post("/mcp/tools/register")
async def register_mcp_tool(tool: MCPTool) -> dict[str, Any]:
    """
    Register a new MCP tool.

    Args:
        tool: MCP tool definition

    Returns:
        Registration confirmation
    """
    return {
        "tool_id": f"mcp_tool_{tool.name}",
        "name": tool.name,
        "status": "registered",
        "protocol": "mcp",
    }


@router.get("/mcp/tools/list")
async def list_mcp_tools() -> dict[str, Any]:
    """
    List available MCP tools.

    Returns:
        List of MCP tools
    """
    return {
        "tools": [
            {
                "name": "code_analysis",
                "description": "Analyze code for quality and issues",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string"},
                        "language": {"type": "string"},
                    },
                },
            },
            {
                "name": "memory_search",
                "description": "Search the knowledge base",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                    },
                },
            },
        ]
    }


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """
    Health check endpoint for Open WebUI.

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "kortana-openwebui-adapter",
        "mcp_enabled": True,
    }
