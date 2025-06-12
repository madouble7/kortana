"""
FastAPI server for Kor'tana chat interface and API endpoints.
"""

import json
import logging
import os
import sys
from datetime import datetime

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

from .brain import ChatEngine

# Configure basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Ensure src is in sys.path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI()

# Allow CORS for local dev/testing and LobeChat
origins = ["http://localhost", "http://localhost:3000", "*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singleton ChatEngine instance (for demo; in prod, use session/user
# management)
engine = ChatEngine()


class MessageRequest(BaseModel):
    """Model for incoming chat messages.

    Attributes:
        message (str): The message content from the user.
        manual_mode (Optional[str]): Optional manual mode for processing.
    """

    message: str
    manual_mode: str | None = None


class MessageResponse(BaseModel):
    """Model for outgoing chat responses.

    Attributes:
        response (str): The response content from the assistant.
        mode (str): The mode used for generating the response.
    """

    response: str
    mode: str


class CsrfSettings(BaseSettings):
    """Settings for CSRF protection.

    Attributes:
        secret_key (str): The secret key used for CSRF protection.
    """

    secret_key: str = os.getenv("CSRF_SECRET_KEY", "supersecret")


@CsrfProtect.load_config
def get_csrf_config() -> CsrfSettings:
    """Load CSRF configuration settings.

    Returns:
        CsrfSettings: The CSRF settings object.
    """
    return CsrfSettings()


@app.post("/chat", response_model=MessageResponse)
async def chat_endpoint(
    request: Request, csrf_protect: CsrfProtect = Depends()
) -> MessageResponse:
    """Endpoint for processing chat messages.

    Args:
        request (Request): The incoming HTTP request.
        csrf_protect (CsrfProtect): CSRF protection dependency.

    Returns:
        MessageResponse: The response model containing the assistant's reply and mode.
    """
    await csrf_protect.validate_csrf(request)
    try:
        request_body_bytes = await request.body()
        logger.info(f"Received request to /chat. Headers: {dict(request.headers)}")
        logger.info(f"Raw request body: {request_body_bytes.decode()}")
        payload = await request.json()
        logger.info(f"Parsed payload: {json.dumps(payload, indent=2)}")
        # Validate payload against the MessageRequest model
        message_request = MessageRequest(**payload)
        user_input = bleach.clean(message_request.message)
        response = engine.get_response(
            user_input, manual_mode=message_request.manual_mode
        )
        logger.info(f"Kor'tana's brain generated response: '{response}'")
        return MessageResponse(response=response, mode=engine.current_mode)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error processing message in Kor'tana's brain: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail=f"Internal server error in Kor'tana: {str(e)}"
        ) from e


# Alias for LobeChat or alternate frontend
@app.post("/kortana-chat")
async def kortana_chat_alias(request: Request, csrf_protect: CsrfProtect = Depends()):
    """Alias endpoint for processing chat messages.

    Args:
        request (Request): The incoming HTTP request.
        csrf_protect (CsrfProtect): CSRF protection dependency.

    Returns:
        dict: The response payload containing the assistant's reply and mode.
    """
    await csrf_protect.validate_csrf(request)
    try:
        request_body_bytes = await request.body()
        logger.info(
            f"Received request to /kortana-chat. Headers: {dict(request.headers)}"
        )
        logger.info(f"Raw request body: {request_body_bytes.decode()}")
        payload = await request.json()
        logger.info(f"Parsed payload: {json.dumps(payload, indent=2)}")
        user_input = bleach.clean(payload.get("message", ""))
        manual_mode = payload.get("manual_mode")
        if not user_input:
            logger.warning("Missing 'message' in payload")
            raise HTTPException(
                status_code=400, detail="Payload must include a 'message' field."
            )
        response = engine.get_response(user_input, manual_mode=manual_mode)
        logger.info(f"Kor'tana's brain generated response: '{response}'")
        response_payload = {"reply": response, "mode": engine.current_mode}
        logger.info(
            f"Sending response payload: {json.dumps(response_payload, indent=2)}"
        )
        return response_payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error processing message in Kor'tana's brain: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail=f"Internal server error in Kor'tana: {str(e)}"
        ) from e


@app.get("/health")
def health_check() -> dict:
    """Health check endpoint.

    Returns:
        dict: A dictionary indicating the server status.
    """
    return {"status": "ok"}


@app.get("/mode")
def get_mode() -> dict:
    """Get the current mode of the chat engine.

    Returns:
        dict: A dictionary containing the current mode.
    """
    return {"mode": engine.current_mode}


@app.post("/mode")
def set_mode(data: dict) -> dict:
    """Set the mode of the chat engine.

    Args:
        data (dict): A dictionary containing the mode to set.

    Returns:
        dict: A dictionary indicating the status and current mode.
    """
    mode = data.get("mode")
    if mode:
        engine.set_mode(mode)
        return {"mode": engine.current_mode, "status": "ok"}
    return {"error": "No mode provided"}


@app.post("/v1/chat/completions")
async def openai_compatible_chat(request: Request) -> dict:
    """OpenAI-compatible chat endpoint.

    Args:
        request (Request): The incoming HTTP request.

    Returns:
        dict: A dictionary containing the chat completion response.
    """
    data = await request.json()
    messages = data.get("messages", [])
    user_message = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            user_message = msg.get("content", "")
            break
    user_input = bleach.clean(user_message)
    response = engine.get_response(user_input)
    return {
        "id": "chatcmpl-kortana",
        "object": "chat.completion",
        "created": int(datetime.now().timestamp()),
        "model": engine.default_model_id,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": response},
                "finish_reason": "stop",
            }
        ],
        "usage": {},
    }


@app.get("/chat")
async def chat_sse(topic: str) -> EventSourceResponse:
    """Basic SSE stub for LobeChat.

    Args:
        topic (str): The topic ID for the SSE connection.

    Returns:
        EventSourceResponse: The SSE response object.
    """

    async def event_generator():
        # initial handshake
        yield f"event: connected\ndata: topic {topic} opened\n\n"
        # you could integrate streaming here:
        # resp = engine.get_response("…")
        # yield f"event: message\ndata: {resp}\n\n"
        # then close stream
        yield "event: end\ndata: \n\n"

    return EventSourceResponse(event_generator())


@app.post("/trigger-ade")
async def trigger_ade() -> JSONResponse:
    """Trigger the ADE cycle.

    Returns:
        JSONResponse: A JSON response indicating the status of the operation.
    """
    try:
        engine._run_daily_planning_cycle()
        return JSONResponse(content={"status": "ADE cycle triggered"}, status_code=200)
    except Exception as e:
        logger.error(f"Error triggering ADE cycle: {e}", exc_info=True)
        return JSONResponse(
            content={"status": "error", "detail": str(e)}, status_code=500
        )


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
    """Login endpoint with rate limiting.

    Args:
        username (str): The username for authentication.
        password (str): The password for authentication.

    Returns:
        JSONResponse: A JSON response indicating the login status.
    """
    # Dummy authentication logic (replace with real logic in production)
    if username == "admin" and password == "secret":
        import uuid

        session_id = str(uuid.uuid4())
        response = JSONResponse(content={"status": "success"})
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=True,
            max_age=60 * 60 * 24,  # 1 day
            samesite="lax",
        )
        return response
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication.

    Args:
        websocket (WebSocket): The WebSocket connection object.
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
            except Exception:
                msg = {"content": data}
            # Heartbeat
            if msg.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
                continue
            # Message acknowledgment
            if "id" in msg:
                await websocket.send_text(json.dumps({"ack": msg["id"]}))
            # ... handle other message types as needed ...
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        await websocket.close()


if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=7777, reload=True)
