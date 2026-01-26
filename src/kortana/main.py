"""
Kor'tana Main FastAPI Application
"""

import asyncio
import json
from contextlib import asynccontextmanager  # For lifespan events
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse

from src.kortana.api.routers import core_router, goal_router
from src.kortana.api.routers import core_router, goal_router from src.kortana.api.routers.core_router import openai_adapter_router from src.kortana.api.routers.conversation_router import router as conversation_router
from src.kortana.core.scheduler import (
    get_scheduler_status,
    start_scheduler,
    stop_scheduler,
)
from src.kortana.modules.memory_core.routers.memory_router import (
    router as memory_router,
)
# Import new module routers
from src.kortana.modules.multilingual.router import router as multilingual_router
from src.kortana.modules.emotional_intelligence.router import (
    router as emotional_intelligence_router,
)
from src.kortana.modules.content_generation.router import router as content_router
from src.kortana.modules.plugin_framework.router import router as plugin_router
from src.kortana.modules.ethical_transparency.router import router as ethics_router
from src.kortana.modules.gaming.router import router as gaming_router
from src.kortana.modules.marketplace.router import router as marketplace_router


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("INFO:     Starting Kor'tana's autonomous scheduler...")
    start_scheduler()
    print("INFO:     Kor'tana's autonomous scheduler started.")
    yield
    # Shutdown
    print("INFO:     Stopping Kor'tana's autonomous scheduler...")
    stop_scheduler()
    print("INFO:     Kor'tana's autonomous scheduler stopped.")


app = FastAPI(
    title="Kor'tana AI System",
    description="The Warchief's AI Companion",
    version="1.0.0",
    lifespan=lifespan,  # Add lifespan manager
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(memory_router)
app.include_router(conversation_router)  # Add conversation history router
app.include_router(core_router.router)
app.include_router(core_router.openai_adapter_router)
app.include_router(goal_router.router)
app.include_router(openai_adapter_router)

# Mount static files
static_dir = Path(__file__).parent.parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
def read_root():
    """Serve the chat interface."""
    static_file = static_dir / "chat.html"
    if static_file.exists():
        return FileResponse(static_file)
    return {"message": "Kor'tana API is running. Use /docs for API documentation."}

# Include new module routers
app.include_router(multilingual_router)
app.include_router(emotional_intelligence_router)
app.include_router(content_router)
app.include_router(plugin_router)
app.include_router(ethics_router)
app.include_router(gaming_router)
app.include_router(marketplace_router)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Kor'tana",
        "version": "1.0.0",
        "message": "The Warchief's companion is ready",
    }


@app.get("/test-db")
def test_db():
    try:
        import os
        import sqlite3

        db_path = "kortana.db"
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            conn.close()
            return {"db_connection": "ok", "result": result[0] if result else None}
        else:
            return {
                "db_connection": "no_database",
                "message": "Run init_db.py to create",
            }
    except Exception as e:
        return {"db_connection": "error", "detail": str(e)}


@app.post("/chat")
async def chat(message: dict):
    """Enhanced chat endpoint using full orchestrator capabilities.
    
    Validates input, processes through orchestrator, and saves to conversation history.
    
    Args:
        message: Dictionary containing 'message' (required) and optional 'conversation_id'
        
    Returns:
        JSON response with assistant reply, conversation_id, and metadata
        
    Raises:
        HTTPException: If message is empty, too long, or processing fails
    """
    try:
        from src.kortana.services.database import get_db_sync
        from src.kortana.core.orchestrator import KorOrchestrator
        from src.kortana.services.conversation_history import conversation_history
        
        user_message = message.get("message", "")
        if not user_message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Validate message length (max 10000 characters)
        if len(user_message) > 10000:
            raise HTTPException(status_code=400, detail="Message too long (max 10000 characters)")
        
        # Get or create conversation
        conv_id = message.get("conversation_id")
        if not conv_id:
            conv_id = conversation_history.create_conversation()
        
        # Save user message to history
        conversation_history.add_message(conv_id, "user", user_message)
        
        # Use a database session for this request
        db = next(get_db_sync())
        try:
            orchestrator = KorOrchestrator(db=db)
            result = await orchestrator.process_query(query=user_message)
            
            # Extract the final response
            final_response = result.get("final_kortana_response", 
                                      result.get("response", 
                                                "I'm having trouble processing that right now."))
            
            # Prepare metadata
            metadata = {
                "model": result.get("llm_metadata", {}).get("model"),
                "context_used": len(result.get("context_from_memory", [])) > 0,
                "memories_accessed": [
                    {
                        "content": mem,
                        "relevance": "high"
                    }
                    for mem in result.get("context_from_memory", [])[:3]
                ]
            }
            
            # Save assistant response to history
            conversation_history.add_message(conv_id, "assistant", final_response, metadata)
            
            return {
                "response": final_response,
                "status": "success",
                "conversation_id": conv_id,
                "metadata": metadata
            }
        finally:
            db.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream(message: dict):
    """Streaming chat endpoint for progressive responses with conversation history integration.
    
    Validates input, streams response through orchestrator, and saves to conversation history.
    
    Args:
        message: Dictionary containing 'message' (required) and optional 'conversation_id'
        
    Returns:
        StreamingResponse with Server-Sent Events
        
    Raises:
        HTTPException: If message is empty, too long, or processing fails
    """
    from src.kortana.services.database import get_db_sync
    from src.kortana.core.orchestrator import KorOrchestrator
    from src.kortana.services.conversation_history import conversation_history
    
    user_message = message.get("message", "")
    if not user_message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    # Validate message length (max 10000 characters)
    if len(user_message) > 10000:
        raise HTTPException(status_code=400, detail="Message too long (max 10000 characters)")
    
    # Get or create conversation
    conv_id = message.get("conversation_id")
    if not conv_id:
        conv_id = conversation_history.create_conversation()
    
    # Save user message to history
    conversation_history.add_message(conv_id, "user", user_message)
    
    async def generate_response():
        """Generator function for streaming response."""
        db = next(get_db_sync())
        try:
            # Send initial event
            yield f"data: {json.dumps({'type': 'start', 'status': 'processing'})}\n\n"
            await asyncio.sleep(0.1)
            
            # Process the query
            orchestrator = KorOrchestrator(db=db)
            result = await orchestrator.process_query(query=user_message)
            
            # Extract the response
            final_response = result.get("final_kortana_response", 
                                      result.get("response", 
                                                "I'm having trouble processing that right now."))
            
            # Stream response in chunks with better chunk sizing
            words = final_response.split()
            if len(words) <= 20:
                chunk_size = 3
            else:
                chunk_size = max(3, len(words) // 20)
            
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i:i+chunk_size])
                if chunk:
                    chunk += " " if i + chunk_size < len(words) else ""
                    event_data = {
                        'type': 'chunk',
                        'content': chunk
                    }
                    yield f"data: {json.dumps(event_data)}\n\n"
                    await asyncio.sleep(0.05)
            

            # Send the full response as a single chunk event
            event_data = {
                'type': 'chunk',
                'content': final_response
            }
            yield f"data: {json.dumps(event_data)}\n\n"
            
            # Send completion event with metadata
            completion_data = {
                'type': 'done',
                'conversation_id': conv_id,
                'metadata': metadata
            }
            yield f"data: {json.dumps(completion_data)}\n\n"
            
        except Exception as e:
            error_data = {
                'type': 'error',
                'error': str(e)
            }
            yield f"data: {json.dumps(error_data)}\n\n"
        finally:
            db.close()
    
    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.get("/status")
def system_status():
    scheduler_info = get_scheduler_status()
    return {
        "autonomous_agent": "ready",
        "scheduler_running": scheduler_info.get("running", False),
        "scheduler_jobs": scheduler_info.get("jobs", []),
        "message": "Kor'tana system operational",
    }


@app.post("/adapters/lobechat/chat")
async def lobechat_adapter(request: dict):
    """LobeChat adapter endpoint using full orchestrator capabilities."""
    try:
        from src.kortana.services.database import get_db_sync
        from src.kortana.core.orchestrator import KorOrchestrator
        
        messages = request.get("messages", [])
        if not messages:
            raise HTTPException(status_code=400, detail="No messages provided")
        
        # Extract the last user message
        user_message = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        
        if not user_message:
            raise HTTPException(status_code=400, detail="No user message found")
        
        # Use a database session for this request
        db = next(get_db_sync())
        try:
            orchestrator = KorOrchestrator(db=db)
            result = await orchestrator.process_query(query=user_message)
            
            # Extract the final response
            final_response = result.get("final_kortana_response", 
                                      result.get("response", 
                                                "I'm having trouble processing that right now."))
            
            # Return in OpenAI-compatible format
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": final_response
                    },
                    "finish_reason": "stop",
                    "index": 0
                }],
                "model": result.get("llm_metadata", {}).get("model", "kortana-custom"),
                "usage": result.get("llm_metadata", {}).get("usage", {})
            }
        finally:
            db.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversations")
def list_conversations(user_id: str | None = None):
    """List all conversations, optionally filtered by user."""
    from src.kortana.services.conversation_history import conversation_history
    return {"conversations": conversation_history.list_conversations(user_id=user_id)}


@app.get("/conversations/{conversation_id}")
def get_conversation(conversation_id: str):
    """Get a specific conversation by ID."""
    from src.kortana.services.conversation_history import conversation_history
    conversation = conversation_history.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@app.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    from src.kortana.services.conversation_history import conversation_history
    if conversation_history.delete_conversation(conversation_id):
        return {"status": "deleted", "conversation_id": conversation_id}
    raise HTTPException(status_code=404, detail="Conversation not found")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
