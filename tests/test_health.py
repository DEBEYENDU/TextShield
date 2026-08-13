"""Tests for the system health endpoints."""
from __future__ import annotations

import pytest

from app.core.settings import settings
from app.database.base import init_db


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DATABASE_URL", f"sqlite:///{tmp_path / 'h.db'}")
    init_db()
    yield


def test_health_endpoint_shape(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert {"version", "model_ready", "rag_ready", "history_rows"} <= set(body)


def test_readiness_endpoint(client):
    response = client.get("/api/readiness")
    assert response.status_code == 200
    body = response.json()
    assert body["ready"] is True
    assert body["components"]["database"] is True


def test_version_endpoint(client):
    response = client.get("/api/version")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "TextShield"
    assert body["version"]


def test_config_status_endpoint(client):
    response = client.get("/api/config/status")
    assert response.status_code == 200
    body = response.json()
    assert {"environment", "model_path", "embedding_provider", "llm_provider"} <= set(body)


def test_app_status_endpoint(client):
    response = client.get("/api/status")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "running"
    assert isinstance(body["uptime_seconds"], float)
    assert "feature_flags" in body


def test_unknown_route_envelope(client):
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "http_error"
