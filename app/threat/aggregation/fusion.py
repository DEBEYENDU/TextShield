from __future__ import annotations

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from .models import ThreatProfile, ThreatSeverity
from .weighting import WeightedScorer
from .confidence import ConfidenceCalculator
from .conflict import ConflictDetector


class EvidenceFuser:
    """Fuse multiple provider evidences into a unified ThreatProfile."""

    def __init__(self,
                 weights: Optional[WeightedScorer] = None,
                 calculator: Optional[ConfidenceCalculator] = None,
                 conflict_detector: Optional[ConflictDetector] = None):
        self.scorer = weights or WeightedScorer()
        self.calculator = calculator or ConfidenceCalculator()
        self.conflict_detector = conflict_detector or ConflictDetector()

    def fuse(
        self,
        evidences: List[dict],
        provider_names: Optional[List[str]] = None,
        provider_reliability: Optional[Dict[str, float]] = None,
        provider_timestamps: Optional[Dict[str, float]] = None,
    ) -> ThreatProfile:
        """Produce a ThreatProfile from the given evidences.

        Args:
            evidences: List of evidence dicts, each with at least:
                - "provider": str
                - "threat_status": "malicious"/"benign"
                - "confidence": float 0-1
                - "indicator": str (the IOC)
                - Optionally "last_updated": epoch or iso
            provider_names: Parallel list of provider names matching evidences.
            provider_reliability: Dict provider_name -> reliability 0-1.
            provider_timestamps: Dict provider_name -> unix epoch of last update.

        Returns:
            ThreatProfile instance.
        """
        provider_names = provider_names or [e.get("provider", "unknown") for e in evidences]

        # 1) Weighted threat score
        threat_score = self.scorer.score_evidence(evidences, provider_names)

        # 2) Confidence
        confidence = self.calculator.calculate(
            evidences, provider_reliability, provider_timestamps,
        )

        # 3) Conflict detection
        conflict_summary = self.conflict_detector.detect(
            evidences,
            provider_reliability,
            ttl_seconds=3600,
            current_time=datetime.now(timezone.utc).timestamp(),
        )

        # 4) Provider agreement ratio
        n = len(evidences)
        agreement_ratio = summary["disagreement_ratio"] if (summary := conflict_summary) else 0.0
        # Actually compute agreement: 1 - disagreement_ratio
        # We'll recompute quickly
        statuses = [e.get("threat_status") for e in evidences]
        malicious = sum(1 for s in statuses if s == "malicious")
        agreement_ratio = (malicious / n) if n else 0.0
        # provider_agreement is 1 - |malicious - benign| / n? We'll use simple ratio of majority
        # We'll set provider_agreement = max(malicious, benign) / n if n else 0
        if n:
            benign = n - malicious
            provider_agreement = max(malicious, benign) / n
        else:
            provider_agreement = 0.0

        # 5) Supporting and conflicting evidence lists
        supporting = [e for e in evidences if e.get("threat_status") == "malicious"]
        conflicting = [e for e in evidences if e.get("threat_status") == "benign"]

        # 6) Evidence count
        evidence_count = len(evidences)

        # 7) Reliability score: average of provider reliabilities
        if provider_reliability:
            rel_vals = list(provider_reliability.values())
            reliability_score = sum(rel_vals) / len(rel_vals) if rel_vals else 0.0
        else:
            # default neutral
            reliability_score = 0.7

        # 8) Severity mapping
        # Simple mapping based on threat_score and confidence
        if threat_score >= 0.7 and confidence >= 0.7:
            severity = ThreatSeverity.CRITICAL
        elif threat_score >= 0.4 and confidence >= 0.5:
            severity = ThreatSeverity.HIGH
        elif threat_score >= 0.2:
            severity = ThreatSeverity.MEDIUM
        else:
            severity = ThreatSeverity.LOW

        # 9) Reasoning summary (human readable)
        reasons = []
        if conflict_summary.get("has_disagreement"):
            reasons.append("provider disagreement detected")
        if conflict_summary.get("low_confidence_providers"):
            reasons.append(f"{len(conflict_summary['low_confidence_providers'])} low-confidence provider(s)")
        if conflict_summary.get("outdated_evidence"):
            reasons.append(f"{len(conflict_summary['outdated_evidence'])} outdated evidence item(s)")
        if threat_score >= 0.7:
            reasons.append("high aggregated threat score")
        elif threat_score < 0.3:
            reasons.append("low aggregated threat score")
        reasoning = " ".join(reasons) if reasons else "No significant threats detected"

        # Build ThreatProfile
        profile = ThreatProfile(
            overall_threat_score=threat_score,
            confidence=confidence,
            severity=severity,
            provider_agreement=provider_agreement,
            supporting_evidence=supporting,
            conflicting_evidence=conflicting,
            evidence_count=evidence_count,
            reliability_score=reliability_score,
            reasoning_summary=reasoning,
            timestamp=datetime.utcnow(),
        )
        return profile