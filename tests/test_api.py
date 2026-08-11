"""End-to-end API tests using FastAPI's TestClient."""
from __future__ import annotations

import pytest


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["model_ready"] is True


def test_analyze_spam(client):
    response = client.post(
        "/api/analyze",
        json={"input_type": "sms",
              "message": "Congratulations! You have won a cash prize. Click now."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["classification"] == "SPAM"
    assert body["confidence"] >= 0.5
    assert body["risk_level"] in {"MEDIUM", "HIGH"}
    assert body["explanation"]
    assert body["recommended_action"]
    assert body["explanation_source"] in {"llm", "template"}
    assert "indicators" in body and "urls" in body


def test_analyze_ham(client):
    response = client.post(
        "/api/analyze",
        json={"input_type": "text", "message": "Hey, are we meeting at 5 PM today?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["classification"] == "HAM"
    assert body["risk_level"] == "LOW"


def test_analyze_banking_scam(client):
    response = client.post(
        "/api/analyze",
        json={"input_type": "sms",
              "message": "Your bank account will be blocked. Verify immediately using this link."},
    )
    assert response.status_code == 200
    assert response.json()["classification"] == "SPAM"


def test_analyze_job_scam(client):
    response = client.post(
        "/api/analyze",
        json={"input_type": "sms",
              "message": "Earn Rs.50,000 per month from home. Pay Rs.999 registration fee."},
    )
    assert response.status_code == 200
    assert response.json()["classification"] == "SPAM"


def test_analyze_email_with_fields(client):
    response = client.post(
        "/api/analyze",
        json={"input_type": "email",
              "subject": "Your account requires verification",
              "sender": "support@secure-update-bank.xyz",
              "body": "Dear customer, verify your account within 24 hours to avoid blocking."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["classification"] == "SPAM"
    assert body["message_type"] == "email"


def test_analyze_url_detection(client):
    response = client.post(
        "/api/analyze",
        json={"input_type": "sms",
              "message": "Claim your FREE gift at http://bit.ly/xyz123 now!"},
    )
    body = response.json()
    assert len(body["urls"]) == 1
    assert body["urls"][0]["is_shortened"] is True


def test_empty_message_rejected(client):
    response = client.post("/api/analyze", json={"input_type": "text", "message": ""})
    assert response.status_code == 422


def test_missing_all_fields_rejected(client):
    response = client.post("/api/analyze", json={"input_type": "text"})
    assert response.status_code == 422


def test_history_roundtrip(client):
    client.post("/api/analyze", json={"input_type": "text", "message": "Hello"})
    response = client.get("/api/history?limit=10")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    entry = body["items"][0]
    assert entry["message_hash"]

    delete_response = client.delete(f"/api/history/{entry['id']}")
    assert delete_response.status_code == 200
    assert client.get("/api/history?limit=10").json()["total"] == body["total"] - 1


def test_history_delete_missing(client):
    assert client.delete("/api/history/999999").status_code == 404


def test_stats_endpoint(client):
    response = client.get("/api/stats")
    assert response.status_code == 200
    body = response.json()
    assert {"total_analyses", "spam_count", "ham_count", "risk_distribution",
            "message_type_distribution"} <= set(body)


def test_model_info_endpoint(client):
    response = client.get("/api/model-info")
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is True
    assert body["algorithm"] in {"Multinomial Naive Bayes", "Logistic Regression", "Linear SVM"}
    assert body["metrics"]["accuracy"] > 0.5


def test_raw_email_auto_detection_in_text_tab(client):
    # a raw email pasted into the generic text box must be auto-detected
    raw = (
        "From: \"Paytm Support\" <support@paytm-verify.xyz>\n"
        "To: victim@example.com\n"
        "Subject: Your wallet needs KYC verification\n\n"
        "Dear customer, your wallet will be blocked in 24 hours. "
        "Verify your account via the link below."
    )
    response = client.post(
        "/api/analyze", json={"input_type": "text", "message": raw}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["message_type"] == "email"
    assert body["classification"] == "SPAM"


def test_raw_email_explicit_tab(client):
    raw = (
        "From: noreply@example.org\nSubject: Hello\n\nThis is a simple body "
        "about our next team meeting on Friday at 10 AM."
    )
    response = client.post(
        "/api/analyze", json={"input_type": "email", "email_raw": raw}
    )
    assert response.status_code == 200
    assert response.json()["message_type"] == "email"


def test_home_page_served(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "TextShield" in response.text


def test_unknown_route_404(client):
    assert client.get("/api/nonexistent").status_code == 404