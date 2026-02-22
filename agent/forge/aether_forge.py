"""
🌌 AetherOS — Aether Forge Core (v2.1.0)
Pillar: Prometheus / QuantumWeaver
Role: The Ephemeral Agent Compiler & Executor

"Manus clicks buttons. AetherOS dissolves them."
"""

import asyncio
import json
import time
import hashlib
import httpx
import os
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, Type
from pathlib import Path

# Setup Clinical Logging (Interface Dissolver Voice)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | 🔮 Forge | %(levelname)s | %(message)s")
logger = logging.getLogger("AetherForge")

# ─────────────────────────────────────────────
from .executors import CoinGeckoExecutor, GitHubExecutor, WeatherExecutor

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
        logger.info(f"Parliament convened with {len(proposals)} proposals.")
        # In MVP, we simply take the highest confidence. 
        # In V2, this triggers parallel SimulationArena runs.
        winner = max(proposals, key=lambda x: x.confidence)
        logger.info(f"Parliament Winner: Agent [{winner.agent_id}] via '{winner.reasoning}'")
        return winner

# ─────────────────────────────────────────────
# 🧠 AETHER NEXUS — Digital Darwinism Hub
# ─────────────────────────────────────────────

class AetherNexus:
    """
    Persistent Knowledge Graph for API DNA.
    Implements Temporal Memory Tides & Evolutionary Pruning.
    """
    def __init__(self, path: str = "agent/memory/nexus_dna.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._dna: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text())
            except json.JSONDecodeError:
                logger.error("Failed to decode NEXUS DNA. Initializing new graph.")
        return {}

    def _save(self):
        self.path.write_text(json.dumps(self._dna, indent=2, ensure_ascii=False))

    def recall(self, service: str) -> Optional[Dict[str, Any]]:
        """System 1: Rapid synaptic recall."""
        entry = self._dna.get(service)
        if entry and entry.get("energy_credits", 0) > 20:
            logger.info(f"Recall: [{service}] DNA matches stability threshold ({entry['energy_credits']}).")
            return entry.get("pattern")
        return None

    def engrave(self, service: str, pattern: Dict[str, Any], success: bool):
        """Update synaptic weights based on success/failure outcome."""
        entry = self._dna.setdefault(service, {
            "service": service,
            "pattern": pattern,
            "energy_credits": 50,
            "success_count": 0,
            "created_at": datetime.now().isoformat()
        })
        
        # Digital Darwinism: Evolutionary Pressure
        delta = 15 if success else -25
        entry["energy_credits"] = max(0, min(100, entry["energy_credits"] + delta))
        
        if success:
            entry["success_count"] += 1
            entry["last_success"] = datetime.now().isoformat()
            entry["pattern"] = pattern 
            
        if entry["energy_credits"] <= 0:
            logger.warning(f"Purge: [{service}] failed Digital Darwinism. Synapse dissolved.")
            del self._dna[service]
        
        self._save()

    def tidal_prune(self):
        """Low Tide: Prune weak synaptic connections (<10 credits)."""
        pruned = [k for k, v in self._dna.items() if v.get("energy_credits", 0) < 10]
        for k in pruned:
            logger.info(f"Low Tide: Pruning weak synapse [{k}].")
            del self._dna[k]
        self._save()
        return len(pruned)

class TemporalMemoryTides:
    """
    REM Sleep for AetherOS.
    Periodically prunes weak synapses and crystallizes strong ones.
    """
    def __init__(self, nexus: AetherNexus):
        self.nexus = nexus

    async def sleep_cycle(self):
        """Execute a Low Tide pruning cycle."""
        logger.info("🌊 Low Tide initiated. Pruning weak synapses...")
        pruned_count = self.nexus.tidal_prune()
        logger.info(f"🌊 Low Tide complete. {pruned_count} synapses dissolved.")

# ─────────────────────────────────────────────
# 🔮 THE FORGE CORE
# ─────────────────────────────────────────────

class AetherForge:
    """The main orchestration hub for Aether Forge Protocol."""
    
    REGISTRY: Dict[str, Type[NanoExecutor]] = {
        "coingecko": CoinGeckoExecutor,
        "github": GitHubExecutor,
        "weather": WeatherExecutor
    }
    
    TEMPLATES = {
        "coingecko": {"base": "https://api.coingecko.com/api/v3", "auth": None},
        "github": {"base": "https://api.github.com", "auth": "Bearer"},
        "weather": {"base": "https://api.openweathermap.org", "auth": "API_KEY"}
    }

    def __init__(self):
        self.nexus = AetherNexus()
        self.parliament = AgentParliament()
        self.tides = TemporalMemoryTides(self.nexus)

    async def rest(self):
        """Trigger a manual memory rest (Low Tide)."""
        await self.tides.sleep_cycle()

    async def execute(self, intent_data: Dict[str, Any]) -> ForgeResult:
        """The 4-Phase Forge Cycle: Deconstruct -> Synthesize -> Deploy -> Harvest."""
        start_time = time.time()
        service = intent_data.get("service", "unknown").lower()
        
        # 1. Deconstruct & Recall (System 1)
        cached_pattern = self.nexus.recall(service)
        crystallized = cached_pattern is not None
        
        # 2. Synthesize & Parliament
        # In a real scenario, we might spawn multiple agent proposals here.
        # For MVP, we simulate a single high-confidence proposal.
        proposal = AgentProposal(
            agent_id=hashlib.md5(str(time.time()).encode()).hexdigest()[:8],
            action=f"Execute {service} query",
            confidence=0.95 if crystallized else 0.70,
            reasoning="Pattern matches crystallized DNA" if crystallized else "Synthesizing new API bridge"
        )
        
        winning_proposal = await self.parliament.deliberate([proposal])
        
        # 3. Deploy & Execution
        executor_cls = self.REGISTRY.get(service)
        if not executor_cls:
            return ForgeResult(False, None, service, 0, winning_proposal.agent_id, False, f"Unsupported service: {service}")

        executor = executor_cls()
        try:
            data = await executor.execute(intent_data.get("params", {}))
            execution_ms = (time.time() - start_time) * 1000
            
            # 4. Harvest & Engrave
            self.nexus.engrave(service, intent_data.get("params", {}), True)
            
            return ForgeResult(
                success=True,
                data=data,
                service=service,
                execution_ms=execution_ms,
                agent_id=winning_proposal.agent_id,
                dna_crystallized=crystallized
            )
        except Exception as e:
            logger.error(f"Forge Failure: {str(e)}")
            self.nexus.engrave(service, {}, False)
            return ForgeResult(False, None, service, 0, winning_proposal.agent_id, False, str(e))

# ─────────────────────────────────────────────
# 🧬 CORE PROTOCOLS & DATA STRUCTURES
# ─────────────────────────────────────────────
# ... (rest of code) ...

class AetherForge:
    """The main orchestration hub for Aether Forge Protocol."""
    
    REGISTRY: Dict[str, Type[NanoExecutor]] = {
        "coingecko": CoinGeckoExecutor,
        "github": GitHubExecutor,
        "weather": WeatherExecutor
    }
    
    # Static Templates for MVP (Mock Archaeology)
    TEMPLATES = {
        "coingecko": {"base": "https://api.coingecko.com/api/v3", "auth": None},
        "github": {"base": "https://api.github.com", "auth": "Bearer"},
        "weather": {"base": "https://api.openweathermap.org", "auth": "API_KEY"}
    }

    def __init__(self):
        self.nexus = AetherNexus()
        self.stats = {"forged": 0, "ms_saved": 0}

    def _deconstruct(self, intent: str) -> tuple[str, Dict[str, Any]]:
        """Deconstruct intent into Service + Params. Uses logical keyword matching (MVP)."""
        intent = intent.lower()
        if any(w in intent for w in ["price", "bitcoin", "crypto", "eth"]):
            coins = []
            if "btc" in intent or "bitcoin" in intent: coins.append("bitcoin")
            if "eth" in intent or "ethereum" in intent: coins.append("ethereum")
            if not coins: coins = ["bitcoin", "ethereum", "solana"]
            return "coingecko", {"coins": coins}
        
        if any(w in intent for w in ["github", "repo", "code"]):
            return "github", {"query": intent.replace("github", "").strip()}
            
        return "coingecko", {"coins": ["bitcoin"]}

    async def forge(self, intent: str) -> ForgeResult:
        start_time = time.time()
        logger.info(f"Synthesizing Nano-Agent for intent: '{intent}'")
        
        # 1. Deconstruction
        service_name, params = self._deconstruct(intent)
        
        # 2. Nexus Recall (System 1)
        pattern = self.nexus.recall(service_name) or self.TEMPLATES.get(service_name)
        
        if not pattern:
            return ForgeResult(False, None, service_name, 0, "null", False, "Service pattern unavailable.")

        # 3. Agent Synthesis
        agent_id = hashlib.md5(f"{intent}{time.time()}".encode()).hexdigest()[:8]
        agent = NanoAgent(id=agent_id, intent=intent, service=service_name, params=params)
        self.stats["forged"] += 1
        
        # 4. Deployment & Execution
        executor_cls = self.REGISTRY.get(service_name)
        if not executor_cls:
            return ForgeResult(False, None, service_name, 0, agent_id, False, f"No executor registered for {service_name}")
        
        executor = executor_cls()
        try:
            data = await executor.execute(params)
            success = True
            error = None
        except Exception as e:
            logger.error(f"Execution Failure [Agent #{agent_id}]: {e}")
            data = None
            success = False
            error = str(e)

        ms_latency = (time.time() - start_time) * 1000
        
        # 5. Harvesting & Crystallization
        self.nexus.engrave(service_name, pattern, success)
        
        if success:
            self.stats["ms_saved"] += max(0, 15000 - ms_latency) # Baseline vs 15s UI navigation

        logger.info(f"Agent #{agent_id} dissolved. Latency: {ms_latency:.2f}ms. Total Forge Savings: {self.stats['ms_saved']/1000:.1f}s")
        
        return ForgeResult(
            success=success,
            data=data,
            service=service_name,
            execution_ms=ms_latency,
            agent_id=agent_id,
            dna_crystallized=success,
            error=error
        )

# ─────────────────────────────────────────────
# 🧪 DEMO SUITE
# ─────────────────────────────────────────────

async def demo():
    forge = AetherForge()
    print("\n" + " ✨ " * 15)
    print("      AETHER OS: FORGE PROTOCOL DEMO")
    print(" ✨ " * 15)

    # Test Case 1: Crypto
    res = await forge.forge("Check Bitcoin and Ethereum prices")
    print(res.display())

    await asyncio.sleep(1)

    # Test Case 2: GitHub
    res = await forge.forge("Find AetherOS on github")
    print(res.display())

    # Test Case 3: System 1 Trigger
    print("\n[Triggering System 1 Recall]")
    res = await forge.forge("BTC price update")
    print(res.display())

if __name__ == "__main__":
    asyncio.run(demo())
