from __future__ import annotations

from typing import List, Dict, Any, Optional
from collections import Counter
from datetime import datetime, timezone


class ConflictDetector:
    """Detect and summarize conflicts among provider evidences.

    Identifies:
    - Provider disagreement (malicious vs benign splits)
    - Conflicting reputations
    - Missing evidence from expected providers
    - Outdated evidence (beyond TTL)
    - Low-confidence providers
    """

    def detect(
        self,
        evidences: List[dict],
        provider_weights: Optional[Dict[str, float]] = None,
        ttl_seconds: int = 3600,
        current_time: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Return a conflict summary dict."""
        if current_time is None:
            current_time = datetime.now(timezone.utc).timestamp()

        n = len(evidences)
        summary: Dict[str, Any] = {
            "has_disagreement": False,
            "disagreement_ratio": 0.0,
            "conflicting_reputations": [],
            "missing_providers": [],
            "outdated_evidence": [],
            "low_confidence_providers": [],
            "conflict_score": 0.0,
        }

        if n == 0:
            return summary

        # 1) Agreement analysis
        statuses = [e.get("threat_status") for e in evidences]
        counts = Counter(statuses)
        malicious_count = counts.get("malicious", 0)
        benign_count = counts.get("benign", 0)
        total = malicious_count + benign_count

        if total > 1 and malicious_count > 0 and benign_count > 0:
            summary["has_disagreement"] = True
            summary["disagreement_ratio"] = malicious_count / total

        # 2) Conflicting reputations list
        # If some say malicious and some benign, record them
        if summary["has_disagreement"]:
            summary["conflicting_reputations"] = [
                {"status": s, "count": c} for s, c in counts.items()
            ]

        # 3) Low-confidence providers
        for ev in evidences:
            conf = ev.get("confidence", 1.0)
            if conf < 0.5:
                summary["low_confidence_providers"].append(
                    {"provider": ev.get("provider", "unknown"), "confidence": conf}
                )

        # 4) Outdated evidence (based on timestamp vs TTL)
        for ev in evidences:
            last_updated = ev.get("last_updated")
            if last_updated:
                age = (current_time - last_updated) if isinstance(last_updated, float) else (
                    current_time - datetime.fromisoformat(last_updated).timestamp()
                )
                if age > ttl_seconds:
                    summary["outdated_evidence"].append(
                        {"provider": ev.get("provider", "unknown"), "age_seconds": int(age)}
                    )

        # 5) Missing providers (if we expect certain ones and they're absent)
        # For now, placeholder: can be extended with expected set.
        summary["missing_providers"] = []

        # 6) Conflict score: weighted sum of disagreement + low confidence + outdated
        disc = summary["disagreement_ratio"]
        lc = len(summary["low_confidence_providers"]) / n if n else 0
        out = len(summary["outdated_evidence"]) / n if n else 0
        summary["conflict_score"] = round(min(disc * 0.5 + lc * 0.3 + out * 0.2, 1.0), 4)

        return summary