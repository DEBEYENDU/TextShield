from __future__ import annotations

import asyncio
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from .ioc import IOCType, IOCExtractor, ExtractedIOC
from .providers.threat_indicator import ThreatIndicator


class ReputationAggregator:
    """Aggregates threat intelligence from multiple providers using configurable weights."""
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """Initialize the aggregator with optional provider weights."""
        # Default weights if not specified
        self.weights: Dict[str, float] = weights or {
            "google_safe_browsing": 0.30,
            "virustotal": 0.25,
            "openphish": 0.20,
            "phishtank": 0.15,
            "urlhaus": 0.10,
            "abuseipdb": 0.05,
        }
        # Normalize weights to sum to 1.0
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in self.weights.items()}
        
        self.provider_results: Dict[str, List[ThreatIndicator]] = {}
        self.aggregation_history: List[Dict[str, Any]] = []
    
    async def aggregate(
        self,
        indicators: List[ThreatIndicator],
        provider_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Aggregate threat indicators from multiple providers.
        
        Returns a dict with:
        - overall_threat_score: 0.0 to 1.0
        - confidence: 0.0 to 1.0
        - evidence_agreement: percentage of providers agreeing
        - provider_reliability: per-provider reliability scores
        - threat_distribution: breakdown by severity
        """
        provider_names = provider_names or self._get_provider_names(indicators)
        self.provider_results = {}
        
        # Group indicators by provider
        for indicator in indicators:
            provider = indicator.provider
            if provider not in self.provider_results:
                self.provider_results[provider] = []
            self.provider_results[provider].append(indicator)
        
        # Calculate aggregation results
        results = await self._calculate_metrics(provider_names)
        
        # Record in history
        self.aggregation_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "provider_names": provider_names,
            "indicators_count": len(indicators),
            "results": results,
        })
        
        # Keep history manageable
        if len(self.aggregation_history) > 100:
            self.aggregation_history = self.aggregation_history[-100:]
        
        return results
    
    def _get_provider_names(self, indicators: List[ThreatIndicator]) -> List[str]:
        """Get provider names from indicators."""
        names = []
        seen = set()
        for indicator in indicators:
            if indicator.provider not in seen:
                seen.add(indicator.provider)
                names.append(indicator.provider)
        return names
    
    async def _calculate_metrics(
        self,
        provider_names: List[str],
    ) -> Dict[str, Any]:
        """Calculate the aggregation metrics."""
        # Collect all malicious indicators with their weights
        malicious_weighted = 0.0
        total_weighted = 0.0
        severity_counts: Dict[str, int] = Counter()
        provider_malicious: Dict[str, int] = Counter()
        provider_total: Dict[str, int] = Counter()
        provider_confidences: Dict[str, List[float]] = {}
        
        for provider_name in provider_names:
            weight = self.weights.get(provider_name, 0.0)
            indicators = self.provider_results.get(provider_name, [])
            provider_total[provider_name] = len(indicators)
            
            malicious_count = 0
            confidences = []
            
            for indicator in indicators:
                total_weighted += weight
                if indicator.detection_status in ("malicious", "phishing", "malware"):
                    malicious_weighted += weight
                    malicious_count += 1
                
                severity_counts[indicator.severity] = severity_counts.get(indicator.severity, 0) + 1
                
                if indicator.provider not in provider_confidences:
                    provider_confidences[indicator.provider] = []
                provider_confidences[indicator.provider].append(indicator.confidence)
                
                if indicator.detection_status in ("malicious", "phishing", "malware"):
                    provider_malicious[provider_name] = provider_malicious.get(provider_name, 0) + 1
            
            provider_malicious[provider_name] = malicious_count
            if confidences:
                provider_confidences[provider_name] = sum(confidences) / len(confidences)
        
        # Overall threat score (weighted average)
        overall_threat_score = malicious_weighted / total_weighted if total_weighted > 0 else 0.0
        
        # Confidence based on provider agreement
        agreement_count = sum(
            1 for pn in provider_names
            if provider_malicious.get(pn, 0) > 0
        )
        evidence_agreement = agreement_count / len(provider_names) if provider_names else 0.0
        
        # Provider reliability based on consistency
        provider_reliability: Dict[str, float] = {}
        for provider_name in provider_names:
            mal_count = provider_malicious.get(provider_name, 0)
            total_count = provider_total.get(provider_name, 1)
            # Reliability: proportion of malicious detections out of total
            # Higher consistency with other providers increases reliability
            provider_reliability[provider_name] = mal_count / total_count if total_count > 0 else 0.0
        
        # Average confidence across all providers
        all_confidences = []
        for pn, confs in provider_confidences.items():
            all_confidences.extend(confs)
        average_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
        
        # Threat distribution
        total_indicators = sum(severity_counts.values()) or 1
        threat_distribution = {
            level: count / total_indicators
            for level, count in severity_counts.items()
        }
        
        return {
            "overall_threat_score": round(overall_threat_score, 4),
            "confidence": round(average_confidence, 4),
            "evidence_agreement": round(evidence_agreement, 4),
            "provider_reliability": {k: round(v, 4) for k, v in provider_reliability.items()},
            "threat_distribution": {k: round(v, 4) for k, v in threat_distribution.items()},
            "malicious_indicators": sum(severity_counts.get("malicious", 0) + severity_counts.get("phishing", 0) + severity_counts.get("malware", 0), 0),
            "total_indicators_considered": len(indicators),
            "provider_weights": self.weights,
        }
    
    def update_weights(self, new_weights: Dict[str, float]) -> None:
        """Update provider weights and renormalize."""
        total = sum(new_weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in new_weights.items()}
        else:
            self.weights = {
                "google_safe_browsing": 0.30,
                "virustotal": 0.25,
                "openphish": 0.20,
                "phishtank": 0.15,
                "urlhaus": 0.10,
                "abuseipdb": 0.05,
            }
    
    def get_weights(self) -> Dict[str, float]:
        """Get current provider weights."""
        return dict(self.weights)
    
    def get_provider_results(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get aggregated results per provider."""
        results: Dict[str, List[Dict[str, Any]]] = {}
        for provider, indicators in self.provider_results.items():
            results[provider] = [indicator.to_dict() for indicator in indicators]
        return results
    
    def clear_history(self) -> None:
        """Clear aggregation history."""
        self.aggregation_history = []


# Global aggregator instance
_aggregator: Optional[ReputationAggregator] = None


def get_aggregator() -> ReputationAggregator:
    """Get the global reputation aggregator instance."""
    global _aggregator
    if _aggregator is None:
        _aggregator = ReputationAggregator()
    return _aggregator


def init_aggregator(weights: Optional[Dict[str, float]] = None) -> ReputationAggregator:
    """Initialize the global reputation aggregator."""
    global _aggregator
    _aggregator = ReputationAggregator(weights=weights)
    return _aggregator