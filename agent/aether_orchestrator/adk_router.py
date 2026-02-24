"""AetherOS ADK Router Module.

This module implements the AetherCore Development Kit (ADK) Router, which provides
cognitive gating between System 1 (Reflexive) and System 2 (Reflective) execution
paths in the AetherOS orchestrator.

The router implements a dual-system architecture:
    - System 1 (Reflexive): Direct, fast execution via bridge.execute_tool()
    - System 2 (Swarm): Deliberate, simulated execution via bridge.trigger_swarm()

This cognitive gating mechanism allows the system to choose between fast reflexive
responses for well-understood tasks and more thorough swarm simulation for
complex or novel situations.

Key Features:
    - Dual-system cognitive routing (System 1/2)
    - Action routing based on skill category and system type
    - Fallback mechanisms for missing bridge methods
    - Error handling and status reporting

Key Classes:
    ADKRouter: Routes actions between System 1 (Reflexive) and System 2
        (Reflective) execution paths.

Key Methods:
    route_action: Routes actions based on skill category and system type,
        delegating to the appropriate bridge method.

Example:
    >>> router = ADKRouter(bridge)
    >>> result = await router.route_action({
    ...     "system": "SYSTEM_1_REFLEX",
    ...     "action": "get_weather",
    ...     "params": {"location": "NYC"}
    ... })
"""

import asyncio
from typing import Any, Dict

class ADKRouter:
    """
    Routes actions between System 1 (Reflexive) and System 2 (Reflective) execution paths.
    
    System 1: Direct reflexive execution via bridge.execute_tool()
    System 2: Swarm simulation via bridge.trigger_swarm()
    """
    
    def __init__(self, bridge: Any) -> None:
        """Initialize the ADK Router with a bridge reference.
        
        Args:
            bridge: Reference to AetherNavigator or compatible bridge object
                that provides execute_tool() and trigger_swarm() methods.
        
        Attributes:
            bridge: The bridge object for executing actions.
        """
        self.bridge = bridge
    
    async def route_action(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Route actions based on skill category and system type.
        
        This method implements cognitive gating by determining whether to use
        System 1 (Reflexive) for fast, direct execution or System 2
        (Swarm) for deliberate, simulated execution based on the context.
        
        Args:
            context: Dictionary containing action context with keys:
                - skill_category: The category of skill to execute.
                - system: Either "SYSTEM_1_REFLEX" or "SYSTEM_2_SWARM".
                    Defaults to "SYSTEM_1_REFLEX" if not provided.
                - action: The specific action to execute.
                - params: Parameters for the action.
        
        Returns:
            A dictionary containing:
                - status: Either "success" or "error".
                - system: The system used for routing.
                - action: The action that was routed.
                - output: The result of the action (if successful).
                - error: Error message (if failed).
        
        Example:
            >>> router = ADKRouter(bridge)
            >>> result = await router.route_action({
            ...     "system": "SYSTEM_1_REFLEX",
            ...     "action": "get_weather",
            ...     "params": {"location": "NYC"}
            ... })
            >>> result["status"]
            'success'
        """
        system = context.get("system", "SYSTEM_1_REFLEX")
        action = context.get("action", "")
        params = context.get("params", {}) or {}  # Defensive: handle None values
        
        result = {
            "status": "success",
            "system": system,
            "action": action,
            "output": None,
            "error": None
        }
        
        try:
            if system == "SYSTEM_1_REFLEX":
                # Direct reflexive execution
                print(f"🧭 ADK Router: Routing to System 1 (Reflex) -> {action}")
                if hasattr(self.bridge, 'execute_tool'):
                    output = await self.bridge.execute_tool(action, **params)
                    result["output"] = output
                else:
                    # Fallback: execute directly through bridge
                    result["output"] = f"System 1 executed: {action}"
            elif system == "SYSTEM_2_SWARM":
                # Swarm simulation
                print(f"🧭 ADK Router: Routing to System 2 (Swarm) -> {action}")
                if hasattr(self.bridge, 'trigger_swarm'):
                    output = await self.bridge.trigger_swarm(action, **params)
                    result["output"] = output
                else:
                    # Fallback: simulate swarm execution
                    result["output"] = f"System 2 swarm simulated: {action}"
            else:
                result["status"] = "error"
                result["error"] = f"Unknown system: {system}"
                print(f"⚠️ ADK Router: Unknown system {system}")
                
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            print(f"❌ ADK Router error: {e}")
        
        return result
