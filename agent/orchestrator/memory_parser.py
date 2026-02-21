import mmap
import os
import yaml
import hashlib
import asyncio
from dataclasses import dataclass
from typing import Any, Optional, Dict

@dataclass
class DNABelief:
    soul: dict[str, Any]
    world: dict[str, Any]
    inference: dict[str, Any]
    version: str

class PersistentMemoryBridge:
    """
    Priority 0 Refactor: Zero-Latency DNA Bridge.
    Keeps mmaps open and provides non-blocking async refreshes.
    """
    def __init__(self, memory_path: str = "agent/memory/"):
        self.memory_path = memory_path
        self._mmaps: Dict[str, mmap.mmap] = {}
        self._file_handles: Dict[str, Any] = {}
        self._hashes: Dict[str, str] = {}
        self.dna_cache: Optional[DNABelief] = None
        self._lock = asyncio.Lock()

    def _get_mmap(self, filename: str) -> mmap.mmap:
        """Returns or creates a persistent mmap for a DNA file."""
        if filename not in self._mmaps:
            path = os.path.join(self.memory_path, filename)
            f = open(path, "r+b")
            mm = mmap.mmap(f.fileno(), 0)
            self._file_handles[filename] = f
            self._mmaps[filename] = mm
        return self._mmaps[filename]

    def _calculate_hash(self, data: bytes) -> str:
        return hashlib.md5(data).hexdigest()

    async def load_dna_async(self, force: bool = False) -> DNABelief:
        """Loads and parses DNA without blocking the event loop."""
        async with self._lock:
            needs_update = False
            raw_contents = {}

            for dna_file in ["SOUL.md", "WORLD.md", "INFERENCE.md"]:
                mm = self._get_mmap(dna_file)
                mm.seek(0)
                content_bytes = mm.read()
                current_hash = self._calculate_hash(content_bytes)

                if force or current_hash != self._hashes.get(dna_file):
                    self._hashes[dna_file] = current_hash
                    raw_contents[dna_file] = content_bytes.decode("utf-8")
                    needs_update = True

            if needs_update:
                # Move blocking YAML parsing to a background thread
                parsed = await asyncio.to_thread(self._parse_blocks, raw_contents)
                
                self.dna_cache = DNABelief(
                    soul=parsed.get("SOUL.md", {}),
                    world=parsed.get("WORLD.md", {}),
                    inference=parsed.get("INFERENCE.md", {}),
                    version=parsed.get("SOUL.md", {}).get("version", "0.0.0")
                )
            
            return self.dna_cache

    def _parse_blocks(self, raw_data: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """Synchronous YAML extractor."""
        results = {}
        for filename, content in raw_data.items():
            if "```yaml" in content:
                block = content.split("```yaml")[1].split("```")[0]
                results[filename] = yaml.safe_load(block) or {}
            else:
                results[filename] = {}
        return results

    def close(self):
        """Cleanup mmaps and file handles on system shutdown."""
        for mm in self._mmaps.values():
            mm.close()
        for f in self._file_handles.values():
            f.close()

if __name__ == "__main__":
    # Test boot
    bridge = PersistentMemoryBridge()
    async def test():
        dna = await bridge.load_dna_async()
        print(f"⚡ Persistent DNA Bridge Active (v{dna.version})")
    asyncio.run(test())
