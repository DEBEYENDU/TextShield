"""Health checks."""

from __future__ import annotations

def check_live() -> dict:
    return {"status": "LIVE"}

def check_ready() -> dict:
    return {"status": "READY"}

def check_health() -> dict:
    return {
        "status": "DEGRADED",
        "components": {
            "database": "healthy",
            "vector_store": "healthy",
            "ml_engine": "healthy",
            "llm": "degraded",
            "threat_intel": "unavailable"
        }
    }
