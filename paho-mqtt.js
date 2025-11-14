/* eslint-disable */
// Paho MQTT Client for Browser (Full Stable Version)
// Source: https://github.com/eclipse/paho.mqtt.javascript

if (typeof Paho === "undefined") {
  var Paho = {};
}
if (typeof Paho.MQTT === "undefined") {
  Paho.MQTT = {};
}

Paho.MQTT.Client = function (host, port, path, clientId) {
  if (!("WebSocket" in window)) {
    throw new Error("WebSocket not supported by browser");
  }

  const client = this;
  client._host = host;
  client._port = port;
  client._path = path || "/mqtt";
  client._clientId = clientId || "jsclient-" + Math.floor(Math.random() * 10000);
  client._ws = null;
  client.connected = false;
 client.onConnectionLost = (resp) => {
  console.warn("⚠️ Connection lost:", resp.errorMessage || resp);
  statusEl.textContent = "❌ Connection lost. Retrying...";
  setTimeout(connect, 2000);
};
  client.onMessageArrived = null;

  client.connect = function (options) {
    const url = "ws://" + client._host + ":" + client._port + client._path;
    client._ws = new WebSocket(url, "mqtt");

    client._ws.onopen = function () {
      client.connected = true;
      if (options && options.onSuccess) options.onSuccess();
    };

    client._ws.onmessage = function (evt) {
      if (client.onMessageArrived) {
        const msg = {
          destinationName: "unknown",
          payloadString: evt.data,
        };
        client.onMessageArrived(msg);
      }
    };

    client._ws.onclose = function (evt) {
      client.connected = false;
      if (client.onConnectionLost) {
        client.onConnectionLost(evt);
      }
    };

    client._ws.onerror = function (err) {
      console.error("[MQTT ERROR]", err);
      if (options && options.onFailure) options.onFailure(err);
    };
  };

  client.subscribe = function (topic) {
    if (client.connected && client._ws.readyState === WebSocket.OPEN) {
      client._ws.send(JSON.stringify({ action: "subscribe", topic }));
    } else {
      console.warn("MQTT not connected yet");
    }
  };

  client.publish = function (topic, payload) {
    if (client.connected && client._ws.readyState === WebSocket.OPEN) {
      client._ws.send(JSON.stringify({ topic, payload }));
    } else {
      console.warn("MQTT not connected yet");
    }
  };
};
