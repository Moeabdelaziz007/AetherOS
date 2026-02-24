"""
📖 Aether Briefing Manager — Tier-0 Autobiography
================================================
Manages the 'Cold Core' memory node (.aether/MEMORY.md).
Uses Atomic Persistence to ensure zero data corruption.

"سيرة الأثير، الحقيقة المطلقة، الذاكرة التي لا تفنى"
(Aether's biography, the absolute truth, the undying memory)
"""

import os
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("📖 AetherBriefing")

class AetherBriefingManager:
    """
    Manages Tier-0 context: a local markdown file that acts as the agent's autobiography.
    """
    def __init__(self, memory_path: str = ".aether/MEMORY.md"):
        self.path = Path(memory_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.path.exists():
            self._initialize_autobiography()

    def _initialize_autobiography(self):
        """Creates the initial template for the Briefing Node."""
        initial_content = (
            "# 🧠 AetherOS: Tier-0 Core Memory\n\n"
            "## 🌌 Identity\n"
            "Name: AetherOS\n"
            "Status: Sovereign\n"
            "Philosophy: From nothing, Aether creates.\n\n"
            "## 📍 Active Mandate\n"
            "Winning the Gemini Live Agent Challenge 2026.\n\n"
            "## 🕰️ Last Session Summary\n"
            "Initializing memory infrastructure...\n"
        )
        self.overwrite(initial_content)

    def overwrite(self, content: str):
        """
        Atomically overwrites the briefing node content.
        Pattern: Create temp file -> Write -> Atomic Rename.
        """
        temp_fd, temp_path = tempfile.mkstemp(dir=self.path.parent, text=True)
        try:
            with os.fdopen(temp_fd, 'w') as f:
                f.write(content)
            # Atomic swap
            os.replace(temp_path, self.path)
            logger.info(f"💾 Briefing Node updated atomically: {self.path.name}")
        except Exception as e:
            logger.error(f"❌ Failed to update Briefing Node: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def read(self) -> str:
        """Reads the current Briefing Node state."""
        try:
            return self.path.read_text()
        except Exception as e:
            logger.error(f"❌ Failed to read Briefing Node: {e}")
            return "Context Unavailable."

    def update_session_summary(self, summary: str):
        """
        Updates only the session summary section while preserving identity.
        """
        content = self.read()
        lines = content.split('\n')
        new_lines = []
        in_summary_section = False
        
        for line in lines:
            if line.startswith("## 🕰️ Last Session Summary"):
                in_summary_section = True
                new_lines.append(line)
                new_lines.append(f"- {summary}")
                continue
            
            if in_summary_section and line.startswith("##"):
                in_summary_section = False
                
            if not in_summary_section:
                new_lines.append(line)
        
        self.overwrite('\n'.join(new_lines))

    def setup_sentinel(self):
        """
        Registers signal handlers to capture the terminal state on exit.
        Pattern: Session Sentinel.
        """
        import signal
        import sys

        def handle_termination(signum, frame):
            logger.warning(f"🛑 Termination signal ({signum}) received. Engraving final memories...")
            self.update_session_summary("Session terminated via signal. Tasks flushed to cold core.")
            sys.exit(0)

        signal.signal(signal.SIGINT, handle_termination)
        signal.signal(signal.SIGTERM, handle_termination)
        logger.info("🛡️ Session Sentinel active. Awaiting inevitable silence.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    mgr = AetherBriefingManager("test_memory.md")
    mgr.setup_sentinel()
    mgr.update_session_summary("Phase 3.5: Semantic Compression implemented.")
    print(mgr.read())
    # Keep alive for manual signal test if needed, or just clean up
    os.remove("test_memory.md")
