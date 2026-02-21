# 🔌 API_CONTRACT.md: The AetherCore Synaptic Protocol

```yaml
version: 0.1.0
channel: Asynchronous_WebSocket (ws://localhost:8000)
format: Binary (Sensory) + JSON (Control)
```

## 🛰️ 1. Edge-to-Brain (Sensory Stream)

To maintain zero-latency, visual data is sent as **Binary Payloads** prefixed with a 1-byte header.

### 🖼️ Visual Delta (Header: `0x01`)

* **Payload:** Compressed JPEG or PNG delta bytes.
* **Frequency:** 1-5 FPS (adaptive based on entropy).
* **Contract:** Must be decodable into the `Latent Space (z)` vector.

### 🎤 Audio Stream (Header: `0x02`)

* **Payload:** Raw PCM bytes (16-bit, 16kHz, Mono).
* **Frequency:** Real-time stream chunks.
* **Contract:** Direct feed to Gemini Live API.

### 📂 State Event (Header: `0x03` | JSON)

```json
{
  "type": "UI_STATE",
  "data": {
    "active_app": "Browser",
    "dom_hash": "sha256...",
    "anomaly_detected": false
  }
}
```

## 🧠 2. Brain-to-Edge (Action Commands)

Commands sent back to Tauri for OS-level execution.

### 🖱️ UI Action (JSON)

```json
{
  "cmd": "EXECUTE",
  "pillar": "ALPHA_MIND",
  "action": "CLICK",
  "params": {
    "x": 450,
    "y": 210,
    "target_id": "submit-btn"
  }
}
```

### 🧘 Cognition Alert (JSON)

```json
{
  "cmd": "SWITCH_SYSTEM",
  "target": "SYSTEM_2",
  "reason": "Free Energy Tau Breached (F=0.25)"
}
```

## 💓 3. The Heartbeat (Synchronicity)

* **Interval:** 1000ms.
* **Schema:** `{"pulse": "NOMINAL", "latency": "ms"}`.
* **Safety:** Connection drop triggers an immediate **AetherCore Veto** on all pending actions.

---
*The Synaptic Bridge is the fiber optic of agency.*
