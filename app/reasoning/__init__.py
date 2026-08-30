"""TextShield Reasoning Engine - Phase 10."""

from __future__ import annotations

from app.reasoning.llm_provider import (
    create_llm_client,
    LLMProvider,
    OllamaProvider,
    OpenAICompatProvider,
)
from app.reasoning.prompt_builder import PromptBuilder
from app.reasoning.evidence_validator import EvidenceValidator, ClaimValidationResult
from app.reasoning.retrieval_confidence import (
    estimate_confidence,
    quick_estimate_confidence,
)
from app.reasoning.response_parser import (
    parse_llm_response,
    ReasoningResponse,
    parse_and_validate_llm_output,
)
from app.reasoning.prompt_injection_protector import (
    detect_injection,
    sanitize_user_input,
    PromptInjectionProtector,
)

__all__ = [
    "LLMProvider",
    "OllamaProvider",
    "OpenAICompatProvider",
    "create_llm_client",
    "PromptBuilder",
    "EvidenceValidator",
    "ClaimValidationResult",
    "estimate_confidence",
    "quick_estimate_confidence",
    "parse_llm_response",
    "ReasoningResponse",
    "parse_and_validate_llm_output",
    "detect_injection",
    "sanitize_user_input",
    "PromptInjectionProtector",
]
