"""Tests for the service layer."""
from __future__ import annotations

import pytest

from app.core.container import ServiceRegistry, create_container, verify_container
from app.core.settings import settings
from app.database.base import init_db
from app.services import analytics_service, configuration_service, history_service, models_service


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DATABASE_URL", f"sqlite:///{tmp_path / 't.db'}")
    init_db()
    yield


class TestContainer:
    def test_create_container_registers_all(self):
        registry = create_container()
        assert verify_container(registry) == []

    def test_custom_registry_override(self):
        registry = ServiceRegistry()
        stub = lambda *a, **k: {"stubbed": True}  # noqa: E731
        registry.register("analytics", stub)
        registry.register("analysis", stub)
        registry.register("history", lambda: stub)
        registry.register("configuration", stub)
        registry.register("kb", stub)
        registry.register("models", stub)
        registry.register("system_status", stub)
        registry.register("semantic", stub)
        registry.register("intent", stub)
        assert verify_container(registry) == []


class TestHistoryService:
    def test_roundtrip(self):
        with _conn_ctx() as conn:
            from app.database.repositories import history_repository

            history_repository.create(
                conn, {
                    "timestamp": "2026-08-13T10:00:00", "input_type": "sms",
                    "message_hash": "h1", "message": "", "classification": "SPAM",
                    "confidence": 0.9, "risk_level": "HIGH", "risk_score": 70.0,
                    "intent": "prize_scam", "message_type": "sms", "preview": None,
                }
            )
        result = history_service.list_history()
        assert result["total"] == 1
        assert result["items"][0]["message_hash"] == "h1"
        assert result["items"][0]["intent"] == "prize_scam"


class TestAnalyticsService:
    def test_empty_stats(self):
        stats = analytics_service.get_stats()
        assert stats["total_analyses"] == 0
        assert stats["spam_percentage"] == 0.0


class TestConfigurationService:
    def test_effective_config(self):
        cfg = configuration_service.effective_config()
        assert cfg["environment"] == settings.ENVIRONMENT
        assert cfg["max_message_length"] > 0
        assert set(cfg) >= {
            "rag_enabled", "llm_enabled", "history_enabled",
            "embedding_provider", "llm_model",
        }

    def test_feature_flags_shape(self):
        flags = configuration_service.feature_flags()
        assert set(flags) == {"rag", "llm", "history", "evidence", "analytics"}
        assert all(isinstance(v, bool) for v in flags.values())


class TestModelsService:
    def test_availability_matches_files(self):
        assert models_service.is_available() == (
            settings.MODEL_PATH.exists() and settings.VECTORIZER_PATH.exists()
        )

    def test_get_model_info(self):
        info = models_service.get_model_info()
        assert "available" in info


def _conn_ctx():
    from app.database.base import get_connection

    return get_connection()
