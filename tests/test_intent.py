"""Tests for sender intent extraction (V2.0)."""
from __future__ import annotations

from app.ml.intent import detect_intent, is_malicious_intent


def test_credential_request():
    result = detect_intent("Your account is blocked. Enter your password and OTP to verify.")
    assert result["label"] == "credential_request"
    assert result["evidence"]
    assert is_malicious_intent(result["label"])


def test_money_transfer():
    result = detect_intent("Pay the processing fee of Rs.499 to release your prize money.")
    assert result["label"] == "money_transfer"
    assert is_malicious_intent(result["label"])


def test_download_install():
    result = detect_intent("Download our new app from the link below to track your parcel.")
    assert result["label"] == "download_install"
    assert is_malicious_intent(result["label"])


def test_personal_data():
    result = detect_intent("Share your Aadhaar number and PAN card to update your account.")
    assert result["label"] == "personal_data"
    assert is_malicious_intent(result["label"])


def test_prize_claim():
    result = detect_intent("Congratulations! You won the lottery. Contact us to claim your prize.")
    assert result["label"] == "prize_claim"
    assert is_malicious_intent(result["label"])


def test_confirmation_request():
    result = detect_intent("Please verify your account details to continue using our service.")
    assert result["label"] == "confirmation_request"


def test_engagement_is_not_malicious():
    result = detect_intent("Hi, please reply to this message to confirm your attendance tomorrow.")
    assert result["label"] == "engagement"
    assert not is_malicious_intent(result["label"])


def test_other_without_request():
    result = detect_intent("The weather in Delhi is sunny today with light clouds.")
    assert result["label"] == "other"
    assert not is_malicious_intent(result["label"])


def test_empty_input():
    result = detect_intent("   ")
    assert result["label"] == "other"


def test_dangerous_intent_wins_over_benign():
    # credential request must take priority over engagement phrasing
    result = detect_intent("Reply with your OTP to confirm your booking for the event.")
    assert result["label"] == "credential_request"