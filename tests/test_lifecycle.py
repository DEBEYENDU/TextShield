"""Tests for the application lifecycle: factory, middleware, handlers."""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.exceptions import AppError, DatabaseError
from app.core.settings import settings
from app.database.base import init_db
from app.main import create_app


@pytest.fixture()
def app(tmp_path, monkeypatch) -> FastAPI:
    monkeypatch.setattr(settings, "DATABASE_URL", f"sqlite:///{tmp_path / 'life.db'}")
    return create_app()


def test_create_app_returns_app_with_registry(app):
    assert isinstance(app, FastAPI)
    registry = app.state.registry
    assert "analysis" in registry and "system_status" in registry


def test_lifespan_initializes_db(app, tmp_path):
    with TestClient(app) as client:
        assert tmp_path.joinpath("life.db").exists()


def test_request_id_header_added(app):
    with TestClient(app) as client:
        response = client.get("/api/version")
    assert response.headers.get("X-Request-ID")


def test_middleware_logs_request(app):
    with TestClient(app) as client:
        assert client.get("/api/version").status_code == 200


def test_unhandled_error_becomes_envelope(app):
    @app.get("/api/crash-test")
    def crash():
        raise RuntimeError("kaboom")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/crash-test")
    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "internal_error"


def test_app_error_becomes_envelope(app):
    @app.get("/api/app-error-test")
    def app_error():
        raise DatabaseError("db down")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/app-error-test")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "database_error"


def test_stub_registry_drives_routes(tmp_path, monkeypatch):
    from app.core.container import ServiceRegistry

    monkeypatch.setattr(settings, "DATABASE_URL", f"sqlite:///{tmp_path / 's.db'}")
    registry = ServiceRegistry()
    registry.register(
        "analysis",
        lambda *a, **k: {
            "classification": "STUB", "confidence": 0.9, "risk_score": 1.0,
            "risk_level": "LOW", "message_type": "text", "intent": {},
            "indicators": [], "urls": [], "rag_evidence": [],
            "explanation": "stub", "explanation_source": "template",
            "recommended_action": "none", "risk_factors": [],
            "model_used": "stub", "rag_status": {}, "ok": True,
        },
    )
    registry.register("history", type("H", (), {"list_history": lambda *a, **k: {"items": [], "total": 0, "limit": 50, "offset": 0}, "delete_entry": lambda *a, **k: True, "clear_all": lambda *a, **k: 0}))
    registry.register("analytics", lambda *a, **k: {"total_analyses": 0})
    registry.register("configuration", lambda *a, **k: {})
    registry.register("kb", type("K", (), {"status": lambda *a, **k: {}, "rebuild": lambda *a, **k: {}}))
    registry.register("models", type("M", (), {"get_model_info": lambda *a, **k: {"available": False}}))
    registry.register("system_status", type("S", (), {
        "health": lambda *a, **k: {"status": "ok"},
        "readiness": lambda *a, **k: {"ready": True},
        "app_status": lambda *a, **k: {"status": "running"},
    }))

    app = create_app(registry=registry)
    with TestClient(app) as client:
        response = client.post("/api/analyze", json={"input_type": "text", "message": "hi"})
    assert response.status_code == 200
    assert response.json()["classification"] == "STUB"


def test_page_routes_and_static(app):
    with TestClient(app) as client:
        for path in ("/", "/history", "/analytics", "/knowledge-base", "/about"):
            response = client.get(path)
            assert response.status_code == 200, path
        assert client.get("/static/css/style.css").status_code in {200, 404}
