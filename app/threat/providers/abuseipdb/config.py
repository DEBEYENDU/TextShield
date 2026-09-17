from __future__ import annotations

from typing import Any, Dict


class AbuseIPDBConfig:
    """Configuration for AbuseIPDB provider."""

    def __init__(self, **kwargs: Any):
        self.api_key: str = kwargs.get("api_key", "")
        self.enabled: bool = kwargs.get("enabled", True)
        self.ttl: int = kwargs.get("ttl", 900)
        self.timeout: float = kwargs.get("timeout", 5.0)
        self.max_retries: int = kwargs.get("max_retries", 3)
        self.backoff_factor: float = kwargs.get("backoff_factor", 2.0)
        self.rate_limit_per_minute: int = kwargs.get("rate_limit_per_minute", 20)
        self.api_url: str = kwargs.get("api_url", "https://api.abuseipdb.com/api/v2/check")
        self.verify_ssl: bool = kwargs.get("verify_ssl", True)
        # Abuse score threshold to consider IP malicious
        self.abuse_threshold: int = kwargs.get("abuse_threshold", 25)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "api_key": self.api_key,
            "enabled": self.enabled,
            "ttl": self.ttl,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "backoff_factor": self.backoff_factor,
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "api_url": self.api_url,
            "verify_ssl": self.verify_ssl,
            "abuse_threshold": self.abuse_threshold,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AbuseIPDBConfig":
        return cls(
            api_key=data.get("api_key", ""),
            enabled=data.get("enabled", True),
            ttl=data.get("ttl", 900),
            timeout=data.get("timeout", 5.0),
            max_retries=data.get("max_retries", 3),
            backoff_factor=data.get("backoff_factor", 2.0),
            rate_limit_per_minute=data.get("rate_limit_per_minute", 20),
            api_url=data.get("api_url", "https://api.abuseipdb.com/api/v2/check"),
            verify_ssl=data.get("verify_ssl", True),
            abuse_threshold=data.get("abuse_threshold", 25),
        )
