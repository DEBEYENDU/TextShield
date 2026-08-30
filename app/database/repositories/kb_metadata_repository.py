"""KB metadata repository: rows in ``kb_metadata``."""

from __future__ import annotations

import sqlite3
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


def upsert(
    conn: sqlite3.Connection,
    document_name: str,
    *,
    category: str | None,
    chunk_count: int,
    source_path: str | None,
    last_rebuilt_at: str | None,
) -> None:
    conn.execute(
        """
        INSERT INTO kb_metadata
            (document_name, category, chunk_count, source_path, added_at, last_rebuilt_at)
        VALUES (?, ?, ?, ?, datetime('now'), ?)
        ON CONFLICT(document_name) DO UPDATE SET
            category = excluded.category,
            chunk_count = excluded.chunk_count,
            source_path = excluded.source_path,
            last_rebuilt_at = excluded.last_rebuilt_at
        """,
        (document_name, category, chunk_count, source_path, last_rebuilt_at),
    )


def list_all(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT * FROM kb_metadata ORDER BY added_at DESC").fetchall()
    return [dict(r) for r in rows]


def get(conn: sqlite3.Connection, document_name: str) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT * FROM kb_metadata WHERE document_name = ?", (document_name,)
    ).fetchone()
    return dict(row) if row else None


def count_documents(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COUNT(*) AS c FROM kb_metadata").fetchone()
    return int(row["c"]) if row else 0


def count_chunks(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "SELECT COALESCE(SUM(chunk_count), 0) AS c FROM kb_metadata"
    ).fetchone()
    return int(row["c"]) if row else 0


def categories(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT DISTINCT category FROM kb_metadata WHERE category IS NOT NULL"
    ).fetchall()
    return [r["category"] for r in rows]


def delete(conn: sqlite3.Connection, document_name: str) -> bool:
    cursor = conn.execute(
        "DELETE FROM kb_metadata WHERE document_name = ?", (document_name,)
    )
    return cursor.rowcount > 0
