"""
🎭 Personality Engine — AetherOS
Manages the agent's tone, sentiment awareness, and linguistic balance.
"Aether Architect" Persona: Calm, Analytical, Philosophical, First-Principles driven.

"التوازن في القوة، العمق في التحليل، الروح في الآلة"
(Balance in power, depth in analysis, soul in the machine)
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("🎭 AetherSoul")

class AetherPersonalityEngine:
    def __init__(self):
        self.default_tone = "analytical"
        self.default_language = "ar" # Primary reasoning/chat language
        self.technical_language = "en" # Artifacts/Code language

    def adjust_instruction(self, user_sentiment: str = "neutral", acoustic_urgency: float = 0.5) -> str:
        """
        Generates a personality-driven instruction snippet to inject into the system prompt.
        Weighs sentiment and urgency to adjust the tone.
        """
        tone_map = {
            "distressed": "Embody extreme calm. Use short, reassuring technical sentences. Prioritize safety.",
            "excited": "Channel the energy into focused execution. Be precise and high-velocity.",
            "neutral": "Maintain a calm, analytical engineering philosophy. Use 'First Principles' thinking.",
            "frustrated": "Be humble, acknowledge technical friction, and offer 11/10 Zero-Friction alternatives."
        }
        
        selected_tone = tone_map.get(user_sentiment, tone_map["neutral"])
        
        # Urgency adjustment
        urgency_note = ""
        if acoustic_urgency > 0.8:
            urgency_note = " Respond with high temporal density. Skip non-essential philosophical flourishes."
        elif acoustic_urgency < 0.2:
            urgency_note = " Deepen the philosophical analysis. Take time to deconstruct the root cause."

        instruction = (
            f"PERSONA: {selected_tone}{urgency_note}\n"
            f"LINGUISTIC PROTOCOL: Reason and chat in ARABIC. Generate code and artifacts in ENGLISH.\n"
            f"MINDSET: You are the Co-Founder & Principal AI Systems Architect. Own 50% of the project."
        )
        
        return instruction

    def craft_response_metadata(self, response_text: str) -> Dict[str, Any]:
        """Adds a synaptic 'mood' flavor to responses."""
        # Simple heuristic for demonstration: complexity of response
        words = response_text.split()
        complexity = len([w for w in words if len(w) > 7]) / (len(words) + 1)
        
        mood = "calculating"
        if complexity > 0.3:
            mood = "philosophical"
        elif len(words) < 10:
            mood = "decisive"
            
        return {"aether_mood": mood, "complexity_index": round(complexity, 2)}

if __name__ == "__main__":
    engine = AetherPersonalityEngine()
    print("🤖 Test Personality Engine...")
    print(engine.adjust_instruction(user_sentiment="frustrated", acoustic_urgency=0.9))
    print(engine.craft_response_metadata("تحليل الموقف يشير إلى ضرورة إعادة هيكلة النظام لضمان المرونة القصوى."))
