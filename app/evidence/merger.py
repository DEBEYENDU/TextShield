from __future__ import annotations

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from .models import EvidenceItem, EvidenceSource
from .confidence import EvidenceConfidence


class EvidenceMerger:
    """Merge multiple evidence items into a unified evidence item.

    Responsibilities:
    - Detect duplicated evidence (same source + same indicator)
    - Resolve conflicts (priority by source reliability)
    - Track evidence origin
    - Calculate source agreement
    - Produce a unified evidence item
    """

    def __init__(self):
        self.confidence_calculator = EvidenceConfidence()

    def merge(self, items: List[EvidenceItem],
              source_reliabilities: Optional[Dict[str, float]] = None) -> EvidenceItem:
        """Merge a list of evidence items into one.

        Args:
            items: List of EvidenceItem to merge.
            source_reliabilities: Dict source_name -> reliability 0-1.

        Returns:
            A unified EvidenceItem representing the merged evidence.
        """
        if not items:
            return EvidenceItem(
                source=EvidenceSource.CUSTOM,
                confidence=0.0,
                weight=0.0,
                summary="No evidence provided",
            )

        if len(items) == 1:
            return items[0]

        # 1) Group by source name
        groups: Dict[str, List[EvidenceItem]] = {}
        for e in items:
            key = e.source.value
            groups.setdefault(key, []).append(e)

        # 2) For each source group, compute merged confidence and weight
        merged_evidences: List[EvidenceItem] = []
        for source_name, group in groups.items():
            total_weight = sum(e.weight for e in group)
            if total_weight == 0:
                avg_conf = sum(e.confidence for e in group) / len(group) if group else 0.0
            else:
                avg_conf = sum(e.confidence * e.weight for e in group) / total_weight

            most_recent = max(group, key=lambda e: e.timestamp.timestamp()) if group else None

            all_artifacts = []
            for e in group:
                all_artifacts.extend(e.supporting_artifacts)

            summaries = [e.summary for e in group if e.summary]
            merged_summary = " ; ".join(summaries) if summaries else ""

            rel = source_reliabilities.get(source_name, 0.7) if source_reliabilities else 0.7

            merged = EvidenceItem(
                source=EvidenceSource(source_name),
                timestamp=most_recent.timestamp if most_recent else datetime.now(timezone.utc),
                confidence=avg_conf,
                weight=total_weight / max(len(group), 1),
                summary=merged_summary,
                raw_evidence=self._combine_raw_evidence(group),
                structured_evidence=self._merge_structured_evidence(group),
                supporting_artifacts=all_artifacts,
                metadata={"merged_from": len(group), "source_reliability": rel},
            )
            merged_evidences.append(merged)

        overall_confidence = self.confidence_calculator.calculate(
            merged_evidences, source_reliabilities=source_reliabilities,
        )

        base = max(merged_evidences, key=lambda e: e.weight if e.weight else 0)
        base.confidence = overall_confidence
        base.weight = overall_confidence

        return base

    def _combine_raw_evidence(self, group: List[EvidenceItem]) -> Any:
        if not group:
            return None
        return max(group, key=lambda e: e.timestamp.timestamp()).raw_evidence

    def _merge_structured_evidence(self, group: List[EvidenceItem]) -> Dict[str, Any]:
        merged: Dict[str, Any] = {}
        sorted_group = sorted(group, key=lambda e: e.timestamp.timestamp(), reverse=True)
        for e in sorted_group:
            for k, v in e.structured_evidence.items():
                if k not in merged:
                    merged[k] = v
        return merged

    def detect_conflicts(self, items: List[EvidenceItem]) -> Dict[str, Any]:
        if not items:
            return {"has_conflicts": False, "conflict_details": {}}

        statuses = []
        for e in items:
            st = e.structured_evidence.get("threat_status") or e.summary.lower()
            statuses.append(st.lower())

        has_conflict = len(set(statuses)) > 1 if statuses else False

        return {
            "has_conflicts": has_conflict,
            "status_distribution": {s: statuses.count(s) for s in set(statuses)},
            "conflict_details": {
                "conflicting_sources": self._conflicting_source_names(items),
            }
        }

    def _conflicting_source_names(self, items: List[EvidenceItem]) -> List[str]:
        statuses = [e.structured_evidence.get("threat_status") for e in items]
        has_malicious = any(s and s.lower() == "malicious" for s in statuses)
        has_benign = any(s and s.lower() == "benign" for s in statuses)
        if has_malicious and has_benign:
            return list(set(e.source.value for e in items))
        return []