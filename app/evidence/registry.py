from __future__ import annotations

from typing import Dict, List, Optional
from .models import EvidenceSource, EvidenceItem


class EvidenceRegistry:
    """Registry for evidence sources.

    Sources can register themselves and the engine can discover them
    without hard‑coupling to concrete implementations.
    """

    def __init__(self):
        self._sources: Dict[str, EvidenceItem] = {}
        self._factories: Dict[str, Any] = {}

    def register(self, name: str, source: EvidenceSource, factory=None) -> None:
        """Register an evidence source.

        Args:
            name: Human-readable name (used for API/debugging).
            source: EvidenceSource enum value.
            factory: Callable that returns an EvidenceCollector instance (optional).
        """
        self._sources[name] = source
        if factory:
            self._factories[name] = factory

    def unregister(self, name: str) -> None:
        self._sources.pop(name, None)
        self._factories.pop(name, None)

    def get(self, name: str) -> Optional[EvidenceSource]:
        return self._sources.get(name)

    def list_sources(self) -> List[str]:
        return list(self._sources.keys())

    def get_all_items(self) -> Dict[str, EvidenceItem]:
        return dict(self._sources)  # simplified – in real code store EvidenceItem instances


_registry_instance: Optional[EvidenceRegistry] = None


def get_registry() -> EvidenceRegistry:
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = EvidenceRegistry()
    return _registry_instance


def register_evidence_source(name: str, source: EvidenceSource, factory=None) -> None:
    get_registry().register(name, source, factory)