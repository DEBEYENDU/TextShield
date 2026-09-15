"""Intent detection with transformer support.

Provides intent classification hints from semantic understanding.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from app.semantic.config import config
from app.semantic.transformer import similarity_score


_INTENT_PATTERNS = {
    "request_information": "please provide information tell me about",
    "request_action": "please do verify confirm submit",
    "offer_service": "we offer discount free prize claim",
    "threat_warning": "urgent immediate action required now",
    "greeting": "hello hi how are you good morning",
}


@dataclass
class IntentHint:
    intent: str
    confidence: float


class IntentEngine:
    def detect(self, text: str) -> List[IntentHint]:
        if not config.enabled:
            return []
        hints = []
        for intent, pattern in _INTENT_PATTERNS.items():
            try:
                sim = similarity_score(text, pattern)
                if sim > 0.4:
                    hints.append(IntentHint(intent=intent, confidence=round(sim, 3)))
            except Exception:
                continue
        hints.sort(key=lambda h: h.confidence, reverse=True)
        return hints[:4]
