"""Centralized exception handling."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

def exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "-")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred",
                "request_id": request_id,
            }
        }
    )
