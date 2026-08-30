"""Database migrations: ordered, append-only schema changes.

Each entry: ``(version, name, [statements])`` where a statement is either
a plain SQL string or a callable ``(conn) -> None`` (for guarded
ALTERs that must check the current schema first). A version applied once
is never re-applied. Never edit an existing migration; add a new one.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable

Statement = str | Callable[[sqlite3.Connection], None]


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cols = {
        row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
    }
    return column in cols


def _add_column(
    table: str, column: str, ddl: str
) -> Callable[[sqlite3.Connection], None]:
    def _apply(conn: sqlite3.Connection) -> None:
        if not _column_exists(conn, table, column):
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")

    return _apply


# Migration 1: original V1 schema (kept in place for existing databases).
_INITIAL_SCHEMA: list[Statement] = [
    """
    CREATE TABLE IF NOT EXISTS analyses (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp     TEXT NOT NULL,
        input_type    TEXT NOT NULL,
        message_hash  TEXT NOT NULL,
        message       TEXT NOT NULL,
        classification TEXT NOT NULL,
        confidence    REAL NOT NULL,
        risk_level    TEXT NOT NULL,
        risk_score    REAL NOT NULL DEFAULT 0,
        intent        TEXT,
        message_type  TEXT NOT NULL DEFAULT 'generic',
        preview       TEXT
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_analyses_timestamp ON analyses (timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_analyses_classification ON analyses (classification)",
    "CREATE INDEX IF NOT EXISTS idx_analyses_risk_level ON analyses (risk_level)",
]

# Migration 2: V2.0 columns for databases created before the V2 schema.
_V2_COLUMNS: list[Statement] = [
    _add_column("analyses", "message", "TEXT NOT NULL DEFAULT ''"),
    _add_column("analyses", "risk_score", "REAL NOT NULL DEFAULT 0"),
    _add_column("analyses", "intent", "TEXT"),
    _add_column("analyses", "message_type", "TEXT NOT NULL DEFAULT 'generic'"),
    "CREATE INDEX IF NOT EXISTS idx_analyses_input_type ON analyses (input_type)",
    "CREATE INDEX IF NOT EXISTS idx_analyses_message_hash ON analyses (message_hash)",
]

# Migration 3: V2.0 metadata tables.
_META_TABLES: list[Statement] = [
    """
    CREATE TABLE IF NOT EXISTS kb_metadata (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        document_name TEXT NOT NULL,
        category      TEXT,
        chunk_count   INTEGER NOT NULL DEFAULT 0,
        source_path   TEXT,
        added_at      TEXT NOT NULL,
        last_rebuilt_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS app_settings (
        key        TEXT PRIMARY KEY,
        value      TEXT,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS system_logs (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        ts        TEXT NOT NULL,
        level     TEXT NOT NULL,
        logger    TEXT,
        message   TEXT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_system_logs_ts ON system_logs (ts)",
]

# Migration 4: uniqueness guarantee for kb_metadata upserts.
_KB_UNIQUE_INDEX: list[Statement] = [
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_kb_metadata_document_name "
    "ON kb_metadata (document_name)",
]

MIGRATIONS: list[tuple[int, str, list[Statement]]] = [
    (1, "initial_schema", _INITIAL_SCHEMA),
    (2, "v2_analysis_columns", _V2_COLUMNS),
    (3, "meta_tables", _META_TABLES),
    (4, "kb_metadata_unique_index", _KB_UNIQUE_INDEX),
]
