import asyncio
import time
from typing import Any
from .memory_parser import MemoryParser

class HyperMindRouter:
    """
    The Cognitive Nerve Center. 
    Implements Active Inference gating (System 1 vs System 2).
    """
    def __init__(self, parser: MemoryParser):
        self.parser = parser
        self.dna = self.parser.load_dna()
        self.tau = self.dna.inference.get("cognitive_weights", {}).get("surprise_threshold", 0.15)

    async def calculate_free_energy(self, state_context: dict[str, Any]) -> float:
        """
        Mock calculation of Variational Free Energy (F).
        In production: Compare Predicted Belief (WORLD.md) vs Actual Edge Perception.
        """
        # Simulate surprise if context has high entropy or unknown flags
        anomaly_signal = state_context.get("anomaly", 0.0)
        return float(anomaly_signal)

    async def route_action(self, state_context: dict[str, Any]) -> str:
        """
        Decision Function:
        Action = System 1 if F < Tau else System 2
        """
        f_score = await self.calculate_free_energy(state_context)
        
        print(f"🧠 Cognitive Routing: F={f_score:.4f}, Tau={self.tau}")

        if f_score < self.tau:
            return self._execute_system_1()
        else:
            return await self._execute_system_2()

    def _execute_system_1(self) -> str:
        """Reflexive mode: Direct stream to Gemini."""
        return "SYSTEM_1_REFLEX"

    async def _execute_system_2(self) -> str:
        """Reflective mode: Swarm & MCTS."""
        # This would trigger QuantumWeaver (Cloud Run)
        print("🧘 High Free Energy! Engaging System 2 (AlphaMind MCTS)...")
        return "SYSTEM_2_SWARM"
