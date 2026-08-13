"""Application exception hierarchy.

Every error that can cross the API boundary is typed here, so routes
stay thin: they raise domain exceptions and the global handlers (see
``app/core/errors.py``) translate them to HTTP responses.
"""
from __future__ import annotations


class AppError(Exception):
    """Base class for all application errors."""

    code = "app_error"
    http_status = 500
    user_message = "An application error occurred."

    def __init__(self, message: str | None = None, *, detail: object = None):
        self.detail = detail
        super().__init__(message or self.user_message)


class ConfigError(AppError):
    """Invalid or inconsistent configuration."""

    code = "config_error"
    http_status = 500
    user_message = "The application is misconfigured."


class DatabaseError(AppError):
    """Persistence-layer failure."""

    code = "database_error"
    http_status = 500
    user_message = "A database error occurred."


class ServiceUnavailableError(AppError):
    """A required capability (model, vector store) is missing."""

    code = "service_unavailable"
    http_status = 503
    user_message = "A required service is unavailable."


class NotFoundError(AppError):
    """Requested resource does not exist."""

    code = "not_found"
    http_status = 404
    user_message = "The requested resource was not found."


class ValidationAppError(AppError):
    """Business-level validation failure (raised by services)."""

    code = "validation_error"
    http_status = 422
    user_message = "The request failed validation."


class KnowledgeBaseError(AppError):
    """Knowledge-base build/index failures."""

    code = "knowledge_base_error"
    http_status = 500
    user_message = "The knowledge base operation failed."


# Compat alias: the analysis service historically raised this name.
ClassifierUnavailableError = ServiceUnavailableError
