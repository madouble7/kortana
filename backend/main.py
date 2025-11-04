import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from routers import agents, gemini, github, memory, autonomy, knowledge
except ImportError as e:
    print(f"Error importing routers: {e}")
    raise

app = FastAPI(title="Kor'tana Backend", version="0.1.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
try:
    app.include_router(gemini.router, prefix="/api/gemini", tags=["gemini"])
    app.include_router(memory.router, prefix="/api/memory", tags=["memory"])
    app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
    app.include_router(github.router, prefix="/api/github", tags=["github"])
    app.include_router(autonomy.router, prefix="/api/autonomy", tags=["autonomy"])
    app.include_router(knowledge.router, prefix="/api/knowledge", tags=["knowledge"])
except Exception as e:
    print(f"Error including routers: {e}")
    raise


@app.get("/api/health")
async def health_check():
    return {"status": "alive", "message": "Kor'tana backend is breathing"}
