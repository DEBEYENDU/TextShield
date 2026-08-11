"""LLM provider abstraction.

Supported providers (configured via environment variables):

* ``ollama``  - local Ollama server           (LLM_BASE_URL, LLM_MODEL)
* ``openai``  - OpenAI-compatible APIs        (LLM_BASE_URL, LLM_MODEL, LLM_API_KEY)
* ``nvidia``  - NVIDIA NIM / build endpoints  (LLM_BASE_URL, LLM_MODEL, LLM_API_KEY)
* ``none``    - disables the LLM entirely

API keys are read from environment variables only, never hard-coded.
The LLM is optional: when unavailable, TextShield falls back to
template-based explanations and classification still works.
"""
from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any

import requests

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMClient(ABC):
    """Minimal chat interface shared by all providers."""

    name = "base"

    @abstractmethod
    def complete(self, system: str, user: str) -> str:
        """Run a single completion; returns the assistant text."""


class OllamaClient(LLMClient):
    name = "ollama"

    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def complete(self, system: str, user: str) -> str:
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": f"{system}\n\n{user}",
                "stream": False,
                "options": {"temperature": settings.LLM_TEMPERATURE},
            },
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json().get("response", "")


class OpenAICompatClient(LLMClient):
    """Works with any OpenAI-compatible /chat/completions API (incl. NIM)."""

    name = "openai_compat"

    def __init__(self, base_url: str, model: str, api_key: str, display_name: str):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.name = display_name

    def complete(self, system: str, user: str) -> str:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": settings.LLM_TEMPERATURE,
                "stream": False,
            },
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


def create_llm_client() -> LLMClient | None:
    """Build the configured LLM client; None when disabled or misconfigured."""
    provider = settings.LLM_PROVIDER
    if provider in {"", "none"}:
        return None
    model = settings.LLM_MODEL
    if not model:
        logger.warning("LLM provider is %s but LLM_MODEL is empty - LLM disabled", provider)
        return None
    try:
        if provider == "ollama":
            return OllamaClient(settings.LLM_BASE_URL, model)
        if provider == "openai":
            return OpenAICompatClient(
                settings.LLM_BASE_URL or "https://api.openai.com/v1",
                model, settings.LLM_API_KEY, "openai",
            )
        if provider == "nvidia":
            return OpenAICompatClient(
                settings.LLM_BASE_URL or "https://integrate.api.nvidia.com/v1",
                model, settings.LLM_API_KEY, "nvidia",
            )
        logger.warning("Unknown LLM_PROVIDER %r - LLM disabled", provider)
        return None
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to create LLM client: %s", exc)
        return None


def extract_json(text: str) -> dict[str, Any] | None:
    """Best-effort JSON extraction from an LLM response."""
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