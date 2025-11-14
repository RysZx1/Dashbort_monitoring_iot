# dummy_publisher.py
import json
import time
import random
import os
import paho.mqtt.client as mqtt

BROKER = os.getenv("MQTT_BROKER", "broker.hivemq.com")
PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC = os.getenv("MQTT_TOPIC", "iot/bandwidth")
DEVICE_ID = os.getenv("DEVICE_ID", "esp32_sim_01")
INTERVAL = float(os.getenv("PUBLISH_INTERVAL", "2"))  # detik

client = mqtt.Client()
client.connect(BROKER, PORT, 60)
client.loop_start()

try:
    while True:
        payload = {
            "device_id": DEVICE_ID,
            "bandwidth": round(random.uniform(0.5, 50.0), 2),  # Mbps
            "unit": "Mbps",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        msg = json.dumps(payload)
        client.publish(TOPIC, msg)
        print("[PUB]", TOPIC, msg)
        time.sleep(INTERVAL)
except KeyboardInterrupt:
    print("Stopped.")
finally:
    client.loop_stop()
    client.disconnect()
