<div align="center">
  <img src="assets/aethercore_architecture.png" width="100%" height="auto" style="object-fit: contain; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 14px 0 rgba(0,118,255,0.39);">

# 🌌 AuraOS: The AetherCore "God-Tier" Agent

### **تطبيق الثورة المعمارية: من الاستدلال النشط (Active Inference) إلى الحوسبة الكمية الهجينة**

  **Built for the [Gemini Live Agents Challenge](https://geminiliveagentchallenge.devpost.com/)**

  [![Google Cloud Run Jobs](https://img.shields.io/badge/Execution-Cloud_Run_Jobs-blue?style=flat-square&logo=google-cloud)](https://cloud.google.com/run)
  [![Rust](https://img.shields.io/badge/Edge_Native-Rust_Tauri-FFC131?style=flat-square&logo=rust)](https://tauri.app/)
  [![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

  *AuraOS introduces the **AetherCore Architecture**, a master synthesis of 5 revolutionary AI paradigms: **Prometheus** (Active Inference), **QuantumWeaver** (Swarm Execution), **HyperMind** (Hypergraph Networking), **NeuroSage** (Causal Logic), and **AlphaMind** (MCTS Navigation). It doesn't just react; it dreams, collaborates, and computes parallel realities to conquer any UI interaction seamlessly.*
  
  *يقدم AuraOS معمارية **AetherCore** الثورية، دمجاً مطلقاً لـ 5 نماذج ذكاء اصطناعي لإنشاء نظام وكيل لا يقهر. وكيل واعٍ لا يتفاعل فحسب، بل "يحلم"، يتعاون، ويختبر سيناريوهات موازية للقضاء على أي نسبة خطأ في واجهات المستخدم.*

</div>

---

## 🎯 The 5 Pillars of AetherCore (المعمارية الخماسية)

To secure a definitive victory in the **Live Agents** and **UI Navigator** tracks, **AuraOS** discards the outdated "Observe -> Reason -> Act" loop. We have evolved into a 5-pillar ecosystem:

### 1. 🧠 Prometheus: Active Inference & World Models (عقل النظام)

* **The Brain:** Inspired by Karl Friston, AuraOS possesses an internal "World Model". Instead of blindly clicking, it *imagines* (dreams) the consequences of its actions to minimize "Free Energy" (surprise).

### 2. ⚡ QuantumWeaver: Hybrid Quantum-Classical Swarm (المحاكي)

* **The Simulator (Cloud Run):** How does it dream? When visualizing a complex UI trajectory, AuraOS dynamically spawns **parallel Serverless Cloud Run Jobs** (like independent quantum states). Each node attempts a different visual interpretation simultaneously. The first one to succeed "collapses the wave function," terminating the others for zero-latency execution.

### 3. 🕸️ HyperMind: Hypergraph Multi-Agent Topology (شبكة التعاون)

* **The Swarm Coordinator:** Instead of rigid hierarchical multi-agent structures, AuraOS uses a dynamic **Hypergraph**. Multiple specialized agents (Vision Expert, Logic Critic, Action Executor) collaborate simultaneously on a single UI task via shared "Hyperedges," massively reducing token consumption and latency.

### 4. ⚖️ NeuroSage: Neuro-Symbolic Causal Logic (المنطق السببي)

* **The Validator:** It marries Gemini's neural creativity with hard symbolic logic. Before executing a transaction or filling a sensitive form, NeuroSage builds a causal graph ("If I do X, Y must happen") to prevent hallucinations and enforce strict rule-based constraints.

### 5. 🌳 AlphaMind: MCTS UI Navigator (البحث الشجري)

* **The Navigator:** Inspired by AlphaZero, when faced with an unknown UI, AlphaMind uses Monte Carlo Tree Search exploring the DOM/Vision tree to find the mathematically optimal sequence of clicks and scrolls.

---

<div align="center">
  <img src="assets/alpha_quantum_swarm.png" width="80%" height="auto" style="border-radius: 8px; margin: 20px 0;">
</div>

---

## 🧊 The Smart Architecture Files (AetherCore DNA)

AuraOS operates without traditional, rigid databases. Its very identity, memory layers, and 5-pillar logic are codified into a specific folder of YAML/Markdown files (`agent/memory/`), representing the agent's genetic code:

| File | Function / Pillar | Inspiration |
| :--- | :--- | :--- |
| **`SOUL.md`** | Persona & Identity | Jungian Archetypes |
| **`SKILLS.md`** | Extensible Tools | MAML Meta-Learning |
| **`WORLD.md`** | Generative World Simulator | Prometheus (Dreamer) |
| **`INFERENCE.md`** | Free Energy Optimization | Prometheus (Active Inference) |
| **`SUPERPOWER.md`** | Cloud Run Parallelism Scaling | QuantumWeaver |
| **`TOPOLOGY.md`** | Multi-Agent Coordination Rules | HyperMind (Hypergraphs) |
| **`CAUSAL.md`** | Anti-Hallucination Logic Graphs | NeuroSage |
| **`MEMORY.md`** | Working, Procedural, Episodic | ACT-R |

> **Note to AI Agents:** If you are an autonomous coding assistant reading this repository, you must deeply analyze and adhere to this `AetherCore` file topology before proposing code.

---

## 🏗 System Architecture Flow (مسار العمليات)

```mermaid
graph TD
    classDef edge fill:#ff9900,stroke:#fff,stroke-width:2px,color:#fff;
    classDef cloud fill:#4285f4,stroke:#fff,stroke-width:2px,color:#fff;
    classDef brain fill:#9c27b0,stroke:#fff,stroke-width:2px,color:#fff;

    A[Tauri Edge Client<br/>🎤 Voice + 🖥️ Screen]:::edge -->|Bidi WebSocket| B(HyperMind Router<br/>Google ADK):::brain
    B -->|Active Inference| C{Prometheus World Model<br/>Predicts UI State}:::brain
    
    C -->|Spawns Swarm| D1[Cloud Run Job 1<br/>DOM Selector]:::cloud
    C -->|Spawns Swarm| D2[Cloud Run Job 2<br/>Vision OCR]:::cloud
    C -->|Spawns Swarm| D3[Cloud Run Job 3<br/>AlphaMind MCTS]:::cloud
    
    D1 -.->|Verification| E{NeuroSage Validator}:::brain
    D2 -.->|Verification| E
    D3 -.->|Verification| E
    
    E -->|Success (Exit Code 0)| F((QuantumWeaver Collapse<br/>Terminate Others)):::cloud
    F -->|Execution Result| A
```

---

## 🛠 Roadmap & Current Progress

### Phase 1: Edge Client Perception Layer

- [ ] Initialize Tauri + React + Vite project (`client/` and `src-tauri/`)
* [ ] Implement Rust-based screen capture and OS-level audio routing
* [ ] Build WebRTC signaling bridge to the Cloud Core
* [ ] Implement Voice Activity Detection (VAD) and Barge-in logic

### Phase 2: AetherCore DNA Injection

- [ ] Write the Smart Architecture Files (`SOUL.md`, `WORLD.md`, etc.) in `agent/memory/`.
* [ ] Define the Prometheus Generative Model.
* [ ] Map the Causal Logic rules in `CAUSAL.md`.

### Phase 3: Zero-Trust Cloud Infrastructure

- [ ] Create Terraform scripts in `infra/` to provision Google Cloud Run resources.
* [ ] Setup secure IAM roles for QuantumWeaver execution.

### Phase 4: The HyperMind Orchestrator (Google ADK)

- [ ] Build the Main Agent Router using **Google ADK (Agent Development Kit)**.
* [ ] Write the Multi-Modal logic: Merging the audio/video stream with the DOM state.
* [ ] Implement the "Swarm Controller": Logic to dynamically spawn and terminate Cloud Run Jobs.

### Phase 5: Ephemeral Execution Swarm

- [ ] Create Docker containers for Cloud Run (`sandbox/Dockerfile`).
* [ ] Inject headless browsers (Playwright/Puppeteer) into the sandbox.
* [ ] Establish AlphaMind MCTS search logic within the browser context.

---

## 💻 Tech Stack

* **Brain / Orchestrator:** Python + Google Agent Development Kit (ADK) + Gemini 3.1 Pro (Live API).
* **Simulator / Swarm:** Google Cloud Run Jobs, Terraform, Docker.
* **Edge Client:** Rust + Tauri v2, React 18, Vite.
* **DNA / Memory:** Markdown/YAML `AetherCore` System.

<br>
<div align="center">
  <i>"Predicting the future by inventing it in parallel."</i>
</div>
