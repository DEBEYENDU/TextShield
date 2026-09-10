"""Decision policies: conservative / balanced / aggressive / enterprise /
research / custom. Loaded from JSON config — no hardcoded thresholds."""

from __future__ import annotations

import json
from pathlib import Path

DEFAULT_POLICY_PATH = Path("config/decision_policies.json")

POLICY_NAMES = ["conservative", "balanced", "aggressive", "enterprise",
                "research", "custom"]


class DecisionPolicy:
    """A named threshold + weight + review-sensitivity bundle."""

    def __init__(self, name: str, data: dict):
        self.name = name
        self.description = str(data.get("description", ""))
        self.spam_threshold = float(data.get("spam_threshold", 0.5))
        self.high_risk_threshold = float(data.get("high_risk_threshold", 0.65))
        self.review_threshold = float(data.get("review_threshold", 0.35))
        self.review_sensitivity = float(data.get("review_sensitivity", 1.0))
        self.base_weights = dict(data.get("base_weights", {}))
        self.min_review_confidence = float(data.get("min_review_confidence", 0.65))
        self.force_review_on_conflict = bool(data.get("force_review_on_conflict", False))
        self.force_review_min_risk = str(data.get("force_review_min_risk", "High"))
        self.extra = {k: v for k, v in data.items() if k not in {
            "description", "spam_threshold", "high_risk_threshold",
            "review_threshold", "review_sensitivity", "base_weights",
            "min_review_confidence", "force_review_on_conflict",
            "force_review_min_risk"}}

    def to_dict(self) -> dict:
        return {"name": self.name, "description": self.description,
                "spam_threshold": self.spam_threshold,
                "high_risk_threshold": self.high_risk_threshold,
                "review_threshold": self.review_threshold,
                "review_sensitivity": self.review_sensitivity,
                "base_weights": self.base_weights,
                "min_review_confidence": self.min_review_confidence,
                "force_review_on_conflict": self.force_review_on_conflict,
                "force_review_min_risk": self.force_review_min_risk}


def load_policies(path: str | Path = DEFAULT_POLICY_PATH) -> dict:
    """Load all policies + category profiles + fusion config from JSON."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return {"policies": {name: DecisionPolicy(name, data)
                         for name, data in raw.get("policies", {}).items()},
            "category_profiles": raw.get("category_profiles", {}),
            "fusion": raw.get("fusion", {})}


def get_policy(name: str = "balanced",
               path: str | Path = DEFAULT_POLICY_PATH,
               overrides: dict | None = None) -> DecisionPolicy:
    """Fetch a policy; ``custom`` merges file defaults with overrides."""
    bundle = load_policies(path)
    if name == "custom":
        base = bundle["policies"].get("balanced")
        data = {"description": "Custom policy (balanced + overrides)"}
        if base is not None:
            data.update({"spam_threshold": base.spam_threshold,
                         "high_risk_threshold": base.high_risk_threshold,
                         "review_threshold": base.review_threshold,
                         "review_sensitivity": base.review_sensitivity,
                         "base_weights": dict(base.base_weights),
                         "min_review_confidence": base.min_review_confidence})
        data.update(overrides or {})
        if "base_weights" in (overrides or {}):
            merged = dict(base.base_weights) if base else {}
            merged.update(overrides["base_weights"])
            data["base_weights"] = merged
        return DecisionPolicy("custom", data)
    if name not in bundle["policies"]:
        raise ValueError(f"Unknown policy '{name}'. Available: "
                         f"{sorted(bundle['policies'])}")
    policy = bundle["policies"][name]
    if overrides:
        data = policy.to_dict()
        data.update(overrides)
        return DecisionPolicy(policy.name, data)
    return policy
