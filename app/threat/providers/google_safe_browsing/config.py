from __future__ import annotations

from typing import Optional, Dict, Any


class GoogleSafeBrowsingConfig:
    """Configuration for Google Safe Browsing provider."""

    def __init__(self, **kwargs: Any):
        self.api_key: str = kwargs.get("api_key", "")
        self.enabled: bool = kwargs.get("enabled", True)
        self.ttl: int = kwargs.get("ttl", 3600)  # Cache TTL in seconds
        self.timeout: float = kwargs.get("timeout", 5.0)  # Request timeout
        self.max_retries: int = kwargs.get("max_retries", 3)
        self.backoff_factor: float = kwargs.get("backoff_factor", 2.0)
        self.rate_limit_per_minute: int = kwargs.get("rate_limit_per_minute", 100)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "api_key": self.api_key,
            "enabled": self.enabled,
            "ttl": self.ttl,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "backoff_factor": self.backoff_factor,
            "rate_limit_per_minute": self.rate_limit_per_minute,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GoogleSafeBrowsingConfig":
        return cls(
            api_key=data.get("api_key", ""),
            enabled=data.get("enabled", True),
            ttl=data.get("ttl", 3600),
            timeout=data.get("timeout", 5.0),
            max_retries=data.get("max_retries", 3),
            backoff_factor=data.get("backoff_factor", 2.0),
            rate_limit_per_minute=data.get("rate_limit_per_minute", 100),
        )