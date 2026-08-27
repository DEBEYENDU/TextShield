from __future__ import annotations

import json
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.threat.cache import ThreatCache
from app.threat.rate_limiting import RateLimitManager
from app.threat.config import ThreatIntelligenceConfig, get_config


class ThreatMonitor:
    """Monitor for threat intelligence system performance and health."""
    
    def __init__(self, config: Optional[ThreatIntelligenceConfig] = None):
        """Initialize the threat monitor."""
        self.config = config or get_config()
        self._latency_samples: Dict[str, List[float]] = defaultdict(list)
        self._event_counts: Dict[str, int] = defaultdict(int)
        self._start_time = time.time()
        self._cache: Optional[ThreatCache] = None
    
    def set_cache(self, cache: ThreatCache) -> None:
        """Set the threat cache instance for monitoring."""
        self._cache = cache
    
    def record_lookup(
        self,
        provider: str,
        success: bool,
        latency: float,
        threat_detected: bool = False,
        cached: bool = False,
    ) -> None:
        """Record a threat intelligence lookup event.
        
        Args:
            provider: Provider name
            success: Whether the lookup was successful
            latency: Response time in milliseconds
            threat_detected: Whether a threat was detected
            cached: Whether the result was from cache
        """
        # Record latency
        self._latency_samples[provider].append(latency)
        # Keep only recent samples (last 100)
        if len(self._latency_samples[provider]) > 100:
            self._latency_samples[provider] = self._latency_samples[provider][-100:]
        
        # Record event count
        event_key = f"{provider}_{'success' if success else 'failure'}_{'cached' if cached else 'live'}"
        self._event_counts[event_key] += 1
        
        # Record cache hit/miss if cache is available
        if self._cache and cached:
            # Cache hit already counted in event key
            pass
    
    def record_cache_access(self, hit: bool) -> None:
        """Record a cache access event."""
        key = "cache_hit" if hit else "cache_miss"
        self._event_counts[key] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics."""
        # Calculate per-provider latency stats
        provider_latency: Dict[str, Dict[str, Any]] = {}
        for provider, samples in self._latency_samples.items():
            if samples:
                provider_latency[provider] = {
                    "avg_latency_ms": round(sum(samples) / len(samples), 2),
                    "min_latency_ms": round(min(samples), 2),
                    "max_latency_ms": round(max(samples), 2),
                    "sample_count": len(samples),
                }
        
        # Calculate overall stats
        total_events = sum(self._event_counts.values())
        
        return {
            "uptime_seconds": round(time.time() - self._start_time, 2),
            "total_events": total_events,
            "event_breakdown": dict(self._event_counts),
            "provider_latency": provider_latency,
            "cache_hit_rate": self._calculate_cache_hit_rate(),
        }
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if "cache_hit" in self._event_counts and "cache_miss" in self._event_counts:
            hits = self._event_counts["cache_hit"]
            misses = self._event_counts["cache_miss"]
            total = hits + misses
            return round(hits / total, 2) if total > 0 else 0.0
        return 0.0
    
    def get_provider_stats(self, provider: str) -> Dict[str, Any]:
        """Get statistics for a specific provider."""
        latency_samples = self._latency_samples.get(provider, [])
        
        return {
            "provider": provider,
            "latency_ms": {
                "avg": round(sum(latency_samples) / len(latency_samples), 2) if latency_samples else 0,
                "min": round(min(latency_samples), 2) if latency_samples else 0,
                "max": round(max(latency_samples), 2) if latency_samples else 0,
                "samples": len(latency_samples),
            },
            "event_count": self._event_counts.get(f"{provider}_success", 0) + self._event_counts.get(f"{provider}_failure", 0),
        }


# Global monitor instance
_monitor: Optional[ThreatMonitor] = None


def get_monitor() -> ThreatMonitor:
    """Get the global threat monitor instance."""
    global _monitor
    if _monitor is None:
        _monitor = ThreatMonitor()
    return _monitor


def init_monitor(config: ThreatIntelligenceConfig) -> ThreatMonitor:
    """Initialize the global threat monitor."""
    global _monitor
    _monitor = ThreatMonitor(config)
    return _monitor