import asyncio
import websockets
import json
import random
import time

connected_clients = set()

async def handler(websocket):
    connected_clients.add(websocket)
    print("🔌 Client connected")
    try:
        while True:
            payload = {
                "device_id": "esp32_sim_01",
                "bandwidth": round(random.uniform(0.5, 50.0), 2),
                "unit": "Mbps",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
            message = json.dumps(payload)
            await websocket.send(message)
            await asyncio.sleep(2)
    except websockets.ConnectionClosed:
        print("❌ Client disconnected")
    finally:
        connected_clients.remove(websocket)

async def main():
    async with websockets.serve(handler, "localhost", 8765):
        print("✅ WebSocket Server running on ws://localhost:8765")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
