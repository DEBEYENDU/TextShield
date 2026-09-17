"""Continuous Evaluation & Learning Framework (v4.0 / RFC-006).

Measures quality, detects false positives/negatives, compares versions,
tracks regressions, records analyst feedback and builds future training
datasets. It NEVER retrains models automatically — it collects
high-quality evidence for future retraining.
"""

from __future__ import annotations

__version__ = "4.0.0"
__rfc__ = "RFC-006"

# Evaluation sample categories (dataset collections).
CATEGORIES = [
    "ham", "spam", "phishing", "recruitment", "government", "banking",
    "healthcare", "courier", "invoices", "otp", "social_media", "corporate",
    "educational", "investment_scam", "lottery_scam", "refund_scam",
    "tech_support_scam", "bec",
]

# Benchmark collections (one command runs any of these).
COLLECTIONS = [
    "banking", "education", "government", "healthcare", "corporate",
    "courier", "recruitment", "phishing", "fraud", "bec",
]

EVAL_DIR = "data/eval"
RUNS_DIR = "data/eval/runs"
FEEDBACK_PATH = "data/eval/feedback.json"
