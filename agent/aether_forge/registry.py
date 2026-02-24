"""
🧬 Aether Superpower Registry — Modular Skill Engine
===================================================
Principal Systems Architect Implementation: Factory + Command Patterns.
Ensures zero-friction skill injection and high-fidelity execution.

"تحرير القوة، تنميط القدرة، سيادة الوجود"
(Liberating power, modularizing ability, sovereignty of existence)
"""

import json
import importlib
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from pathlib import Path

logger = logging.getLogger("🧬 AetherRegistry")

class AetherSuperpower(ABC):
    """
    Abstract Base Class for all AetherOS Superpowers (Command Pattern).
    Every superpower must implement the 'execute' method.
    """
    def __init__(self, context: Optional[Dict[str, Any]] = None):
        self.context = context or {}

    @abstractmethod
    async def execute(self, args: Dict[str, Any]) -> Any:
        """Execute the core logic of the superpower."""
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """Returns standard metadata for semantic recording."""
        return {
            "class": self.__class__.__name__,
            "module": self.__module__
        }

class AetherSuperpowerRegistry:
    """
    Singleton Registry that manages the lifecycle of Superpowers (Factory Pattern).
    Loads skill manifests and instantiates executors on-demand.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AetherSuperpowerRegistry, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self.manifest_path = Path(__file__).parent / "superpowers.json"
        self.superpowers: Dict[str, Dict[str, Any]] = {}
        self._executors_cache: Dict[str, AetherSuperpower] = {}
        self._load_manifest()
        self._initialized = True
        logger.info(f"✨ Superpower Registry initialized with {len(self.superpowers)} capabilities.")

    def _load_manifest(self):
        """Loads and validates the superpowers.json manifest."""
        try:
            if not self.manifest_path.exists():
                logger.warning(f"⚠️ Manifest not found at {self.manifest_path}. Starting empty.")
                return

            with open(self.manifest_path, 'r') as f:
                data = json.load(f)
                for entry in data:
                    self.superpowers[entry['id']] = entry
        except Exception as e:
            logger.error(f"❌ Failed to load manifest: {e}")

    def get_tool_declarations(self) -> List[Dict[str, Any]]:
        """
        Generates the standard tool declaration format for Gemini Live.
        Translates our manifest schema to Google GenAI format.
        """
        declarations = []
        for sp_id, data in self.superpowers.items():
            declarations.append({
                "name": sp_id.replace('.', '_'), # Replace dots for function compatibility
                "description": data['description'],
                "parameters": data['parameters']
            })
        return declarations

    def get_executor(self, superpower_id: str, context: Optional[Dict[str, Any]] = None) -> Optional[AetherSuperpower]:
        """
        Dynamic Factory: Instantiates and caches the executor class based on manifest ID.
        Injects the provided context (e.g., HTTP clients, DB handles).
        """
        # Normalize ID (in case dots were replaced)
        normalized_id = superpower_id.replace('_', '.')
        if normalized_id not in self.superpowers:
            # Try raw ID if normalized failed
            normalized_id = superpower_id 
            if normalized_id not in self.superpowers:
                logger.error(f"❌ Superpower '{superpower_id}' not found in registry.")
                return None

        # Even if cached, we might want to update context? 
        # For now, we cache the instance but executors use self.context.
        if normalized_id in self._executors_cache:
            executor = self._executors_cache[normalized_id]
            if context:
                executor.context.update(context)
            return executor

        data = self.superpowers[normalized_id]
        executor_path = data['executor_path']
        
        try:
            module_name, class_name = executor_path.rsplit('.', 1)
            module = importlib.import_module(module_name)
            executor_class: Type[AetherSuperpower] = getattr(module, class_name)
            
            # Instantiate with context and cache
            executor = executor_class(context=context)
            self._executors_cache[normalized_id] = executor
            logger.info(f"🚀 Loaded executor for '{normalized_id}': {class_name}")
            return executor
        except Exception as e:
            logger.error(f"❌ Failed to load executor for '{normalized_id}': {e}")
            return None

    def register_superpower(self, superpower_manifest: Dict[str, Any]):
        """Dynamically adds a new superpower to the registry at runtime."""
        sp_id = superpower_manifest.get('id')
        if sp_id:
            self.superpowers[sp_id] = superpower_manifest
            logger.info(f"🧬 Runtime Registration: Superpower '{sp_id}' added.")

# Verification logic for development
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    reg = AetherSuperpowerRegistry()
    print(json.dumps(reg.get_tool_declarations(), indent=2))
