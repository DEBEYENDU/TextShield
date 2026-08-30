from __future__ import annotations

from typing import List, Dict, Any, Optional
from datetime import datetime

from .models import ThreatProfile
from .fusion import EvidenceFuser


class AggregationEngine:
    """Engine that aggregates evidence from multiple threat intelligence
    providers into a unified ThreatProfile.

    The engine is provider‑independent: it only needs evidences conforming
    to the internal ThreatEvidence schema (or a dict with the same keys).
    """

    def __init__(self,
                 weights: Optional[Any] = None,
                 confidence_calc: Optional[Any] = None,
                 conflict_detector: Optional[Any] = None):
        self.fuser = EvidenceFuser(
            weights=weights,
            calculator=confidence_calc,
            conflict_detector=conflict_detector,
        )

    def aggregate(self,
                  evidences: List[dict],
                  provider_names: Optional[List[str]] = None,
                  provider_reliability: Optional[dict] = None,
                  provider_timestamps: Optional[dict] = None) -> ThreatProfile:
        """Aggregate the given evidences and return a ThreatProfile.

        Args:
            evidences: List of evidence dicts as produced by threat providers.
            provider_names: Optional parallel list of provider names.
            provider_reliability: Optional dict provider_name -> reliability 0‑1.
            provider_timestamps: Optional dict provider_name -> unix epoch.

        Returns:
            ThreatProfile with overall score, confidence, severity, etc.
        """
        return self.fuser.fuse(
            evidences=evidences,
            provider_names=provider_names,
            provider_reliability=provider_reliability,
            provider_timestamps=provider_timestamps,
        )

    def aggregate_from_indicators(self,
                                  indicators: List[Any],  # List of ThreatIndicator or dict
                                  provider_names: Optional[List[str]] = None) -> ThreatProfile:
        """Convert a list of ThreatIndicator objects (or dicts) into evidences
        and aggregate them.

        Each indicator may have attributes: indicator, indicator_type,
        detection_status, confidence, severity, source, explanation, ttl,
        metadata.  Missing keys default to safe values.
        """
        evidences = []
        for ind in indicators:
            if isinstance(ind, dict):
                ev = ind
            else:
                # ThreatIndicator object
                ev = {
                    "provider": getattr(ind, "provider", "unknown"),
                    "threat_status": getattr(ind, "detection_status", "unknown"),
                    "confidence": getattr(ind, "confidence", 0.5),
                    "indicator": getattr(ind, "indicator", ""),
                    "last_updated": getattr(ind, "timestamp", None),
                    "metadata": getattr(ind, "metadata", {}),
                }
            evidences.append(ev)
        return self.aggregate(evidences, provider_names=provider_names)