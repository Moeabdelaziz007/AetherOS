"""
🧬 Aether Compressor — Semantic Density Engine
=============================================
Implementation of the Strategy Pattern for high-velocity semantic compression.
Bypasses raw data bloat in favor of "Agentic Observations".

"تكثيف المعنى، تقليل الهدر، سرعة الوجود"
(Compressing meaning, reducing waste, speed of existence)
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import google.generativeai as genai
import os

logger = logging.getLogger("🧬 AetherCompressor")

class AetherBaseCompressor(ABC):
    """Abstract Strategy for semantic compression."""
    @abstractmethod
    async def compress(self, content: Any, context_type: str) -> str:
        pass

class AetherFlashCompressor(AetherBaseCompressor):
    """
    Concrete Strategy using Gemini 2.0 Flash for low-latency compression.
    Focuses on 'Observational Extraction'.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("⚠️ No API key for Compressor. Falling back to truncated strings.")
            self.model = None
        else:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-2.0-flash-exp")

    async def compress(self, content: Any, context_type: str) -> str:
        if not self.model or not isinstance(content, str):
            # Fallback: Truncated string representation
            return str(content)[:500] + "..." if len(str(content)) > 500 else str(content)

        prompt = self._build_prompt(content, context_type)
        try:
            # Using low-temp for precision in observation
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config={"temperature": 0.1, "max_output_tokens": 256}
            )
            compressed = response.text.strip()
            logger.info(f"✨ Compressed {context_type} from {len(content)} to {len(compressed)} chars.")
            return compressed
        except Exception as e:
            logger.error(f"❌ Compression failed: {e}")
            return str(content)[:500]

    def _build_prompt(self, content: str, context_type: str) -> str:
        if context_type == "api_result":
            return (
                f"Extract high-density 'Agentic Observations' from this raw API output. "
                f"Ignore schema noise. Focus on data values, trends, and outcomes.\n\n"
                f"Raw Data: {content}\n\nObservation:"
            )
        elif context_type == "agent_response":
            return (
                f"Summarize this agent response into a single, dense semantic observation for long-term memory. "
                f"Keep the core intent and result. Avoid flourishes.\n\n"
                f"Response: {content}\n\nObservation:"
            )
        else:
            return f"Compress this content into a dense observation: {content}"

# Standard Python 3.11 pattern: helper for testing
import asyncio
if __name__ == "__main__":
    async def test():
        compressor = AetherFlashCompressor()
        raw_api = "{ 'bitcoin': { 'usd': 98200, 'usd_24h_change': 2.4 }, 'ethereum': { 'usd': 2800 } }"
        obs = await compressor.compress(raw_api, "api_result")
        print(f"Original: {len(raw_api)} chars")
        print(f"Compressed: {obs}")

    asyncio.run(test())
