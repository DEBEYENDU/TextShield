"""Review queue management: list, claim and resolve human reviews.

Backed by the evaluation feedback store (verdict ``needs_review``), so
review outcomes flow directly into training-candidate evidence.
"""

from __future__ import annotations

import time

from app.evaluation.feedback import FeedbackStore


class ReviewQueue:
    """Thin workflow layer over analyst feedback records."""

    def __init__(self, store: FeedbackStore | None = None):
        self.store = store or FeedbackStore()

    def submit(self, message: str, reasons: list[str], priority: str = "medium",
               analyst: str = "decision-engine", run_id: str = "",
               decision: dict | None = None) -> dict:
        item = self.store.record(
            message, "needs_review", analyst,
            comment="; ".join(reasons[:6]),
            expected="", predicted=(decision or {}).get("decision", ""),
            run_id=run_id)
        item["priority"] = priority
        item["submitted_at"] = time.time()
        return item

    def queue(self, limit: int = 50) -> list[dict]:
        return self.store.review_queue()[:limit]

    def claim(self, feedback_id: str, analyst: str) -> bool:
        for item in self.store._items:
            if item["id"] == feedback_id and not item.get("resolved"):
                item["claimed_by"] = analyst
                item["claimed_at"] = time.time()
                self.store._save()
                return True
        return False

    def resolve(self, feedback_id: str, verdict: str, analyst: str = "",
                comment: str = "") -> bool:
        if verdict not in {"correct", "incorrect", "false_positive",
                           "false_negative"}:
            raise ValueError(f"Resolution must be a final verdict, got '{verdict}'")
        for item in self.store._items:
            if item["id"] == feedback_id:
                item["resolved"] = True
                item["resolution"] = verdict
                item["resolved_by"] = analyst
                item["resolution_comment"] = comment
                item["resolved_at"] = time.time()
                self.store._save()
                return True
        return False

    def stats(self) -> dict:
        base = self.store.stats()
        base["priorities"] = {}
        for item in self.store.review_queue():
            key = item.get("priority", "medium")
            base["priorities"][key] = base["priorities"].get(key, 0) + 1
        return base


review_queue = ReviewQueue()
