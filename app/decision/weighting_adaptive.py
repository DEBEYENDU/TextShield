"""Adaptive evidence weighting: policy base × category profile × reliability.

No static weights: the same evidence weighs differently for a recruitment
notice (legitimacy/agents/graph up, raw threat down) versus a bank alert
(threat intel/ML/entities up). Floors keep every source audible; caps
prevent any single source from dominating.
"""

from __future__ import annotations

from app.decision.policy import DecisionPolicy, load_policies

SOURCES = ["ml", "rag", "graph", "threat_intel", "behavior", "intent",
           "message_type", "entities", "llm", "agents", "history",
           "legitimacy"]


def adaptive_weights(category: str, policy: DecisionPolicy,
                     confidences: dict | None = None,
                     config_path: str | None = None) -> dict:
    """Compute per-source weights for a message category under a policy."""
    bundle = load_policies() if config_path is None else load_policies(config_path)
    fusion_cfg = bundle.get("fusion", {})
    floor = float(fusion_cfg.get("weight_floor", 0.4))
    cap = float(fusion_cfg.get("weight_cap", 1.8))
    profile = bundle.get("category_profiles", {}).get(category or "Unknown",
                                                      bundle.get("category_profiles", {}).get("Unknown", {}))
    confidences = confidences or {}
    weights = {}
    for source in SOURCES:
        base = float(policy.base_weights.get(source, 0.8))
        multiplier = float(profile.get(source, 1.0))
        reliability = 0.5 + 0.5 * float(confidences.get(source, 0.5))
        weights[source] = round(max(floor, min(cap, base * multiplier * reliability)), 3)
    return weights


def capped_shares(weights: dict, max_share: float = 0.35) -> dict:
    """Normalize weights; clip any source above max_share, redistribute."""
    total = sum(weights.values()) or 1e-9
    shares = {k: v / total for k, v in weights.items()}
    for _ in range(10):
        over = {k: s for k, s in shares.items() if s > max_share}
        if not over:
            break
        excess = sum(s - max_share for s in over.values())
        for k in over:
            shares[k] = max_share
        under = [k for k in shares if k not in over]
        under_total = sum(shares[k] for k in under) or 1e-9
        for k in under:
            shares[k] += excess * (shares[k] / under_total)
    total = sum(shares.values()) or 1e-9
    return {k: round(v / total, 4) for k, v in shares.items()}
