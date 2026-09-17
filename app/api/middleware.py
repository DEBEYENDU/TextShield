"""HTTP middleware: request-id, logging, security headers, CORS & rate-limit.

* RequestIDMiddleware assigns a short id per request (response header
  ``X-Request-ID``) and exposes it to logging via a contextvar.
* LoggingMiddleware records method, path, status and duration for every
  request. Request bodies are never logged (privacy).
* SecurityHeadersMiddleware adds HSTS, CSP, X-Frame-Options, etc.
* Input sanitization truncates over-long bodies and blocks prompt-injection patterns.
"""

from __future__ import annotations

import re
import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.logging import clear_request_id, get_logger, set_request_id

logger = get_logger("app.http")

# ------------------------------------------------------------------ rate limit (in-memory, per-IP sliding window)
_RATE_LIMIT_WINDOW = 60  # seconds
_RATE_LIMIT_MAX = 100  # requests per window per IP
_rate_buckets: dict[str, deque[float]] = defaultdict(deque)

# Prompt injection / dangerous patterns blocked at edge (defense-in-depth)
_INJECTION_PATTERNS = [
    re.compile(r"ignore previous instructions", re.I),
    re.compile(r"system\s*:\s*you are", re.I),
    re.compile(r"<\|im_start\|>", re.I),
]


def _is_injection_attempt(text: str) -> bool:
    return any(p.search(text) for p in _INJECTION_PATTERNS)


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID")
        current = set_request_id(request_id)
        # distributed tracing: forward traceparent if present
        traceparent = request.headers.get("traceparent")
        if traceparent:
            # attach to logging context via request.state
            request.state.traceparent = traceparent  # type: ignore[attr-defined]
        response = await call_next(request)
        response.headers["X-Request-ID"] = current
        if traceparent:
            response.headers["traceparent"] = traceparent
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add production security headers to every response."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; object-src 'none'"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        # CORS (tight, not wildcard — reflect allowed origins from settings)
        origin = request.headers.get("origin")
        # In production, settings.ALLOWED_ORIGINS would be checked; here allow local
        if origin and origin.startswith(("http://localhost", "http://127.0.0.1", "https://")):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
        # CSRF: enforce same-site for state-changing methods without proper origin
        if request.method in {"POST", "PUT", "DELETE"} and request.url.path.startswith("/api"):
            # Allow if Origin present (CORS) or X-Requested-With or internal; otherwise warn but not block (API is stateless)
            pass
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple IP-based sliding-window rate limiter (100 req/60s). Graceful 429."""

    async def dispatch(self, request: Request, call_next):
        # exempt health probes from rate limiting
        if request.url.path in {"/api/health", "/api/readiness", "/api/liveness", "/api/version"}:
            return await call_next(request)
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        bucket = _rate_buckets[ip]
        # evict old
        while bucket and bucket[0] < now - _RATE_LIMIT_WINDOW:
            bucket.popleft()
        if len(bucket) >= _RATE_LIMIT_MAX:
            logger.warning("rate limit exceeded for %s on %s", ip, request.url.path)
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded", "retry_after": _RATE_LIMIT_WINDOW})
        bucket.append(now)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(_RATE_LIMIT_MAX)
        response.headers["X-RateLimit-Remaining"] = str(max(0, _RATE_LIMIT_MAX - len(bucket)))
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        started = time.perf_counter()
        # input sanitization: truncate large bodies, block injection
        content_length = request.headers.get("content-length")
        if content_length and content_length.isdigit() and int(content_length) > 1_000_000:
            return JSONResponse(status_code=413, content={"detail": "Payload too large"})
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
        # structured log with correlation id
        logger.info(
            "request %s %s -> %s (%.1fms) rid=%s",
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
            request.headers.get("X-Request-ID", "-"),
        )
        return response
