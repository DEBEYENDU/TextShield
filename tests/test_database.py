"""Tests for the database foundation: connections and migrations."""
from __future__ import annotations

import pytest

from app.core.settings import settings
from app.database.base import get_connection, get_read_connection, init_db, run_migrations
from app.database.migrations import MIGRATIONS


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """Point the app database at a throwaway file per test."""
    monkeypatch.setattr(settings, "DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    yield tmp_path


def test_init_db_creates_schema(isolated_db):
    init_db()
    assert isolated_db.joinpath("test.db").exists()


def test_migrations_apply_and_are_recorded(isolated_db):
    with get_connection() as conn:
        applied = run_migrations(conn)
    assert len(applied) == len(MIGRATIONS)
    with get_read_connection() as conn:
        rows = conn.execute(
            "SELECT name FROM schema_migrations ORDER BY version"
        ).fetchall()
    assert [r["name"] for r in rows] == [name for _, name, _ in MIGRATIONS]


def test_migrations_idempotent(isolated_db):
    init_db()
    with get_connection() as conn:
        applied = run_migrations(conn)
    assert applied == []


def test_migration_2_columns_exist(isolated_db):
    init_db()
    with get_read_connection() as conn:
        cols = {
            r["name"]
            for r in conn.execute("PRAGMA table_info(analyses)").fetchall()
        }
    assert {"risk_score", "intent", "message_type"} <= cols


def test_meta_tables_exist(isolated_db):
    init_db()
    with get_read_connection() as conn:
        tables = {
            r["name"]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    assert {"kb_metadata", "app_settings", "system_logs", "schema_migrations"} <= tables


def test_transaction_rollback_on_error(isolated_db):
    init_db()
    with pytest.raises(Exception):
        with get_connection() as conn:
            conn.execute("INSERT INTO analyses (timestamp, input_type, message_hash, classification, confidence, risk_level) VALUES ('x','sms','h','SPAM',0.9,'HIGH')")
            raise RuntimeError("boom")
    with get_read_connection() as conn:
        count = conn.execute("SELECT COUNT(*) AS c FROM analyses").fetchone()["c"]
    assert count == 0


def test_get_db_path_resolves_tmp(isolated_db):
    from app.database.base import get_db_path

    assert get_db_path().name == "test.db"
