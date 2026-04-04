from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.kortana.swarm.hive_bus import HiveBus
from src.kortana.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

# The global unified bus connection for WebSockets
shared_bus = None

async def get_shared_bus():
    global shared_bus
    if shared_bus is None:
        shared_bus = HiveBus()
        await shared_bus.connect()
    return shared_bus

@router.websocket("/stream")
async def matrix_stream(websocket: WebSocket):
    """
    Connects the React Fractal Dashboard directly to the Swarm's Redis Pub/Sub Matrix.
    """
    await websocket.accept()
    logger.info("New client connected to Matrix Stream.")

    await get_shared_bus()

    try:
        # We need a dedicated subscriber for each websocket connection,
        # or we could multiplex them. For simplicity, we create a fresh bus connection
        # specific to this client's streaming loop.
        client_bus = HiveBus()
        await client_bus.connect()

        async for message in client_bus.subscribe():
            # Broadcast the pure thought-stream to the Fractal Dashboard
            await websocket.send_text(message)
    except WebSocketDisconnect:
        logger.info("Client disconnected from Matrix Stream.")
    except Exception as e:
        logger.error(f"Matrix Stream Error: {e}")
        await websocket.close()

# Provide an HTTP fallback or stat route
@router.get("/status")
async def matrix_status():
    return {"status": "Matrix Stream is online", "endpoint": "ws://[host]/api/matrix/stream"}
