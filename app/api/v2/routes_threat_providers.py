from __future__ import annotations

from fastapi import APIRouter, HTTPException
from typing import Any, Dict

router = APIRouter(prefix="/v2/threat/providers", tags=["threat-providers"])

# Also expose under /api/v2 for compatibility with spec
api_router = APIRouter(prefix="/api/v2/threat/providers", tags=["threat-providers"])


def _get_provider(name: str):
    name = name.lower()
    if name == "openphish":
        from app.threat.providers.openphish import OpenPhishProvider
        return OpenPhishProvider()
    if name == "phishtank":
        from app.threat.providers.phishtank import PhishTankProvider
        return PhishTankProvider()
    if name == "urlhaus":
        from app.threat.providers.urlhaus import URLhausProvider
        return URLhausProvider()
    if name == "abuseipdb":
        from app.threat.providers.abuseipdb import AbuseIPDBProvider
        return AbuseIPDBProvider()
    if name == "google_safe_browsing":
        from app.threat.providers.google_safe_browsing import GoogleSafeBrowsingProvider
        return GoogleSafeBrowsingProvider()
    if name == "virustotal":
        from app.threat.providers.virustotal import VirusTotalProvider
        return VirusTotalProvider()
    return None


def _provider_info(name: str) -> Dict[str, Any]:
    provider = _get_provider(name)
    if provider is None:
        raise HTTPException(status_code=404, detail=f"Provider not found: {name}")
    # Ensure initialized for health metadata
    try:
        if not getattr(provider, "_initialized", False):
            provider.initialize()
    except Exception:
        pass
    meta = provider.metadata if isinstance(provider.metadata, dict) else provider.metadata()
    # Add health
    try:
        health = provider.health_check()
    except Exception as exc:  # noqa: BLE001
        health = {"healthy": False, "error": str(exc)}
    return {
        "provider": name,
        "metadata": meta,
        "health": health,
        "capabilities": provider.capabilities() if hasattr(provider, "capabilities") else meta.get("capabilities", []),
    }


@router.get("/openphish")
async def get_openphish() -> Dict[str, Any]:
    return _provider_info("openphish")


@router.get("/phishtank")
async def get_phishtank() -> Dict[str, Any]:
    return _provider_info("phishtank")


@router.get("/urlhaus")
async def get_urlhaus() -> Dict[str, Any]:
    return _provider_info("urlhaus")


@router.get("/abuseipdb")
async def get_abuseipdb() -> Dict[str, Any]:
    return _provider_info("abuseipdb")


@router.get("/{provider_name}")
async def get_provider_generic(provider_name: str) -> Dict[str, Any]:
    # Guard against collision with static routes (they are matched first)
    return _provider_info(provider_name)


# Mirror routes onto api_router for /api/v2 prefix compatibility
@api_router.get("/openphish")
async def api_get_openphish() -> Dict[str, Any]:
    return _provider_info("openphish")


@api_router.get("/phishtank")
async def api_get_phishtank() -> Dict[str, Any]:
    return _provider_info("phishtank")


@api_router.get("/urlhaus")
async def api_get_urlhaus() -> Dict[str, Any]:
    return _provider_info("urlhaus")


@api_router.get("/abuseipdb")
async def api_get_abuseipdb() -> Dict[str, Any]:
    return _provider_info("abuseipdb")


@api_router.get("/{provider_name}")
async def api_get_provider_generic(provider_name: str) -> Dict[str, Any]:
    return _provider_info(provider_name)
