"""Tests for the risk engine."""
from __future__ import annotations

from app.services.risk_engine import compute_risk

SMALL = []
URL_CLEAN = []
URL_IP = [{"url": "http://185.220.101.5", "warnings": ["x"], "has_ip_host": True,
           "suspicious_tld": False, "is_shortened": False, "suspicious_chars": False}]

CRED_INTENT = {"label": "credential_request", "description": "d", "evidence": "enter your password"}


def test_ham_low_risk():
    result = compute_risk("HAM", 0.98, SMALL, URL_CLEAN, [])
    assert result["level"] == "LOW"
    assert result["score"] < 30


def test_spam_medium_at_least():
    result = compute_risk("SPAM", 0.6, SMALL, URL_CLEAN, [])
    assert result["level"] in {"MEDIUM", "HIGH"}


def test_spam_with_high_indicators_is_high():
    indicators = [
        {"indicator": "Prize / lottery claim", "severity": "high", "category": "prize"},
        {"indicator": "Excessive urgency", "severity": "high", "category": "urgency"},
        {"indicator": "Financial request", "severity": "medium", "category": "financial"},
    ]
    result = compute_risk("SPAM", 0.97, indicators, URL_IP, [])
    assert result["level"] == "HIGH"


def test_spam_with_banking_rag_evidence_is_high():
    indicators = [{"indicator": "Account verification request", "severity": "high",
                   "category": "phishing"}]
    evidence = [{"category": "banking_scams", "source": "note.md", "score": 0.6}]
    result = compute_risk("SPAM", 0.95, indicators, URL_CLEAN, evidence)
    assert result["level"] == "HIGH"


def test_factors_are_transparent():
    result = compute_risk("SPAM", 0.9, SMALL, URL_CLEAN, [])
    assert result["factors"] and any("0.9" in f or "90%" in f for f in result["factors"])


def test_score_is_scaled_to_100():
    indicators = [{"indicator": "x", "severity": "high", "category": "p"}] * 12
    result = compute_risk("SPAM", 1.0, indicators, URL_IP, [])
    assert result["score"] <= 100.0


def test_critical_requires_malicious_intent_and_corroboration():
    indicators = [{"indicator": "Password or credential request", "severity": "high",
                   "category": "credentials"}]
    result = compute_risk("SPAM", 0.97, indicators, URL_IP, [], intent=CRED_INTENT)
    assert result["level"] == "CRITICAL"
    assert result["score"] >= 50
    assert any("CRITICAL" in f for f in result["factors"])


def test_critical_never_granted_without_corroboration():
    # malicious intent but weak corroboration (no high indicator, no flagged URL)
    result = compute_risk("SPAM", 0.9, SMALL, URL_CLEAN, [], intent=CRED_INTENT)
    assert result["level"] != "CRITICAL"
    assert result["level"] in {"HIGH", "MEDIUM"}


def test_critical_not_granted_on_ham():
    result = compute_risk("HAM", 0.97, SMALL, URL_CLEAN, [], intent=CRED_INTENT)
    assert result["level"] != "CRITICAL"


def test_uncertain_when_model_is_guessing():
    # low confidence HAM, no strong signals either way -> UNCERTAIN
    result = compute_risk("HAM", 0.45, SMALL, URL_CLEAN, [])
    assert result["level"] == "UNCERTAIN"
    assert any("UNCERTAIN" in f for f in result["factors"])


def test_uncertain_not_used_when_evidence_exists():
    indicators = [{"indicator": "Excessive urgency", "severity": "high", "category": "urgency"}]
    result = compute_risk("HAM", 0.45, indicators, URL_CLEAN, [])
    assert result["level"] != "UNCERTAIN"


def test_uncertain_never_on_spam():
    result = compute_risk("SPAM", 0.45, SMALL, URL_CLEAN, [])
    assert result["level"] != "UNCERTAIN"