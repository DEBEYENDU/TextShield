"""Confusion analysis: matrix plus grouped false-positive and
false-negative breakdowns with per-group statistics."""

from __future__ import annotations

from app.evaluation.metrics import binary_counts

# FP grouping: by understanding message type (benign message misjudged).
FP_GROUPS = ["Recruitment", "Educational Announcement", "Government Advisory",
             "Bank Notification", "Courier / Logistics", "Corporate",
             "OTP / Authentication", "Healthcare", "Personal Communication",
             "Unknown"]

# FN grouping: by threat family (missed attack pattern).
FN_GROUPS = ["credential_harvesting", "credential_request", "lottery",
             "investment_scam", "refund_scam", "tech_support", "crypto_scam",
             "ceo_fraud", "bec", "phishing", "romance_scam", "qr_scam",
             "other"]


def confusion_matrix(records: list[dict]) -> dict:
    counts = binary_counts([r.get("expected", "") for r in records],
                           [r.get("predicted", "") for r in records])
    return {"labels": ["HAM", "SPAM"],
            "matrix": [[counts["tn"], counts["fp"]],
                       [counts["fn"], counts["tp"]]],
            **counts}


def false_positives(records: list[dict]) -> dict:
    """Group benign messages predicted SPAM by message type."""
    fps = [r for r in records
           if r.get("expected") == "HAM" and r.get("predicted") == "SPAM"]
    by_type: dict[str, list] = {}
    for record in fps:
        key = str(record.get("message_type", "Unknown"))
        by_type.setdefault(key, []).append(record.get("id"))
    total_ham = sum(1 for r in records if r.get("expected") == "HAM") or 1
    return {"count": len(fps),
            "rate": round(len(fps) / total_ham, 4),
            "by_message_type": {k: {"count": len(v), "ids": v[:10]}
                                for k, v in sorted(by_type.items(),
                                                   key=lambda kv: -len(kv[1]))},
            "statistics": {"total_ham": total_ham,
                           "worst_type": max(by_type, key=lambda k: len(by_type[k]))
                           if by_type else None}}


def false_negatives(records: list[dict]) -> dict:
    """Group missed SPAM by threat family / scam pattern."""
    fns = [r for r in records
           if r.get("expected") == "SPAM" and r.get("predicted") == "HAM"]
    by_family: dict[str, list] = {}
    for record in fns:
        families = record.get("threat_families", []) or ["other"]
        key = str(families[0]) if families else "other"
        by_family.setdefault(key, []).append(record.get("id"))
    total_spam = sum(1 for r in records if r.get("expected") == "SPAM") or 1
    return {"count": len(fns),
            "rate": round(len(fns) / total_spam, 4),
            "by_threat_family": {k: {"count": len(v), "ids": v[:10]}
                                 for k, v in sorted(by_family.items(),
                                                    key=lambda kv: -len(kv[1]))},
            "statistics": {"total_spam": total_spam,
                           "worst_family": max(by_family,
                                               key=lambda k: len(by_family[k]))
                           if by_family else None}}


def error_records(records: list[dict]) -> list[dict]:
    """Minimal review payload for every misclassification."""
    return [{"id": r.get("id"), "expected": r.get("expected"),
             "predicted": r.get("predicted"),
             "confidence": r.get("confidence"),
             "message_type": r.get("message_type"),
             "threat_families": r.get("threat_families", []),
             "message": str(r.get("message", ""))[:200]}
            for r in records if r.get("expected") != r.get("predicted")]
