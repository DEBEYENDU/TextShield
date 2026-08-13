"""Tests for the repository layer."""
from __future__ import annotations

import pytest

from app.core.settings import settings
from app.database.base import get_connection, init_db
from app.database.repositories import (
    analytics_repository,
    history_repository,
    kb_metadata_repository,
    settings_repository,
    system_logs_repository,
)


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DATABASE_URL", f"sqlite:///{tmp_path / 't.db'}")
    init_db()
    yield


def _record(overrides=None):
    record = {
        "timestamp": "2026-08-13T10:00:00",
        "input_type": "sms",
        "message_hash": "abc123",
        "message": "win a prize",
        "classification": "SPAM",
        "confidence": 0.95,
        "risk_level": "HIGH",
        "risk_score": 82.0,
        "intent": "prize_scam",
        "message_type": "sms",
        "preview": None,
    }
    if overrides:
        record.update(overrides)
    return record


class TestHistoryRepository:
    def test_create_and_get_by_id(self):
        with get_connection() as conn:
            entry_id = history_repository.create(conn, _record())
            row = history_repository.get_by_id(conn, entry_id)
        assert row["classification"] == "SPAM"
        assert row["risk_score"] == 82.0
        assert row["intent"] == "prize_scam"

    def test_list_all_with_filters(self):
        with get_connection() as conn:
            history_repository.create(conn, _record())
            history_repository.create(
                conn, _record({"classification": "HAM", "risk_level": "LOW", "message_hash": "x2"})
            )
            rows = history_repository.list_all(conn, classification="SPAM")
            assert len(rows) == 1 and rows[0]["classification"] == "SPAM"
            rows = history_repository.list_all(conn, risk_level="LOW")
            assert len(rows) == 1

    def test_count(self):
        with get_connection() as conn:
            history_repository.create(conn, _record())
            history_repository.create(conn, _record({"classification": "HAM"}))
            assert history_repository.count(conn) == 2
            assert history_repository.count(conn, classification="HAM") == 1

    def test_delete_and_clear(self):
        with get_connection() as conn:
            entry_id = history_repository.create(conn, _record())
            assert history_repository.delete_by_id(conn, entry_id) is True
            assert history_repository.delete_by_id(conn, entry_id) is False
            history_repository.create(conn, _record({"message_hash": "y"}))
            assert history_repository.clear(conn) == 1

    def test_latest_timestamp(self):
        with get_connection() as conn:
            history_repository.create(conn, _record({"timestamp": "2026-08-13T09:00:00"}))
            history_repository.create(conn, _record({"timestamp": "2026-08-13T11:00:00"}))
            assert history_repository.latest_timestamp(conn) == "2026-08-13T11:00:00"


class TestAnalyticsRepository:
    def test_totals(self):
        with get_connection() as conn:
            history_repository.create(conn, _record({"classification": "SPAM", "confidence": 0.9}))
            history_repository.create(
                conn, _record({"classification": "HAM", "confidence": 0.8, "message_hash": "h2"})
            )
            totals = analytics_repository.totals(conn)
        assert totals["total"] == 2
        assert totals["spam"] == 1 and totals["ham"] == 1
        assert totals["risk_distribution"]["HIGH"] == 2
        assert totals["message_type_distribution"]["sms"] == 2
        assert totals["intent_distribution"]["prize_scam"] == 2

    def test_per_day(self):
        with get_connection() as conn:
            history_repository.create(conn, _record())
            days = analytics_repository.per_day(conn, days=7)
        assert days and all(d["count"] >= 1 for d in days)


class TestKbMetadataRepository:
    def test_upsert_and_read(self):
        with get_connection() as conn:
            kb_metadata_repository.upsert(
                conn, "phishing.md", category="phishing", chunk_count=3,
                source_path="kb/phishing.md", last_rebuilt_at="now",
            )
            kb_metadata_repository.upsert(
                conn, "phishing.md", category="phishing", chunk_count=5,
                source_path="kb/phishing.md", last_rebuilt_at="later",
            )
            assert kb_metadata_repository.count_documents(conn) == 1
            assert kb_metadata_repository.count_chunks(conn) == 5
            assert kb_metadata_repository.categories(conn) == ["phishing"]
            assert kb_metadata_repository.get(conn, "phishing.md")["last_rebuilt_at"] == "later"

    def test_delete(self):
        with get_connection() as conn:
            kb_metadata_repository.upsert(conn, "x.md", category=None, chunk_count=1,
                                          source_path=None, last_rebuilt_at=None)
            assert kb_metadata_repository.delete(conn, "x.md") is True


class TestSettingsRepository:
    def test_get_set(self):
        with get_connection() as conn:
            assert settings_repository.get(conn, "k") is None
            settings_repository.set_value(conn, "k", "v1")
            settings_repository.set_value(conn, "k", "v2")
            assert settings_repository.get(conn, "k") == "v2"
            assert settings_repository.get_all(conn) == {"k": "v2"}


class TestSystemLogsRepository:
    def test_append_and_list(self):
        with get_connection() as conn:
            system_logs_repository.append(conn, "info", "tests", "hello")
            rows = system_logs_repository.list_all(conn)
            assert rows[0]["level"] == "INFO"
            assert rows[0]["message"] == "hello"
            assert system_logs_repository.list_all(conn, level="error") == []
