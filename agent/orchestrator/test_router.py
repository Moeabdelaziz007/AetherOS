import asyncio
import sys
import os

# Add the project root to path
sys.path.append(os.getcwd())

from agent.orchestrator.memory_parser import PersistentMemoryBridge
from agent.orchestrator.cognitive_router import HyperMindRouter

async def main():
    bridge = PersistentMemoryBridge()
    router = HyperMindRouter(bridge)
    
    print("🔬 Testing HyperMindRouter Gating Logic...")
    
    # Test Case 1: Low Anomaly (Reflexive)
    print("\nCase 1: Low Anomaly (Expected outcome: SYSTEM_1_REFLEX)")
    ctx_low = {"anomaly": 0.05, "novelty": 0.1, "goal_alignment": 1.0}
    action1 = await router.route_action(ctx_low)
    print(f"Result: {action1}")
    
    # Test Case 2: High Anomaly (Reflective)
    print("\nCase 2: High Anomaly (Expected outcome: SYSTEM_2_SWARM)")
    ctx_high = {"anomaly": 0.8, "novelty": 0.5, "goal_alignment": 0.5}
    action2 = await router.route_action(ctx_high)
    print(f"Result: {action2}")
    
    # Test Case 3: EFE Calculation
    print("\nCase 3: Calculating EFE (G)...")
    g_score = await router.calculate_efe(ctx_high)
    print(f"EFE (G-Score): {g_score:.4f}")

    bridge.close()

if __name__ == "__main__":
    asyncio.run(main())
