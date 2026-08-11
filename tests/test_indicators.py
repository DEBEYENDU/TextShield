"""Tests for the indicator engine."""
from __future__ import annotations

from app.ml.indicators import detect_indicators


def categories(indicators) -> set[str]:
    return {item["category"] for item in indicators}


def severities(indicators) -> dict[str, str]:
    return {item["indicator"]: item["severity"] for item in indicators}


def test_prize_claim_detected():
    indicators = detect_indicators("Congratulations! You have won a cash prize!")
    assert "prize" in categories(indicators)
    assert indicators[0]["severity"] in {"high", "medium"}


def test_urgency_detected():
    indicators = detect_indicators("Act immediately! Your account expires today.")
    assert "urgency" in categories(indicators)


def test_banking_phishing_detected():
    indicators = detect_indicators(
        "Dear customer, your bank account will be blocked. Verify immediately via link."
    )
    assert "banking" in categories(indicators)
    assert "phishing" in categories(indicators)


def test_otp_request_detected():
    indicators = detect_indicators("Share the OTP to complete KYC verification.")
    assert "credentials" in categories(indicators)


def test_job_scam_detected():
    indicators = detect_indicators(
        "Earn Rs.50,000 per month from home. Pay Rs.999 registration fee."
    )
    assert "job_scam" in categories(indicators)


def test_delivery_scam_detected():
    indicators = detect_indicators(
        "Your parcel is stuck at customs. Pay the delivery fee to reschedule."
    )
    assert "delivery" in categories(indicators)


def test_investment_scam_detected():
    indicators = detect_indicators(
        "Double your money in 30 days with guaranteed crypto returns."
    )
    assert "investment" in categories(indicators)


def test_loan_scam_detected():
    indicators = detect_indicators(
        "Instant loan of Rs.5,00,000 approved. Pay processing fee to release."
    )
    assert "loan_scam" in categories(indicators)


def test_ham_message_has_no_high_severity_indicators():
    indicators = detect_indicators("Hey, are we meeting at 5 PM today?")
    high = [i for i in indicators if i["severity"] == "high"]
    assert high == []


def test_structured_output_shape():
    indicators = detect_indicators("URGENT! You have won a FREE gift. Hurry!")
    for item in indicators:
        assert {"indicator", "severity", "evidence", "category"} <= set(item)


def test_empty_input():
    assert detect_indicators("") == []
    assert detect_indicators("   ") == []