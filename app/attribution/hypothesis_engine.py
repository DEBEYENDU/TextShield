"""Hypothesis generation for actor attribution."""

from __future__ import annotations
from typing import List, Dict
from datetime import datetime
from .models import Hypothesis, EvidenceItem
from .config import config
from app.core.logging import get_logger

logger = get_logger(__name__)


class HypothesisEngine:
    def __init__(self):
        self._hypotheses: List[Hypothesis] = []

    def generate(self, actor_id: str, campaign_id: str,
                 evidence_items: List[EvidenceItem]) -> Hypothesis:
        if not evidence_items:
            confidence = 0.0
        else:
            avg_conf = sum(e.confidence * e.weight for e in evidence_items) / len(evidence_items)
            confidence = min(1.0, avg_conf)
        hyp = Hypothesis(
            id=f"hyp:{actor_id}:{campaign_id}:{int(datetime.utcnow().timestamp())}",
            actor_id=actor_id,
            campaign_id=campaign_id,
            confidence=confidence,
            evidence=evidence_items,
            reasoning=f"Generated from {len(evidence_items)} evidence items",
            created_at=datetime.utcnow(),
            status="ACTIVE" if confidence >= config.attribution_confidence_threshold else "LOW_CONF"
        )
        self._hypotheses.append(hyp)
        logger.info("Hypothesis generated for %s -> %s confidence %.2f", actor_id, campaign_id, confidence)
        return hyp

    def get_for_actor(self, actor_id: str) -> List[Hypothesis]:
        return [h for h in self._hypotheses if h.actor_id == actor_id]

    def get_for_campaign(self, campaign_id: str) -> List[Hypothesis]:
        return [h for h in self._hypotheses if h.campaign_id == campaign_id]
