from __future__ import annotations

import threading
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict

from .models import CacheRecord, CacheRevision
from .storage import InMemoryStorage
from .eviction import LRUEviction, TTLEviction


class CacheManager:
    def __init__(self, max_size: int = 10000, default_ttl: int = 3600):
        self.storage = InMemoryStorage()
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.lock = threading.RLock()
        self.revisions: Dict[str, List[CacheRevision]] = {}
        self.stats = {
            "hits": 0,
            "misses": 0,
            "puts": 0,
            "deletes": 0,
        }

    def create(self, record: CacheRecord) -> CacheRecord:
        with self.lock:
            now = datetime.now(timezone.utc)
            if record.expiration_time is None:
                record.expiration_time = now + timedelta(seconds=record.ttl or self.default_ttl)
            record.first_seen = now
            record.last_updated = now
            record.revision_number = 1
            self.storage.put(record)
            self.stats["puts"] += 1
            self._evict_if_needed()
            return record

    def read(self, cache_id: str) -> Optional[CacheRecord]:
        with self.lock:
            rec = self.storage.get(cache_id)
            if rec and not rec.is_expired():
                rec.lookup_count += 1
                rec.cache_hit_count += 1
                self.stats["hits"] += 1
                return rec
            self.stats["misses"] += 1
            return None

    def update(self, cache_id: str, updates: Dict) -> Optional[CacheRecord]:
        with self.lock:
            rec = self.storage.get(cache_id)
            if not rec:
                return None
            # revision
            rev = CacheRevision(
                cache_id=cache_id,
                revision_number=rec.revision_number,
                previous_version=None,
                change_timestamp=datetime.now(timezone.utc),
                reason=updates.get("reason", "update"),
                provider=updates.get("provider", ""),
                data=rec.to_dict(),
            )
            self.revisions.setdefault(cache_id, []).append(rev)
            for k, v in updates.items():
                if hasattr(rec, k):
                    setattr(rec, k, v)
            rec.last_updated = datetime.now(timezone.utc)
            rec.revision_number += 1
            self.storage.put(rec)
            return rec

    def delete(self, cache_id: str) -> bool:
        with self.lock:
            ok = self.storage.delete(cache_id)
            if ok:
                self.stats["deletes"] += 1
            return ok

    def bulk_insert(self, records: List[CacheRecord]) -> int:
        count = 0
        for r in records:
            self.create(r)
            count += 1
        return count

    def lookup_by_ioc(self, ioc_type: str, normalized_value: str) -> List[CacheRecord]:
        with self.lock:
            recs = self.storage.find_by_ioc(ioc_type, normalized_value)
            valid = [r for r in recs if not r.is_expired()]
            for r in valid:
                r.lookup_count += 1
                r.cache_hit_count += 1
                self.stats["hits"] += 1
            return valid

    def _evict_if_needed(self):
        all_recs = self.storage.list_all()
        if len(all_recs) <= self.max_size:
            return
        evictor = LRUEviction()
        to_evict = evictor.select_for_eviction(all_recs, len(all_recs) - self.max_size)
        for r in to_evict:
            self.storage.delete(r.cache_id)

    def get_statistics(self):
        all_recs = self.storage.list_all()
        hits = self.stats["hits"]
        misses = self.stats["misses"]
        total = hits + misses
        hit_ratio = hits / total if total else 0.0
        return {
            "cache_size": len(all_recs),
            "hit_ratio": hit_ratio,
            "miss_ratio": 1 - hit_ratio,
            "expired_records": sum(1 for r in all_recs if r.is_expired()),
            "hits": hits,
            "misses": misses,
        }
