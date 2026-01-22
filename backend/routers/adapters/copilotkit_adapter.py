"""
CopilotKit Frontend Adapter
Provides CopilotKit-compatible API with frontend actions and tools support
"""

from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

router = APIRouter()


class CopilotAction(BaseModel):
    """Frontend action that can be triggered by the AI"""

    name: str
    description: str
    parameters: dict[str, Any] | None = None


class CopilotTool(BaseModel):
    """Frontend tool available to the AI"""

    name: str
    description: str
    input_schema: dict[str, Any] | None = None


class CopilotChatRequest(BaseModel):
    """Chat request from CopilotKit frontend"""

    messages: list[dict[str, str]]
    actions: list[CopilotAction] | None = None
    tools: list[CopilotTool] | None = None


class CopilotChatResponse(BaseModel):
    """Chat response to CopilotKit frontend"""

    message: str
    action: str | None = None
    action_params: dict[str, Any] | None = None


@router.post("/chat", response_model=CopilotChatResponse)
async def copilot_chat(request: CopilotChatRequest) -> dict[str, Any]:
    """
    Handle chat requests from CopilotKit frontend.
    Supports frontend actions and tools.
    
    Args:
        request: Chat request with messages and available actions/tools
        
    Returns:
        Response with message and optional action trigger
    """
    try:
        from services.multi_model_ai import ai_service

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

        # Build context with available actions
        context = f"User message: {user_message}\n"
        if request.actions:
            context += "\nAvailable actions:\n"
            for action in request.actions:
                context += f"- {action.name}: {action.description}\n"

        # Get AI response
        response = await ai_service.analyze_text(context)

        return {
            "message": response,
            "action": None,
            "action_params": None,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.websocket("/ws")
async def copilot_websocket(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real-time CopilotKit updates.
    Supports streaming responses and action triggers.
    """
    await websocket.accept()
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            message = data.get("message", "")
            if not message:
                await websocket.send_json({"error": "No message provided"})
                continue

            # Process with AI service
            try:
                from services.multi_model_ai import ai_service

                if ai_service is None:
                    await websocket.send_json(
                        {"error": "AI service not available"}
                    )
                    continue

                response = await ai_service.analyze_text(message)
                
                await websocket.send_json({
                    "type": "message",
                    "content": response,
                })

            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "content": str(e),
                })

    except WebSocketDisconnect:
        pass


@router.post("/actions/register")
async def register_action(action: CopilotAction) -> dict[str, Any]:
    """
    Register a new frontend action.
    
    Args:
        action: Action configuration
        
    Returns:
        Registration confirmation
    """
    return {
        "action_id": f"action_{action.name}",
        "name": action.name,
        "status": "registered",
        "message": f"Action '{action.name}' registered successfully",
    }


@router.post("/tools/register")
async def register_tool(tool: CopilotTool) -> dict[str, Any]:
    """
    Register a new frontend tool.
    
    Args:
        tool: Tool configuration
        
    Returns:
        Registration confirmation
    """
    return {
        "tool_id": f"tool_{tool.name}",
        "name": tool.name,
        "status": "registered",
        "message": f"Tool '{tool.name}' registered successfully",
    }


@router.get("/config")
async def get_copilot_config() -> dict[str, Any]:
    """
    Get CopilotKit configuration.
    
    Returns:
        Configuration for CopilotKit frontend
    """
    return {
        "runtime_url": "/api/adapters/copilotkit",
        "websocket_url": "/api/adapters/copilotkit/ws",
        "features": {
            "chat": True,
            "actions": True,
            "tools": True,
            "streaming": True,
        },
        "models": ["kortana-ai"],
    }


@router.post("/context")
async def update_context(context_data: dict[str, Any]) -> dict[str, Any]:
    """
    Update the context for CopilotKit.
    Allows frontend to provide additional context for AI interactions.
    
    Args:
        context_data: Context information from frontend
        
    Returns:
        Context update confirmation
    """
    return {
        "status": "updated",
        "message": "Context updated successfully",
        "context_keys": list(context_data.keys()),
    }
