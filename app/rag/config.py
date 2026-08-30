"""RAG-specific configuration settings.

Extends the central Settings class with RAG-specific parameters that can be
configured via environment variables or the .env file.

All values have sensible defaults and are typed for IDE support and validation.
Module-level constants for external access.

From the application Settings class, these are re-exported as defaults.
"""

from __future__ import annotations

from app.core.settings import Settings

#: Minimum similarity threshold for chunk acceptance (0.0-1.0)
RAG_SIMILARITY_THRESHOLD: float = 0.35

#: Maximum number of chunks in final context
RAG_MAX_CONTEXT_CHUNKS: int = 5

#: Maximum estimated token limit for context
RAG_MAX_TOKEN_LIMIT: int = 2000

#: Default number of chunks to retrieve per query type
RAG_TOP_K: int = 5

#: Minimum number of required metadata fields
RAG_MIN_METADATA_FIELDS: int = 3

#: Agreement weights for confidence estimation
RAG_AGREEMENT_WEIGHTS: dict = {
    "similarity": 0.30,
    "agreement": 0.25,
    "metadata": 0.20,
    "trust": 0.15,
    "coverage": 0.10,
}


class RagConfig:
    """RAG configuration settings with defaults."""

    # Re-ranking weights
    RERANK_INTENT_WEIGHT: float = 0.20
    RERANK_BEHAVIOR_WEIGHT: float = 0.15
    RERANK_METADATA_WEIGHT: float = 0.15
    RERANK_TRUST_WEIGHT: float = 0.10
    RERANK_CATEGORY_WEIGHT: float = 0.10
    RERANK_SIMILARITY_WEIGHT: float = 0.30
    RERANK_FRESHNESS_WEIGHT: float = 0.0  # Can be enabled

    # Filter parameters
    RAG_ENABLE_CATEGORY_FILTER: bool = True
    RAG_ENABLE_TAG_FILTER: bool = True
    RAG_ENABLE_LANGUAGE_FILTER: bool = True
    RAG_ENABLE_TRUST_FILTER: bool = True

    # Metadata validation
    RAG_VALIDATE_METADATA: bool = True
    RAG_VALIDATE_TRUST: bool = True
    RAG_MIN_METADATA_FIELDS: int = 3  # Minimum required metadata fields

    # Confidence estimation
    RAG_AGREEMENT_WEIGHTS: dict = {
        "similarity": 0.30,
        "agreement": 0.25,
        "metadata": 0.20,
        "trust": 0.15,
        "coverage": 0.10,
    }

    # Context construction
    RAG_INCLUDE_BEHAVIORAL: bool = True
    RAG_INCLUDE_EXAMPLES: bool = True
    RAG_INCLUDE_COUNTER_EXAMPLES: bool = True

    # Context limits
    RAG_MAX_CONTEXT_CHUNKS: int = 5
    RAG_MAX_TOKEN_LIMIT: int = 2000

    # Service integration flags
    RAG_INTEGRATE_SEMANTIC_ENGINE: bool = True
    RAG_INTEGRATE_INTENT_ENGINE: bool = True
    RAG_INTEGRATE_KNOWLEDGE_LOADER: bool = True
    RAG_INTEGRATE_VECTOR_STORE: bool = True

    @classmethod
    def from_settings(cls, settings: Settings) -> "RagConfig":
        """Create RagConfig from the application Settings, overriding defaults
        with environment-configured values where available."""
        config = cls()

        # Override from settings if configured
        if hasattr(settings, "RAG_TOP_K") and settings.RAG_TOP_K:
            config.RAG_TOP_K = settings.RAG_TOP_K
        else:
            config.RAG_TOP_K = RagConfig.RAG_TOP_K
        if (
            hasattr(settings, "RAG_MAX_CONTEXT_CHUNKS")
            and settings.RAG_MAX_CONTEXT_CHUNKS
        ):
            config.RAG_MAX_CONTEXT_CHUNKS = settings.RAG_MAX_CONTEXT_CHUNKS
        else:
            config.RAG_MAX_CONTEXT_CHUNKS = RagConfig.RAG_MAX_CONTEXT_CHUNKS
        if hasattr(settings, "RAG_MAX_TOKEN_LIMIT") and settings.RAG_MAX_TOKEN_LIMIT:
            config.RAG_MAX_TOKEN_LIMIT = settings.RAG_MAX_TOKEN_LIMIT
        else:
            config.RAG_MAX_TOKEN_LIMIT = RagConfig.RAG_MAX_TOKEN_LIMIT
        if (
            hasattr(settings, "RAG_SIMILARITY_THRESHOLD")
            and settings.RAG_SIMILARITY_THRESHOLD
        ):
            config.RAG_SIMILARITY_THRESHOLD = settings.RAG_SIMILARITY_THRESHOLD

        return config


# Global config instance
config = RagConfig.from_settings(Settings)


def get_config() -> RagConfig:
    """Get the global RAG configuration instance."""
    return config
