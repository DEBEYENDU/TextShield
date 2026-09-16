"""Evidence validator."""

from __future__ import annotations
from .models import Evidence

class EvidenceValidator:
    def validate(self, evidence: Evidence) -> bool:
        return evidence.confidence >= 0.5
