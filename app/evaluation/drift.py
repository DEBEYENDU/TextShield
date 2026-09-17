"""Drift detection: snapshot distributions from run records and flag
unusual shifts (message types, threat bands, languages, entities,
confidence) via Population Stability Index."""

from __future__ import annotations

import math

PSI_WARN = 0.25
PSI_ALARM = 0.5


def snapshot(records: list[dict]) -> dict:
    """Build a distribution snapshot from evaluation records."""
    dist: dict[str, dict[str, int]] = {
        "message_type": {}, "threat_band": {}, "language": {},
        "intent": {}, "confidence_bin": {}, "collection": {},
    }
    for record in records:
        _bump(dist["message_type"], str(record.get("message_type", "Unknown")))
        threat = float(record.get("threat_score", 0.0) or 0.0)
        band = ("low" if threat < 0.35 else "medium" if threat < 0.6 else "high")
        _bump(dist["threat_band"], band)
        _bump(dist["language"], str(record.get("language", "en")))
        _bump(dist["intent"], str(record.get("intent", "Inform")))
        conf = float(record.get("confidence", 0.0) or 0.0)
        _bump(dist["confidence_bin"], f"{min(int(conf * 5), 4)}")
        _bump(dist["collection"], str(record.get("collection", "general")))
    return {"n": len(records), "distributions": dist}


def _bump(bucket: dict[str, int], key: str) -> None:
    bucket[key] = bucket.get(key, 0) + 1


def psi(expected: dict[str, int], actual: dict[str, int]) -> float:
    """Population Stability Index between two count distributions."""
    total_e = sum(expected.values()) or 1
    total_a = sum(actual.values()) or 1
    keys = set(expected) | set(actual)
    total = 0.0
    for key in keys:
        e = max(expected.get(key, 0) / total_e, 1e-6)
        a = max(actual.get(key, 0) / total_a, 1e-6)
        total += (a - e) * math.log(a / e)
    return round(total, 4)


def detect_drift(baseline: dict, current: dict) -> dict:
    """Compare snapshots; flag dimensions with unusual change."""
    flags = []
    scores = {}
    for dim, base_dist in baseline.get("distributions", {}).items():
        cur_dist = current.get("distributions", {}).get(dim, {})
        score = psi(base_dist, cur_dist)
        scores[dim] = score
        if score >= PSI_ALARM:
            flags.append({"dimension": dim, "psi": score, "level": "alarm",
                          "message": f"{dim} distribution shifted sharply ({score})"})
        elif score >= PSI_WARN:
            flags.append({"dimension": dim, "psi": score, "level": "warning",
                          "message": f"{dim} distribution drifted ({score})"})
    # confidence shift: mean absolute movement
    return {"psi_scores": scores, "flags": flags,
            "drifted": bool(flags),
            "baseline_n": baseline.get("n", 0), "current_n": current.get("n", 0)}
