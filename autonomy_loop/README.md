**note**: for project coordination and agent handover protocols, please see the [senior admin agent guide](./ADMIN_AGENT.md).

# kor'tana builder pack (v2)

the exhaustive guide to building, running, and testing your own local kor'tana server.

## what's new in v2

this builder pack adds major features to make your local server a high-fidelity development environment.

• streaming api: a new `/chat-text-stream` endpoint delivers real-time, token-by-token responses for a modern chat experience.
• day capture backend: full local implementation of the day capture feature, including session management, audio chunk uploads, and rolling snapshots.
• improved api mimicry: the local server's upload endpoint now perfectly mimics the behavior of a cloud presigned URL, allowing the frontend to work without changes.
• security & ops: adds rate limiting, pii redaction, and prometheus metrics for observability.

## core persona (system rules)

you are kor’tana.

style:

- always respond in all lowercase.
- be concise by default; friendly, direct, and helpful.
- avoid purple prose; use plain language.

audio policy:

- if the user sends audio, immediately transcribe it, summarize it, and respond accordingly based on the transcription. include key points and action items.

interaction policy:

- do not defer or promise background work. always deliver whatever you can in the current response.
- if a task is complex and you lack inputs, make your best effort with what you have rather than asking for confirmation.
- if a request is unsafe or disallowed, refuse with a brief reason and, if possible, safer alternatives.

reasoning:

- think carefully, but keep internal reasoning hidden; only share final results unless the user explicitly requests an explanation.
- for arithmetic: compute step-by-step to avoid mistakes.

memory:

- keep a short rolling memory of recent turns (configurable). summarize aggressively beyond the window.

formatting:

- use simple markdown headings when helpful.
- do not over-list unless the user asks for lists or the content truly benefits from it.

compliance:

- never claim you performed future work. never ask the user to wait for you to do work later.

## architecture at a glance (v2)

gateway api (fastapi): /chat-text, /chat-audio, /chat-text-stream, /session/*, /upload

adapters:
• llm_adapter: gemini (google ai studio) with streaming, optional ollama local
• asr_adapter: local faster-whisper (primary), optional remote (placeholder)
• memory: bounded rolling buffer + auto-summarization
• day capture: in-memory session manager for local dev
• rag (optional): chroma vector store + embedding adapter
• ops: logging, redaction, rate limiting, health, metrics
• packaging: docker + compose; pytest + eval scenarios

## project tree

### Project structure
```bash
kortana/
  .env.example
  requirements.txt
  docker-compose.yml
  Dockerfile
  README.md
  openapi.yaml
  app/
    __init__.py
    main.py
    router.py
    middleware.py   # new
    persona.txt
    memory.py
    summarize.py
    day_capture.py
    adapters/
      __init__.py
      llm_gemini.py
      llm_ollama.py
      asr_faster_whisper.py
    rag/
      __init__.py
      embed.py
      store.py
      retrieve.py
    utils/
      audio.py
      redact.py
      logging.py
  tests/
    test_security.py # new
    # ...
  cli.py
```

## environment & config

### .env.example
```bash
# llm
GOOGLE_API_KEY=replace_me
KORTANA_MODEL_ID=gemini-2.5-flash   # fast and capable
# optional local llm
OLLAMA_MODEL=llama3.1:8b
OLLAMA_HOST=http://localhost:11434

# asr
ASR_MODEL_SIZE=small              # tiny/base/small/medium
ASR_COMPUTE_TYPE=int8             # int8/float16
ASR_LANGUAGE=                     # optional; e.g., en

# server
HOST=0.0.0.0
PORT=8000
MAX_MEMORY_TURNS=8
MAX_UPLOAD_MB=50
RATE_LIMIT_RPS=5

# rag (optional)
RAG_ENABLED=false
RAG_DB_PATH=./data/chroma
RAG_TOP_K=4

# logging
LOG_LEVEL=info
REDACT_PII=true

# v1.1+ feature flags
SSE_ENABLED=true                  # enable server-sent events for streaming
GPU_ASR_ENABLED=false             # enable async s3/sqs offload for audio
EFS_ENABLED=false                 # for shared rag storage in prod
USE_AWS_SECRETS=false             # load secrets from aws secrets manager
```

### requirements.txt
```text
fastapi
uvicorn[standard]
pydantic>=2
python-dotenv
python-multipart
google-generativeai
httpx
faster-whisper
soundfile
numpy
pydub
chromadb
scikit-learn
pytest
pytest-asyncio
aiofiles
prometheus-client
```

## openapi (contract) v2

the v2 openapi spec including streaming and day capture endpoints.

### openapi.yaml
```yaml
openapi: 3.0.3
info:
  title: kortana api
  version: "2.0.0"
paths:
  /chat-text:
    post:
      summary: text chat (non-streaming)
      requestBody:
        # ... (same as v1)
  /chat-text-stream:
    post:
      summary: text chat (streaming)
      requestBody:
        required: true
        content:
          application/x-www-form-urlencoded:
            schema:
              type: object
              properties:
                message: { type: string }
      responses:
        "200":
          description: ok (server-sent event stream)
          content:
            text/event-stream:
              schema:
                type: string
  /chat-audio:
    post:
      summary: audio chat (auto transcribe + respond)
      requestBody:
        # ... (same as v1)
  # new in v1.1
  /chat-audio-async:
    post:
      summary: audio chat (async job)
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                file: { type: string, format: binary }
      responses:
        "202":
          description: accepted
          content:
            application/json:
              schema:
                type: object
                properties:
                  job_id: { type: string }
  /jobs/{job_id}:
    get:
      summary: get job status and result
      parameters:
        - name: job_id
          in: path
          required: true
          schema: { type: string }
      responses:
        "200":
          description: ok
          content:
            application/json:
              schema:
                type: object
                properties:
                  status: { type: string, enum: [pending, completed, failed] }
                  result:
                    type: object
                    properties:
                      transcript: { type: string }
                      summary: { type: string }
                      reply: { type: string }
        "404":
          description: job not found
  /session/start:
    post:
      summary: start a new day capture session
      responses:
        "200":
          description: ok
          content:
            application/json:
              schema:
                type: object
                properties:
                  session_id: { type: string }
                  presign: { type: object }
  /upload:
    post:
      summary: upload an audio chunk (local dev only)
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                session_id: { type: string }
                key: { type: string }
                file:
                  type: string
                  format: binary
      responses:
        "204":
          description: upload successful
  /session/ingest:
    post:
      summary: ingest processed audio chunk keys
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                session_id: { type: string }
                chunks:
                  type: array
                  items: { type: string }
      responses:
        "200":
          description: ok
          content:
            application/json:
              schema:
                type: object
                properties:
                  accepted: { type: integer }
  /session/{session_id}/snapshot:
    get:
      summary: get the latest snapshot for a session
      parameters:
        - name: session_id
          in: path
          required: true
          schema: { type: string }
      responses:
        "200":
          description: ok
          content:
            application/json:
              schema:
                type: object # see Snapshot model in day_capture.py
  /health:
    get:
      summary: health check for server status
      tags: ["ops"]
      responses:
        "200":
          description: ok
          content:
            application/json:
              schema:
                type: object
                properties:
                  status: { type: string }
                  backend: { type: string }
```

## server code (fastapi)

the core python files for the fastapi server.

### app/main.py
```python
import os
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from .middleware import MetricsAndRateLimitMiddleware

load_dotenv()

app = FastAPI(title="kor’tana")

# Middleware ordering is important. Add custom middleware first.
app.add_middleware(MetricsAndRateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# pick llm backend
BACKEND = os.getenv("BACKEND", "gemini")  # gemini|ollama
if BACKEND == "ollama":
    from .adapters.llm_ollama import complete as llm_complete
else:
    from .adapters.llm_gemini import complete as llm_complete

from .router import router
from .rag.router import router as rag_router # new
app.include_router(router)
app.include_router(rag_router, prefix="/rag", tags=["rag"]) # new

# Expose /metrics for Prometheus
@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

### app/day_capture.py (new)
```python
import uuid, asyncio
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import List, Dict, Literal

# In-memory store for sessions (for local dev)
SESSIONS: Dict[str, 'Session'] = {}

class Snapshot(BaseModel):
    session_id: str
    updated_at: str
    last_chunk_ts: str
    summary: str
    words: int
    actions: List[str]
    diarization: Literal['on', 'off'] = 'off'
    pii_redaction: bool = True

class Session:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now(timezone.utc)
        self.chunks: List[str] = []
        self.snapshot = Snapshot(
            session_id=session_id,
            updated_at=self.created_at.isoformat(),
            last_chunk_ts=self.created_at.isoformat(),
            summary="session started.",
            words=0,
            actions=[],
        )

    async def add_chunk(self, key: str):
        # In a real app, this would trigger a background job.
        # Here, we'll simulate processing.
        self.chunks.append(key)
        self.snapshot.last_chunk_ts = datetime.now(timezone.utc).isoformat()
        await asyncio.sleep(2) # Simulate background processing delay
        new_words = 150 # dummy value
        self.snapshot.words += new_words
        self.snapshot.summary += f"\n- processed chunk '{key[-10:]}', adding {new_words} words."
        if "urgent" in key.lower():
            self.snapshot.actions.append(f"follow up on urgent item in {key[-10:]}")
        self.snapshot.updated_at = datetime.now(timezone.utc).isoformat()

def create_session() -> Session:
    session_id = str(uuid.uuid4())
    session = Session(session_id)
    SESSIONS[session_id] = session
    return session

def get_session(session_id: str) -> Session | None:
    return SESSIONS.get(session_id)
```

### app/router.py
```python
import os, json, asyncio, uuid
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import List
from pathlib import Path
import aiofiles

from .memory import Memory
from .summarize import local_summarize
from .utils.audio import to_wav_bytes
from .utils.redact import redact_text
from .adapters.asr_faster_whisper import transcribe_wav_bytes
from .main import llm_complete
from .day_capture import create_session, get_session # new
from .adapters import code_generator

router = APIRouter()

@router.get("/health", tags=["ops"])
async def health():
    """operational health check."""
    return {"status": "ok", "backend": os.getenv("BACKEND", "gemini")}

memory = Memory()
JOBS = {} # Dummy job store for async ASR (v1.1)
PERSONA = open(os.path.join(os.path.dirname(__file__), "persona.txt"), "r", encoding="utf-8").read()
REDACT_PII_ENABLED = os.getenv("REDACT_PII", "false").lower() == "true"

def stitch_prompt(history, transcript: str | None = None):
    # ... (same as v1)
    parts = [f"system: {PERSONA}"]
    for t in history:
        parts.append(f'{t["role"]}: {t["content"]}')
    if transcript:
        parts.append("system: the last user input was audio; first provide a concise summary, then respond accordingly.")
    return "\\n\\n".join(parts)


@router.post("/chat-text")
async def chat_text(message: str = Form(...), include_rag: bool = Form(False)):
    # ... (same as v1)
    user_message = redact_text(message) if REDACT_PII_ENABLED else message
    memory.add("user", user_message)
    memory.summarize_if_needed(local_summarize)
    prompt = stitch_prompt(memory.as_list())
    out = await llm_complete(prompt)
    out = out.lower().strip()
    memory.add("assistant", out)
    return JSONResponse({"reply": out, "used_rag": bool(include_rag and os.getenv("RAG_ENABLED","false")=="true")})


@router.post("/chat-text-stream")
async def chat_text_stream(message: str = Form(...)):
    user_message = redact_text(message) if REDACT_PII_ENABLED else message
    memory.add("user", user_message)
    memory.summarize_if_needed(local_summarize)
    prompt = stitch_prompt(memory.as_list())
    try:
        from .adapters.llm_gemini import complete_stream
        
        async def stream_generator():
            full_reply = ""
            async for chunk in await complete_stream(prompt):
                full_reply += chunk
                yield f"data: {json.dumps({'text': chunk})}\\n\\n"
            memory.add("assistant", full_reply.strip())
            
        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    except Exception as e:
        print(f"Streaming not supported or failed: {e}")
        out = await llm_complete(prompt)
        out = out.lower().strip()
        memory.add("assistant", out)
        async def fallback_generator():
            yield f"data: {json.dumps({'text': out})}\\n\\n"
        return StreamingResponse(fallback_generator(), media_type="text/event-stream")

@router.post("/chat-audio")
async def chat_audio(file: UploadFile = File(...), language: str = Form(None)):
    # ... (same as v1)
    max_mb = int(os.getenv("MAX_UPLOAD_MB","50"))
    if file.size and file.size > max_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="file too large")
    raw = await file.read()
    wav = to_wav_bytes(raw)
    transcript = transcribe_wav_bytes(wav, language)

    user_message = f"[audio transcript] {transcript}"
    if REDACT_PII_ENABLED:
        user_message = redact_text(user_message)
    
    summary = local_summarize(transcript)
    memory.add("user", user_message)
    memory.summarize_if_needed(local_summarize)
    prompt = stitch_prompt(memory.as_list(), transcript=transcript)
    out = await llm_complete(prompt)
    out = out.lower().strip()
    memory.add("assistant", out)
    return JSONResponse({"transcript": transcript, "summary": summary.lower(), "reply": out})

# --- Web Search ---
class WebSearchRequest(BaseModel):
    query: str

@router.post("/chat-web-search")
async def chat_web_search(req: WebSearchRequest):
    """
    performs a web search using gemini with google search grounding.
    """
    if not req.query:
        raise HTTPException(status_code=400, detail="query cannot be empty")

    try:
        from .adapters.llm_gemini import complete_with_search
        reply, sources = await complete_with_search(req.query)
        
        # ensure sources have titles, fallback to uri if missing
        formatted_sources = [{"uri": s.get("uri", ""), "title": s.get("title", s.get("uri", ""))} for s in sources]

        return {"reply": reply, "sources": formatted_sources}
    except Exception as e:
        print(f"Web search failed: {e}")
        raise HTTPException(status_code=500, detail="failed to perform web search") from e

# --- Code Generation ---
class CodeGenRequest(BaseModel):
    prompt: str

@router.post("/code/generate")
async def code_generate(req: CodeGenRequest):
    """generates a code snippet."""
    if not req.prompt:
        raise HTTPException(status_code=400, detail="prompt cannot be empty")
    
    json_string_response = await code_generator.generate(req.prompt)
    return Response(content=json_string_response, media_type="application/json")

# --- Async ASR Endpoints (v1.1) ---

@router.post("/chat-audio-async")
async def chat_audio_async(file: UploadFile = File(...)):
    if os.getenv("GPU_ASR_ENABLED", "false").lower() != "true":
        raise HTTPException(status_code=501, detail="async asr feature is not enabled")
    
    # In production, this would upload to S3 and push a message to SQS.
    # This stub simulates job creation for local development.
    job_id = str(uuid.uuid4())
    JOBS[job_id] = {"status": "pending", "result": None}
    
    # You would typically not block here. This would be handled by a separate worker.
    # To simulate for now, you could create a background task, but for a simple
    # stub, just returning the job_id is sufficient.
    
    return JSONResponse(status_code=202, content={"job_id": job_id})

@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return JSONResponse(content=job)

# --- Day Capture Endpoints ---
UPLOAD_DIR = Path("./data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class IngestRequest(BaseModel):
    session_id: str
    chunks: List[str]

@router.post("/session/start")
async def session_start(request: Request):
    session = create_session()
    upload_url = str(request.base_url.replace(path="/upload"))
    # The key_template must produce a literal '${filename}' for the client uploader.
    key_template = f"{session.session_id}/" + "\\${filename}"
    return {
        "session_id": session.session_id,
        "presign": {"url": upload_url, "fields": {"session_id": session.session_id, "key": key_template}},
        "bucket": "local", "prefix": session.session_id
    }

@router.post("/upload")
async def upload_chunk(session_id: str = Form(...), key: str = Form(...), file: UploadFile = File(...)):
    if not get_session(session_id):
        raise HTTPException(status_code=404, detail="session not found")
    filepath = UPLOAD_DIR / key
    filepath.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(filepath, 'wb') as f:
        await f.write(await file.read())
    return Response(status_code=204)

@router.post("/session/ingest")
async def session_ingest(req: IngestRequest):
    session = get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    tasks = [session.add_chunk(key) for key in req.chunks]
    await asyncio.gather(*tasks)
    return JSONResponse({"accepted": len(req.chunks)})

@router.get("/session/{session_id}/snapshot")
async def session_snapshot(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    return session.snapshot
```

### app/adapters/llm_gemini.py
```python
import os, google.generativeai as genai
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

MODEL_ID = os.getenv("KORTANA_MODEL_ID", "gemini-2.5-flash")

async def complete(prompt: str) -> str:
    model = genai.GenerativeModel(MODEL_ID)
    resp = await model.generate_content_async(prompt, generation_config={"temperature": 0.3})
    try:
        return (resp.text or "").strip()
    except ValueError:
        return "i am unable to respond to that." # Handle blocked response

async def complete_stream(prompt: str):
    model = genai.GenerativeModel(MODEL_ID)
    stream = await model.generate_content_async(
        prompt,
        generation_config={"temperature": 0.3},
        stream=True
    )
    async for chunk in stream:
        try:
            if chunk.text:
                yield chunk.text
        except ValueError:
            yield "..." # Handle blocked content in stream
```

## Utilities & Middleware

these modules provide core functionality like pii redaction and request handling.

### app/middleware.py (new)
```python
import os
import time
from collections import defaultdict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from prometheus_client import Counter, Histogram

# --- Metrics ---
REQUEST_COUNT = Counter("request_count", "App Request Count", ["method", "endpoint", "http_status"])
REQUEST_LATENCY = Histogram("request_latency_seconds", "Request latency", ["endpoint"])

# --- Rate Limiting (in-memory) ---
RATE_LIMIT_RPS = int(os.getenv("RATE_LIMIT_RPS", "5"))
# Dictionary to store request timestamps for each client IP
request_timestamps = defaultdict(list)

class MetricsAndRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        endpoint = request.url.path
        
        # --- Rate Limiting Logic ---
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        
        # Clean up old timestamps
        request_timestamps[client_ip] = [t for t in request_timestamps[client_ip] if now - t < 1]
        
        if len(request_timestamps[client_ip]) >= RATE_LIMIT_RPS:
            response = Response("Too Many Requests", status_code=429)
            REQUEST_COUNT.labels(method=request.method, endpoint=endpoint, http_status=429).inc()
            return response
            
        request_timestamps[client_ip].append(now)

        # --- Metrics Logic ---
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        REQUEST_LATENCY.labels(endpoint=endpoint).observe(process_time)
        REQUEST_COUNT.labels(method=request.method, endpoint=endpoint, http_status=response.status_code).inc()
        
        return response
```

### app/utils/redact.py (new)
```python
import re

# Simple regex for emails and a common US phone number format
# Note: This is not exhaustive and for demonstration purposes.
REDACTION_PATTERNS = {
    "EMAIL": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"),
    "PHONE": re.compile(r"\b(?:\+?1[ -]?)?\(?\d{3}\)?[ -]?\d{3}[ -]?\d{4}\b"),
}

def redact_text(text: str) -> str:
    """
    Redacts sensitive information (emails, phone numbers) from a string.
    """
    if not text:
        return ""
    
    redacted_text = text
    for pii_type, pattern in REDACTION_PATTERNS.items():
        redacted_text = pattern.sub(f"[{pii_type}_REDACTED]", redacted_text)
        
    return redacted_text
```

## docker & running

### Dockerfile
```dockerfile
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml
```yaml
services:
  kortana:
    build: .
    env_file: .env
    ports:
      - "${PORT-8000}:8000"
    volumes:
      - ./data:/app/data
```

## quick start v2 (copy/paste)

### Setup and Run
```bash
git clone <your repo>
cd kortana
cp .env.example .env
# add GOOGLE_API_KEY in .env
docker compose up --build
```

### Test with cURL
```bash
# test non-streaming
curl -X POST http://localhost:8000/chat-text -F message="hi"

# test streaming
curl -N -X POST http://localhost:8000/chat-text-stream -F message="tell me a very short story"

# test day capture
SESSION_ID=$(curl -s -X POST http://localhost:8000/session/start | jq -r .session_id)
echo "session started: $SESSION_ID"
# (then use frontend to upload a file, and...)
curl http://localhost:8000/session/$SESSION_ID/snapshot
```

## Security & Testing

includes basic tests for security features like pii redaction.

### tests/test_security.py (new)
```python
import pytest
from app.utils.redact import redact_text

@pytest.mark.parametrize("input_text, expected_output", [
    ("my email is test@example.com", "my email is [EMAIL_REDACTED]"),
    ("call me at (123) 456-7890", "call me at [PHONE_REDACTED]"),
    ("mixed info: foo@bar.net and 123-456-7890", "mixed info: [EMAIL_REDACTED] and [PHONE_REDACTED]"),
    ("no pii here", "no pii here"),
    ("email with dots.and-dashes@sub.domain.co.uk", "[EMAIL_REDACTED]"),
])
def test_redaction(input_text, expected_output):
    assert redact_text(input_text) == expected_output

# Note: Testing the rate limit middleware typically requires an integration test setup
# with a TestClient, which is more involved than a simple unit test.
# This file serves as a starting point for security-related unit tests.
```

## GPU ASR Worker Artifacts (v1.1)

For production-grade performance on large audio files, the v1.1 architecture introduces a dedicated ECS service for GPU-accelerated ASR. Here are the key configuration artifacts.

### worker/Dockerfile.gpu
```dockerfile
# syntax=docker/dockerfile:1.6
# GPU-enabled worker image for faster-whisper on CUDA
FROM pytorch/pytorch:2.3.1-cuda12.1-cudnn8-runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    CT2_USE_CUDA=1 \
    TOKENIZERS_PARALLELISM=false \
    WHISPER_COMPUTE_TYPE=float16

WORKDIR /app

# System deps (ffmpeg required by whisper)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Python deps (Torch preinstalled in base image)
RUN pip install --no-cache-dir \
    'faster-whisper>=1.0.1' \
    'boto3>=1.34,<2' \
    'uvloop>=0.19' \
    'prometheus-client>=0.20'

# Copy repo (assumes build context is repo root)
COPY . /app

# Non-root user
RUN useradd -m -u 10001 appuser && chown -R appuser:appuser /app
USER appuser

# Optional healthcheck (replace with real /health if added to worker)
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python - <<'PY'\
import sys; sys.exit(0)
PY
```

### Build Example
```bash
docker build -f worker/Dockerfile.gpu -t $ECR/worker:gpu-v1.1 .
```

### ECS Task Definition (GPU EC2) – ecs/asr-worker-gpu-task.json
```json
{
  "family": "asr-worker-gpu-v1-1",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["EC2"],
  "cpu": "1024",
  "memory": "4096",
  "taskRoleArn": "arn:aws:iam::<account-id>:role/asr-worker-task",
  "executionRoleArn": "arn:aws:iam::<account-id>:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "asr-worker",
      "image": "<ecr-repo-uri>/worker:gpu-v1.1",
      "essential": true,
      "resourceRequirements": [ { "type": "GPU", "value": "1" } ],
      "linuxParameters": { "initProcessEnabled": true },
      "environment": [
        { "name": "GPU_ASR_ENABLED", "value": "true" },
        { "name": "ASR_QUEUE_URL", "value": "https://sqs.us-east-1.amazonaws.com/<account-id>/asr-queue" },
        { "name": "ASR_BUCKET", "value": "kortana-asr-prod" },
        { "name": "ASR_MAX_SYNC_MB", "value": "15" },
        { "name": "LOG_LEVEL", "value": "INFO" },
        { "name": "WHISPER_COMPUTE_TYPE", "value": "float16" }
      ],
      "secrets": [
        {
          "name": "GOOGLE_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:<account-id>:secret:kortana/prod/GOOGLE_API_KEY-XXXX"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/asr-worker",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "gpu"
        }
      }
    }
  ]
}
```

### Deployment Notes
```markdown
- Launch type: EC2 with GPU-optimized ECS-optimized AMI; ensure the instance type (e.g., g4dn.xlarge) joins the cluster and the agent has GPU support enabled.
- Capacity: Start with 1 GPU per task; scale service horizontally based on SQS ApproximateNumberOfMessagesVisible.
- Model caching (optional): To cache models across deployments, mount a writeable volume (EBS or EFS) at /app/.cache and set XDG_CACHE_HOME=/app/.cache.
```

### IAM Policy Snippet for Task Role – iam/asr-worker-policy.json
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"],
      "Resource": "arn:aws:sqs:us-east-1:<account-id>:asr-queue"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": "arn:aws:s3:::kortana-asr-prod/*"
    },
    {
      "Effect": "Allow",
      "Action": ["logs:CreateLogStream", "logs:PutLogEvents"],
      "Resource": "arn:aws:logs:us-east-1:<account-id>:log-group:/ecs/asr-worker:*"
    }
  ]
}
```

### Optional: Local GPU Compose Overlay – docker-compose.gpu.yml
```yaml
version: "3.9"

services:
  worker-gpu:
    profiles: [gpu]
    build:
      context: .
      dockerfile: worker/Dockerfile.gpu
    environment:
      GPU_ASR_ENABLED: "true"
      ASR_QUEUE_URL: http://localstack:4566/000000000000/asr
      ASR_BUCKET: local-asr-bucket
      ASR_MAX_SYNC_MB: "15"
      LOG_LEVEL: INFO
      WHISPER_COMPUTE_TYPE: float16
    depends_on:
      - localstack
    # Compose V2 supports 'gpus: all' for local NVIDIA runtime
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]
    # If your Compose doesn't honor 'deploy' outside Swarm, uncomment:
    # runtime: nvidia

  localstack:
    image: localstack/localstack
    ports: ["4566:4566"]
    environment:
      - SERVICES=s3,sqs
```

### CI Add-on (build GPU image)
```yaml
# in .github/workflows/spec-001.yml
# ...
jobs:
  # ... existing jobs
  build_worker_gpu:
    name: Build Worker (GPU)
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Build and tag image
        run: |
          docker build -f worker/Dockerfile.gpu -t my-app/worker:gpu-latest .
          # In a real CI/CD pipeline, you would push this to a registry like ECR
```

## production deployment & troubleshooting

When deploying to a cloud environment like AWS, a common "Failed to fetch" error is caused by a TLS certificate mismatch, not CORS. This guide explains the issue and how to fix it.

### The Problem: TLS/Hostname Mismatch

Your Application Load Balancer (ALB) HTTPS listener (port 443) uses an ACM SSL certificate for your custom domain (e.g., `api.kortana.example.com`). If your frontend tries to call the raw ALB DNS name (e.g., `kortana-alb-....elb.amazonaws.com`), the browser will reject the connection because the domain name in the URL doesn't match the name in the SSL certificate. This security measure prevents man-in-the-middle attacks.

### Step 1: Configure DNS
```bash
# In your DNS provider (e.g., Amazon Route 53), create a CNAME record.
# This points your desired API domain to the ALB's DNS name.

api.kortana.example.com.  CNAME  kortana-alb-1234567890.us-east-2.elb.amazonaws.com.
```

### Step 2: Update Frontend Configuration for Production
```html
<!-- In index.html, update the configuration for your production environment. -->
<script>
  window.__KORTANA__ = {
    apiBase: "https://api.kortana.example.com",
    apiKey:  "krtna_prod_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" // Use a production key
  };
</script>
```

### Deployment Sanity Checklist
```text
✅ ALB Listener (443) uses the correct ACM certificate for your domain.
✅ Security Group for ALB allows inbound HTTPS (443) from the internet.
✅ Security Group for ECS Task/Fargate allows inbound traffic on the app port (e.g., 8000) ONLY from the ALB's security group.
✅ Target Group is healthy and using the 'IP' target type for Fargate.
```

### elevation toggle (ui)
kor'tana gates admin features via a local feature flag.

```localStorage
localStorage.setItem('kortana:isElevated','true'); // enable
localStorage.removeItem('kortana:isElevated');        // disable
```
