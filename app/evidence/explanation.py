from __future__ import annotations

from typing import List, Dict, Any
from datetime import datetime, timezone
from .models import EvidenceItem, EvidenceSource


class EvidenceExplanation:
    """Generate human-readable explanations for evidence items and graphs.

    The frontend uses these summaries to show users why a piece of evidence
    was collected, its confidence, and its provenance.
    """

    @staticmethod
    def evidence_summary(evidence: EvidenceItem) -> str:
        """Return a one‑sentence summary of a single evidence item."""
        ts = evidence.timestamp.strftime("%Y-%m-%d %H:%M UTC")
        return (
            f"[{evidence.source.value}] {evidence.summary} "
            f"(confidence: {evidence.confidence:.1%}, collected at {ts})"
        )

    @staticmethod
    def graph_provenance(graph: Any, node_id: str) -> str:
        """Return a provenance chain for a given graph node.

        Useful for the frontend to display "this evidence came from...".
        """
        chain = graph.trace_from(node_id) if hasattr(graph, 'trace_from') else []
        if not chain:
            return "Provenance unknown."
        lines = []
        for step in chain:
            lines.append(
                f"  {step['timestamp'].strftime('%H:%M:%S')} "
                f"({step['source']}) – {step['evidence_id'][:8]}..."
            )
        return "Provenance chain:\n" + "\n".join(lines)

    @staticmethod
    def collection_summary(engine: Any) -> str:
        """Summarise the whole evidence collection from an EvidenceEngine."""
        merged = engine._collected.get("current")
        if not merged:
            return "No evidence collected yet."
        return EvidenceExplanation.evidence_summary(merged)