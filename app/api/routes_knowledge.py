"""Route module: knowledge-base status and rebuild."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.container import ServiceRegistry, get_request_registry
from app.schemas.system import KBStatusResponse

router = APIRouter(prefix="/api", tags=["knowledge-base"])


@router.get("/knowledge-base", response_model=KBStatusResponse)
def knowledge_base_status(registry: ServiceRegistry = Depends(get_request_registry)) -> dict:
    """Knowledge base build status (no rebuild)."""
    return registry.get("kb").status()


@router.post("/knowledge-base/rebuild", response_model=KBStatusResponse)
def rebuild_knowledge_base(registry: ServiceRegistry = Depends(get_request_registry)) -> dict:
    """Rebuild the vector database from the knowledge_base directory."""
    return registry.get("kb").rebuild()