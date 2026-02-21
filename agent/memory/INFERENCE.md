# 🧠 INFERENCE.md: Active Inference & Gating Logic

```yaml
version: 0.2.0
pillar: Prometheus (Cognitive Engine)
math_model: VFE + EFE (Active Inference)
```

## 📐 Expected Free Energy ($G$)

Planning in AuraOS is the selection of a policy $\pi$ that minimizes the *Expected* Free Energy $G(\pi)$:

$$G(\pi, \tau) = \underbrace{E_{q(o, s | \pi)} [ \ln q(s | \pi) - \ln p(o, s | \pi) ]}_{\text{Total Loss}}$$

Calculated by the Orchestrator as:
$G \approx \text{Complexity} - \underbrace{\text{Epistemic Value}}_{\text{Discovery}} - \underbrace{\text{Pragmatic Value}}_{\text{Utility}}$

## ⚙️ Orchestrator Cognitive Weights

These weights determine the "curiosity" vs "compliance" of the agent:

```yaml
cognitive_weights:
  pragmatic_utility (pref): 0.85 # Drive to reach SOUL goals
  epistemic_curiosity (info): 0.65 # Drive to explore unknown UI elements
  novelty_bias: 0.25 # Preference for new states
  surprise_threshold (tau): 0.15 # System 1 -> 2 Switch

policy_selection:
  algorithm: Dirichlet_Sampling
  temperature: 0.05 # Low temperature = Deterministic
```

## 📏 System 1/2 Gating Protocol

### 🏎️ System 1 (Reflexive)

* **Trigger:** Prediction Error $\Delta F < \tau$.
* **Inference:** $q(s) \to a_{direct}$.
* **Latency:** < 150ms.

### 🧘 System 2 (Reflective)

* **Trigger:** $\Delta F \ge \tau$ OR Explicit User Query.
* **Search:** AlphaMind MCTS search on latent manifold $z$.
* **Loop:** GIF-MCTS (Identify -> Fix -> Verify).

---
*Inference is a battle between what the agent knows and what it needs to find out.*
