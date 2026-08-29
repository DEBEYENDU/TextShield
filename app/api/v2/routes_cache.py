from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.threat.cache.manager import CacheManager
from app.threat.cache.models import CacheRecord
from app.threat.cache.statistics import CacheStatistics

router = APIRouter(prefix="/threat/cache", tags=["threat-cache"])
manager = CacheManager()
stats = CacheStatistics(manager)


class CacheCreate(BaseModel):
    ioc_id: str
    ioc_type: str
    original_value: str
    normalized_value: str
    provider_name: str
    threat_status: str = "unknown"
    threat_score: float = 0.0
    confidence: float = 0.0
    ttl: int = 3600


@router.get("")
def list_cache():
    recs = manager.storage.list_all()
    return {"count": len(recs), "records": [r.to_dict() for r in recs]}


@router.get("/{ioc}")
def get_cache(ioc: str):
    # search by normalized value simple
    recs = [r for r in manager.storage.list_all() if r.normalized_value == ioc]
    if not recs:
        raise HTTPException(status_code=404, detail="Not found")
    return [r.to_dict() for r in recs]


@router.delete("/{ioc}")
def delete_cache(ioc: str):
    recs = [r for r in manager.storage.list_all() if r.normalized_value == ioc]
    removed = 0
    for r in recs:
        if manager.delete(r.cache_id):
            removed += 1
    return {"removed": removed}


@router.post("/refresh")
def refresh_cache():
    # dummy refresh
    return {"status": "ok"}


@router.get("/statistics")
def get_statistics():
    return stats.get_summary()
