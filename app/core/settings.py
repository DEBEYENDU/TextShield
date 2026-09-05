"""Centralized application configuration (V2.0 foundation).

Every module loads its configuration from this single place. Values come
from the environment / ``.env`` file; secrets are environment-only and
never hard-coded.

Modules:
* ``settings``  - typed Settings singleton (paths, limits, providers,
                  risk weights, thresholds)
* ``load_settings`` - explicit factory used by the DI container and tests
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Project root: TextShield/
BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / ".env")


def _get_secret(key: str, default: str = "") -> str:
    """Env var or Docker secret file (<KEY>_FILE). Secret never logged."""
    file_key = f"{key}_FILE"
    file_path = os.getenv(file_key)
    if file_path:
        try:
            p = Path(file_path)
            if p.exists():
                return p.read_text(encoding="utf-8").strip()
        except Exception:
            pass
    return os.getenv(key, default).strip()


def _get(key: str, default: str = "") -> str:
    return _get_secret(key, default)


def _get_bool(key: str, default: bool = False) -> bool:
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


def _get_float(key: str, default: float) -> float:
    try:
        return float(os.getenv(key, str(default)))
    except ValueError:
        return default


class Settings:
    """Typed access to application settings."""

    ENVIRONMENT: str = _get("APP_ENV", "development")
    APP_HOST: str = _get("APP_HOST", "127.0.0.1")
    APP_PORT: int = _get_int("APP_PORT", 8000)
    APP_TITLE: str = _get("APP_TITLE", "TextShield")
    APP_TAGLINE: str = "Detect Spam. Understand the Risk. Stay Protected."

    DATABASE_URL: str = _get("DATABASE_URL", "sqlite:///./textshield.db")

    HISTORY_STORE_PREVIEW: bool = _get_bool("HISTORY_STORE_PREVIEW", False)
    HISTORY_PREVIEW_LENGTH: int = _get_int("HISTORY_PREVIEW_LENGTH", 120)

    MAX_MESSAGE_LENGTH: int = _get_int("MAX_MESSAGE_LENGTH", 10000)

    MODEL_PATH: Path = BASE_DIR / _get("MODEL_PATH", "models/spam_classifier.joblib")
    VECTORIZER_PATH: Path = BASE_DIR / _get(
        "VECTORIZER_PATH", "models/tfidf_vectorizer.joblib"
    )
    MODEL_METADATA_PATH: Path = BASE_DIR / _get(
        "MODEL_METADATA_PATH", "models/model_metadata.json"
    )
    MODEL_METRICS_PATH: Path = BASE_DIR / _get(
        "MODEL_METRICS_PATH", "models/evaluation_report.json"
    )

    VECTOR_DB_PATH: Path = BASE_DIR / _get("VECTOR_DB_PATH", "vector_db")
    RAG_TOP_K: int = _get_int("RAG_TOP_K", 4)

    EMBEDDING_PROVIDER: str = _get("EMBEDDING_PROVIDER", "sentence_transformers")
    EMBEDDING_MODEL: str = _get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # Semantic Understanding Engine (Phase 5).
    # Independent of RAG/LLM: its own embedder and caches.
    SEMANTIC_ENABLED: bool = _get_bool("SEMANTIC_ENABLED", True)
    SEMANTIC_EMBEDDING_MODEL: str = _get("SEMANTIC_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    SEMANTIC_EMBEDDING_DIMENSION: int = _get_int("SEMANTIC_EMBEDDING_DIMENSION", 384)
    SEMANTIC_CACHE_SIZE: int = _get_int("SEMANTIC_CACHE_SIZE", 512)
    SEMANTIC_BATCH_SIZE: int = _get_int("SEMANTIC_BATCH_SIZE", 16)
    SEMANTIC_DEVICE: str = _get("SEMANTIC_DEVICE", "auto").lower()
    SEMANTIC_LANGUAGE_DETECTION: str = _get(
        "SEMANTIC_LANGUAGE_DETECTION", "auto"
    ).lower()

    # Intent & Behavior Analysis Engine (Phase 6).
    # Deterministic, configurable thresholds. No classification.
    INTENT_ENABLED: bool = _get_bool("INTENT_ENABLED", True)
    INTENT_CONFIDENCE_THRESHOLD: float = _get_float("INTENT_CONFIDENCE_THRESHOLD", 0.35)
    INTENT_BEHAVIOR_THRESHOLD: float = _get_float("INTENT_BEHAVIOR_THRESHOLD", 0.30)
    INTENT_URGENCY_THRESHOLD: float = _get_float("INTENT_URGENCY_THRESHOLD", 0.30)
    INTENT_MAX_INTENTS: int = _get_int("INTENT_MAX_INTENTS", 4)

    LLM_PROVIDER: str = _get("LLM_PROVIDER", "ollama").lower()
    LLM_MODEL: str = _get("LLM_MODEL", "")
    LLM_BASE_URL: str = _get("LLM_BASE_URL", "http://localhost:11434")
    LLM_API_KEY: str = _get("LLM_API_KEY", "")
    LLM_TIMEOUT_SECONDS: int = _get_int("LLM_TIMEOUT_SECONDS", 30)
    LLM_TEMPERATURE: float = _get_float("LLM_TEMPERATURE", 0.2)

    # Risk engine parameters (transparent, informational scoring).
    RISK_SPAM_BASE: float = _get_float("RISK_SPAM_BASE", 50.0)
    RISK_HAM_BASE: float = _get_float("RISK_HAM_BASE", 5.0)
    RISK_INDICATOR_WEIGHTS: dict = {
        "high": _get_float("RISK_INDICATOR_HIGH_WEIGHT", 12.0),
        "medium": _get_float("RISK_INDICATOR_MEDIUM_WEIGHT", 7.0),
        "low": _get_float("RISK_INDICATOR_LOW_WEIGHT", 3.0),
    }
    RISK_URL_HIGH_PATTERN: float = _get_float("RISK_URL_HIGH_PATTERN", 10.0)
    RISK_URL_SUSPICIOUS: float = _get_float("RISK_URL_SUSPICIOUS", 6.0)
    RISK_URL_SHORTENER: float = _get_float("RISK_URL_SHORTENER", 4.0)
    RISK_HIGH_CONF_BONUS: float = _get_float("RISK_HIGH_CONF_BONUS", 15.0)
    RISK_RAG_CATEGORY_BONUS: float = _get_float("RISK_RAG_CATEGORY_BONUS", 8.0)
    RISK_INTENT_MALICIOUS: float = _get_float("RISK_INTENT_MALICIOUS", 12.0)
    RISK_MEDIUM_THRESHOLD: float = _get_float("RISK_MEDIUM_THRESHOLD", 30.0)
    RISK_HIGH_THRESHOLD: float = _get_float("RISK_HIGH_THRESHOLD", 60.0)
    RISK_CRITICAL_THRESHOLD: float = _get_float("RISK_CRITICAL_THRESHOLD", 80.0)
    RISK_CRITICAL_CONFIDENCE: float = _get_float("RISK_CRITICAL_CONFIDENCE", 0.85)
    RISK_UNCERTAIN_CONFIDENCE: float = _get_float("RISK_UNCERTAIN_CONFIDENCE", 0.5)

    # Feature flags (see app/core/features.py).
    FEATURE_RAG: bool = _get_bool("FEATURE_RAG", True)
    FEATURE_LLM: bool = _get_bool("FEATURE_LLM", True)
    FEATURE_HISTORY: bool = _get_bool("FEATURE_HISTORY", True)

    CONFIG_VERSION: str = "2.2.0"

    # Security / hardening
    API_KEY: str = _get_secret("API_KEY", "")
    ALLOWED_ORIGINS: str = _get("ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000")

    # JWT / Auth (used by app/authentication/manager.py)
    JWT_SECRET_KEY: str = _get_secret("JWT_SECRET_KEY", "change-me-in-production-please-rotate")
    JWT_ALGORITHM: str = _get("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_MINUTES: int = _get_int("JWT_EXPIRATION_MINUTES", 60)

    # RAG extended (centralized to avoid duplication with app/rag/config.py;
    # RagConfig.from_settings reads these if present)
    RAG_MAX_CONTEXT_CHUNKS: int = _get_int("RAG_MAX_CONTEXT_CHUNKS", 5)
    RAG_MAX_TOKEN_LIMIT: int = _get_int("RAG_MAX_TOKEN_LIMIT", 2000)
    RAG_SIMILARITY_THRESHOLD: float = _get_float("RAG_SIMILARITY_THRESHOLD", 0.35)

    # Backward-compat alias: APP_ENV was renamed to ENVIRONMENT.
    # New code should use settings.ENVIRONMENT; old code using settings.APP_ENV still works.
    @property
    def APP_ENV(self) -> str:  # noqa: N802
        return self.ENVIRONMENT

    @APP_ENV.setter
    def APP_ENV(self, value: str) -> None:
        self.ENVIRONMENT = value

    # Lowercase JWT aliases for legacy code that uses settings.jwt_*
    @property
    def jwt_secret_key(self) -> str:
        return self.JWT_SECRET_KEY

    @property
    def jwt_algorithm(self) -> str:
        return self.JWT_ALGORITHM

    @property
    def jwt_expiration_minutes(self) -> int:
        return self.JWT_EXPIRATION_MINUTES

    @property
    def database_path(self) -> Path:
        """Resolve the sqlite:/// URL to a path (absolute or project-relative)."""
        url = self.DATABASE_URL
        if url.startswith("sqlite:///"):
            raw = url[len("sqlite:///") :]
            if raw.startswith("./"):
                raw = raw[2:]
            candidate = Path(raw)
            if candidate.is_absolute():
                return candidate
            return BASE_DIR / raw
        return BASE_DIR / "textshield.db"

    def ensure_directories(self) -> None:
        """Create all runtime directories if they do not exist."""
        for path in (
            self.MODEL_PATH.parent,
            self.VECTOR_DB_PATH,
            BASE_DIR / "logs",
            BASE_DIR / "data" / "processed",
            BASE_DIR / "knowledge_base",
        ):
            path.mkdir(parents=True, exist_ok=True)

    def validate(self) -> list[str]:
        """Startup validation; returns list of errors (empty = ok)."""
        errors: list[str] = []
        if not self.DATABASE_URL:
            errors.append("DATABASE_URL must not be empty")
        if not (1 <= self.MAX_MESSAGE_LENGTH <= 100000):
            errors.append(f"MAX_MESSAGE_LENGTH {self.MAX_MESSAGE_LENGTH} out of range 1..100000")
        if not (1 <= self.LLM_TIMEOUT_SECONDS <= 300):
            errors.append(f"LLM_TIMEOUT_SECONDS {self.LLM_TIMEOUT_SECONDS} out of range 1..300")
        if self.RAG_TOP_K < 1 or self.RAG_TOP_K > 20:
            errors.append(f"RAG_TOP_K {self.RAG_TOP_K} out of range 1..20")
        if self.RISK_MEDIUM_THRESHOLD >= self.RISK_HIGH_THRESHOLD:
            errors.append("RISK thresholds mis-ordered: medium < high required")
        if self.RISK_HIGH_THRESHOLD >= self.RISK_CRITICAL_THRESHOLD:
            errors.append("RISK thresholds mis-ordered: high < critical required")
        if self.ENVIRONMENT not in {"development", "staging", "production", "test"}:
            errors.append(f"Unknown ENVIRONMENT {self.ENVIRONMENT}")
        return errors


def load_settings() -> Settings:
    """Factory used by the DI container and tests."""
    s = Settings()
    errs = s.validate()
    if errs:
        raise ValueError("Invalid configuration: " + "; ".join(errs))
    s.ensure_directories()
    return s


settings = Settings()
settings.ensure_directories()
