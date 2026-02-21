import mmap
import os
import yaml
from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class DNABelief:
    soul: dict[str, Any]
    world: dict[str, Any]
    inference: dict[str, Any]

class MemoryParser:
    """
    Zero-Latency DNA Parser using Memory-Mapped Files.
    Designed for AetherCore's prompt-speed inference.
    """
    def __init__(self, memory_path: str = "agent/memory/"):
        self.memory_path = memory_path
        self.dna_cache: Optional[DNABelief] = None

    def _read_file_fast(self, filename: str) -> str:
        """Reads file using mmap for kernel-level speed."""
        path = os.path.join(self.memory_path, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"DNA File {filename} not found.")

        with open(path, "r+b") as f:
            # Memory map the file
            mm = mmap.mmap(f.fileno(), 0)
            content = mm.read().decode("utf-8")
            mm.close()
            return content

    def _extract_yaml(self, content: str) -> dict[str, Any]:
        """Extracts YAML frontmatter/blocks from the Markdown DNA."""
        try:
            # Simple extractor for YAML code blocks or frontmatter
            if "```yaml" in content:
                block = content.split("```yaml")[1].split("```")[0]
                return yaml.safe_load(block) or {}
            return {}
        except Exception as e:
            print(f"Error parsing DNA schema: {e}")
            return {}

    def load_dna(self) -> DNABelief:
        """Synchronizes DNA files into high-speed memory objects."""
        soul_raw = self._read_file_fast("SOUL.md")
        world_raw = self._read_file_fast("WORLD.md")
        inference_raw = self._read_file_fast("INFERENCE.md")

        self.dna_cache = DNABelief(
            soul=self._extract_yaml(soul_raw),
            world=self._extract_yaml(world_raw),
            inference=self._extract_yaml(inference_raw)
        )
        return self.dna_cache

    def get_inference_weights(self) -> dict[str, float]:
        if not self.dna_cache:
            self.load_dna()
        return self.dna_cache.inference.get("cognitive_weights", {})

if __name__ == "__main__":
    parser = MemoryParser()
    dna = parser.load_dna()
    print(f"AetherCore DNA Loaded. Soul Version: {dna.soul.get('version')}")
