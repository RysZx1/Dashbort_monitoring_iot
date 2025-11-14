import asyncio
import json
import paho.mqtt.client as mqtt
import websockets
import os

# ================= MQTT CONFIG =================
BROKER = os.getenv("MQTT_BROKER", "broker.hivemq.com")
PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPICS = [("iot/bandwidth", 0), ("iot/temperature", 0)]

# ================= WEBSOCKET SERVER =================
clients = set()
main_loop = asyncio.new_event_loop()

async def ws_handler(websocket, path):
    clients.add(websocket)
    print(f"[NEW] Client connected. Total: {len(clients)}")
    try:
        while True:
            # tunggu pesan masuk (atau timeout biar gak close)
            try:
                msg = await asyncio.wait_for(websocket.recv(), timeout=60)
                print(f"[WS] Received from client: {msg}")
            except asyncio.TimeoutError:
                # kirim heartbeat tiap 60 detik biar koneksi tetap hidup
                await websocket.send(json.dumps({"type": "ping"}))
    except websockets.ConnectionClosed:
        print(f"[BYE] Client disconnected.")
    finally:
        clients.remove(websocket)

async def send_to_ws_clients(message):
    if clients:
        msg_str = json.dumps(message)
        await asyncio.gather(*(client.send(msg_str) for client in clients))

# ================= MQTT CALLBACKS =================
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[OK] Connected to MQTT broker: {BROKER}")
        for topic, qos in TOPICS:
            client.subscribe(topic)
            print(f"[SUB] Subscribed to {topic}")
    else:
        print(f"[ERR] Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    try:
        payload_str = msg.payload.decode()
        try:
            payload = json.loads(payload_str)
        except json.JSONDecodeError:
            payload = payload_str  # fallback kalau bukan JSON valid

        print(f"\n📩 Topic: {msg.topic}")
        print(f"   Payload: {payload}")

        # Cek tipe data payload-nya
        if isinstance(payload, dict):
            if msg.topic == "iot/bandwidth":
                val = payload.get("bandwidth", "N/A")
                unit = payload.get("unit", "")
                print(f"   💡 Bandwidth: {val} {unit}")
            elif msg.topic == "iot/temperature":
                val = payload.get("temperature", "N/A")
                unit = payload.get("unit", "")
                print(f"   🌡️ Suhu: {val} {unit}")
        else:
            # Kalau bukan dict, tampilkan langsung
            print(f"   🔹 Value: {payload}")

        # kirim ke websocket (apapun datanya)
        data_json = {"topic": msg.topic, "payload": payload}
        asyncio.run_coroutine_threadsafe(send_to_ws_clients(data_json), main_loop)

    except Exception as e:
        print(f"[ERR] Gagal parsing data: {e}")

    try:
        payload = json.loads(msg.payload.decode())
        print(f"\n📩 Topic: {msg.topic}")
        print(f"   Payload: {json.dumps(payload, indent=4)}")

        if msg.topic == "iot/bandwidth":
            print(f"   💡 Bandwidth: {payload['bandwidth']} {payload['unit']}")
        elif msg.topic == "iot/temperature":
            print(f"   🌡️ Suhu: {payload['temperature']} {payload['unit']}")

        data_json = {"topic": msg.topic, "payload": payload}
        asyncio.run_coroutine_threadsafe(send_to_ws_clients(data_json), main_loop)

    except Exception as e:
        print(f"[ERR] Gagal parsing data: {e}")

# ================= MAIN SERVER =================
async def main():
    global main_loop
    main_loop = asyncio.get_running_loop()

    ws_server = await websockets.serve(ws_handler, "localhost", 8765)
    print("[RUN] WebSocket server running at ws://localhost:8765")

    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(BROKER, PORT, 60)
    mqtt_client.loop_start()

    try:
        await asyncio.Future()
    except KeyboardInterrupt:
        print("\n[STOP] Server stopped.")
        mqtt_client.loop_stop()
        ws_server.close()
        await ws_server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
