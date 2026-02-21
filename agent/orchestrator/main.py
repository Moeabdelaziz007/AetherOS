import asyncio
import json
import websockets
from typing import Any
from .memory_parser import MemoryParser
from .cognitive_router import HyperMindRouter

class AetherCoreOrchestrator:
    """
    The main asynchronous event loop for AuraOS.
    Bridges the Edge Client (Sensory) via WebSockets to the DNA Brain.
    """
    def __init__(self, host: str = "127.0.0.1", port: int = 8000):
        self.host = host
        self.port = port
        self.parser = MemoryParser()
        self.router = HyperMindRouter(self.parser)
        self.is_running = False

    async def boot_sequence(self):
        """Initializes DNA and validates Persona logic."""
        print("🪐 AuraOS: AetherCore Prometheus Booting...")
        dna = self.parser.load_dna()
        print(f"🧬 DNA Sequence Verified: {dna.soul.get('version', 'Unknown')}")
        self.is_running = True

    async def handle_optic_nerve(self, websocket):
        """Processes real-time binary/JSON synaptic bridge signals."""
        async for message in websocket:
            try:
                if isinstance(message, bytes):
                    header = message[0]
                    payload = message[1:]
                    
                    if header == 0x01: # Visual Delta
                        print(f"🖼️ Synaptic: Received Visual Frame ({len(payload)} bytes)")
                        # In production: pass to z-compression encoder
                    elif header == 0x02: # Audio Chunk
                        print(f"🎤 Synaptic: Received Audio Chunk ({len(payload)} bytes)")
                        # In production: stream to Gemini Live PCM
                else:
                    data = json.loads(message)
                    print(f"📂 Synaptic: Received JSON State -> {data.get('type')}")
                    
                    # Routing Logic (Active Inference)
                    mode = await self.router.route_action(data.get("data", {}))
                    response = {
                        "cmd": "EXECUTE" if mode == "SYSTEM_1_REFLEX" else "SWITCH_SYSTEM",
                        "mode": mode
                    }
                    await websocket.send(json.dumps(response))

            except Exception as e:
                print(f"⚠️ Neural Anomaly: {e}")

    async def run_server(self):
        await self.boot_sequence()
        print(f"🛰️ Synaptic Bridge Listening on ws://{self.host}:{self.port}...")
        async with websockets.serve(self.handle_optic_nerve, self.host, self.port):
            await asyncio.Future()  # Run forever

if __name__ == "__main__":
    orchestrator = AetherCoreOrchestrator()
    asyncio.run(orchestrator.run_server())
