from __future__ import annotations

from typing import Callable, Dict, Optional, Any
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.authentication.manager import get_current_user, create_access_token, JWTManager
from app.core.config import settings


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for authentication."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extract authentication from headers
        authorization = request.headers.get("Authorization")
        api_key = request.headers.get("X-API-Key")

        user_payload = None

        if authorization and authorization.startswith("Bearer "):
            token = authorization[7:]
            try:
                user_payload = JWTManager.decode_token(token)
            except Exception:
                pass
        elif api_key:
            # Validate API key
            from app.authentication.manager import jwt_manager
            validated = jwt_manager.validate_key(api_key)
            if validated:
                user_payload = validated

        # Attach user to request state
        request.state.user = user_payload

        # Skip authentication for public endpoints
        path = request.url.path
        public_paths = [
            "/api/v2/system/health",
            "/api/v2/system/version",
            "/api/v2/auth/login",
            "/api/v2/auth/register",
        ]

        if path in public_paths:
            response = await call_next(request)
            return response

        # Authenticate protected endpoints
        if not user_payload:
            from fastapi import HTTPException
            from starlette.status import HTTP_401_UNAUTHORIZED

            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        response = await call_next(request)
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware."""

    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self._calls: Dict[str, List[float]] = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host
        now = time.time()

        # Get or initialize call timestamps for this IP
        if client_ip not in self._calls:
            self._calls[client_ip] = []

        # Remove timestamps outside the period
        self._calls[client_ip] = [
            ts for ts in self._calls[client_ip] if now - ts < self.period
        ]

        # Check rate limit
        if len(self._calls[client_ip]) >= self.calls:
            from fastapi import HTTPException
            from starlette.status import HTTP_429_TOO_MANY_REQUESTS

            raise HTTPException(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {self.calls} calls per {self.period}s",
            )

        # Record this call
        self._calls[client_ip].append(now)

        response = await call_next(request)
        return response


class CORSMiddleware:
    """Custom CORS middleware."""

    def __init__(
        self,
        app,
        allow_origins: List[str] = None,
        allow_methods: List[str] = None,
        allow_headers: List[str] = None,
        allow_credentials: bool = True,
    ):
        self.app = app
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["*"]
        self.allow_headers = allow_headers or ["*"]
        self.allow_credentials = allow_credentials

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # This is a simplified CORS handling
            # In production, use FastAPI's CORS middleware
            pass
        await self.app(scope, receive, send)