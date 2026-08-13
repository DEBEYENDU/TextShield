"""Database foundation: connection management and migrations.

* Connections are short-lived and guarded by a process-wide ``RLock``
  (SQLite writes must not interleave).
* Schema evolution is versioned: migrations live in ``app/database/
  migrations.py`` and are applied in order, each in its own transaction,
  recorded in ``schema_migrations``.
"""
from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

from app.core.logging import get_logger
from app.core.settings import settings
from app.database.migrations import MIGRATIONS, Statement

logger = get_logger(__name__)

_lock = threading.RLock()


def get_db_path() -> Path:
    return settings.database_path


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path(), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_connection():
    """Yield a committed-on-exit connection (thread-safe)."""
    with _lock:
        conn = _connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


@contextmanager
def get_read_connection():
    """Yield a read-only convenience connection (no commit)."""
    with _lock:
        conn = _connect()
        try:
            yield conn
        finally:
            conn.close()


def run_migrations(conn: sqlite3.Connection) -> list[str]:
    """Apply pending migrations; returns the applied migration names."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version    INTEGER PRIMARY KEY,
            name       TEXT NOT NULL,
            applied_at TEXT NOT NULL
        )
        """
    )
    applied = {
        row["version"]
        for row in conn.execute("SELECT version FROM schema_migrations").fetchall()
    }
    executed: list[str] = []
    for version, name, statements in MIGRATIONS:
        if version in applied:
            continue
        for statement in statements:
            if isinstance(statement, str):
                conn.execute(statement)
            else:
                statement(conn)
        conn.execute(
            "INSERT INTO schema_migrations (version, name, applied_at) "
            "VALUES (?, ?, datetime('now'))",
            (version, name),
        )
        executed.append(name)
    return executed


def init_db() -> None:
    """Ensure the schema is present and up to date."""
    path = get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        applied = run_migrations(conn)
        if applied:
            logger.info("Applied database migrations: %s", ", ".join(applied))
