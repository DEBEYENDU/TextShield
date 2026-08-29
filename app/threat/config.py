from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.threat.providers import ThreatProviderABC


@dataclass
class ProviderConfig:
    """Configuration for a single threat intelligence provider."""
    
    name: str
    enabled: bool = True
    api_key: Optional[str] = None
    ttl: int = 3600  # Default TTL in seconds
    timeout: float = 5.0  # Default timeout in seconds
    burst_limit: int = 10  # Default burst limit
    period: int = 60  # Default period in seconds
    daily_quota: int = 1000  # Default daily quota
    concurrency: int = 5  # Default concurrent requests
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProviderConfig":
        """Create ProviderConfig from dictionary."""
        return cls(
            name=data.get("name", ""),
            enabled=data.get("enabled", True),
            api_key=data.get("api_key"),
            ttl=data.get("ttl", 3600),
            timeout=data.get("timeout", 5.0),
            burst_limit=data.get("burst_limit", 10),
            period=data.get("period", 60),
            daily_quota=data.get("daily_quota", 1000),
            concurrency=data.get("concurrency", 5),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "api_key": self.api_key,
            "ttl": self.ttl,
            "timeout": self.timeout,
            "burst_limit": self.burst_limit,
            "period": self.period,
            "daily_quota": self.daily_quota,
            "concurrency": self.concurrency,
        }


@dataclass
class ThreatIntelligenceConfig:
    """Main configuration for the threat intelligence layer."""
    
    # Provider configurations
    providers: Dict[str, ProviderConfig] = field(default_factory=dict)
    
    # Global settings
    default_ttl: int = 3600
    default_timeout: float = 5.0
    max_concurrent_lookups: int = 5
    enable_caching: bool = True
    enable_aggregation: bool = True
    enable_rate_limiting: bool = True
    
    # Cache settings
    cache_max_size: int = 10000
    cache_default_ttl: int = 3600
    
    # Aggregation weights
    # These override the default weights if specified
    aggregation_weights: Optional[Dict[str, float]] = None
    
    # Monitoring settings
    monitor_provider_latency: bool = True
    monitor_cache_hits: bool = True
    monitor_rate_limit_events: bool = True
    
    def __post_init__(self) -> None:
        """Post-initialization processing."""
        # Initialize default provider configs if none specified
        if not self.providers:
            # Default providers with no API keys (will be configured by admin)
            default_providers = {
                "google_safe_browsing": ProviderConfig(name="google_safe_browsing"),
                "virustotal": ProviderConfig(name="virustotal"),
                "phishtank": ProviderConfig(name="phishtank"),
                "urlhaus": ProviderConfig(name="urlhaus"),
                "openphish": ProviderConfig(name="openphish"),
                "abuseipdb": ProviderConfig(name="abuseipdb"),
            }
            self.providers = default_providers
        
        # Set default aggregation weights if not specified
        if self.aggregation_weights is None:
            self.aggregation_weights = {
                "google_safe_browsing": 0.30,
                "virustotal": 0.25,
                "openphish": 0.20,
                "phishtank": 0.15,
                "urlhaus": 0.10,
                "abuseipdb": 0.05,
            }
    
    def get_provider_config(self, name: str) -> Optional[ProviderConfig]:
        """Get configuration for a specific provider."""
        return self.providers.get(name)
    
    def set_provider_config(self, config: ProviderConfig) -> None:
        """Set configuration for a provider."""
        self.providers[config.name] = config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "providers": {
                name: config.to_dict() for name, config in self.providers.items()
            },
            "default_ttl": self.default_ttl,
            "default_timeout": self.default_timeout,
            "max_concurrent_lookups": self.max_concurrent_lookups,
            "enable_caching": self.enable_caching,
            "enable_aggregation": self.enable_aggregation,
            "enable_rate_limiting": self.enable_rate_limiting,
            "cache_max_size": self.cache_max_size,
            "cache_default_ttl": self.cache_default_ttl,
            "aggregation_weights": self.aggregation_weights,
            "monitor_provider_latency": self.monitor_provider_latency,
            "monitor_cache_hits": self.monitor_cache_hits,
            "monitor_rate_limit_events": self.monitor_rate_limit_events,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThreatIntelligenceConfig":
        """Create ThreatIntelligenceConfig from dictionary."""
        providers_data = data.get("providers", {})
        providers = {}
        for name, pdata in providers_data.items():
            providers[name] = ProviderConfig.from_dict(pdata)
        
        config = cls(
            providers=providers,
            default_ttl=data.get("default_ttl", 3600),
            default_timeout=data.get("default_timeout", 5.0),
            max_concurrent_lookups=data.get("max_concurrent_lookups", 5),
            enable_caching=data.get("enable_caching", True),
            enable_aggregation=data.get("enable_aggregation", True),
            enable_rate_limiting=data.get("enable_rate_limiting", True),
            cache_max_size=data.get("cache_max_size", 10000),
            cache_default_ttl=data.get("cache_default_ttl", 3600),
            aggregation_weights=data.get("aggregation_weights"),
            monitor_provider_latency=data.get("monitor_provider_latency", True),
            monitor_cache_hits=data.get("monitor_cache_hits", True),
            monitor_rate_limit_events=data.get("monitor_rate_limit_events", True),
        )
        return config


# Global configuration instance
_config: Optional[ThreatIntelligenceConfig] = None


def get_config() -> ThreatIntelligenceConfig:
    """Get the global threat intelligence configuration instance."""
    global _config
    if _config is None:
        _config = ThreatIntelligenceConfig()
    return _config


def init_config(config_data: Optional[Dict[str, Any]] = None) -> ThreatIntelligenceConfig:
    """Initialize the global threat intelligence configuration."""
    global _config
    _config = ThreatIntelligenceConfig.from_dict(config_data or {})
    return _config