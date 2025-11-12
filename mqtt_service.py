# mqtt_service.py
import sqlite3
import json
import time
from datetime import datetime
import threading
import os

import paho.mqtt.client as mqtt
from flask import Flask, jsonify

# CONFIG
BROKER_HOST = os.getenv("MQTT_BROKER", "broker.hivemq.com")   # ganti broker lu (e.g. broker.hivemq.com)
BROKER_PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC = os.getenv("MQTT_TOPIC", "iot/bandwidth")
DB_PATH = os.getenv("DB_PATH", "data.db")
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000

# --- Database helper ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS bandwidth (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT,
        bandwidth REAL,
        unit TEXT,
        raw_payload TEXT,
        ts TEXT
    )
    """)
    conn.commit()
    conn.close()

def insert_record(device_id, bandwidth, unit, raw_payload):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    ts = datetime.utcnow().isoformat()
    cur.execute("INSERT INTO bandwidth (device_id, bandwidth, unit, raw_payload, ts) VALUES (?, ?, ?, ?, ?)",
                (device_id, bandwidth, unit, raw_payload, ts))
    conn.commit()
    conn.close()

def fetch_all(limit=500):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, device_id, bandwidth, unit, raw_payload, ts FROM bandwidth ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [
        {"id": r[0], "device_id": r[1], "bandwidth": r[2], "unit": r[3], "raw_payload": json.loads(r[4]), "ts": r[5]}
        for r in rows
    ]

def fetch_latest_per_device():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT device_id, bandwidth, unit, raw_payload, ts
        FROM bandwidth b1
        WHERE id = (
            SELECT MAX(id) FROM bandwidth b2 WHERE b2.device_id = b1.device_id
        )
    """)
    rows = cur.fetchall()
    conn.close()
    return [
        {"device_id": r[0], "bandwidth": r[1], "unit": r[2], "raw_payload": json.loads(r[3]), "ts": r[4]}
        for r in rows
    ]

# --- MQTT callbacks ---
def on_connect(client, userdata, flags, rc):
    print("[MQTT] connected, rc =", rc)
    client.subscribe(TOPIC)
    print(f"[MQTT] subscribed to {TOPIC}")

def on_message(client, userdata, msg):
    payload = msg.payload.decode('utf-8')
    print(f"[MQTT] {msg.topic} -> {payload}")
    # try parse JSON, expect fields device_id, bandwidth, unit (unit optional)
    try:
        j = json.loads(payload)
        device_id = j.get("device_id", j.get("device", "unknown"))
        bandwidth = float(j.get("bandwidth", j.get("value", 0)))
        unit = j.get("unit", "Mbps")
    except Exception as e:
        # fallback: store raw text
        device_id = "unknown"
        try:
            bandwidth = float(payload)
        except:
            bandwidth = 0.0
        unit = "raw"
        j = {"raw": payload}

    insert_record(device_id, bandwidth, unit, json.dumps(j))

# --- MQTT client thread ---
def start_mqtt_loop():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER_HOST, BROKER_PORT, 60)
    client.loop_forever()

# --- Flask API ---
app = Flask(__name__)

@app.route("/data")
def api_data():
    return jsonify(fetch_all())

@app.route("/latest")
def api_latest():
    return jsonify(fetch_latest_per_device())

@app.route('/api/bandwidth', methods=['GET'])
def get_bandwidth():
    conn = sqlite3.connect('data.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM bandwidth ORDER BY ts DESC LIMIT 10;")
    data = cur.fetchall()
    conn.close()

    result = []
    for row in data:
        result.append({
            "device_id": row[0],
            "bandwidth": row[1],
            "unit": row[2],
            "raw_payload": row[3],
            "timestamp": row[4]
        })
    return jsonify(result)

@app.route('/api/bandwidth/<device_id>', methods=['GET'])
def get_bandwidth_by_device(device_id):
    conn = sqlite3.connect('data.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM bandwidth WHERE device_id=? ORDER BY ts DESC LIMIT 20;", (device_id,))
    data = cur.fetchall()
    conn.close()

    result = []
    for row in data:
        result.append({
            "device_id": row[0],
            "bandwidth": row[1],
            "unit": row[2],
            "raw_payload": row[3],
            "timestamp": row[4]
        })
    return jsonify(result)


if __name__ == "__main__":
    init_db()
    t = threading.Thread(target=start_mqtt_loop, daemon=True)
    t.start()
    print("[Service] MQTT listener started in background.")
    print(f"[Service] Flask API running on http://{FLASK_HOST}:{FLASK_PORT}")
    app.run(host=FLASK_HOST, port=FLASK_PORT)