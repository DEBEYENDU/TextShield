"""Lightweight agent memory: previous analyses, similar messages,
retrieval history, agent confidence and future feedback."""

from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path

_TOKEN = re.compile(r"[a-z]{3,}")


def _message_hash(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8", errors="replace")).hexdigest()[:16]


def _tokens(text: str) -> set[str]:
    return set(_TOKEN.findall((text or "").lower()))


class AgentMemory:
    """JSON-backed recall: exact hash hits + token-overlap similar search."""

    def __init__(self, path: str | Path = "data/agent_memory.json",
                 max_records: int = 500):
        self.path = Path(path)
        self.max_records = max_records
        self._records: list[dict] = []
        self._load()

    # ------------------------------------------------------- persistence
    def _load(self) -> None:
        try:
            if self.path.exists():
                data = json.loads(self.path.read_text(encoding="utf-8"))
                self._records = data.get("records", [])
        except Exception:
            self._records = []

    def _save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(
                {"version": "1.0", "records": self._records[-self.max_records:]},
                indent=1), encoding="utf-8")
        except Exception:
            pass

    # ------------------------------------------------------- recall
    def recall_exact(self, text: str) -> dict | None:
        digest = _message_hash(text)
        for record in reversed(self._records):
            if record.get("hash") == digest:
                return record
        return None

    def recall_similar(self, text: str, top_k: int = 3,
                       min_overlap: float = 0.25) -> list[dict]:
        needle = _tokens(text)
        if not needle:
            return []
        scored = []
        for record in self._records:
            hay = set(record.get("tokens", []))
            if not hay:
                continue
            overlap = len(needle & hay) / max(len(needle | hay), 1)
            if overlap >= min_overlap:
                scored.append((overlap, record))
        scored.sort(key=lambda t: -t[0])
        return [{"overlap": round(s, 3),
                 "consensus": r.get("consensus"),
                 "risk": r.get("risk"),
                 "category": r.get("category")}
                for s, r in scored[:top_k]]

    def agent_confidence_history(self, agent_name: str, limit: int = 20) -> list[float]:
        out = []
        for record in reversed(self._records):
            agents = record.get("agents", {})
            if agent_name in agents:
                out.append(agents[agent_name])
                if len(out) >= limit:
                    break
        return out

    # ------------------------------------------------------- learning
    def remember(self, text: str, category: str, risk: str, consensus: str,
                 agent_confidences: dict, retrieval_terms: list | None = None,
                 feedback: dict | None = None) -> None:
        self._records.append({
            "hash": _message_hash(text),
            "tokens": sorted(_tokens(text))[:60],
            "category": category, "risk": risk, "consensus": consensus,
            "agents": {k: round(float(v), 3) for k, v in agent_confidences.items()},
            "retrieval_terms": list(retrieval_terms or [])[:10],
            "feedback": feedback or {},
            "timestamp": time.time(),
        })
        self._records = self._records[-self.max_records:]
        self._save()

    def record_feedback(self, text: str, feedback: dict) -> bool:
        """Future feedback hook: attach human verdict to a past analysis."""
        digest = _message_hash(text)
        for record in reversed(self._records):
            if record.get("hash") == digest:
                record["feedback"] = feedback
                self._save()
                return True
        return False

    def stats(self) -> dict:
        return {"records": len(self._records), "path": str(self.path)}


agent_memory = AgentMemory()
