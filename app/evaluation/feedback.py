"""Analyst feedback system: marks, comments and review queue.

Verdicts: correct | incorrect | false_positive | false_negative |
needs_review. Feedback feeds the review queue and future training
datasets — it never triggers automatic retraining.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

from app.evaluation import FEEDBACK_PATH

VERDICTS = ["correct", "incorrect", "false_positive", "false_negative",
            "needs_review"]


class FeedbackStore:
    """JSON-backed analyst feedback with a needs-review queue."""

    def __init__(self, path: str | Path = FEEDBACK_PATH):
        self.path = Path(path)
        self._items: list[dict] = []
        self._load()

    def _load(self) -> None:
        try:
            if self.path.exists():
                self._items = json.loads(self.path.read_text(encoding="utf-8")).get("items", [])
        except Exception:
            self._items = []

    def _save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps({"version": "1.0", "items": self._items},
                                            indent=1), encoding="utf-8")
        except Exception:
            pass

    # ------------------------------------------------------- recording
    def record(self, message: str, verdict: str, analyst: str = "anonymous",
               comment: str = "", expected: str = "", predicted: str = "",
               run_id: str = "") -> dict:
        if verdict not in VERDICTS:
            raise ValueError(f"Unknown verdict: {verdict}. Use one of {VERDICTS}")
        item = {"id": uuid.uuid4().hex[:8], "message": (message or "")[:500],
                "verdict": verdict, "analyst": analyst, "comment": comment,
                "expected": expected, "predicted": predicted, "run_id": run_id,
                "timestamp": time.time(), "resolved": False}
        self._items.append(item)
        self._save()
        return item

    def resolve(self, feedback_id: str, resolution: str = "") -> bool:
        for item in self._items:
            if item["id"] == feedback_id:
                item["resolved"] = True
                item["resolution"] = resolution
                self._save()
                return True
        return False

    # ------------------------------------------------------- queue
    def review_queue(self, unresolved_only: bool = True) -> list[dict]:
        items = [i for i in self._items
                 if not unresolved_only or not i.get("resolved")]
        priority = {"false_negative": 0, "false_positive": 1,
                    "incorrect": 2, "needs_review": 3, "correct": 4}
        return sorted(items, key=lambda i: (priority.get(i["verdict"], 5),
                                            -i["timestamp"]))

    def stats(self) -> dict:
        by_verdict: dict[str, int] = {}
        for item in self._items:
            by_verdict[item["verdict"]] = by_verdict.get(item["verdict"], 0) + 1
        return {"total": len(self._items),
                "unresolved": sum(1 for i in self._items if not i.get("resolved")),
                "by_verdict": by_verdict}

    # ------------------------------------------------------- training data
    def export_training_candidates(self, min_verdicts: tuple = ("false_positive", "false_negative", "incorrect")) -> list[dict]:
        """High-quality relabel candidates for FUTURE retraining (manual gate)."""
        return [{"message": i["message"], "suggested_label": i["expected"],
                 "reason": i["verdict"], "comment": i["comment"]}
                for i in self._items if i["verdict"] in min_verdicts and i["expected"]]
