"""SQLite access layer for analysis history.

Uses the Python standard library ``sqlite3`` (thread-safe with proper
connection handling per call). By default only a SHA-256 hash of the
message is stored; message content is never saved unless
HISTORY_STORE_PREVIEW=true, in which case a short truncated preview is
stored and an explicit delete option is provided in the UI.
"""
from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_lock = threading.RLock()

SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS analyses (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp   TEXT    NOT NULL,
        input_type  TEXT    NOT NULL,
        message_hash TEXT   NOT NULL,
        classification TEXT NOT NULL,
        confidence  REAL    NOT NULL,
        risk_level  TEXT    NOT NULL,
        preview     TEXT
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_analyses_timestamp ON analyses(timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_analyses_classification ON analyses(classification)",
]


def get_db_path() -> Path:
    return settings.database_path


def init_db() -> None:
    """Create the database and tables if they do not exist."""
    path = get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with _lock, sqlite3.connect(path) as conn:
        for statement in SCHEMA:
            conn.execute(statement)
        conn.commit()


@contextmanager
def get_connection():
    with _lock:
        conn = sqlite3.connect(get_db_path())
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()


def insert_analysis(record: dict) -> int:
    """Insert one history record; returns the new row id."""
    init_db()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO analyses
                (timestamp, input_type, message_hash, classification,
                 confidence, risk_level, preview)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["timestamp"],
                record["input_type"],
                record["message_hash"],
                record["classification"],
                record["confidence"],
                record["risk_level"],
                record.get("preview"),
            ),
        )
        return int(cursor.lastrowid)


def query_history(
    filters: dict | None = None,
    limit: int = 50,
    offset: int = 0,
    order_by: str = "timestamp",
    direction: str = "desc",
) -> list[dict]:
    """Query history with optional filters and ordering."""
    init_db()
    allowed_columns = {"timestamp", "input_type", "classification", "risk_level",
                       "confidence", "id"}
    if order_by not in allowed_columns:
        order_by = "timestamp"
    direction = "asc" if direction.lower() == "asc" else "desc"

    where, params = [], []
    filters = filters or {}
    if filters.get("input_type"):
        where.append("input_type = ?")
        params.append(filters["input_type"])
    if filters.get("classification"):
        where.append("classification = ?")
        params.append(filters["classification"])
    if filters.get("risk_level"):
        where.append("risk_level = ?")
        params.append(filters["risk_level"])
    where_sql = (" WHERE " + " AND ".join(where)) if where else ""

    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT id, timestamp, input_type, message_hash, classification,
                   confidence, risk_level, preview
            FROM analyses
            {where_sql}
            ORDER BY {order_by} {direction}
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        ).fetchall()
        total = conn.execute(
            f"SELECT COUNT(*) FROM analyses{where_sql}", params
        ).fetchone()[0]
    return [dict(row) for row in rows], int(total)


def delete_history_entry(entry_id: int) -> bool:
    init_db()
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM analyses WHERE id = ?", (entry_id,))
        return cursor.rowcount > 0


def clear_history() -> int:
    init_db()
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM analyses")
        return int(cursor.rowcount)


def aggregate_stats() -> dict:
    """Compute dashboard statistics from the history table."""
    init_db()
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
        spam = conn.execute(
            "SELECT COUNT(*) FROM analyses WHERE classification = 'SPAM'"
        ).fetchone()[0]
        ham = total - spam
        avg_conf = conn.execute(
            "SELECT AVG(confidence) FROM analyses"
        ).fetchone()[0]
        risk_rows = conn.execute(
            "SELECT risk_level, COUNT(*) AS c FROM analyses GROUP BY risk_level"
        ).fetchall()
        type_rows = conn.execute(
            "SELECT input_type, COUNT(*) AS c FROM analyses GROUP BY input_type"
        ).fetchall()
        daily = conn.execute(
            "SELECT substr(timestamp, 1, 10) AS day, COUNT(*) AS c "
            "FROM analyses GROUP BY day ORDER BY day DESC LIMIT 14"
        ).fetchall()
        latest = conn.execute("SELECT MAX(timestamp) FROM analyses").fetchone()[0]

    risk_distribution = {row["risk_level"]: row["c"] for row in risk_rows}
    type_distribution = {row["input_type"]: row["c"] for row in type_rows}
    return {
        "total_analyses": int(total),
        "spam_count": int(spam),
        "ham_count": int(ham),
        "spam_percentage": round(spam / total * 100, 1) if total else 0.0,
        "average_confidence": round(float(avg_conf), 4) if avg_conf else 0.0,
        "risk_distribution": risk_distribution,
        "message_type_distribution": type_distribution,
        "analyses_per_day": [
            {"date": row["day"], "count": row["c"]} for row in reversed(daily)
        ],
        "latest_analysis_at": latest,
    }