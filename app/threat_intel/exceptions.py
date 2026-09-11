"""Threat-intel exceptions (no secrets ever attached)."""

from __future__ import annotations


class ThreatIntelError(Exception):
    """Base error; never carries API keys or message content."""


class ProviderUnavailableError(ThreatIntelError):
    """Provider unreachable, unconfigured or rate-limited."""


class ProviderTimeoutError(ThreatIntelError):
    """Provider lookup exceeded its timeout."""


class ProviderConfigError(ThreatIntelError):
    """Provider misconfigured (never includes the key value)."""


class RateLimitExceededError(ThreatIntelError):
    """Provider quota exhausted; caller should use cache/local intel."""


class PrivacyViolationError(ThreatIntelError):
    """IOC blocked from external sharing by the privacy policy."""
