"""
🧬 Memory Tiers — AetherOS
The "Memory Trident" implementation.

1. WorkingMemory  (Redis)     : Instant contextual state (UI, current intent).
2. EpisodicMemory (Firestore) : Sequential events and conversation history.
3. SemanticMemory (ChromaDB)  : Vectorized knowledge and RAG facts.

"تذكر الماضي، عش الحاضر، خطط للمستقبل"
(Remember the past, live the present, plan for the future)
"""

import os
import time
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict

import redis.asyncio as redis
from google.cloud import firestore
import chromadb
from chromadb.config import Settings

# Logging setup
logger = logging.getLogger("📊 AetherTelemetry")

@dataclass
class MemoryEvent:
    id: str
    type: str  # e.g., "interaction", "ui_event", "vision_insight"
    content: Any
    timestamp: float = time.time()
    metadata: Dict[str, Any] = None

    def to_dict(self):
        return asdict(self)

class WorkingMemory:
    """Tier 1: Fast, ephemeral state (Redis)"""
    def __init__(self, host="localhost", port=6379, db=0):
        self._url = f"redis://{host}:{port}/{db}"
        self._client: Optional[redis.Redis] = None

    async def connect(self):
        if not self._client:
            self._client = redis.from_url(self._url, decode_responses=True)
            logger.info(f"⚡ Working Memory (Redis) connected at {self._url}")

    async def set(self, key: str, value: Any, ttl: int = 3600):
        await self.connect()
        val_str = json.dumps(value)
        await self._client.set(key, val_str, ex=ttl)

    async def get(self, key: str) -> Optional[Any]:
        await self.connect()
        val = await self._client.get(key)
        return json.loads(val) if val else None

    async def delete(self, key: str):
        await self.connect()
        await self._client.delete(key)

class EpisodicMemory:
    """Tier 2: Historical events (Firestore)"""
    def __init__(self, project_id: Optional[str] = None):
        self.db = firestore.Client(project=project_id)
        self.collection = self.db.collection("aether_episodes")
        logger.info(f"📖 Episodic Memory (Firestore) initialized")

    def store_event(self, event: MemoryEvent):
        """Stores a memory event in Firestore"""
        doc_id = event.id or f"evt_{int(event.timestamp * 1000)}"
        self.collection.document(doc_id).set(event.to_dict())
        logger.debug(f"💾 Event stored: {event.type} (id={doc_id})")

    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves most recent events"""
        docs = self.collection.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit).stream()
        return [doc.to_dict() for doc in docs]

class SemanticMemory:
    """Tier 3: Long-term vectorized knowledge (ChromaDB)"""
    def __init__(self, persist_directory="./.aether_memory/semantic"):
        os.makedirs(persist_directory, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(name="aether_knowledge")
        logger.info(f"🧬 Semantic Memory (ChromaDB) initialized at {persist_directory}")

    def add_knowledge(self, ids: List[str], documents: List[str], metadatas: Optional[List[Dict]] = None):
        """Adds vectorized knowledge to the store"""
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        logger.info(f"🧠 Knowledge ingested: {len(ids)} items added to semantic store")

    def query(self, query_text: str, n_results: int = 3) -> Dict[str, Any]:
        """Queries the semantic memory for relevant facts"""
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        return results

# Integration Test logic
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
    
    async def main():
        print("🚀 Testing Memory Trident Tiers...")
        
        # 1. Working Memory
        wm = WorkingMemory()
        await wm.set("test_key", {"status": "active", "lvl": 99})
        val = await wm.get("test_key")
        print(f"✅ Working Memory: {val}")
        
        # 2. Episodic Memory (Simulated if credentials missing, but here we assume setup)
        try:
            em = EpisodicMemory()
            event = MemoryEvent(id="test_evt_1", type="interaction", content="User said hi")
            em.store_event(event)
            print(f"✅ Episodic Memory: Event stored")
        except Exception as e:
            print(f"⚠️ Episodic Memory Error (likely GCP credentials): {e}")

        # 3. Semantic Memory
        sm = SemanticMemory()
        sm.add_knowledge(["k1"], ["AetherOS is a voice-native sovereign OS."], [{"source": "manual"}])
        res = sm.query("What is AetherOS?")
        print(f"✅ Semantic Memory: {res['documents'][0]}")

    asyncio.run(main())
