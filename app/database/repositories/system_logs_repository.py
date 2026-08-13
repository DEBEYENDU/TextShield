"""System logs repository: rows in ``system_logs``."""
from __future__ import annotations

import sqlite3


def append(conn: sqlite3.Connection, level: str, logger_name: str, message: str) -> int:
    cursor = conn.execute(
        "INSERT INTO system_logs (ts, level, logger, message) "
        "VALUES (datetime('now'), ?, ?, ?)",
        (level.upper(), logger_name, message[:1000]),
    )
    return int(cursor.lastrowid)


def list_all(
    conn: sqlite3.Connection,
    *,
    limit: int = 100,
    level: str | None = None,
) -> list[dict]:
    conditions, params = "", []
    if level:
        conditions, params = "WHERE level = ?", [level.upper()]
    rows = conn.execute(
        f"SELECT id, ts, level, logger, message FROM system_logs {conditions} "
        "ORDER BY id DESC LIMIT ?",
        (*params, limit),
    ).fetchall()
    return [dict(r) for r in rows]
