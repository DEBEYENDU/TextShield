"""Evidence aggregation for attribution."""

from __future__ import annotations
from typing import List, Dict
from datetime import datetime
from .models import EvidenceItem
from app.core.logging import get_logger
from .config import config

logger = get_logger(__name__)


class EvidenceAggregator:
    def __init__(self):
        self._evidence: List[EvidenceItem] = []

    def add_evidence(self, ev_type: str, source_id: str, target_id: str,
                     confidence: float, weight: float = 1.0,
                     metadata: Dict | None = None) -> EvidenceItem:
        item = EvidenceItem(
            id=f"{ev_type}:{source_id}:{target_id}:{int(datetime.utcnow().timestamp())}",
            type=ev_type,
            source_id=source_id,
            target_id=target_id,
            confidence=confidence,
            weight=weight,
            created_at=datetime.utcnow(),
            metadata=metadata or {}
        )
        self._evidence.append(item)
        return item

    def aggregate_for_target(self, target_id: str) -> Dict[str, float]:
        items = [e for e in self._evidence if e.target_id == target_id]
        scores: Dict[str, float] = {}
        for e in items:
            scores[e.type] = scores.get(e.type, 0.0) + e.confidence * e.weight
        return scores

    def compute_attribution_score(self, target_id: str) -> float:
        scores = self.aggregate_for_target(target_id)
        total = 0.0
        total_weight = 0.0
        mapping = {
            "ttp": config.evidence_weight_ttps,
            "infrastructure": config.evidence_weight_infrastructure,
            "linguistic": config.evidence_weight_linguistic,
            "temporal": config.evidence_weight_temporal,
        }
        for k, w in mapping.items():
            total += scores.get(k, 0.0) * w
            total_weight += w
        return total / total_weight if total_weight else 0.0
