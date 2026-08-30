"""HTTP middleware: request-id and request logging.

* RequestIDMiddleware assigns a short id per request (response header
  ``X-Request-ID``) and exposes it to logging via a contextvar.
* LoggingMiddleware records method, path, status and duration for every
  request. Request bodies are never logged (privacy).
"""

from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import clear_request_id, get_logger, set_request_id

logger = get_logger("app.http")


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID")
        set_request_id(request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = set_request_id()
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            elapsed = (time.perf_counter() - started) * 1000
            logger.exception(
                "request %s %s failed after %.1fms",
                request.method,
                request.url.path,
                elapsed,
            )
            raise
        finally:
            clear_request_id()
        elapsed = (time.perf_counter() - started) * 1000
        if request.url.path.startswith("/api"):
            logger.info(
                "request %s %s -> %s (%.1fms)",
                request.method,
                request.url.path,
                response.status_code,
                elapsed,
            )
        return response
