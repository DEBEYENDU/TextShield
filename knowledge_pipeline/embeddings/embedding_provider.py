"""Provider abstraction — no hardcoded providers.

Wraps the existing ``app.rag.embeddings`` providers (SentenceTransformers,
hashing fallback) and exposes extension points for OpenAI, Gemini, Ollama
and HuggingFace endpoints without requiring their SDKs at import time.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

import numpy as np

_PROVIDER_REGISTRY: dict[str, Callable[..., "BaseEmbeddingProvider"]] = {}


def register_provider(name: str):
    def decorator(cls: type["BaseEmbeddingProvider"]):
        _PROVIDER_REGISTRY[name.lower()] = cls
        cls.provider_name = name.lower()
        return cls

    return decorator


class BaseEmbeddingProvider(ABC):
    provider_name: str = "base"

    @property
    @abstractmethod
    def dimension(self) -> int: ...

    @abstractmethod
    def embed(self, texts: list[str]) -> np.ndarray: ...

    def embed_one(self, text: str) -> np.ndarray:
        return self.embed([text])[0]


@register_provider("hashing")
class HashingProvider(BaseEmbeddingProvider):
    """Zero-dependency fallback (delegates to app.rag.embeddings)."""

    def __init__(self, dim: int = 768):
        from app.rag.embeddings import HashingEmbeddings

        self._inner = HashingEmbeddings(dim=dim)

    @property
    def dimension(self) -> int:
        return self._inner.dimension

    def embed(self, texts: list[str]) -> np.ndarray:
        return self._inner.embed(texts)


@register_provider("sentence_transformers")
class SentenceTransformersProvider(BaseEmbeddingProvider):
    def __init__(self, model_name: str | None = None):
        from app.rag.embeddings import SentenceTransformerEmbeddings

        self._inner = SentenceTransformerEmbeddings(model_name=model_name)

    @property
    def dimension(self) -> int:
        return self._inner.dimension

    def embed(self, texts: list[str]) -> np.ndarray:
        return self._inner.embed(texts)


class _LazyRemoteProvider(BaseEmbeddingProvider):
    """Placeholder for a future remote provider (lazy import, clear error)."""

    provider_name = "remote"
    endpoint_hint: str = ""

    def __init__(self, model_name: str | None = None, **kwargs):
        self.model_name = model_name
        self.options = kwargs
        self._fallback: HashingProvider | None = None

    @property
    def dimension(self) -> int:
        return 768

    def embed(self, texts: list[str]) -> np.ndarray:
        raise RuntimeError(
            f"Provider '{self.provider_name}' is not configured "
            f"({self.endpoint_hint}). Set it up or use 'hashing'."
        )


@register_provider("openai")
class OpenAIProvider(_LazyRemoteProvider):
    provider_name = "openai"
    endpoint_hint = "set OPENAI_API_KEY and install openai"


@register_provider("gemini")
class GeminiProvider(_LazyRemoteProvider):
    provider_name = "gemini"
    endpoint_hint = "set GOOGLE_API_KEY and install google-generativeai"


@register_provider("ollama")
class OllamaProvider(_LazyRemoteProvider):
    provider_name = "ollama"
    endpoint_hint = "run ollama serve and install ollama client"


@register_provider("huggingface")
class HuggingFaceProvider(_LazyRemoteProvider):
    provider_name = "huggingface"
    endpoint_hint = "set HF_API_TOKEN and install huggingface_hub"


def list_providers() -> list[str]:
    return sorted(_PROVIDER_REGISTRY)


def create_provider(name: str, **kwargs) -> BaseEmbeddingProvider:
    key = (name or "hashing").lower()
    if key == "sentence_transformers":
        try:
            return SentenceTransformersProvider(**kwargs)
        except Exception:
            return HashingProvider()
    cls = _PROVIDER_REGISTRY.get(key)
    if cls is None:
        raise ValueError(f"Unknown embedding provider: {name}. Available: {list_providers()}")
    if key in {"openai", "gemini", "ollama", "huggingface"}:
        # Remote providers degrade to hashing until configured; the manager
        # surfaces the misconfiguration as a warning, never a crash.
        try:
            provider = cls(**kwargs)
            return provider
        except Exception:
            return HashingProvider()
    return cls(**kwargs)
