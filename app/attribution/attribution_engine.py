"""Main attribution engine."""

from __future__ import annotations
from typing import List, Dict
from datetime import datetime
from .models import AttributionResult, Hypothesis
from .actor_profile import ActorProfiler
from .infrastructure_intel import InfrastructureIntel
from .evidence_aggregator import EvidenceAggregator
from .hypothesis_engine import HypothesisEngine
from app.core.logging import get_logger

logger = get_logger(__name__)


class AttributionEngine:
    def __init__(self):
        self.profiler = ActorProfiler()
        self.infra = InfrastructureIntel()
        self.evidence = EvidenceAggregator()
        self.hypothesis = HypothesisEngine()

    def analyze_message(self, message_id: str, text: str,
                        campaign_id: str | None = None) -> AttributionResult:
        nodes = self.infra.ingest_message(message_id, text)
        # Simple heuristic: create a generic actor hypothesis if infrastructure shared
        hypotheses: List[Hypothesis] = []
        for node in nodes:
            # link node to existing actors
            for actor_id in node.associated_actors:
                ev = self.evidence.add_evidence(
                    ev_type="infrastructure",
                    source_id=node.id,
                    target_id=actor_id,
                    confidence=0.6,
                    weight=1.0
                )
                # generate hypothesis if campaign provided
                if campaign_id:
                    hyp = self.hypothesis.generate(actor_id, campaign_id, [ev])
                    hypotheses.append(hyp)
        # If no actors, create placeholder
        if not hypotheses and nodes:
            actor_id = f"actor:auto:{message_id}"
            profile = self.profiler.create_profile(actor_id, "Auto Actor", ["UNKNOWN"])
            for node in nodes:
                self.infra.link_to_actor(node.id, actor_id)
                ev = self.evidence.add_evidence(
                    "infrastructure", node.id, actor_id, 0.5, 1.0
                )
                if campaign_id:
                    hyp = self.hypothesis.generate(actor_id, campaign_id, [ev])
                    hypotheses.append(hyp)
        confidence = max([h.confidence for h in hypotheses], default=0.0)
        result = AttributionResult(
            message_id=message_id,
            actor_hypotheses=hypotheses,
            infrastructure_links=nodes,
            confidence=confidence,
            explanation=f"Attribution based on {len(nodes)} infrastructure nodes"
        )
        logger.info("Attribution analysis completed for %s confidence %.2f", message_id, confidence)
        return result
