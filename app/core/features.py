"""Feature flags.

Central place to toggle major capabilities at runtime through the
environment. Each flag degrades gracefully: disabling a feature must
never break the application - the corresponding stage simply skips and
the response reflects the disabled state.

Flags are resolved once at import time (consistent for the process).
"""
from __future__ import annotations

from app.core.settings import Settings, _get_bool

_ENABLED_CACHE: dict[str, bool] = {}


def _flag(key: str, default: bool) -> bool:
    if key not in _ENABLED_CACHE:
        _ENABLED_CACHE[key] = _get_bool(key, default)
    return _ENABLED_CACHE[key]


class FeatureFlags:
    """Boolean feature gates resolved from the environment."""

    @property
    def rag_enabled(self) -> bool:
        return _flag("FEATURE_RAG", True)

    @property
    def llm_enabled(self) -> bool:
        # LLM is also disabled when no model is configured.
        return _flag("FEATURE_LLM", True)

    @property
    def history_enabled(self) -> bool:
        return _flag("FEATURE_HISTORY", True)

    @property
    def evidence_enabled(self) -> bool:
        return _flag("FEATURE_EVIDENCE", True)

    @property
    def analytics_enabled(self) -> bool:
        return _flag("FEATURE_ANALYTICS", True)

    def summary(self) -> dict[str, bool]:
        return {
            "rag": self.rag_enabled,
            "llm": self.llm_enabled,
            "history": self.history_enabled,
            "evidence": self.evidence_enabled,
            "analytics": self.analytics_enabled,
        }

    @staticmethod
    def effective_llm_enabled(settings: Settings, llm_available: bool) -> bool:
        """LLM is effective only when both the flag and a model are present."""
        return settings.FEATURE_LLM and bool(settings.LLM_MODEL) and llm_available


features = FeatureFlags()
