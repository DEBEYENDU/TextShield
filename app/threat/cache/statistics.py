from __future__ import annotations

from collections import Counter
from typing import Dict

from .manager import CacheManager


class CacheStatistics:
    def __init__(self, manager: CacheManager):
        self.manager = manager

    def get_summary(self) -> Dict:
        base = self.manager.get_statistics()
        recs = self.manager.storage.list_all()
        provider_dist = Counter(r.provider_name for r in recs)
        avg_ttl = sum(r.ttl for r in recs) / len(recs) if recs else 0
        top_queried = Counter(r.normalized_value for r in recs)
        top_5 = top_queried.most_common(5)
        base.update({
            "provider_distribution": dict(provider_dist),
            "average_ttl": avg_ttl,
            "top_queried_iocs": top_5,
        })
        return base
