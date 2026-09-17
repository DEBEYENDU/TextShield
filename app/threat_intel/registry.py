"""Dynamic provider registry: register/unregister/get/list.

No provider-specific logic lives outside providers themselves; adding a
provider means implementing ThreatIntelProvider and registering it.
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.threat_intel.provider import ThreatIntelProvider

logger = get_logger(__name__)


class ThreatIntelRegistry:
    """Name -> provider instance mapping with lifecycle helpers."""

    def __init__(self):
        self._providers: dict[str, ThreatIntelProvider] = {}

    def register(self, provider: ThreatIntelProvider) -> ThreatIntelProvider:
        self._providers[provider.name] = provider
        logger.info("Threat-intel provider registered: %s", provider.name)
        return provider

    def unregister(self, name: str) -> bool:
        if name in self._providers:
            del self._providers[name]
            logger.info("Threat-intel provider unregistered: %s", name)
            return True
        return False

    def get_provider(self, name: str) -> ThreatIntelProvider | None:
        return self._providers.get(name)

    def list_providers(self) -> list[str]:
        return sorted(self._providers)

    def enabled_providers(self) -> list[ThreatIntelProvider]:
        return [p for p in self._providers.values() if p.is_configured()]

    def all_metadata(self) -> dict[str, dict]:
        return {name: provider.health() for name, provider in self._providers.items()}

    def __len__(self) -> int:
        return len(self._providers)


_registry: ThreatIntelRegistry | None = None


def get_registry(reset: bool = False) -> ThreatIntelRegistry:
    """Process-wide registry (pass reset=True in tests)."""
    global _registry
    if _registry is None or reset:
        _registry = ThreatIntelRegistry()
    return _registry


def register(provider: ThreatIntelProvider) -> ThreatIntelProvider:
    """Decorator for plugin providers."""
    get_registry().register(provider)
    return provider
