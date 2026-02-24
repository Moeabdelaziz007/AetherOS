"""AetherOS Nano-Agent Lambda Module.

This module provides the fundamental stateless execution unit for the AetherOS
system. The AetherNanoAgent class implements an ephemeral, coroutine-based agent
lifecycle designed for high-concurrency operations with minimal memory footprint.

The module follows the "spawn-hydrate-execute-dehydrate-dissolve" pattern,
enabling agents to:
    - Spawn with unique identifiers
    - Hydrate state from persistent storage (Cloud Nexus)
    - Execute custom logic with intent and context
    - Dehydrate state back to persistent storage
    - Dissolve to free resources

Key Features:
    - Stateless execution model with ephemeral lifecycle
    - Automatic state hydration and dehydration via Cloud Nexus
    - Zero-friction cleanup and garbage collection
    - High-concurrency support through async/await patterns

Key Classes:
    AetherNanoAgent: The fundamental stateless execution unit.

Key Methods:
    aether_spawn: Main lifecycle method for agent execution.
    _aether_hydrate: Fetches persistent state from Firestore.
    _aether_dehydrate: Persists state changes to Firestore.
    aether_dissolve: Performs cleanup and resource deallocation.

Example:
    >>> async def my_logic(intent, context, state):
    ...     return {"result": "task completed"}
    >>> agent = AetherNanoAgent()
    >>> result = await agent.aether_spawn("test intent", {}, my_logic)
"""

import asyncio
import logging
import uuid
from typing import Any, Dict, Optional, Callable
from agent.aether_forge.cloud_nexus import AetherCloudNexus

logger = logging.getLogger("aether.lambda")

class AetherNanoAgent:
    """The Fundamental Stateless Unit of AetherOS."""

    def __init__(self, agent_id: Optional[str] = None) -> None:
        """Initialize a new Nano-Agent instance.
        
        Args:
            agent_id: Optional unique identifier for this agent. If not provided,
                a UUID-based ID will be generated.
        
        Attributes:
            id: The unique identifier for this agent.
            nexus: Reference to AetherCloudNexus for state persistence.
            _state: Internal state dictionary for this agent's lifecycle.
        """
        self.id = agent_id or f"nano-{uuid.uuid4().short}"
        self.nexus = AetherCloudNexus()
        self._state = {}

    async def aether_spawn(self, intent: str, context: Dict[str, Any], logic: Callable) -> Dict[str, Any]:
        """Spawn the agent and execute its lifecycle.
        
        This method orchestrates the complete agent lifecycle:
        1. Hydration: Load state from persistent storage
        2. Execution: Run the provided logic function
        3. Dehydration: Persist state changes back to storage
        4. Dissolution: Clean up resources
        
        Args:
            intent: The natural language intent describing the task.
            context: Additional context information for the task execution.
            logic: An async callable that takes (intent, context, state)
                and returns the task result.
        
        Returns:
            A dictionary containing:
                - agent_id: The ID of this agent
                - success: Boolean indicating if execution succeeded
                - result: The result from logic execution (if success=True)
                - error: Error message (if success=False)
        
        Example:
            >>> async def my_logic(intent, context, state):
            ...     return {"data": "task completed"}
            >>> agent = AetherNanoAgent()
            >>> result = await agent.aether_spawn("test", {}, my_logic)
            >>> result["success"]
            True
        """
        logger.info(f"🧬 [AetherNanoAgent {self.id}]: Spawning for intent: {intent}")
        
        try:
            # 1. Hydration (Stateless -> Contextual)
            self._state = await self._aether_hydrate(intent)
            
            # 2. Execution (The Cognitive Work)
            result = await logic(intent, context, self._state)
            
            # 3. Dehydration (Consistency Loop)
            await self._aether_dehydrate(self._state)
            
            return {
                "agent_id": self.id,
                "success": True,
                "result": result
            }
        except Exception as e:
            logger.error(f"💥 [AetherNanoAgent {self.id}] Execution Fault: {e}")
            return {"agent_id": self.id, "success": False, "error": str(e)}
        finally:
            await self.aether_dissolve()

    async def _aether_hydrate(self, intent: str) -> Dict[str, Any]:
        """Fetch persistent DNA/State from Firestore.
        
        This method retrieves historical state for this agent from the Cloud Nexus,
        enabling stateful execution despite the agent's stateless architecture.
        In a full implementation, this would use KNN to find relevant
        historical state patterns.
        
        Args:
            intent: The current intent being processed (used for state lookup).
        
        Returns:
            A dictionary containing the fetched state, or an empty dict
            if no previous state exists.
        
        Note:
            This is a private method called internally by aether_spawn.
        """
        # In a real impl, this uses KNN to find relevant historical state
        return await self.nexus.get_agent_context(self.id) or {}

    async def _aether_dehydrate(self, state: Dict[str, Any]) -> None:
        """Persist state changes back to Firestore.
        
        This method saves the agent's final state to the Cloud Nexus,
        ensuring that future executions can benefit from this execution's
        learnings and context.
        
        Args:
            state: The state dictionary to persist to storage.
        
        Note:
            This is a private method called internally by aether_spawn.
        """
        await self.nexus.update_agent_context(self.id, state)

    async def aether_dissolve(self) -> None:
        """Perform zero-friction cleanup of agent resources.
        
        This method cleans up all agent resources, including clearing
        internal state and releasing the Nexus connection. This ensures
        minimal memory footprint for high-concurrency operations.
        
        Note:
            This is called automatically by aether_spawn in a finally block,
            ensuring cleanup even if execution fails.
            
            Garbage collection is triggered at the Parliament level rather
            than per-agent to batch cleanup operations more efficiently.
        """
        logger.info(f"🫧 [AetherNanoAgent {self.id}]: Dissolving into ether.")
        self._state = None
        self.nexus = None
        # Explicitly aid GC (though not strictly necessary for local scopes)
        import gc
        # gc.collect() # Triggered by the Parliament instead to batch cleanup
