"""Application configuration loaded from environment variables (.env file).

All secrets (API keys) are read from the environment and are never
hard-coded in source code.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Project root: TextShield/
BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / ".env")


def _get(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


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


class Settings:
    """Typed access to application settings."""

    APP_ENV: str = _get("APP_ENV", "development")
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

    LLM_PROVIDER: str = _get("LLM_PROVIDER", "ollama").lower()
    LLM_MODEL: str = _get("LLM_MODEL", "")
    LLM_BASE_URL: str = _get("LLM_BASE_URL", "http://localhost:11434")
    LLM_API_KEY: str = _get("LLM_API_KEY", "")
    LLM_TIMEOUT_SECONDS: int = _get_int("LLM_TIMEOUT_SECONDS", 30)
    LLM_TEMPERATURE: float = 0.2

    # Risk engine parameters (transparent, informational scoring).
    RISK_SPAM_BASE: float = 50.0
    RISK_HAM_BASE: float = 5.0
    RISK_INDICATOR_WEIGHTS: dict = {"high": 12.0, "medium": 7.0, "low": 3.0}
    RISK_URL_HIGH_PATTERN: float = 10.0
    RISK_URL_SUSPICIOUS: float = 6.0
    RISK_URL_SHORTENER: float = 4.0
    RISK_HIGH_CONF_BONUS: float = 15.0
    RISK_RAG_CATEGORY_BONUS: float = 8.0
    RISK_MEDIUM_THRESHOLD: float = 30.0
    RISK_HIGH_THRESHOLD: float = 60.0

    @property
    def database_path(self) -> Path:
        """Resolve the sqlite:/// URL to a project-relative path."""
        url = self.DATABASE_URL
        if url.startswith("sqlite:///"):
            raw = url[len("sqlite:///") :]
            if raw.startswith("./"):
                raw = raw[2:]
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


settings = Settings()
settings.ensure_directories()