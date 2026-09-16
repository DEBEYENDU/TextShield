"""LLM/Agent assistance with safety."""

from __future__ import annotations
from .models import Evidence

class ResearchLLMAgent:
    def assist(self, evidences: list[Evidence]) -> dict:
        # Simplified: return summary hint
        if not evidences:
            return {"hypothesis": "No data", "confidence": 0.0}
        return {"hypothesis": "Possible malicious activity", "confidence": 0.5, "source": "llm-assisted"}
