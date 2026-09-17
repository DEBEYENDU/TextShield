from __future__ import annotations

from typing import Dict, Any, List, Optional
from datetime import datetime


def get_threat_score_distribution() -> Dict[str, Any]:
    """Return threat score distribution for dashboard charts."""
    return {
        "labels": ["Low", "Medium", "High", "Critical"],
        "data": [520, 410, 210, 107],
        "background_colors": ["#4e73df", "#1cc88a", "#36b9cc", "#f6c23e"],
    }


def get_provider_comparison(ioc_value: str) -> Dict[str, Any]:
    """Return comparison of provider responses for a given IOC.

    In production this would look up the IOC across all active providers.
    """
    # Mock data
    return {
        "ioc_value": ioc_value,
        "providers": {
            "google_safe_browsing": {
                "threat_status": "malicious",
                "confidence": 0.85,
                "latency_ms": 120,
            },
            "virustotal": {
                "threat_status": "malicious",
                "confidence": 0.92,
                "latency_ms": 210,
            },
            "openphish": {
                "threat_status": "benign",
                "confidence": 0.45,
                "latency_ms": 300,
            },
        },
        "agreement": "google_safe_browsing & virustotal agree (malicious)",
        "disagreement": "openphish reports benign",
        "confidence_range": [0.45, 0.92],
    }