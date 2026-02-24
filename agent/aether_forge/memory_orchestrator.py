"""
🧠 Memory Orchestrator — AetherOS
The central nervous system for data persistence and retrieval.
Unifies the 3-tier Memory Trident: Working, Episodic, and Semantic.

"تنسيق الأفكار، حفظ الذاكرة، توحيد الوجود"
(Coordinating thoughts, preserving memory, unifying existence)
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from .memory_tiers import WorkingMemory, EpisodicMemory, SemanticMemory, MemoryEvent
from .compressor import AetherFlashCompressor
from .briefing_manager import AetherBriefingManager

logger = logging.getLogger("🧠 AetherMemory")

class AetherMemoryOrchestrator:
    def __init__(self, project_id: Optional[str] = None):
        self.working = WorkingMemory()
        self.episodic = EpisodicMemory(project_id=project_id)
        self.semantic = SemanticMemory()
        self.compressor = AetherFlashCompressor()
        self.briefing = AetherBriefingManager()
        logger.info("🧠 Aether Memory Orchestrator initialized with Compression & Briefing Node.")

    async def initialize(self):
        """Initializes all memory tiers concurrently."""
        try:
            await asyncio.gather(
                self.working.connect(),
                # Firestore and ChromaDB are initialized synchronously in their __init__
            )
            # Sync Briefing Node on boot
            boot_context = self.briefing.read()
            logger.info("📖 Tier-0 Briefing Node synchronized.")
            logger.info("✨ All memory tiers synchronized and online.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize memory tiers: {e}")

    async def remember(self, event_type: str, content: Any, metadata: Dict[str, Any] = None, compress: bool = True):
        """
        Stores an event in both Episodic (Firestore) and Semantic (ChromaDB) memory.
        Uses Semantic Compressor if compress=True to optimize storage density.
        """
        # OPTIMIZATION: Compress before storage if it's textual and requested
        final_content = content
        if compress and isinstance(content, str) and len(content) > 100:
            final_content = await self.compressor.compress(content, event_type)

        event = MemoryEvent(
            id=None, # Auto-generated
            type=event_type,
            content=final_content,
            metadata=metadata
        )

        # 1. Store in Episodic (Firestore)
        try:
            self.episodic.store_event(event)
        except Exception as e:
            logger.warning(f"⚠️ Episodic store failed: {e}")

        # 2. Store in Semantic (ChromaDB) if the content is textual
        if isinstance(final_content, str):
            try:
                self.semantic.add_knowledge(
                    ids=[f"evt_{int(event.timestamp * 1000)}"],
                    documents=[final_content],
                    metadatas=[metadata or {}]
                )
            except Exception as e:
                logger.warning(f"⚠️ Semantic store failed: {e}")

        # 3. Update Working Memory (Redis)
        try:
            await self.working.set("last_interaction", {
                "type": event_type,
                "timestamp": event.timestamp,
                "summary": str(final_content)[:100]
            }, ttl=3600)
        except Exception as e:
            logger.warning(f"⚠️ Working store failed: {e}")

    async def get_working_context(self, key: str) -> Optional[Any]:
        """Retrieves instant state from Redis."""
        return await self.working.get(key)

    async def recall_recent_episodes(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieves recent history from Firestore."""
        return self.episodic.get_recent(limit=limit)

    async def search_knowledge(self, query: str, limit: int = 3) -> List[str]:
        """Performs a vector search in ChromaDB."""
        results = self.semantic.query(query, n_results=limit)
        return results.get("documents", [[]])[0]

    async def get_comprehensive_context(self, query: str) -> Dict[str, Any]:
        """
        Synthesizes a master context object from all three tiers.
        Useful for injecting into Gemini SYSTEM_PROMPT.
        """
        working_ctx = await self.get_working_context("last_interaction")
        recent_events = await self.recall_recent_episodes(limit=3)
        knowledge = await self.search_knowledge(query)
        tier0 = self.briefing.read()

        return {
            "immediate_state": working_ctx,
            "recent_history": recent_events,
            "relevant_knowledge": knowledge,
            "tier0_briefing": tier0
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    async def test_orchestrator():
        orchestrator = AetherMemoryOrchestrator()
        await orchestrator.initialize()
        
        print("💾 Saving interaction...")
        await orchestrator.remember(
            "interaction", 
            "The user asked to check Bitcoin prices and display a chart.",
            {"mood": "curious"}
        )
        
        print("🔍 Recalling context...")
        ctx = await orchestrator.get_comprehensive_context("Bitcoin price")
        print(f"✅ Master Context: {ctx}")

    asyncio.run(test_orchestrator())
