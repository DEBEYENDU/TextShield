"""Semantic Understanding Engine — output schema.

All structured outputs of the engine are defined here so downstream
modules (intent, behavior, decision, explainability) consume one stable
contract.

Determinism: every field below is derived deterministically from the
input text (plus, optionally, cached embeddings). No probability of
spam is ever estimated by this engine.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

# ----------------------------------------------------------------- context
CONTEXT_DOMAINS = [
    "banking",
    "finance",
    "shopping",
    "education",
    "employment",
    "government",
    "healthcare",
    "technology",
    "personal_communication",
    "business",
    "social_media",
    "unknown",
]

LanguageLabel = str


class SemanticContext(BaseModel):
    """A contextual domain with the engine's confidence."""

    domain: str = Field(description="One of CONTEXT_DOMAINS")
    confidence: float = Field(ge=0.0, le=1.0)


class SemanticTopic(BaseModel):
    """A detected semantic topic with confidence."""

    topic: str
    confidence: float = Field(ge=0.0, le=1.0)


# ----------------------------------------------------------------- entities
class SemanticEntity(BaseModel):
    """One extracted entity.

    ``value`` is the exact surface text; ``normalized`` is the canonical
    form (e.g. digits-only phone, uppercase domain). Offsets are
    character indices into the original input text when available.
    """

    type: str = Field(
        description="person|organization|bank|company|location|money|phone|"
        "email|url|date|time|account_number|tracking_number"
    )
    value: str
    normalized: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    start: int | None = None
    end: int | None = None
    attributes: dict = Field(default_factory=dict)


# ----------------------------------------------------------------- features
class SemanticFeatures(BaseModel):
    """Semantic surface features.

    These are *descriptive* indicators feeding downstream understanding;
    they are NOT spam indicators by themselves.
    """

    message_length: int
    word_count: int
    sentence_count: int
    question_count: int
    imperative_count: int
    emoji_count: int
    url_count: int
    email_count: int
    phone_count: int
    money_count: int
    date_count: int
    time_count: int
    has_request: bool
    has_offer: bool
    has_urgency: bool
    has_financial_reference: bool
    has_credential_request: bool
    has_personal_information_request: bool


class SemanticConfidence(BaseModel):
    """Confidence estimates for each extraction stage (0..1).

    Language/context/topic/entity confidences only — never a spam
    probability.
    """

    language: float = Field(ge=0.0, le=1.0)
    context: float = Field(ge=0.0, le=1.0)
    topic: float = Field(ge=0.0, le=1.0)
    entity: float = Field(ge=0.0, le=1.0)


# ----------------------------------------------------------------- output
class SemanticAnalysisResult(BaseModel):
    """The complete structured output of the Semantic Understanding Engine."""

    language: LanguageLabel
    contexts: list[SemanticContext]
    topics: list[SemanticTopic]
    entities: list[SemanticEntity]
    embedding_dimension: int
    embeddings: dict[str, Any] = Field(
        default_factory=dict,
        description="{'message': [...], 'sentences': [[...]], 'subject': [...], "
        "'body': [...]} — only when include_embeddings=True",
    )
    semantic_features: SemanticFeatures
    confidence: SemanticConfidence
    sentences: list[str] = Field(
        default_factory=list, description="Sentence segmentation of the message"
    )
    embedding_provider: str = Field(default="")
    engine_version: str = Field(default="1.0.0")
    normalized_text: str = Field(
        default="",
        description="Canonically normalized full text (reused by later engines)",
    )
    message_preview: str = Field(
        default="", description="Truncated, safe preview for logs"
    )
