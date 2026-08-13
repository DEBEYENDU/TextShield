"""Global exception handlers.

Registers FastAPI-level handlers so that *every* route (current and
future) reports errors through one consistent envelope:

    {"error": {"code": ..., "message": ..., "detail": ...}}

Sensitive details (stack traces) are logged server-side, never returned.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError

logger = logging.getLogger("app.errors")


def _error_response(status_code: int, code: str, message: str, detail: object) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "detail": detail}},
    )


def _register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError):
        logger.warning("AppError %s: %s", exc.code, exc)
        return _error_response(exc.http_status, exc.code, str(exc), exc.detail)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_request: Request, exc: RequestValidationError):
        raw_errors = exc.errors()
        sanitized = [
            {"loc": err.get("loc"), "msg": err.get("msg"), "type": err.get("type")}
            for err in raw_errors[:10]
        ]
        summary = "; ".join(
            f"{'.'.join(str(p) for p in err.get('loc', []))}: {err.get('msg', '')}"
            for err in raw_errors[:5]
        )
        logger.warning("Validation error: %s", summary)
        return _error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "validation_error",
            "The request failed validation.",
            sanitized,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(_request: Request, exc: StarletteHTTPException):
        return _error_response(
            exc.status_code, "http_error", str(exc.detail) or "HTTP error", None
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        logger.exception(
            "Unhandled exception on %s %s: %s",
            request.method,
            request.url.path,
            exc,
        )
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "internal_error",
            "An internal error occurred.",
            None,
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Public entry point used by the application factory."""
    _register_exception_handlers(app)
