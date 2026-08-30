"""History repository: analysis rows in ``analyses``."""

from __future__ import annotations

import sqlite3
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)

_FIELDS = (
    "timestamp, input_type, message_hash, message, classification, confidence, "
    "risk_level, risk_score, intent, message_type, preview"
)


def create(conn: sqlite3.Connection, record: dict[str, Any]) -> int:
    """Insert an analysis; returns its id."""
    cursor = conn.execute(
        f"INSERT INTO analyses ({_FIELDS}) VALUES ({','.join('?' * 11)})",
        (
            record["timestamp"],
            record["input_type"],
            record["message_hash"],
            record.get("message") or "",
            record["classification"],
            record["confidence"],
            record["risk_level"],
            record["risk_score"],
            record.get("intent"),
            record.get("message_type") or "generic",
            record.get("preview"),
        ),
    )
    return int(cursor.lastrowid)


def _row_to_entry(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "timestamp": row["timestamp"],
        "input_type": row["input_type"],
        "message_hash": row["message_hash"],
        "classification": row["classification"],
        "confidence": row["confidence"],
        "risk_level": row["risk_level"],
        "intent": row["intent"],
        "preview": row["preview"],
    }


def list_all(
    conn: sqlite3.Connection,
    *,
    limit: int = 50,
    offset: int = 0,
    input_type: str | None = None,
    classification: str | None = None,
    risk_level: str | None = None,
    intent: str | None = None,
    order_by: str = "timestamp",
    direction: str = "desc",
) -> list[dict[str, Any]]:
    conditions, params = [], []
    for column, value in (
        ("input_type", input_type),
        ("classification", classification),
        ("risk_level", risk_level),
        ("intent", intent),
    ):
        if value:
            conditions.append(f"{column} = ?")
            params.append(value)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    rows = conn.execute(
        f"SELECT * FROM analyses {where} ORDER BY {order_by} {direction} LIMIT ? OFFSET ?",
        (*params, limit, offset),
    ).fetchall()
    return [_row_to_entry(r) for r in rows]


def count(
    conn: sqlite3.Connection,
    *,
    input_type: str | None = None,
    classification: str | None = None,
    risk_level: str | None = None,
    intent: str | None = None,
) -> int:
    conditions, params = [], []
    for column, value in (
        ("input_type", input_type),
        ("classification", classification),
        ("risk_level", risk_level),
        ("intent", intent),
    ):
        if value:
            conditions.append(f"{column} = ?")
            params.append(value)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    row = conn.execute(f"SELECT COUNT(*) AS c FROM analyses {where}", params).fetchone()
    return int(row["c"])


def get_by_id(conn: sqlite3.Connection, entry_id: int) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM analyses WHERE id = ?", (entry_id,)).fetchone()
    return dict(row) if row else None


def delete_by_id(conn: sqlite3.Connection, entry_id: int) -> bool:
    cursor = conn.execute("DELETE FROM analyses WHERE id = ?", (entry_id,))
    return cursor.rowcount > 0


def clear(conn: sqlite3.Connection) -> int:
    return conn.execute("DELETE FROM analyses").rowcount


def latest_timestamp(conn: sqlite3.Connection) -> str | None:
    row = conn.execute("SELECT MAX(timestamp) AS t FROM analyses").fetchone()
    return row["t"] if row and row["t"] else None
