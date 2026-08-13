"""Tests for the centralized settings module."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.core.features import FeatureFlags
from app.core.settings import BASE_DIR, Settings, load_settings, settings


def test_settings_singleton_is_typed():
    assert isinstance(settings, Settings)
    assert settings.APP_TITLE == "TextShield"


def test_defaults_present():
    assert settings.MAX_MESSAGE_LENGTH == 10_000
    assert settings.RISK_CRITICAL_THRESHOLD == 80.0
    assert settings.RISK_CRITICAL_CONFIDENCE == 0.85
    assert settings.ENVIRONMENT in {"development", "test", "production"}


def test_database_path_resolution():
    original = settings.DATABASE_URL
    try:
        settings.DATABASE_URL = "sqlite:///./custom.db"
        assert settings.database_path == BASE_DIR / "custom.db"
        settings.DATABASE_URL = "sqlite:///C:/tmp/absolute.db"
        assert settings.database_path == Path("C:/tmp/absolute.db")
    finally:
        settings.DATABASE_URL = original


def test_load_settings_factory():
    loaded = load_settings()
    assert isinstance(loaded, Settings)


def test_ensure_directories_creates_runtime_dirs(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "MODEL_PATH", tmp_path / "models" / "m.joblib")
    monkeypatch.setattr(settings, "VECTOR_DB_PATH", tmp_path / "vdb")
    settings.ensure_directories()
    assert (tmp_path / "models").exists()
    assert (tmp_path / "vdb").exists()


def test_feature_flags_env_driven(monkeypatch):
    from app.core import features as features_module

    monkeypatch.setenv("FEATURE_RAG", "false")
    features_module._ENABLED_CACHE.clear()
    assert FeatureFlags().rag_enabled is False
    monkeypatch.setenv("FEATURE_RAG", "true")
    features_module._ENABLED_CACHE.clear()
    assert FeatureFlags().rag_enabled is True


def test_effective_llm_enabled():
    assert FeatureFlags.effective_llm_enabled(settings, llm_available=False) is False
