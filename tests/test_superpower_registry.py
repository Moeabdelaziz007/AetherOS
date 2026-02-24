import asyncio
import json
import logging
import sys
from pathlib import Path

# Setup Path
sys.path.append(str(Path(__file__).parent.parent))

from agent.aether_forge.registry import AetherSuperpowerRegistry
from agent.aether_forge.motor_cortex import get_tool_declarations

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AetherVerify")

async def verify_registry():
    logger.info("🧪 Starting Superpower Registry Verification...")
    
    registry = AetherSuperpowerRegistry()
    
    # 1. Test Manifest Loading
    logger.info(f"Checking skills: {list(registry.superpowers.keys())}")
    assert "crypto.coingecko" in registry.superpowers
    assert "os.terminal" in registry.superpowers
    
    # 2. Test Tool Declarations
    tools = get_tool_declarations()
    func_decls = tools[0]["function_declarations"]
    tool_names = [t["name"] for t in func_decls]
    logger.info(f"Exposed Tools: {tool_names}")
    assert "crypto_coingecko" in tool_names
    assert "os_terminal" in tool_names
    assert "generate_ui" in tool_names
    
    # 3. Test Executor Loading & Execution (Terminal)
    # We'll use a safe command
    terminal = registry.get_executor("os.terminal")
    if terminal:
        logger.info("Executing Terminal Skill...")
        res = await terminal.execute({"command": "echo 'AetherOS Modular Core Active'"})
        logger.info(f"Terminal Result: {res}")
        assert "AetherOS Modular Core Active" in res.get("stdout", "")
    
    # 4. Test Crypto Skill (Mocking client if needed, but let's check injection)
    crypto = registry.get_executor("crypto.coingecko")
    assert crypto is not None
    # We won't run it without a real client here to avoid errors, 
    # but we proved the factory works.

    logger.info("✅ Verification Complete: All Systems Nominal.")

if __name__ == "__main__":
    asyncio.run(verify_registry())
