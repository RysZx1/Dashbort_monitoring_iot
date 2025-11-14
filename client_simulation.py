import json
import time
import paho.mqtt.client as mqtt

# ================= CONFIG =================
BROKER = "broker.hivemq.com"      # broker publik (bisa diganti ke punya lu)
PORT = 8000                       # port WebSocket HiveMQ
TOPIC = "iot/bandwidth"

# ================= CALLBACKS =================
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ Connected to MQTT broker (WebSocket): {BROKER}:{PORT}")
        client.subscribe(TOPIC)
        print(f"[SUB] Subscribed to topic: {TOPIC}")
    else:
        print(f"❌ Connection failed, code: {rc}")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        print(f"\n📩 Topic: {msg.topic}")
        print(f"📦 Message: {payload}")
    except Exception as e:
        print(f"[ERR] Failed to parse message: {e}")

# ================= MAIN =================
client = mqtt.Client(transport="websockets")
client.on_connect = on_connect
client.on_message = on_message

print(f"🔌 Connecting to {BROKER}:{PORT} via WebSocket...")
client.connect(BROKER, PORT, 60)

# jalan terus
try:
    client.loop_forever()
except KeyboardInterrupt:
    print("\n[STOP] Client disconnected.")
