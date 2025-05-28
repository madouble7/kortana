import logging
import json
from fastapi import FastAPI, HTTPException, Request, Depends, Form, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
import os
import sys
from datetime import datetime
from sse_starlette.sse import EventSourceResponse
from fastapi.responses import JSONResponse
import bleach
from fastapi_csrf_protect import CsrfProtect
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure src is in sys.path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from .brain import ChatEngine

app = FastAPI()

# Allow CORS for local dev/testing and LobeChat
origins = [
    "http://localhost",
    "http://localhost:3000",
    "*"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singleton ChatEngine instance (for demo; in prod, use session/user management)
engine = ChatEngine()

class MessageRequest(BaseModel):
    message: str
    manual_mode: Optional[str] = None

class MessageResponse(BaseModel):
    response: str
    mode: str

class CsrfSettings:
    secret_key: str = os.getenv("CSRF_SECRET_KEY", "supersecret")

@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()

@app.post("/chat", response_model=MessageResponse)
async def chat_endpoint(request: Request, csrf_protect: CsrfProtect = Depends()):
    csrf_protect.validate_csrf_in_cookies(request)
    try:
        request_body_bytes = await request.body()
        logger.info(f"Received request to /chat. Headers: {dict(request.headers)}")
        logger.info(f"Raw request body: {request_body_bytes.decode()}")
        logger.info(f"Parsed payload: {req.json()}")
        user_input = bleach.clean(req.message)
        response = engine.get_response(user_input, manual_mode=req.manual_mode)
        logger.info(f"Kor'tana's brain generated response: '{response}'")
        return MessageResponse(response=response, mode=engine.current_mode)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing message in Kor'tana's brain: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error in Kor'tana: {str(e)}")

# Alias for LobeChat or alternate frontend
@app.post("/kortana-chat")
async def kortana_chat_alias(request: Request, csrf_protect: CsrfProtect = Depends()):
    csrf_protect.validate_csrf_in_cookies(request)
    try:
        request_body_bytes = await request.body()
        logger.info(f"Received request to /kortana-chat. Headers: {dict(request.headers)}")
        logger.info(f"Raw request body: {request_body_bytes.decode()}")
        payload = await request.json()
        logger.info(f"Parsed payload: {json.dumps(payload, indent=2)}")
        user_input = bleach.clean(payload.get("message", ""))
        manual_mode = payload.get("manual_mode")
        if not user_input:
            logger.warning("Missing 'message' in payload")
            raise HTTPException(status_code=400, detail="Payload must include a 'message' field.")
        response = engine.get_response(user_input, manual_mode=manual_mode)
        logger.info(f"Kor'tana's brain generated response: '{response}'")
        response_payload = {"reply": response, "mode": engine.current_mode}
        logger.info(f"Sending response payload: {json.dumps(response_payload, indent=2)}")
        return response_payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing message in Kor'tana's brain: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error in Kor'tana: {str(e)}")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/mode")
def get_mode():
    return {"mode": engine.current_mode}

@app.post("/mode")
def set_mode(data: dict):
    mode = data.get("mode")
    if mode:
        engine.set_mode(mode)
        return {"mode": engine.current_mode, "status": "ok"}
    return {"error": "No mode provided"}

@app.post("/v1/chat/completions")
async def openai_compatible_chat(request: Request):
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
                "message": {
                    "role": "assistant",
                    "content": response
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {}
    }

@app.get("/chat")
async def chat_sse(topic: str):
    """
    Basic SSE stub for LobeChat.
    Listens for GET /chat?topic=<id> and streams back events.
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
async def trigger_ade():
    try:
        engine._run_daily_planning_cycle()
        return JSONResponse(content={"status": "ADE cycle triggered"}, status_code=200)
    except Exception as e:
        logger.error(f"Error triggering ADE cycle: {e}", exc_info=True)
        return JSONResponse(content={"status": "error", "detail": str(e)}, status_code=500)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda request, exc: JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"}))

@app.post("/login")
@limiter.limit("5/minute")
async def login(username: str = Form(...), password: str = Form(...)):
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
            max_age=60*60*24,  # 1 day
            samesite="lax"
        )
        return response
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
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
