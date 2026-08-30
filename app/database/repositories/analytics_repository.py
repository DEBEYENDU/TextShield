"""Analytics repository: aggregate queries over ``analyses``."""

from __future__ import annotations

import sqlite3
from typing import Any


def totals(conn: sqlite3.Connection) -> dict[str, Any]:
    """Total counts and risk/type/intent distributions."""
    row = conn.execute("""
        SELECT
            COUNT(*)                          AS total,
            COALESCE(SUM(classification = 'SPAM'), 0)  AS spam,
            COALESCE(SUM(classification = 'HAM'), 0)   AS ham,
            COALESCE(AVG(confidence), 0)      AS avg_conf
        FROM analyses
        """).fetchone()
    risk = {
        r["risk_level"]: r["c"]
        for r in conn.execute(
            "SELECT risk_level, COUNT(*) AS c FROM analyses GROUP BY risk_level"
        ).fetchall()
    }
    mtypes = {
        r["message_type"]: r["c"]
        for r in conn.execute(
            "SELECT message_type, COUNT(*) AS c FROM analyses GROUP BY message_type"
        ).fetchall()
    }
    intents = {
        r["intent"]: r["c"]
        for r in conn.execute(
            "SELECT intent, COUNT(*) AS c FROM analyses "
            "WHERE intent IS NOT NULL AND intent != '' GROUP BY intent"
        ).fetchall()
    }
    return {
        "total": int(row["total"]),
        "spam": int(row["spam"]),
        "ham": int(row["ham"]),
        "average_confidence": round(float(row["avg_conf"] or 0), 4),
        "risk_distribution": risk,
        "message_type_distribution": mtypes,
        "intent_distribution": intents,
    }


def per_day(conn: sqlite3.Connection, days: int = 14) -> list[dict[str, Any]]:
    """Daily analysis counts for the last N days."""
    rows = conn.execute(
        """
        SELECT substr(timestamp, 1, 10) AS day, COUNT(*) AS c
        FROM analyses
        WHERE timestamp >= date('now', ?)
        GROUP BY day ORDER BY day
        """,
        (f"-{max(days, 1)} days",),
    ).fetchall()
    return [{"date": r["day"], "count": int(r["c"])} for r in rows]
