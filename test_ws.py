import asyncio
import websockets
import json
import uuid

async def test_ws():
    uri = "ws://localhost:7777/ws"
    async with websockets.connect(uri) as ws:
        # Test ping/pong
        await ws.send(json.dumps({"type": "ping"}))
        pong = await ws.recv()
        print("Received:", pong)

        # Test message with ID and ack
        msg_id = str(uuid.uuid4())
        await ws.send(json.dumps({"id": msg_id, "content": "Hello Kor'tana!"}))
        ack = await ws.recv()
        print("Received:", ack)

if __name__ == "__main__":
    asyncio.run(test_ws()) 