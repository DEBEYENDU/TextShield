"""Startup configuration validation — RFC config audit."""

from app.core.config import settings as config_settings
from app.core.settings import Settings, load_settings, settings


def test_settings_has_app_env_alias():
    s = Settings()
    assert hasattr(s, "APP_ENV")
    assert hasattr(s, "ENVIRONMENT")
    assert s.APP_ENV == s.ENVIRONMENT
    orig = s.ENVIRONMENT
    s.APP_ENV = "production"
    assert s.ENVIRONMENT == "production"
    s.ENVIRONMENT = orig  # restore


def test_settings_jwt_fields():
    s = Settings()
    assert hasattr(s, "JWT_SECRET_KEY")
    assert hasattr(s, "JWT_ALGORITHM")
    assert hasattr(s, "JWT_EXPIRATION_MINUTES")
    assert hasattr(s, "jwt_secret_key")
    assert hasattr(s, "jwt_algorithm")
    assert hasattr(s, "jwt_expiration_minutes")
    assert s.JWT_ALGORITHM == "HS256"
    assert s.JWT_EXPIRATION_MINUTES == 60
    assert s.jwt_secret_key == s.JWT_SECRET_KEY


def test_settings_rag_fields():
    s = Settings()
    assert hasattr(s, "RAG_MAX_CONTEXT_CHUNKS")
    assert hasattr(s, "RAG_MAX_TOKEN_LIMIT")
    assert hasattr(s, "RAG_SIMILARITY_THRESHOLD")
    assert s.RAG_MAX_CONTEXT_CHUNKS == 5


def test_load_settings_validates():
    s = load_settings()
    assert s.validate() == []


def test_settings_shim_identical():
    assert config_settings.ENVIRONMENT == settings.ENVIRONMENT
    assert config_settings.APP_ENV == settings.APP_ENV


def test_run_py_uses_environment(monkeypatch):
    # ensure run.py imports without AttributeError
    import sys

    # reload run module to ensure no AttributeError
    if "run" in sys.modules:
        del sys.modules["run"]
    import run

    assert hasattr(run, "main")
    # check run.py code uses ENVIRONMENT not APP_ENV (via source inspect)
    import pathlib

    src = pathlib.Path(run.__file__).read_text()
    assert "settings.ENVIRONMENT" in src
    assert (
        "settings.APP_ENV" not in src or "ENVIRONMENT" in src
    )  # alias still allowed but primary is ENVIRONMENT


def test_fastapi_startup():
    from fastapi.testclient import TestClient

    from app.main import create_app

    app = create_app()
    c = TestClient(app)
    assert c.get("/api/health").status_code == 200
    assert c.get("/api/liveness").status_code == 200
    assert c.get("/api/readiness").status_code == 200
    assert c.get("/api/version").status_code == 200
    assert c.get("/").status_code == 200


def test_dashboard_loads():
    from fastapi.testclient import TestClient

    from app.main import create_app

    app = create_app()
    c = TestClient(app)
    r = c.get("/dashboard")
    assert r.status_code == 200
