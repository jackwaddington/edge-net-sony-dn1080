#!/usr/bin/env python3
"""Edge-NET adapter: Sony STR-DN1080 ↔ MQTT.

Polls the Sony Audio Control API and publishes retained state to
edge-net/avr/state. Subscribes to command topics and forwards to the API.

Config via env vars (written by provision script to /etc/edge-net-avr/.env):
  AVR_HOST     - Sony IP, default 192.168.0.6
  MQTT_BROKER  - broker IP, default 192.168.0.145
  MQTT_PORT    - default 1883
  POLL_INTERVAL - seconds between state polls, default 5
"""

import json
import logging
import os
import time
import requests
import paho.mqtt.client as mqtt

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

AVR_HOST = os.getenv("AVR_HOST", "192.168.0.6")
MQTT_BROKER = os.getenv("MQTT_BROKER", "192.168.0.145")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "5"))

BASE_URL = f"http://{AVR_HOST}:10000/sony"

# Maps friendly source names (MQTT payload) to Sony URI strings
SOURCE_MAP = {
    "tv":       "extInput:tv",
    "bd-dvd":   "extInput:bd-dvd",
    "game":     "extInput:game",
    "sat-catv": "extInput:sat-catv",
    "bt":       "extInput:btAudio",
    "btaudio":  "extInput:btAudio",
    "sacd-cd":  "extInput:sacd-cd",
    "video1":   "extInput:video?port=1",
    "video2":   "extInput:video?port=2",
}
SOURCE_MAP_INV = {v: k for k, v in SOURCE_MAP.items()}


def sony_call(service: str, method: str, params: list, version: str = "1.0"):
    payload = {"method": method, "params": params, "id": 1, "version": version}
    try:
        r = requests.post(f"{BASE_URL}/{service}", json=payload, timeout=3)
        r.raise_for_status()
        body = r.json()
        if "error" in body:
            log.warning("Sony error %s calling %s.%s", body["error"], service, method)
            return None
        return body.get("result")
    except Exception as exc:
        log.warning("Sony API call failed (%s.%s): %s", service, method, exc)
        return None


def get_state() -> dict | None:
    power = sony_call("system", "getPowerStatus", [], version="1.1")
    if power is None:
        return None
    status = power[0].get("status", "unknown")

    vol_result = sony_call("audio", "getVolumeInformation", [{}], version="1.1")
    volume, mute = None, None
    if vol_result:
        zone1 = next((z for z in vol_result[0] if z.get("output") == "extOutput:zone?zone=1"), None)
        if zone1:
            volume = zone1.get("volume")
            mute = zone1.get("mute")

    source = None
    terminals = sony_call("avContent", "getCurrentExternalTerminalsStatus", [], version="1.0")
    if terminals:
        active = [t for t in terminals[0] if t.get("active") == "active" and t.get("uri", "").startswith("extInput:")]
        if active:
            uri = active[0]["uri"]
            source = SOURCE_MAP_INV.get(uri, uri)

    return {"power": status, "source": source, "volume": volume, "mute": mute}


def handle_command(client, topic: str, payload: str):
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        data = {"value": payload}

    if topic == "edge-net/avr/power":
        state = data.get("state", data.get("value", ""))
        sony_call("system", "setPowerStatus", [{"status": state}], version="1.1")

    elif topic == "edge-net/avr/volume":
        level = data.get("level", data.get("value"))
        if isinstance(level, int):
            sony_call("audio", "setAudioVolume",
                      [{"output": "extOutput:zone?zone=1", "volume": str(level)}],
                      version="1.1")
        elif level in ("up", "down"):
            step = 1 if level == "up" else -1
            state = get_state()
            if state and state["volume"] is not None:
                new_vol = max(0, min(55, state["volume"] + step))
                sony_call("audio", "setAudioVolume",
                          [{"output": "extOutput:zone?zone=1", "volume": str(new_vol)}],
                          version="1.1")

    elif topic == "edge-net/avr/mute":
        value = data.get("value", data.get("state", ""))
        if value == "toggle":
            state = get_state()
            value = "off" if state and state["mute"] == "on" else "on"
        sony_call("audio", "setAudioMute",
                  [{"output": "extOutput:zone?zone=1", "mute": value}],
                  version="1.1")

    elif topic == "edge-net/avr/input":
        source = data.get("source", data.get("value", ""))
        uri = SOURCE_MAP.get(source.lower(), source)
        sony_call("avContent", "setPlayContent", [{"uri": uri}], version="1.2")


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="edge-net-sony-dn1080")
    last_state = {}

    def on_connect(c, userdata, flags, reason_code, props):
        if reason_code == 0:
            log.info("Connected to broker %s:%s", MQTT_BROKER, MQTT_PORT)
            for topic in ("edge-net/avr/power", "edge-net/avr/volume",
                          "edge-net/avr/mute", "edge-net/avr/input"):
                c.subscribe(topic)
        else:
            log.error("Broker connect failed: %s", reason_code)

    def on_message(c, userdata, msg):
        payload = msg.payload.decode(errors="replace")
        log.info("CMD %s %s", msg.topic, payload)
        handle_command(c, msg.topic, payload)
        # Publish updated state after command
        time.sleep(0.5)
        state = get_state()
        if state:
            c.publish("edge-net/avr/state", json.dumps(state), retain=True)

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()

    while True:
        state = get_state()
        if state and state != last_state:
            log.info("State changed: %s", state)
            client.publish("edge-net/avr/state", json.dumps(state), retain=True)
            last_state = state
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
