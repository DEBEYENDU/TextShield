"""Regression / e2e tests — RFC-011 Part 10."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.routes_system import router as sys_router
from app.api.v2.routes_threat_providers import router as prov_router

def test_health_e2e():
    app = FastAPI()
    app.include_router(sys_router)
    c = TestClient(app)
    assert c.get("/api/health").status_code == 200 or c.get("/api/liveness").status_code == 200

def test_threat_providers_regression():
    app = FastAPI()
    app.include_router(prov_router)
    c = TestClient(app)
    assert c.get("/v2/threat/providers/openphish").status_code == 200

def test_error_boundary_404():
    app = FastAPI()
    @app.get("/api/exists")
    def exists(): return {"ok": True}
    c = TestClient(app)
    assert c.get("/api/nonexistent-xyz").status_code == 404

def test_version_consistency():
    from app.api.routes_system import router
    app = FastAPI()
    app.include_router(router)
    c = TestClient(app)
    v = c.get("/api/version").json()
    assert "version" in v
    assert v["name"] == "TextShield"

def test_pagination_not_500():
    # simulate dashboard history pagination
    from app.analytics.history import get_dashboard_history
    hist = get_dashboard_history(page=1, page_size=5)
    assert "entries" in hist
    assert hist["page"] == 1
