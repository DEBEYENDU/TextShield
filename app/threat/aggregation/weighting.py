from __future__ import annotations

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class ProviderWeights:
    """Configurable weights per threat intelligence provider.

    Defaults (tunable via configuration or API):
        Google Safe Browsing   0.35
        VirusTotal             0.30
        OpenPhish              0.15
        PhishTank              0.10
        URLhaus                0.10
    """
    weights: Dict[str, float] = field(default_factory=lambda: {
        "google_safe_browsing": 0.35,
        "virustotal": 0.30,
        "openphish": 0.15,
        "phishtank": 0.10,
        "urlhaus": 0.10,
    })

    def set_weight(self, provider_name: str, weight: float) -> None:
        """Set the weight for a specific provider."""
        self.weights[provider_name] = max(0.0, min(1.0, weight))

    def get_weight(self, provider_name: str) -> float:
        """Return the weight for a provider (0 if not configured)."""
        return self.weights.get(provider_name, 0.0)

    def total_weight(self) -> float:
        return sum(self.weights.values())


class WeightedScorer:
    """Score evidence from providers using configured weights.

    Responsibilities:
    - Apply provider weights to each evidence item
    - Compute a weighted threat score
    - Normalise scores to 0.0 - 1.0 range
    """

    def __init__(self, weights: Optional[ProviderWeights] = None):
        self.weights = weights or ProviderWeights()

    def score_evidence(
        self, evidences: List[dict], provider_names: List[str]
    ) -> float:
        """Compute weighted threat score from a list of evidence dicts.

        Each evidence dict should contain at least:
            - "threat_status": "malicious" or "benign"
            - "confidence": float 0-1
            - Optionally "severity": "low"|"medium"|"high"|"critical"
        """
        if not evidences:
            return 0.0

        weighted_sum = 0.0
        weight_total = 0.0
        for ev, provider in zip(evidences, provider_names):
            w = self.weights.get_weight(provider)
            if w <= 0:
                continue
            # Base threat score from status
            status = ev.get("threat_status", "benign")
            base = 1.0 if status == "malicious" else 0.0
            conf = ev.get("confidence", 0.5)
            weighted_sum += w * base * conf
            weight_total += w

        if weight_total == 0:
            return 0.0
        return min(round(weighted_sum / weight_total, 4), 1.0)

    def weights(self) -> Dict[str, float]:
        return dict(self.weights.weights)