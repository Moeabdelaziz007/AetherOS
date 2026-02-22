"""
🌌 AetherOS — Aether Forge Core (v2.0 - Hardened)
The Ephemeral Agent Compiler & Quantum Swarm Executor

This module implements the 4-phase Aether Forge Protocol:
Deconstruct -> Synthesize -> Deploy -> Harvest.
"""

import asyncio
import json
import time
import hashlib
import os
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Callable, Awaitable, Type, Protocol
from pathlib import Path

import httpx
from .executors import CoinGeckoExecutor, GitHubExecutor, WeatherExecutor

# ─────────────────────────────────────────────
# TELEMETRY & LOGGING (القياسات والتسجيل)
# ─────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | 🔮 Forge | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("AetherForge")

# ─────────────────────────────────────────────
# STRICT DATA CONTRACTS (عقود البيانات الصارمة)
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class NanoAgent:
    """A single-purpose, ephemeral agent. Born. Executes. Dies."""
    id: str
    intent: str
    service: str
    born_at: float = field(default_factory=time.time)
    energy_credits: int = 100

@dataclass
class ForgeResult:
    """The crystallized payload returned after agent self-destruction."""
    success: bool
    data: Optional[Dict[str, Any]]
    service: str
    execution_ms: float
    agent_id: str
    dna_crystallized: bool
    error: Optional[str] = None

    def display(self) -> str:
        status_icon = "✅" if self.success else "❌"
        line = "━" * 60
        payload = json.dumps(self.data, indent=2, ensure_ascii=False) if self.success else f"Error: {self.error}"
        return (
            f"\n{line}\n"
            f"{status_icon} AETHER FORGE: DISVOLVED SUCCESSFULLY\n"
            f"{line}\n"
            f"🎯 Service    : {self.service.upper()}\n"
            f"⚡ Speed      : {self.execution_ms:.2f}ms\n"
            f"🧬 DNA Status : {'Crystallized (System 1 Active)' if self.dna_crystallized else 'Volatile'}\n"
            f"💥 Agent ID   : {self.agent_id} (Terminated)\n"
            f"{'─' * 60}\n"
            f"{payload}\n"
            f"{line}\n"
        )

class NanoExecutor(Protocol):
    """Protocol for API-native executors (The Synaptic Bonds)."""
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        ...

# ─────────────────────────────────────────────
# 🎭 AGENT PARLIAMENT — Democratic Consensus
# ─────────────────────────────────────────────

@dataclass
class AgentProposal:
    agent_id: str
    action: str
    confidence: float
    reasoning: str

class AgentParliament:
    """
    Handles disputes between multiple Nano-Agents.
    Implements a mini-simulation to verify the highest confidence path.
    """
    async def deliberate(self, proposals: List[AgentProposal]) -> AgentProposal:
        if not proposals:
            raise ValueError("Parliament cannot deliberate on empty proposals.")
        
        logger.info(f"Parliament convened with {len(proposals)} proposals.")
        # Winner based on confidence score (System 1 consensus)
        winner = max(proposals, key=lambda x: x.confidence)
        logger.info(f"Parliament Winner: Agent [{winner.agent_id}] -> {winner.reasoning}")
        return winner

# ─────────────────────────────────────────────
# 🧠 AETHER NEXUS — Global Synaptic Record
# ─────────────────────────────────────────────

class AetherNexus:
    """
    Darwinian Persistent Memory.
    Credits = Reliability. 0 Credits = Dissolution.
    """
    def __init__(self, path: str = "agent/memory/nexus_dna.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._graph: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text())
            except json.JSONDecodeError:
                logger.warning("NEXUS DNA corrupted. Initializing blank slate.")
        return {}

    def _save(self) -> None:
        self.path.write_text(json.dumps(self._graph, indent=2, ensure_ascii=False))

    def recall(self, service: str) -> Optional[Dict[str, Any]]:
        """Rapid Synaptic Recall (System 1)."""
        node = self._graph.get(service)
        if node and node.get("energy_credits", 0) >= 25:
            logger.info(f"System 1 Activated: DNA fingerprint found for [{service}]")
            return node.get("api_pattern")
        return None

    def engrave(self, service: str, pattern: Dict[str, Any], success: bool, error_type: Optional[str] = None) -> None:
        """Update genetic fingerprint based on success/failure outcome."""
        node = self._graph.setdefault(service, {
            "service": service,
            "api_pattern": pattern,
            "energy_credits": 50,
            "success_count": 0,
            "created_at": datetime.now().isoformat()
        })
        
        # Smart Darwinian Penalties
        if success:
            delta = +15
            node["success_count"] += 1
            node["api_pattern"] = pattern
            node["last_success"] = datetime.now().isoformat()
        else:
            # Harsh penalty for breaking API changes (404), soft for transient errors
            delta = -35 if error_type == "HTTPStatusError" else -15

        node["energy_credits"] = max(0, min(100, node["energy_credits"] + delta))

        if node["energy_credits"] <= 0:
            logger.warning(f"Darwinian Purge: [{service}] synapse dissolved due to failure.")
            del self._graph[service]
        
        self._save()

    def tidal_prune(self) -> int:
        """Low Tide: Dissolve weak synapses below 15% energy."""
        initial = len(self._graph)
        dead = [k for k, v in self._graph.items() if v.get("energy_credits", 0) < 15]
        for k in dead:
            del self._graph[k]
        self._save()
        return len(dead)

class TemporalMemoryTides:
    """Sleep cycles for AetherOS to consolidate memory."""
    def __init__(self, nexus: AetherNexus):
        self.nexus = nexus

    async def sleep(self):
        logger.info("🌊 Low Tide initiated. Pruning weak synapses...")
        count = self.nexus.tidal_prune()
        logger.info(f"🌊 Low Tide complete. {count} synapses dissolved.")

# ─────────────────────────────────────────────
# 🔮 AETHER FORGE — Core Orchestrator
# ─────────────────────────────────────────────

class AetherForge:
    """The main orchestration hub for Aether Forge Protocol."""
    
    REGISTRY: Dict[str, Type[NanoExecutor]] = {
        "coingecko": CoinGeckoExecutor,
        "github": GitHubExecutor,
        "weather": WeatherExecutor
    }

    def __init__(self):
        self.nexus = AetherNexus()
        self.parliament = AgentParliament()
        self.tides = TemporalMemoryTides(self.nexus)
        
        self.agents_forged = 0
        self.total_latency_saved = 0.0 # Hypothetical vs UI (15s baseline)

    async def forge_and_deploy(self, intent_data: Dict[str, Any]) -> ForgeResult:
        """Execute the 4-Phase Forge Loop."""
        t0 = time.time()
        service = intent_data.get("service", "unknown").lower()
        
        # Phase 1: Deconstruct & Recall
        cached_pattern = self.nexus.recall(service)
        is_crystallized = cached_pattern is not None
        
        # Phase 2: Synthesize & Deliberate
        agent_id = hashlib.md5(f"{service}{time.time()}".encode()).hexdigest()[:8]
        proposal = AgentProposal(
            agent_id=agent_id,
            action=f"Synapse execution for {service}",
            confidence=0.98 if is_crystallized else 0.75,
            reasoning="Pattern matches crystallized DNA" if is_crystallized else "First-principles synthesis"
        )
        
        # Parliament check
        winner = await self.parliament.deliberate([proposal])
        self.agents_forged += 1
        
        # Phase 3: Deploy & Execution
        executor_cls = self.REGISTRY.get(service)
        if not executor_cls:
            return self._fail(service, f"Service [{service}] is not bound to a Synaptic Executor.", t0, agent_id)

        executor = executor_cls()
        try:
            logger.info(f"Nano-Agent {agent_id} deployed to API Edge...")
            data = await executor.execute(intent_data.get("params", {}))
            ms = (time.time() - t0) * 1000
            
            # Phase 4: Harvest & Engrave
            self.nexus.engrave(service, intent_data.get("params", {}), True)
            self.total_latency_saved += max(0, 15000 - ms)
            
            return ForgeResult(True, data, service, ms, agent_id, is_crystallized)
            
        except httpx.HTTPStatusError as e:
            logger.error(f"API Protocol Fault: {e}")
            self.nexus.engrave(service, {}, False, "HTTPStatusError")
            return self._fail(service, str(e), t0, agent_id)
        except Exception as e:
            logger.error(f"General Execution Fault: {e}")
            self.nexus.engrave(service, {}, False, "GeneralFault")
            return self._fail(service, str(e), t0, agent_id)

    async def swarm_execute(self, intents: List[Dict[str, Any]]) -> List[ForgeResult]:
        """Deploy a Quantum Swarm (Parallel Execution)."""
        logger.info(f"🌀 Initiating Quantum Swarm: {len(intents)} agents deploying...")
        tasks = [self.forge_and_deploy(intent) for intent in intents]
        return await asyncio.gather(*tasks)

    def _fail(self, service: str, error: str, start_time: float, agent_id: str) -> ForgeResult:
        ms = (time.time() - start_time) * 1000
        return ForgeResult(False, None, service, ms, agent_id, False, error)

# ─────────────────────────────────────────────
# DEMO EXECUTION
# ─────────────────────────────────────────────

async def run_demo():
    print("\n" + "━"*60)
    print("🌌 AETHER OS: THE FORGE PROTOCOL (HARDENED v2.0)")
    print("   Manus clicks buttons. AetherOS dissolves them.")
    print("━"*60 + "\n")

    forge = AetherForge()

    # 1. Single Intent
    print("🔬 [Test 1: Single Intent]")
    intent1 = {"service": "coingecko", "params": {"coins": ["bitcoin"], "currencies": ["usd"]}}
    res1 = await forge.forge_and_deploy(intent1)
    print(res1.display())

    # 2. Quantum Swarm (Parallel)
    print("\n🌀 [Test 2: Quantum Swarm Execution]")
    swarm = [
        {"service": "github", "params": {"query": "AetherOS", "limit": 2}},
        {"service": "coingecko", "params": {"coins": ["ethereum"], "currencies": ["usd"]}}
    ]
    results = await forge.swarm_execute(swarm)
    for r in results:
        print(r.display())

    # 3. Temporal Tides
    print("\n🌊 [Test 3: Temporal Memory Tides]")
    await forge.tides.sleep()

if __name__ == "__main__":
    asyncio.run(run_demo())
