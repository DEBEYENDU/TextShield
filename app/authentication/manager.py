from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List, Set

import jwt

try:
    from fastapi import HTTPException, Request, Security
    from fastapi.security import APIKeyHeader
    from starlette.requests import Request as StarletteRequest
    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False

from app.core.config import settings


class APIKeyManager:
    """Manages API key storage and validation."""

    def __init__(self):
        self._keys: Dict[str, Dict[str, Any]] = {}
        self._role_mapping: Dict[str, List[str]] = {}

    def register_key(
        self,
        key: str,
        roles: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register an API key with its associated roles."""
        self._keys[key] = {
            "roles": roles,
            "created_at": datetime.utcnow(),
            "metadata": metadata or {},
            "last_used": None,
            "usage_count": 0,
        }
        self._role_mapping[key] = roles

    def validate_key(self, key: str) -> Optional[Dict[str, Any]]:
        """Validate an API key and return its payload."""
        if key not in self._keys:
            return None

        key_data = self._keys[key]
        key_data["last_used"] = datetime.utcnow()
        key_data["usage_count"] += 1

        return {
            "key": key,
            "roles": key_data["roles"],
            "metadata": key_data["metadata"],
        }

    def has_role(self, key: str, required_role: str) -> bool:
        """Check if the key has a required role."""
        key_data = self._keys.get(key)
        if not key_data:
            return False
        return required_role in key_data["roles"]


jwt_manager = APIKeyManager()


def get_api_key(
    authorization: Optional[str] = None,
    x_api_key: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Dependency to extract and validate API key from Authorization header or X-API-Key header."""
    key = None

    if authorization and authorization.startswith("Bearer "):
        key = authorization[7:]
    elif x_api_key:
        key = x_api_key

    if not key:
        return None

    return jwt_manager.validate_key(key)


def require_roles(*required_roles: str):
    """FastAPI dependency that requires specific roles."""

    def dependency(api_key_payload: Optional[Dict[str, Any]] = Depends(get_api_key)):
        if not api_key_payload:
            raise HTTPException(
                status_code=401,
                detail="Invalid or missing API key",
            )

        user_roles = api_key_payload.get("roles", [])
        missing = [r for r in required_roles if r not in user_roles]

        if missing:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Missing roles: {missing}",
            )

        return api_key_payload

    return dependency


class JWTManager:
    """Manages JWT token creation and validation."""

    @staticmethod
    def create_token(
        subject: str,
        roles: List[str],
        expires_minutes: int = settings.jwt_expiration_minutes,
        secret_key: str = settings.jwt_secret_key,
    ) -> str:
        """Create a JWT token."""
        expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)

        to_encode = {
            "sub": subject,
            "roles": roles,
            "iat": datetime.utcnow(),
            "exp": expires_at,
        }

        encoded = jwt.encode(
            to_encode,
            secret_key,
            algorithm=settings.jwt_algorithm,
        )

        return encoded

    @staticmethod
    def decode_token(
        token: str,
        secret_key: str = settings.jwt_secret_key,
    ) -> Dict[str, Any]:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(
                token,
                secret_key,
                algorithms=[settings.jwt_algorithm],
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")


def create_access_token(
    subject: str,
    roles: List[str],
    expires_minutes: Optional[int] = None,
) -> str:
    """Create an access token."""
    if expires_minutes is None:
        expires_minutes = settings.jwt_expiration_minutes

    return JWTManager.create_token(
        subject=subject,
        roles=roles,
        expires_minutes=expires_minutes,
    )


def get_current_user(
    token: str = Security(APIKeyHeader(name="Authorization", auto_error=False)),
) -> Dict[str, Any]:
    """Get current user from JWT token in Authorization header."""
    # Remove "Bearer " prefix if present
    actual_token = token
    if token and token.startswith("Bearer "):
        actual_token = token[7:]

    if not actual_token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    try:
        payload = JWTManager.decode_token(actual_token)
        return payload
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
        )