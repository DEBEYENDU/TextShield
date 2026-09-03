from __future__ import annotations

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from .models import EvidenceItem, EvidenceSource


class EvidenceConfidence:
    """Calculate overall confidence for a collection of evidence items.

    Formula considers:
    - Evidence count (more = higher confidence, diminishing returns)
    - Agreement ratio (how many sources agree)
    - Source reliability (historical accuracy weights)
    - Freshness (how recent the evidence is)
    - Completeness (coverage of required fields)

    Returns a confidence score in range [0.0, 1.0], which can be
    multiplied by 100 for a percentage.
    """

    @staticmethod
    def calculate(items: List[EvidenceItem],
                  source_reliabilities: Optional[Dict[str, float]] = None,
                  now: Optional[float] = None) -> float:
        if not items:
            return 0.0

        if now is None:
            now = datetime.now(timezone.utc).timestamp()

        n = len(items)

        # 1) Evidence count factor (diminishing returns)
        count_factor = min(n / 5.0, 1.0)  # 5+ evidence = full count factor

        # 2) Agreement ratio
        # Count how many sources have the most common status/conclusion
        # For simplicity, treat confidence values as agreement signal
        avg_conf = sum(e.confidence for e in items) / n

        # 3) Source reliability weighting
        if source_reliabilities is None:
            # default neutral reliability per source name
            source_reliabilities = {
                e.source.value: 0.7 for e in items
            }
        weighted_conf = 0.0
        weight_total = 0.0
        for e in items:
            rel = source_reliabilities.get(e.source.value, 0.7)
            weighted_conf += e.confidence * rel
            weight_total += rel
        if weight_total == 0:
            weighted_conf = avg_conf
        else:
            weighted_conf /= weight_total

        # 3) Freshness factor
        ages = [now - e.timestamp.timestamp() for e in items]
        max_age = max(ages) if ages else 0
        # half-life 24h = 86400s; exponential decay
        freshness_factor = max(0.0, 1.0 - (max_age / 86400.0))

        # 4) Completeness factor (fraction of required fields present)
        # Required: source, timestamp, confidence, summary, structured_evidence
        required_fields = 5
        present = sum(
            1 for e in items
            if e.source != EvidenceSource.CUSTOM
            and e.timestamp
            and 0.0 <= e.confidence <= 1.0
            and e.summary
            and e.structured_evidence
        )
        completeness_factor = present / (n * required_fields) if n else 0.0

        # Combine with weights (tunable)
        overall = (
            0.35 * count_factor
            + 0.30 * weighted_conf
            + 0.20 * freshness_factor
            + 0.15 * completeness_factor
        )
        return min(max(overall, 0.0), 1.0)