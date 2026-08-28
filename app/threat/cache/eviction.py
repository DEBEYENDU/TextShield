from __future__ import annotations

from typing import List

from .models import CacheRecord


class EvictionPolicy:
    def select_for_eviction(self, records: List[CacheRecord], limit: int) -> List[CacheRecord]:
        raise NotImplementedError


class LRUEviction(EvictionPolicy):
    def select_for_eviction(self, records: List[CacheRecord], limit: int) -> List[CacheRecord]:
        # Evict least recently accessed
        sorted_recs = sorted(records, key=lambda r: r.last_updated)
        return sorted_recs[:limit]


class TTLEviction(EvictionPolicy):
    def select_for_eviction(self, records: List[CacheRecord], limit: int) -> List[CacheRecord]:
        expired = [r for r in records if r.is_expired()]
        return expired[:limit]
