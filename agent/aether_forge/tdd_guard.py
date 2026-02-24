import os
import logging
from typing import Dict, Any

logger = logging.getLogger("aether.guard")

class AetherTDDGuard:
    """
    Quality Sentinel: Blocks non-tested evolutionary patches.
    Ensures that every code mutation proposed by AetherEvolve includes verification logic.
    """

    @staticmethod
    def verify_patch_quality(patch_data: Dict[str, Any]) -> bool:
        """
        Analyzes a proposed code patch for test coverage.
        
        A valid patch MUST:
        1. Contain at least one 'assert' statement OR
        2. Modify/Create a file in the 'tests/' directory.
        """
        code_content = patch_data.get("code", "")
        target_file = patch_data.get("file", "")
        
        # 1. Check for explicit tests
        if "tests/" in target_file:
            logger.info(f"✅ TDD Guard: Test file modification detected for '{target_file}'.")
            return True
            
        # 2. Check for inline assertions/guards if it's a logic patch
        if "assert " in code_content:
            logger.info(f"✅ TDD Guard: Inline assertions detected in patch.")
            return True
            
        logger.warning(f"❌ TDD Guard Violation: Patch for '{target_file}' lacks verification logic.")
        return False

class DesignSentinel:
    """
    Enforces specification standards for new superpowers.
    """
    
    @staticmethod
    def verify_specification(executor_path: str) -> bool:
        """
        Checks if a superpower has a corresponding SPEC.md in its directory.
        """
        executor_dir = os.path.dirname(executor_path)
        spec_path = os.path.join(executor_dir, "SPEC.md")
        
        if os.path.exists(spec_path):
            logger.info(f"✅ Design Sentinel: SPEC.md found for executor at '{executor_path}'.")
            return True
            
        logger.error(f"❌ Design Sentinel Error: Missing SPEC.md for executor at '{executor_path}'.")
        return False
