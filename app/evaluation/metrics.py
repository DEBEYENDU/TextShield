"""Evaluation metrics: accuracy, precision, recall, F1, ROC-AUC, balanced
accuracy, FPR/FNR, per-category and per-agent accuracy, calibration and
inference timing. Pure functions over (y_true, y_pred) pairs."""

from __future__ import annotations

import math


def _safe_div(num: float, den: float) -> float:
    return num / den if den else 0.0


def binary_counts(y_true: list[str], y_pred: list[str],
                  positive: str = "SPAM") -> dict:
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == positive and p == positive)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t != positive and p != positive)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t != positive and p == positive)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == positive and p != positive)
    return {"tp": tp, "tn": tn, "fp": fp, "fn": fn, "n": len(y_true)}


def classification_metrics(y_true: list[str], y_pred: list[str],
                           y_score: list[float] | None = None) -> dict:
    """y_score: P(SPAM) per sample for ROC-AUC (optional)."""
    counts = binary_counts(y_true, y_pred)
    tp, tn, fp, fn = counts["tp"], counts["tn"], counts["fp"], counts["fn"]
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    specificity = _safe_div(tn, tn + fp)
    out = {
        **counts,
        "accuracy": round(_safe_div(tp + tn, counts["n"]), 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(_safe_div(2 * precision * recall, precision + recall), 4),
        "balanced_accuracy": round((recall + specificity) / 2, 4),
        "false_positive_rate": round(_safe_div(fp, fp + tn), 4),
        "false_negative_rate": round(_safe_div(fn, fn + tp), 4),
        "specificity": round(specificity, 4),
    }
    auc = roc_auc(y_true, y_score) if y_score else None
    out["roc_auc"] = round(auc, 4) if auc is not None else None
    return out


def roc_auc(y_true: list[str], y_score: list[float],
            positive: str = "SPAM") -> float | None:
    """Mann-Whitney ROC-AUC (no hard sklearn dependency here)."""
    pos = [s for t, s in zip(y_true, y_score) if t == positive]
    neg = [s for t, s in zip(y_true, y_score) if t != positive]
    if not pos or not neg:
        return None
    wins = sum(1 if p > n else 0.5 if p == n else 0 for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def per_category_accuracy(records: list[dict],
                          category_key: str = "collection") -> dict:
    groups: dict[str, dict] = {}
    for record in records:
        key = str(record.get(category_key, "unknown"))
        bucket = groups.setdefault(key, {"correct": 0, "total": 0})
        bucket["total"] += 1
        if record.get("expected") == record.get("predicted"):
            bucket["correct"] += 1
    return {k: {"accuracy": round(_safe_div(v["correct"], v["total"]), 4),
                **v} for k, v in sorted(groups.items())}


def per_agent_accuracy(records: list[dict]) -> dict:
    """Fraction of records where each agent's lean matched the outcome."""
    agents: dict[str, dict] = {}
    for record in records:
        expected = record.get("expected")
        for name, opinion in (record.get("agent_opinions", {}) or {}).items():
            bucket = agents.setdefault(name, {"agree": 0, "total": 0})
            bucket["total"] += 1
            lean_spam = opinion.get("risk_score", 0.0) >= 0.5
            if (expected == "SPAM") == lean_spam:
                bucket["agree"] += 1
    return {k: {"accuracy": round(_safe_div(v["agree"], v["total"]), 4), **v}
            for k, v in sorted(agents.items())}


def confidence_calibration(records: list[dict], bins: int = 5) -> dict:
    """Expected calibration error over confidence bins."""
    buckets: list[dict] = [{"n": 0, "correct": 0, "conf_sum": 0.0}
                           for _ in range(bins)]
    for record in records:
        conf = float(record.get("confidence", 0.0) or 0.0)
        idx = min(int(conf * bins), bins - 1)
        buckets[idx]["n"] += 1
        buckets[idx]["conf_sum"] += conf
        if record.get("expected") == record.get("predicted"):
            buckets[idx]["correct"] += 1
    ece = 0.0
    total = sum(b["n"] for b in buckets) or 1
    rows = []
    for i, bucket in enumerate(buckets):
        if not bucket["n"]:
            rows.append({"bin": f"{i / bins:.1f}-{(i + 1) / bins:.1f}",
                         "n": 0, "accuracy": None, "avg_confidence": None})
            continue
        acc = bucket["correct"] / bucket["n"]
        avg_conf = bucket["conf_sum"] / bucket["n"]
        ece += (bucket["n"] / total) * abs(acc - avg_conf)
        rows.append({"bin": f"{i / bins:.1f}-{(i + 1) / bins:.1f}",
                     "n": bucket["n"], "accuracy": round(acc, 4),
                     "avg_confidence": round(avg_conf, 4)})
    return {"expected_calibration_error": round(ece, 4), "bins": rows}


def timing_stats(records: list[dict]) -> dict:
    times = [float(r.get("inference_ms", 0.0) or 0.0) for r in records]
    if not times:
        return {"avg_ms": 0.0, "max_ms": 0.0, "n": 0}
    ordered = sorted(times)
    return {"avg_ms": round(sum(times) / len(times), 2),
            "p50_ms": round(ordered[len(ordered) // 2], 2),
            "max_ms": round(ordered[-1], 2), "n": len(times)}


def log_loss_bits(_y_true: list[str], _y_score: list[float]) -> float:
    """Mean binary log-loss in bits (diagnostic, lower is better)."""
    eps = 1e-9
    losses = []
    for label, score in zip(_y_true, _y_score):
        p = min(max(score, eps), 1 - eps)
        losses.append(-(math.log2(p) if label == "SPAM" else math.log2(1 - p)))
    return round(sum(losses) / len(losses), 4) if losses else 0.0
