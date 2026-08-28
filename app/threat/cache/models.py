from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass
class CacheRecord:
    cache_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    ioc_id: str = ""
    ioc_type: str = ""
    original_value: str = ""
    normalized_value: str = ""
    provider_name: str = ""
    provider_version: str = ""
    threat_status: str = "unknown"
    threat_score: float = 0.0
    confidence: float = 0.0
    evidence: str = ""
    provider_metadata: Dict[str, Any] = field(default_factory=dict)
    first_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expiration_time: Optional[datetime] = None
    ttl: int = 3600
    lookup_count: int = 0
    cache_hit_count: int = 0
    provider_response_hash: str = ""
    source: str = ""
    revision_number: int = 1
    status: str = "active"

    def is_expired(self) -> bool:
        if self.expiration_time is None:
            return False
        return datetime.now(timezone.utc) >= self.expiration_time

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cache_id": self.cache_id,
            "ioc_id": self.ioc_id,
            "ioc_type": self.ioc_type,
            "original_value": self.original_value,
            "normalized_value": self.normalized_value,
            "provider_name": self.provider_name,
            "provider_version": self.provider_version,
            "threat_status": self.threat_status,
            "threat_score": self.threat_score,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "provider_metadata": self.provider_metadata,
            "first_seen": self.first_seen.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "expiration_time": self.expiration_time.isoformat() if self.expiration_time else None,
            "ttl": self.ttl,
            "lookup_count": self.lookup_count,
            "cache_hit_count": self.cache_hit_count,
            "provider_response_hash": self.provider_response_hash,
            "source": self.source,
            "revision_number": self.revision_number,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheRecord":
        obj = cls()
        obj.cache_id = data.get("cache_id", str(uuid.uuid4()))
        obj.ioc_id = data.get("ioc_id", "")
        obj.ioc_type = data.get("ioc_type", "")
        obj.original_value = data.get("original_value", "")
        obj.normalized_value = data.get("normalized_value", "")
        obj.provider_name = data.get("provider_name", "")
        obj.provider_version = data.get("provider_version", "")
        obj.threat_status = data.get("threat_status", "unknown")
        obj.threat_score = data.get("threat_score", 0.0)
        obj.confidence = data.get("confidence", 0.0)
        obj.evidence = data.get("evidence", "")
        obj.provider_metadata = data.get("provider_metadata", {})
        obj.first_seen = datetime.fromisoformat(data["first_seen"]) if data.get("first_seen") else datetime.now(timezone.utc)
        obj.last_updated = datetime.fromisoformat(data["last_updated"]) if data.get("last_updated") else datetime.now(timezone.utc)
        obj.expiration_time = datetime.fromisoformat(data["expiration_time"]) if data.get("expiration_time") else None
        obj.ttl = data.get("ttl", 3600)
        obj.lookup_count = data.get("lookup_count", 0)
        obj.cache_hit_count = data.get("cache_hit_count", 0)
        obj.provider_response_hash = data.get("provider_response_hash", "")
        obj.source = data.get("source", "")
        obj.revision_number = data.get("revision_number", 1)
        obj.status = data.get("status", "active")
        return obj


@dataclass
class CacheRevision:
    cache_id: str
    revision_number: int
    previous_version: Optional[str]
    change_timestamp: datetime
    reason: str
    provider: str
    data: Dict[str, Any]
