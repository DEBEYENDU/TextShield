"""Dependency-injection container (service registry).

Services are registered lazily as singletons and resolved by name, so
routes depend on a registry entry, not on import-time construction. The
app factory seeds ``create_container``; tests may build their own
container with stubbed services.
"""

from __future__ import annotations

import logging
from typing import Any

from starlette.requests import Request

_REQUIRED_SERVICES = (
    "analysis",
    "history",
    "analytics",
    "configuration",
    "kb",
    "models",
    "system_status",
    "semantic",
    "intent",
)


class ServiceRegistry:
    """Registry of named service providers.

    Providers are resolved as-is (stateless modules/functions); no
    memoized instantiation is needed because Python modules are already
    singletons and the service functions are pure. ``register``/``get``
    make the registry swappable in tests (stub providers).
    """

    def __init__(self) -> None:
        self._providers: dict[str, Any] = {}

    def register(self, name: str, provider: Any) -> None:
        self._providers[name] = provider

    def get(self, name: str) -> Any:
        return self._providers[name]

    def __contains__(self, name: str) -> bool:
        return name in self._providers


def create_container(registry: ServiceRegistry | None = None) -> ServiceRegistry:
    """Seed the registry with the default service providers.

    Providers already registered (e.g. stubs from a test) are kept:
    only missing names are filled in.
    """
    registry = registry or ServiceRegistry()

    from app.intent.pipeline import intent_pipeline
    from app.semantic.semantic_service import semantic_service
    from app.services import (
        analysis_service,
        analytics_service,
        configuration_service,
        history_service,
        kb_service,
        models_service,
        system_status_service,
    )

    defaults = {
        "analysis": analysis_service.analyze,
        "history": history_service,
        "analytics": analytics_service.get_stats,
        "configuration": configuration_service.effective_config,
        "kb": kb_service,
        "models": models_service,
        "system_status": system_status_service,
        "semantic": semantic_service,
        "intent": intent_pipeline,
    }
    for name, provider in defaults.items():
        if name not in registry:
            registry.register(name, provider)
    return registry


def verify_container(
    registry: ServiceRegistry, logger: logging.Logger | None = None
) -> list[str]:
    """Ensure every required service is registered; returns missing names."""
    missing = [name for name in _REQUIRED_SERVICES if name not in registry]
    if missing and logger:
        logger.error("Missing service registrations: %s", ", ".join(missing))
    return missing


# Lazy module-level instance: created on first use, so importing this
# module never pulls in the whole service stack.
_container: ServiceRegistry | None = None


def get_container() -> ServiceRegistry:
    global _container
    if _container is None:
        _container = create_container()
    return _container


def get_request_registry(request: Request) -> ServiceRegistry:
    """Request-scoped dependency: the app's own registry.

    Uses ``request.app.state.registry`` when present (set by
    ``create_app``) so tests can inject a stub registry; falls back to
    the module-level container for compatibility.
    """
    registry = getattr(request.app.state, "registry", None)
    return registry or get_container()
