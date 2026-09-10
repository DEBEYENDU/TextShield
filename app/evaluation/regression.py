"""Regression testing: compare old vs new runs sample-by-sample.

Reports improved / regressed / unchanged counts plus per-sample deltas.
``check_threshold`` fails CI when regressions exceed the allowed rate.
"""

from __future__ import annotations

from app.evaluation.metrics import classification_metrics


def compare_runs(old_run: dict, new_run: dict) -> dict:
    """Diff two runs on shared sample ids."""
    old = {r["id"]: r for r in old_run.get("records", [])}
    new = {r["id"]: r for r in new_run.get("records", [])}
    shared = sorted(set(old) & set(new))
    improved, regressed, unchanged = [], [], []
    for sample_id in shared:
        was_right = old[sample_id].get("expected") == old[sample_id].get("predicted")
        is_right = new[sample_id].get("expected") == new[sample_id].get("predicted")
        entry = {"id": sample_id,
                 "old": old[sample_id].get("predicted"),
                 "new": new[sample_id].get("predicted"),
                 "expected": new[sample_id].get("expected")}
        if is_right and not was_right:
            improved.append(entry)
        elif was_right and not is_right:
            regressed.append(entry)
        else:
            unchanged.append(entry)
    old_metrics = classification_metrics(
        [old[i].get("expected", "") for i in shared],
        [old[i].get("predicted", "") for i in shared]) if shared else {}
    new_metrics = classification_metrics(
        [new[i].get("expected", "") for i in shared],
        [new[i].get("predicted", "") for i in shared]) if shared else {}
    return {
        "old_run": old_run.get("run_id"), "new_run": new_run.get("run_id"),
        "old_fingerprint": old_run.get("fingerprint_id"),
        "new_fingerprint": new_run.get("fingerprint_id"),
        "shared_samples": len(shared),
        "improved": improved, "regressed": regressed,
        "improved_count": len(improved), "regressed_count": len(regressed),
        "unchanged_count": len(unchanged),
        "regression_rate": round(len(regressed) / len(shared), 4) if shared else 0.0,
        "improvement_rate": round(len(improved) / len(shared), 4) if shared else 0.0,
        "old_metrics": {k: old_metrics.get(k) for k in ("accuracy", "f1", "false_positive_rate", "false_negative_rate")},
        "new_metrics": {k: new_metrics.get(k) for k in ("accuracy", "f1", "false_positive_rate", "false_negative_rate")},
        "accuracy_delta": round((new_metrics.get("accuracy", 0) or 0) - (old_metrics.get("accuracy", 0) or 0), 4),
    }


def check_threshold(comparison: dict, max_regression_rate: float = 0.02) -> dict:
    """CI gate: pass when regression rate is within budget."""
    rate = comparison.get("regression_rate", 0.0)
    passed = rate <= max_regression_rate
    return {"passed": passed, "regression_rate": rate,
            "threshold": max_regression_rate,
            "message": ("OK: regression rate within budget"
                        if passed else
                        f"FAIL: regression rate {rate:.2%} exceeds {max_regression_rate:.2%}")}
