"""Hardening/resilience/observability tests — RFC-011 Part 3,4."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.core.settings import Settings
from app.api.routes_system import router as system_router

def _sys_app():
    app = FastAPI()
    app.include_router(system_router)
    return app

def test_liveness_and_healthz():
    c = TestClient(_sys_app())
    assert c.get("/api/liveness").status_code == 200
    assert c.get("/api/liveness").json()["status"] == "alive"
    assert c.get("/api/healthz").status_code == 200
    assert c.get("/api/healthz").json()["ok"] is True

def test_settings_validate_success():
    assert Settings().validate() == []

def test_settings_validate_failure():
    s2 = Settings()
    s2.RISK_MEDIUM_THRESHOLD = 90
    s2.RISK_HIGH_THRESHOLD = 80
    s2.RISK_CRITICAL_THRESHOLD = 85
    errs = s2.validate()
    assert any("mis-ordered" in e for e in errs)

def test_observability_metrics():
    from app.observability.metrics import incr, observe, get_metrics
    incr("test_counter_h", 2)
    observe("test_hist_h", 1.5)
    observe("test_hist_h", 2.5)
    m = get_metrics()
    assert "counters" in m
    assert "histograms" in m
    assert "uptime_seconds" in m

def test_structured_json_logging(tmp_path, monkeypatch):
    monkeypatch.setenv("LOG_FORMAT", "json")
    from app.core.logging import setup_logging, get_logger, set_request_id
    import logging
    root = logging.getLogger()
    if hasattr(root, "_textshield_configured"):
        delattr(root, "_textshield_configured")
    setup_logging(level=logging.INFO, log_dir=tmp_path)
    logger = get_logger("test.json")
    set_request_id("abc123")
    logger.info("json test message")
    log_file = tmp_path / "textshield.log"
    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "abc123" in content or "json test" in content
    monkeypatch.delenv("LOG_FORMAT")
    # reset
    root.handlers.clear()
    if hasattr(root, "_textshield_configured"):
        delattr(root, "_textshield_configured")

def test_db_pramas_and_indexes():
    from app.database.base import get_connection, init_db
    init_db()
    with get_connection() as conn:
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode.lower() == "wal"
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_analyses_timestamp_id'").fetchall()
        assert len(rows) == 1

def test_provider_isolation():
    from app.threat.providers.openphish import OpenPhishProvider
    import asyncio
    prov = OpenPhishProvider(enabled=True)
    async def run():
        good = await prov.lookup_url("http://example.com")
        assert good is None
        prov.enabled = False
        bad = await prov.lookup_url("http://openphish-malicious-test.com")
        assert bad is None
        prov.enabled = True
    asyncio.run(run())

def test_correlation_id_propagation():
    from app.api.middleware import RequestIDMiddleware, LoggingMiddleware
    app = FastAPI()
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)
    @app.get("/api/health")
    def h(): return {"ok": True}
    c = TestClient(app)
    r = c.get("/api/health", headers={"X-Request-ID": "my-rid-123"})
    assert r.headers.get("X-Request-ID") == "my-rid-123"
    r2 = c.get("/api/health", headers={"traceparent": "00-abc-def-01"})
    assert r2.headers.get("traceparent") == "00-abc-def-01"
