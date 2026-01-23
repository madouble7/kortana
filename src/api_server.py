"""
FastAPI server for Kor'tana chat interface and API endpoints.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime # Added datetime
from typing import Optional # Added Optional

import bleach
import uvicorn
from fastapi import Depends, FastAPI, Form, HTTPException, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_csrf_protect import CsrfProtect
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sse_starlette.sse import EventSourceResponse

# Updated ChatEngine import
from src.kortana.core.brain import ChatEngine

# Imports for the new ChatEngine dependencies
from kortana.services.llm_service import LLMService
from kortana.memory.memory_manager import MemoryManager


# Configure basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Ensure src is in sys.path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI()

# Allow CORS for local dev/testing and LobeChat
origins = ["http://localhost", "http://localhost:3000", "*"] # Keep existing origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REMOVED old global ChatEngine instance:
# # Singleton ChatEngine instance (for demo; in prod, use session/user
# # management)
# engine = ChatEngine()


class MessageRequest(BaseModel):
    message: str
    manual_mode: Optional[str] = None
    user_id: Optional[str] = "default" # Added user_id, made it optional with default

class MessageResponse(BaseModel):
    response: str
    # mode: Optional[str] = None # Mode is not explicitly returned by new ChatEngine's process_message
    timestamp: str # Timestamp is now part of the response


class CsrfSettings(BaseSettings):
    secret_key: str = "your_secret_key" # Replace with a secure key

@CsrfProtect.load_config
def get_csrf_config() -> CsrfSettings:
    return CsrfSettings()

# NEW helper function to get the enhanced ChatEngine
def get_enhanced_chat_engine() -> ChatEngine:
    """Get ChatEngine with autonomous awareness capabilities."""
    # These services need to be correctly imported and instantiated
    # Assuming LLMService and MemoryManager can be instantiated without arguments
    # or that their configuration is handled internally/globally.
    # Adjust instantiation if they require specific configurations or a shared context.
    llm_service = LLMService()
    memory_manager = MemoryManager()
    return ChatEngine(llm_service, memory_manager)

# UPDATED chat endpoint
@app.post("/chat", response_model=MessageResponse)
async def chat_endpoint(
    request_data: MessageRequest, csrf_protect: CsrfProtect = Depends() # Changed to use MessageRequest directly
) -> MessageResponse:
    """Enhanced chat endpoint with autonomous awareness."""
    await csrf_protect.validate_csrf_for_json(request_data.model_dump()) # Adjusted CSRF for JSON payload
    try:
        chat_engine = get_enhanced_chat_engine()

        # Sanitize user message if necessary (bleach was used before)
        user_message = bleach.clean(request_data.message)

        response_text = await chat_engine.process_message(
            message=user_message,
            user_id=request_data.user_id or "default" # Ensure user_id is passed
        )

        logger.info(f"Kor'tana's brain generated response: '{response_text}'")
        return MessageResponse(
            response=response_text,
            timestamp=datetime.now().isoformat()
        )

    except HTTPException: # Re-raise HTTPExceptions directly
        raise
    except Exception as e:
        logger.error(
            f"Error processing message in Kor'tana's brain: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail=f"Internal server error in Kor'tana: {str(e)}"
        ) from e

# Alias for LobeChat or alternate frontend - THIS MIGHT ALSO NEED UPDATING
# For now, focusing on the main /chat endpoint.
# If kortana_chat_alias uses the old `engine` instance, it will fail or use outdated logic.
@app.post("/kortana-chat")
async def kortana_chat_alias(request: Request, csrf_protect: CsrfProtect = Depends()):
    await csrf_protect.validate_csrf(request)
    try:
        payload = await request.json()
        message_request = MessageRequest(**payload)
        user_input = bleach.clean(message_request.message)

        # This alias should also use the new engine
        chat_engine = get_enhanced_chat_engine()
        response = await chat_engine.process_message(
            message=user_input,
            user_id=message_request.user_id or "default"
        )

        logger.info(f"Kor'tana's brain generated response for alias: '{response}'")
        # Adjust response payload as needed, new ChatEngine doesn't directly return mode
        response_payload = {"reply": response, "timestamp": datetime.now().isoformat()}
        logger.info(
            f"Sending response payload for alias: {json.dumps(response_payload, indent=2)}"
        )
        return response_payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error processing message in Kor'tana's brain (alias): {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail=f"Internal server error in Kor'tana (alias): {str(e)}"
        ) from e

# ... (rest of the file remains the same, including /health, /mode, /v1/chat/completions etc.)
# Note: /v1/chat/completions and other endpoints might also need review if they
# relied on the old ChatEngine or its specific behaviors.

@app.get("/health")
def health_check() -> dict:
    return {"status": "Kor'tana is awake and responsive"}

@app.get("/mode")
def get_mode_api() -> dict: # Renamed to avoid conflict if 'get_mode' is used elsewhere
    # This needs to be re-evaluated as 'mode' is not directly part of the new ChatEngine response
    # For now, returning a placeholder or a general status
    return {"current_mode": "autonomous_unified", "status": "Enhanced ChatEngine active"}

@app.post("/mode")
def set_mode_api(data: dict) -> dict: # Renamed to avoid conflict
    # Mode setting logic needs to be re-evaluated with the new ChatEngine
    # The new ChatEngine doesn't have an explicit set_mode method in the provided snippet
    logger.warning("set_mode API called, but mode management has changed with new ChatEngine.")
    return {"status": "Mode management updated", "requested_mode_change": data.get("mode")}


@app.post("/v1/chat/completions")
async def openai_compatible_chat(request: Request) -> JSONResponse: # Changed to JSONResponse
    # This endpoint likely needs significant rework to use the new ChatEngine
    # or a dedicated adapter. For now, logging a warning.
    logger.warning("OpenAI compatible chat endpoint (/v1/chat/completions) called. Needs review for new ChatEngine.")
    try:
        payload = await request.json()
        # Simplified: assuming the first message content is the user input
        user_message_content = "No message found"
        if payload.get("messages") and isinstance(payload["messages"], list) and len(payload["messages"]) > 0:
            user_message_content = payload["messages"][-1].get("content", "No content in last message")

        chat_engine = get_enhanced_chat_engine()
        # user_id might come from headers or a token in a real scenario
        response_text = await chat_engine.process_message(message=user_message_content, user_id="openai_adapter_user")

        # Construct an OpenAI-like response
        # This is a simplified example and might not be fully compliant
        return JSONResponse(content={
            "id": f"chatcmpl-{os.urandom(12).hex()}",
            "object": "chat.completion",
            "created": int(datetime.now().timestamp()),
            "model": "kortana_unified_engine",
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": response_text},
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0} # Placeholder usage
        })
    except Exception as e:
        logger.error(f"Error in OpenAI compatible chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error in OpenAI adapter: {str(e)}")


@app.get("/chat") # This is an SSE endpoint, different from the POST /chat
async def chat_sse(topic: str) -> EventSourceResponse:
    # This SSE endpoint would need its own logic, potentially also using ChatEngine
    # but in a streaming fashion if supported, or for different event types.
    # For now, it's not directly modified by the ChatEngine changes for POST /chat.
    logger.warning("SSE /chat endpoint called. Not directly modified by new POST /chat ChatEngine.")
    async def event_generator():
        # Placeholder SSE logic
        yield {"event": "message", "data": json.dumps({"topic": topic, "message": "SSE connection established"})}
        await asyncio.sleep(1) # Requires asyncio import
        yield {"event": "message", "data": json.dumps({"topic": topic, "message": "Still connected..."})}
    return EventSourceResponse(event_generator())


@app.post("/trigger-ade")
async def trigger_ade() -> JSONResponse:
    logger.info("ADE trigger endpoint called.")
    # ADE (Autonomous Development Engine) logic would go here.
    # This might involve creating specific goals for the ChatEngine to pick up.
    return JSONResponse(content={"message": "ADE cycle triggered (simulated)"}, status_code=200)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    lambda request, exc: JSONResponse(
        status_code=429, content={"detail": "Rate limit exceeded"}
    ),
)


@app.post("/login")
@limiter.limit("5/minute")
async def login(username: str = Form(...), password: str = Form(...)) -> JSONResponse:
    # Placeholder login logic
    if username == "admin" and password == "password": # Never use hardcoded credentials in production
        return JSONResponse(content={"message": "Login successful"}, status_code=200)
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        # Echoing back for now, or integrate with ChatEngine
        await websocket.send_text(f"Message text was: {data}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 7777)))
