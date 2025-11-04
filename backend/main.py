from fastapi import FastAPI
from routers import gemini, memory, agents

app = FastAPI(title="Kor'tana Backend", version="0.1.0")

# Mount routers
app.include_router(gemini.router, prefix="/api/gemini", tags=["gemini"])
app.include_router(memory.router, prefix="/api/memory", tags=["memory"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])

@app.get("/api/health")
async def health_check():
    return {"status": "alive", "message": "Kor'tana backend is breathing"}
