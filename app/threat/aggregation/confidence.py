from __future__ import annotations

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone


class ConfidenceCalculator:
    """Calculate aggregated confidence from multiple provider evidences.

    Formula considers:
    - Number of providers participating
    - Agreement ratio (how many say malicious vs benign)
    - Evidence quality (confidence values)
    - Evidence freshness (last_updated age)
    - Provider reliability (historical accuracy)
    - Stability (variance across rounds)
    """

    def __init__(self):
        pass

    def calculate(
        self,
        evidences: List[dict],
        provider_reliability: Optional[Dict[str, float]] = None,
        provider_timestamps: Optional[Dict[str, float]] = None,
    ) -> float:
        """Return confidence score in range [0.0, 1.0].

        Args:
            evidences: List of evidence dicts from each provider.
            provider_reliability: Dict provider_name -> reliability 0-1 (optional).
            provider_timestamps: Dict provider_name -> unix epoch of last update (optional).

        Returns:
            float in [0.0, 1.0] representing confidence.
        """
        if not evidences:
            return 0.0

        n = len(evidences)

        # 1) Agreement ratio: count malicious vs benign
        malicious = sum(1 for e in evidences if e.get("threat_status") == "malicious")
        agreement_ratio = malicious / n if n else 0.0

        # 2) Average confidence
        avg_conf = sum(e.get("confidence", 0.5) for e in evidences) / n

        # 3) Provider reliability weight
        rel = {}
        if provider_reliability:
            rel = provider_reliability
        else:
            # default neutral reliability
            rel = {e.get("provider", "unknown"): 0.7 for e in evidences}

        # Weighted agreement
        weighted_agreement = 0.0
        for i, ev in enumerate(evidences):
            provider = ev.get("provider", "unknown")
            r = rel.get(provider, 0.7)
            weighted_agreement += r * ev.get("confidence", 0.5)
        weighted_agreement /= n if n else 1

        # 4) Freshness factor
        freshness = 1.0
        if provider_timestamps:
            now = datetime.now(timezone.utc).timestamp()
            ages = [now - provider_timestamps.get(p, now) for p in (ev.get("provider", "unknown") for ev in evidences)]
            max_age = max(ages) if ages else 0
            # Decay over 24h half-life
            freshness = max(0.0, 1.0 - (max_age / 86400.0))

        # 5) Stability: count distinct opinions; less variance -> higher stability
        # Simple proxy: if all say malicious or all benign -> stable
        unique_statuses = len(set(e.get("threat_status") for e in evidences))
        stability = 1.0 if unique_statuses <= 1 else 0.5

        # Combine with equal weights (can be tuned)
        confidence = (
            0.4 * agreement_ratio
            + 0.3 * avg_conf
            + 0.15 * weighted_agreement
            + 0.1 * freshness
            + 0.05 * stability
        )
        return round(min(max(confidence, 0.0), 1.0), 4)