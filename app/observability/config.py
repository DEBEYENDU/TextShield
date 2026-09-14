"""Observability configuration with safe defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

def _get(key: str, default: str) -> str:
    return os.getenv(key, default)

def _get_bool(key: str, default: bool) -> bool:
    v = os.getenv(key)
    if v is None:
        return default
    return v.lower() in {"1", "true", "yes", "on"}

def _get_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default

@dataclass
class ObservabilityConfig:
    log_level: str = field(default_factory=lambda: _get("TEXTSHIELD_LOG_LEVEL", "INFO"))
    structured_logging: bool = field(default_factory=lambda: _get_bool("TEXTSHIELD_STRUCTURED_LOGGING", True))
    audit_enabled: bool = field(default_factory=lambda: _get_bool("TEXTSHIELD_AUDIT_ENABLED", True))
    metrics_enabled: bool = field(default_factory=lambda: _get_bool("TEXTSHIELD_METRICS_ENABLED", True))
    tracing_enabled: bool = field(default_factory=lambda: _get_bool("TEXTSHIELD_TRACING_ENABLED", False))
    privacy_mode: str = field(default_factory=lambda: _get("TEXTSHIELD_PRIVACY_MODE", "standard"))
    message_logging_policy: str = field(default_factory=lambda: _get("TEXTSHIELD_MESSAGE_LOGGING_POLICY", "hash"))
    rate_limit_enabled: bool = field(default_factory=lambda: _get_bool("TEXTSHIELD_RATE_LIMIT_ENABLED", True))
    request_timeout: int = field(default_factory=lambda: _get_int("TEXTSHIELD_REQUEST_TIMEOUT", 30))
    analysis_timeout: int = field(default_factory=lambda: _get_int("TEXTSHIELD_ANALYSIS_TIMEOUT", 60))
    health_check_interval: int = field(default_factory=lambda: _get_int("TEXTSHIELD_HEALTH_CHECK_INTERVAL", 30))
    diagnostic_mode: bool = field(default_factory=lambda: _get_bool("TEXTSHIELD_DIAGNOSTIC_MODE", False))

    def validate(self) -> list[str]:
        errors = []
        if self.privacy_mode not in {"strict", "standard", "debug"}:
            errors.append("TEXTSHIELD_PRIVACY_MODE must be strict/standard/debug")
        if self.message_logging_policy not in {"none", "hash", "preview"}:
            errors.append("TEXTSHIELD_MESSAGE_LOGGING_POLICY invalid")
        if self.request_timeout <= 0 or self.analysis_timeout <= 0:
            errors.append("Timeouts must be positive")
        return errors

config = ObservabilityConfig()
