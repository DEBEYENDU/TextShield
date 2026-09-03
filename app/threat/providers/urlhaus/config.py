from __future__ import annotations

from typing import Any, Dict


class URLhausConfig:
    """Configuration for URLhaus provider."""

    def __init__(self, **kwargs: Any):
        self.api_key: str = kwargs.get("api_key", "")
        self.enabled: bool = kwargs.get("enabled", True)
        self.ttl: int = kwargs.get("ttl", 600)
        self.timeout: float = kwargs.get("timeout", 5.0)
        self.max_retries: int = kwargs.get("max_retries", 3)
        self.backoff_factor: float = kwargs.get("backoff_factor", 2.0)
        self.rate_limit_per_minute: int = kwargs.get("rate_limit_per_minute", 40)
        self.api_url: str = kwargs.get("api_url", "https://urlhaus-api.abuse.ch/v1/url/")
        self.verify_ssl: bool = kwargs.get("verify_ssl", True)

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
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "URLhausConfig":
        return cls(
            api_key=data.get("api_key", ""),
            enabled=data.get("enabled", True),
            ttl=data.get("ttl", 600),
            timeout=data.get("timeout", 5.0),
            max_retries=data.get("max_retries", 3),
            backoff_factor=data.get("backoff_factor", 2.0),
            rate_limit_per_minute=data.get("rate_limit_per_minute", 40),
            api_url=data.get("api_url", "https://urlhaus-api.abuse.ch/v1/url/"),
            verify_ssl=data.get("verify_ssl", True),
        )
