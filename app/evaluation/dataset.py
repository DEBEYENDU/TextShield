"""Dataset manager: unified evaluation samples across collections.

Each sample stores: message, expected label, message type, intent,
difficulty, source, notes. Collections live in ``data/eval/*.json``;
legacy v4 benchmark files are importable as collections too.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from app.evaluation import EVAL_DIR


@dataclass
class EvalSample:
    id: str
    message: str
    expected_label: str  # "HAM" | "SPAM"
    collection: str = "general"
    message_type: str = "Unknown"
    intent: str = "Inform"
    difficulty: str = "medium"  # easy | medium | hard
    source: str = "manual"
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# Legacy benchmark file -> (collection, label) mapping for import.
_LEGACY_IMPORTS = {
    "understanding_benchmark.json": ("understanding", {
        "legitimate": "HAM", "malicious": "SPAM"}),
    "behavior_benchmark.json": ("behavior", {
        "legitimate": "HAM", "malicious": "SPAM"}),
    "agent_benchmark.json": ("agents", {
        "legitimate": "HAM", "malicious": "SPAM"}),
}


class DatasetManager:
    """Load, filter and validate evaluation datasets."""

    def __init__(self, eval_dir: str | Path = EVAL_DIR):
        self.eval_dir = Path(eval_dir)

    # ------------------------------------------------------- loading
    # Files in the eval dir that are stores, not datasets.
    NON_COLLECTIONS = {"feedback"}

    def collections(self) -> list[str]:
        names = [p.stem for p in sorted(self.eval_dir.glob("*.json"))
                 if p.stem != "runs" and p.stem not in self.NON_COLLECTIONS]
        return names

    def load_collection(self, name: str) -> list[EvalSample]:
        path = self.eval_dir / f"{name}.json"
        if not path.exists():
            raise FileNotFoundError(f"Evaluation collection not found: {name}")
        return self._parse_collection(name, json.loads(path.read_text(encoding="utf-8")))

    def load_all(self) -> list[EvalSample]:
        samples: list[EvalSample] = []
        for name in self.collections():
            try:
                samples.extend(self.load_collection(name))
            except Exception:
                continue
        return samples

    def filter(self, samples: list[EvalSample], category: str | None = None,
               difficulty: str | None = None) -> list[EvalSample]:
        out = samples
        if category:
            out = [s for s in out if s.collection == category]
        if difficulty:
            out = [s for s in out if s.difficulty == difficulty]
        return out

    def import_legacy_benchmarks(self, data_dir: str | Path = "data") -> list[EvalSample]:
        """Convert v4 *_benchmark.json files into unified samples."""
        samples: list[EvalSample] = []
        for filename, (collection, label_map) in _LEGACY_IMPORTS.items():
            path = Path(data_dir) / filename
            if not path.exists():
                continue
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            for slice_name, label in label_map.items():
                for item in raw.get(slice_name, []):
                    text = item.get("text", "")
                    if not text:
                        continue
                    samples.append(EvalSample(
                        id=f"legacy-{collection}-{item.get('id', len(samples))}",
                        message=text,
                        expected_label=label,
                        collection=collection,
                        message_type=item.get("expected_type", "Unknown") or "Unknown",
                        intent=self._first(item.get("expected_intent", "Inform")),
                        difficulty="medium",
                        source=f"legacy:{filename}",
                        notes="imported from v4 benchmark",
                    ))
        return samples

    # ------------------------------------------------------- parsing
    @staticmethod
    def _first(value) -> str:
        if isinstance(value, list):
            return str(value[0]) if value else "Inform"
        return str(value or "Inform")

    def _parse_collection(self, name: str, raw: dict) -> list[EvalSample]:
        samples: list[EvalSample] = []
        items = raw.get("samples", raw.get("legitimate", []) + raw.get("malicious", []))
        # legacy-shaped collections carry expected_* fields instead
        for i, item in enumerate(items):
            if "message" not in item and "text" not in item:
                continue
            label = item.get("expected_label") or item.get("label") or "HAM"
            samples.append(EvalSample(
                id=str(item.get("id", f"{name}-{i}")),
                message=item.get("message", item.get("text", "")),
                expected_label=str(label).upper(),
                collection=name,
                message_type=item.get("message_type",
                                      item.get("expected_type", "Unknown")) or "Unknown",
                intent=self._first(item.get("intent", item.get("expected_intent", "Inform"))),
                difficulty=item.get("difficulty", "medium"),
                source=item.get("source", f"collection:{name}"),
                notes=item.get("notes", ""),
            ))
        return [s for s in samples if s.message.strip()
                and s.expected_label in {"HAM", "SPAM"}]

    # ------------------------------------------------------- validation
    @staticmethod
    def validate(samples: list[EvalSample]) -> dict:
        issues = []
        seen = set()
        for s in samples:
            if s.id in seen:
                issues.append(f"duplicate id: {s.id}")
            seen.add(s.id)
            if s.expected_label not in {"HAM", "SPAM"}:
                issues.append(f"bad label {s.id}: {s.expected_label}")
            if len(s.message.strip()) < 10:
                issues.append(f"message too short: {s.id}")
        return {"samples": len(samples), "issues": issues, "valid": not issues}

    def stats(self) -> dict:
        samples = self.load_all()
        by_collection: dict[str, int] = {}
        by_label: dict[str, int] = {"HAM": 0, "SPAM": 0}
        for s in samples:
            by_collection[s.collection] = by_collection.get(s.collection, 0) + 1
            by_label[s.expected_label] = by_label.get(s.expected_label, 0) + 1
        return {"total": len(samples), "by_collection": by_collection,
                "by_label": by_label,
                "legacy_available": len(self.import_legacy_benchmarks())}
