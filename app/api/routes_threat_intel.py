"""Dashboard API: threat-intel providers, status, checks and IOC history."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.core.container import ServiceRegistry, get_request_registry
from app.core.exceptions import AppError
from app.core.logging import get_logger
from app.threat_intel.config import config as ti_config
from app.threat_intel.manager import build_default_manager
from app.threat_intel.models import IOC
from app.threat_intel.normalizer import normalize_ioc
from app.threat_intel.schemas import AggregatedResponse, CheckRequest

logger = get_logger(__name__)

router = APIRouter(prefix="/api/threat-intel", tags=["threat-intel"])

_manager_instance = None


def get_manager():
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = build_default_manager()
    return _manager_instance


@router.get("/providers")
def list_providers() -> dict:
    """Registered providers with capabilities and key presence (never values)."""
    manager = get_manager()
    providers = []
    for name in manager.registry.list_providers():
        provider = manager.registry.get_provider(name)
        providers.append({"name": name, "version": provider.version,
                          "enabled": name in ti_config.enabled_providers,
                          "configured": provider.is_configured(),
                          "capabilities": provider.capabilities})
    return {"providers": providers, "config": ti_config.redacted()}


@router.get("/status")
def intel_status() -> dict:
    """Cache, rate-limiter, reputation and offline-readiness status."""
    manager = get_manager()
    return {"cache": manager.cache.stats(),
            "rate_limits": manager.limiter.stats(),
            "reputation": manager.reputation.stats(),
            "offline_ready": True,
            "external_lookups_allowed": ti_config.allow_external_lookups}


@router.post("/check", response_model=AggregatedResponse)
def check_ioc(payload: CheckRequest,
              registry: ServiceRegistry = Depends(get_request_registry)) -> dict:
    """Check a single IOC across providers with aggregation."""
    manager = get_manager()
    ioc_type = (payload.ioc_type or "").lower() or None
    if ioc_type is None:
        from app.threat_intel.extractor import extract_iocs

        found = extract_iocs(payload.ioc)
        if not found:
            raise HTTPException(status_code=422,
                                detail="no IOC detected in input")
        ioc_type = found[0].ioc_type
        raw = found[0].original_value
    else:
        raw = payload.ioc
    try:
        ioc = normalize_ioc(IOC(original_value=raw, normalized_value=raw,
                                ioc_type=ioc_type))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    try:
        result = manager.check_ioc(ioc, payload.providers)
    except Exception as exc:
        logger.exception("Threat-intel check failed")
        raise AppError("Threat-intel check failed") from exc
    return {"ioc": result["ioc"], "ioc_type": result["ioc_type"],
            "results": result["results"],
            "aggregated_verdict": result["aggregated_verdict"],
            "confidence": result["confidence"], "cached": result["cached"]}


@router.get("/ioc/{ioc:path}")
def ioc_history(ioc: str) -> dict:
    """Local history for an IOC: reputation + cached provider results."""
    from app.threat_intel.extractor import extract_iocs

    found = extract_iocs(ioc)
    ioc_type = found[0].ioc_type if found else "unknown"
    normalized = found[0].normalized_value.lower() if found else ioc.lower()
    manager = get_manager()
    reputation = manager.reputation.lookup(ioc_type, normalized).to_dict()
    cached = []
    for name in manager.registry.list_providers():
        hit = manager.cache.get(ioc_type, normalized, name)
        if hit is not None:
            cached.append(hit.to_dict())
    return {"ioc": ioc, "ioc_type": ioc_type, "normalized": normalized,
            "reputation": reputation, "cached_results": cached}
