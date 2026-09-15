"""Legitimate message protection rules.

Prevents false positives for recruitment, campus drive, education, etc.
"""

from __future__ import annotations

LEGITIMATE_KEYWORDS = {
    "recruitment", "placement", "campus drive", "internship", "job offer",
    "admission", "exam", "scholarship", "university", "college", "school",
    "teacher", "professor", "student", "career fair", "hiring",
}


def is_legitimate_context(text: str) -> bool:
    lowered = text.lower()
    return any(kw in lowered for kw in LEGITIMATE_KEYWORDS)


def protect_score(base_score: float, text: str) -> float:
    if is_legitimate_context(text):
        return max(0.0, base_score - 0.15)
    return base_score
