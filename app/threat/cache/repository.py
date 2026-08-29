from __future__ import annotations

from typing import List, Optional

from .models import CacheRecord
from .manager import CacheManager


class CacheRepository:
    def __init__(self, manager: CacheManager):
        self.manager = manager

    def find_by_provider(self, provider_name: str) -> List[CacheRecord]:
        recs = self.manager.storage.list_all()
        return [r for r in recs if r.provider_name == provider_name and not r.is_expired()]

    def find_by_type(self, ioc_type: str) -> List[CacheRecord]:
        recs = self.manager.storage.list_all()
        return [r for r in recs if r.ioc_type == ioc_type and not r.is_expired()]

    def find_by_score_range(self, min_score: float, max_score: float) -> List[CacheRecord]:
        recs = self.manager.storage.list_all()
        return [r for r in recs if min_score <= r.threat_score <= max_score and not r.is_expired()]

    def find_by_confidence(self, min_confidence: float) -> List[CacheRecord]:
        recs = self.manager.storage.list_all()
        return [r for r in recs if r.confidence >= min_confidence and not r.is_expired()]

    def find_by_date_range(self, start, end) -> List[CacheRecord]:
        recs = self.manager.storage.list_all()
        return [r for r in recs if start <= r.last_updated <= end and not r.is_expired()]
