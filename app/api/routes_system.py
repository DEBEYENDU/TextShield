"""Route module: system health, readiness, version, config and status."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app import __version__
from app.core.container import ServiceRegistry, get_request_registry
from app.core.settings import settings
from app.schemas.system import (
    AppStatusResponse,
    ConfigStatusResponse,
    HealthResponse,
    ReadinessResponse,
    VersionResponse,
)

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health(registry: ServiceRegistry = Depends(get_request_registry)) -> dict:
    """Service health: model, RAG and LLM availability."""
    return registry.get("system_status").health()


@router.get("/readiness", response_model=ReadinessResponse)
def readiness(registry: ServiceRegistry = Depends(get_request_registry)) -> dict:
    """Readiness probe: database reachable, migrations applied."""
    return registry.get("system_status").readiness()


@router.get("/version", response_model=VersionResponse)
def version() -> dict:
    """Application version information."""
    return {
        "name": "TextShield",
        "version": __version__,
        "tagline": "AI-powered phishing, spam and scam message analysis",
        "environment": settings.ENVIRONMENT,
    }


@router.get("/config/status", response_model=ConfigStatusResponse)
def config_status(registry: ServiceRegistry = Depends(get_request_registry)) -> dict:
    """Effective runtime configuration snapshot."""
    return registry.get("configuration")()


@router.get("/status", response_model=AppStatusResponse)
def app_status(registry: ServiceRegistry = Depends(get_request_registry)) -> dict:
    """Application status: uptime, feature flags, model readiness."""
    return registry.get("system_status").app_status()
