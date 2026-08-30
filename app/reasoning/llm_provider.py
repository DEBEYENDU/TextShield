"""LLM Provider Abstraction for Reasoning Engine.

Defines the common interface for all LLM providers and a factory function
to create instances based on configuration. Provider-independent: switch
providers via configuration only, never hardcode.

Supported providers:
- Ollama (local)
- OpenAI-compatible (OpenAI, Azure, NVIDIA NIM)
- None (disabled/fallback)

API keys are read from environment variables only, never hard-coded.
"""

from __future__ import annotations

import json
import re
import os
from abc import ABC, abstractmethod
from typing import Any


def extract_json(text: str) -> dict[str, Any] | None:
    """Best-effort JSON extraction from an LLM response.

    Tries direct parsing first, then regex search for a JSON object
    within the text (handles cases where LLM includes prose or
    markdown formatting around the JSON).

    Args:
        text: The LLM response text.

    Returns:
        Parsed JSON dict if found, None otherwise.
    """
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return None


class LLMProvider(ABC):
    """Abstract base class for all LLM providers."""

    name: str = "base"

    @abstractmethod
    def complete(self, system: str, user: str) -> str:
        """Run a single completion; returns the assistant text."""
        pass

    @abstractmethod
    def supports_function_calling(self) -> bool:
        """Whether the provider supports function calling / JSON mode."""
        pass

    @abstractmethod
    def estimate_cost(self, text: str) -> Optional[float]:
        """Estimate processing cost in USD for given text length."""
        pass


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""

    name = "ollama"

    def __init__(self, base_url: str = "", model: str = ""):
        self.base_url = base_url or settings.LLM_BASE_URL
        self.model = model or settings.LLM_MODEL

    def complete(self, system: str, user: str) -> str:
        """Generate a completion via Ollama API."""
        import requests

        url = f"{self.base_url.rstrip('/')}/api/generate"
        payload = {
            "model": self.model,
            "prompt": f"{system}\n\n{user}",
            "stream": False,
            "options": {
                "temperature": getattr(settings, "LLM_TEMPERATURE", 0.2),
            },
        }

        try:
            response = requests.post(
                url, json=payload, timeout=settings.LLM_TIMEOUT_SECONDS
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except Exception as exc:
            from app.core.logging import get_logger

            logger = get_logger(__name__)
            logger.error("Ollama completion failed: %s", exc)
            return ""

    def supports_function_calling(self) -> bool:
        """Ollama does not natively support function calling."""
        return False

    def estimate_cost(self, text: str) -> Optional[float]:
        """Ollama cost estimation not available (local inference)."""
        return None


class OpenAICompatProvider(LLMProvider):
    """OpenAI-compatible provider (OpenAI, Azure, NVIDIA NIM)."""

    name = "openai_compat"

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str,
        display_name: str = "openai",
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.name = display_name

    def complete(self, system: str, user: str) -> str:
        """Generate a completion via OpenAI-compatible chat API."""
        import requests

        url = f"{self.base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": getattr(settings, "LLM_TEMPERATURE", 0.2),
            "stream": False,
        }

        try:
            response = requests.post(
                url, headers=headers, json=payload, timeout=settings.LLM_TIMEOUT_SECONDS
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as exc:
            from app.core.logging import get_logger

            logger = get_logger(__name__)
            logger.error("OpenAI-compatible completion failed: %s", exc)
            return ""

    def supports_function_calling(self) -> bool:
        """OpenAI-compatible providers support function calling / JSON mode."""
        return True

    def estimate_cost(self, text: str) -> Optional[float]:
        """Estimate cost based on token count.

        Returns approximate cost in USD. Uses OpenAI pricing as reference.
        """
        try:
            # Rough estimation: ~1 token = ~4 characters for English
            # GPT-4o: $5.00 / 1M input tokens, $15.00 / 1M output tokens
            # GPT-4: $10.00 / 1M input tokens, $30.00 / 1M output tokens
            # GPT-3.5 Turbo: $0.50 / 1M input tokens, $1.50 / 1M output tokens

            input_chars = len(system) + len(user) if False else len(user)
            # Simplified: estimate based on total text length
            total_chars = len(system) + len(user) if system else len(user)
            total_tokens = max(1, int(total_chars / 4))

            # Default to GPT-4o pricing if model not specified
            input_price_per_k = 0.005  # GPT-4o input
            output_price_per_k = 0.015  # GPT-4o output

            # Rough split: ~70% input, ~30% output for reasoning prompts
            input_tokens = max(1, int(total_tokens * 0.7))
            output_tokens = max(1, total_tokens - input_tokens)

            input_cost = (input_tokens / 1000) * input_price_per_k
            output_cost = (output_tokens / 1000) * output_price_per_k

            return round(input_cost + output_cost, 6)
        except Exception:
            return None


def create_llm_client(provider: str | None = None) -> Optional[LLMProvider]:
    """Factory function to create an LLM provider instance based on configuration.

    Args:
        provider: Override the default provider from settings. If None,
                  uses settings.LLM_PROVIDER.

    Returns:
        An LLMProvider instance, or None if disabled/misconfigured.
    """
    provider = (provider or settings.LLM_PROVIDER).lower()

    if provider in {"", "none"}:
        return None

    model = settings.LLM_MODEL
    if not model:
        from app.core.logging import get_logger

        logger = get_logger(__name__)
        logger.warning(
            "LLM provider %s specified but LLM_MODEL is empty - LLM disabled", provider
        )
        return None

    try:
        if provider == "ollama":
            return OllamaProvider()

        if provider == "openai":
            api_key = settings.LLM_API_KEY or os.getenv("OPENAI_API_KEY")
            base_url = settings.LLM_BASE_URL or "https://api.openai.com/v1"
            return OpenAICompatProvider(
                base_url=base_url,
                model=model,
                api_key=api_key or "",
                display_name="openai",
            )

        if provider == "nvidia":
            api_key = settings.LLM_API_KEY or os.getenv("NVIDIA_API_KEY")
            base_url = settings.LLM_BASE_URL or "https://integrate.api.nvidia.com/v1"
            return OpenAICompatProvider(
                base_url=base_url,
                model=model,
                api_key=api_key or "",
                display_name="nvidia",
            )

        from app.core.logging import get_logger

        logger = get_logger(__name__)
        logger.warning("Unknown LLM provider %r - LLM disabled", provider)
        return None
    except Exception as exc:
        from app.core.logging import get_logger

        logger = get_logger(__name__)
        logger.error("Failed to create LLM provider %s: %s", provider, exc)
        return None
