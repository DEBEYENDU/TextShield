from __future__ import annotations

from typing import List

from .models import CacheRecord
from .manager import CacheManager


class CacheCleanup:
    def __init__(self, manager: CacheManager):
        self.manager = manager

    def remove_expired(self) -> int:
        recs = self.manager.storage.list_all()
        removed = 0
        for r in recs:
            if r.is_expired():
                if self.manager.delete(r.cache_id):
                    removed += 1
        return removed

    def prune_revisions(self, cache_id: str, keep_last: int = 10) -> int:
        revs = self.manager.revisions.get(cache_id, [])
        if len(revs) <= keep_last:
            return 0
        to_remove = len(revs) - keep_last
        del self.manager.revisions[cache_id][:to_remove]
        return to_remove

    def compact(self) -> int:
        # Remove expired and prune revisions
        expired = self.remove_expired()
        # For simplicity, prune all revisions to keep 10
        pruned = 0
        for cid in list(self.manager.revisions.keys()):
            pruned += self.prune_revisions(cid, keep_last=10)
        return expired + pruned
