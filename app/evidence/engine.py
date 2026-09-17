from __future__ import annotations

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from .models import EvidenceItem, EvidenceSource
from .registry import get_registry, register_evidence_source
from .validator import EvidenceValidator
from .confidence import EvidenceConfidence
from .merger import EvidenceMerger
from .graph import EvidenceGraph


class EvidenceEngine:
    """Orchestrates evidence collection from all registered subsystems.

    The Decision Engine should only ever interact with this engine –
    it does NOT call ML, LLM, RAG, threat providers, or rules directly.
    """

    def __init__(self):
        self.registry = get_registry()
        self.validator = EvidenceValidator()
        self.merger = EvidenceMerger()
        self.graph = EvidenceGraph()
        self._collected: Dict[str, EvidenceItem] = {}  # analysis_id -> root evidence

    def collect(self, analysis_id: str, force: bool = False) -> EvidenceItem:
        """Collect evidence from all registered sources for a given analysis.

        Args:
            analysis_id: Unique identifier for this analysis/run.
            force: If True, re‑collect even if evidence already exists.

        Returns:
            The root EvidenceItem summarising the collection.
        """
        if not force and self._collected.get(analysis_id):
            return self._collected[analysis_id]

        # gather items from all registered sources
        sources = self.registry.list_sources()
        collected: List[EvidenceItem] = []

        for src_name in sources:
            source = self.registry.get(src_name)
            if source is None:
                continue
            # each source should have been registered with a factory;
            # for now we create a minimal EvidenceItem from registry metadata
            # in a full integration each subsystem would call engine.collect_source(...)
            item = EvidenceItem(
                source=source,
                timestamp=datetime.now(timezone.utc),
                confidence=0.5,
                weight=1.0,
                summary=f"Evidence from {src_name}",
                raw_evidence={},
                structured_evidence={},
                metadata={"registry_name": src_name},
            )
            collected.append(item)

        # validate each item
        validation_errors = EvidenceValidator.bulk_validate(collected)
        # store errors in metadata for debugging
        for item in collected:
            item.metadata["validation_errors"] = validation_errors.get(item.evidence_id, [])

        # build initial graph nodes for each item
        for item in collected:
            node_id = item.evidence_id
            self.graph.add_node(node_id, item, f"evidence_{src_name}")

        # merge merged evidence
        merged = self.merger.merge(collected)

        # add merged node
        merged_node_id = merged.evidence_id
        self.graph.add_node(merged_node_id, merged, "evidence_merged")

        # connect merged node to source nodes
        for item in collected:
            self.graph.add_link(item.evidence_id, merged_node_id)

        # compute overall confidence
        overall_conf = EvidenceConfidence.calculate(collected)
        merged.confidence = overall_conf
        merged.weight = overall_conf

        # store
        self._collected[analysis_id] = merged
        return merged

    def get_evidence(self, analysis_id: str) -> Optional[EvidenceItem]:
        return self._collected.get(analysis_id)

    def get_graph(self, analysis_id: str) -> Optional[EvidenceGraph]:
        # return a copy or the relevant subgraph
        # for simplicity return the global graph (in production would filter)
        return self.graph

    def explain(self, analysis_id: str) -> str:
        """Generate human-readable explanation of the evidence graph.

        The frontend can display this to users.
        """
        merged = self._collected.get(analysis_id)
        if not merged:
            return "No evidence collected for this analysis."

        # simple narrative
        parts = []
        parts.append(f"Evidence collected from {len(merged.supporting_artifacts) or 'multiple'} sources.")
        parts.append(f"Overall confidence: {merged.confidence:.1%}.")
        if merged.reasoning_summary if hasattr(merged, 'reasoning_summary') else None:
            parts.append(f"Reasoning: {merged.reasoning_summary}")
        # list sources
        sources = set(e.source.value for e in [merged] if hasattr(e, 'source')) or []
        parts.append(f"Sources: {', '.join(sources)}.")
        return " ".join(parts)