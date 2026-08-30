"""Shared helpers for the Intent & Behavior Analysis Engine.

Builds a normalized ``AnalysisContext`` from a semantic result (or raw
message) and provides deterministic scoring primitives used by every
detector. All logic here is deterministic: the same input always yields
the same context.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Sequence

from app.semantic.semantic_models import SemanticAnalysisResult
from app.semantic.semantic_pipeline import SemanticPipeline

# ------------------------------------------------------------ primitives


def compile_word_patterns(*words: str) -> tuple[re.Pattern, ...]:
    """Compile word-boundary patterns.

    A trailing ``\\b`` is only appended when the pattern ends on a word
    character or a closing group, so patterns ending in literal
    punctuation (``reminder:``, ``status:``, ``no.:?``) still match.
    """
    compiled: list[re.Pattern] = []
    for word in words:
        source = r"\b(?:{})".format(word)
        if word[-1:] in ")]}" or word[-1:].isalnum():
            source += r"\b"
        compiled.append(re.compile(source, re.IGNORECASE | re.UNICODE))
    return tuple(compiled)


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def round_conf(value: float) -> float:
    """Round a confidence to 4 decimals deterministically."""
    return round(clamp(value), 4)


def hit_confidence(
    hits: int, total_markers: int, base: float = 0.35, boost: float = 0.14
) -> float:
    """Map marker hits to a confidence: base + boost * (hits/total)."""
    if hits <= 0 or total_markers <= 0:
        return 0.0
    return round_conf(base + boost * (hits / min(total_markers, 8)))


def unique(seq: Iterable[str], limit: int = 3) -> list[str]:
    seen: list[str] = []
    for item in seq:
        item = item.strip()[:64]
        if item and item not in seen:
            seen.append(item)
            if len(seen) >= limit:
                break
    return seen


def regex_snippets(
    text: str, patterns: Sequence[re.Pattern], limit: int = 3
) -> list[str]:
    """Collect unique matched snippets for a list of compiled regexes."""
    found: list[str] = []
    for pattern in patterns:
        for match in pattern.finditer(text):
            snippet = match.group(0).strip()[:64]
            if snippet and snippet not in found:
                found.append(snippet)
                if len(found) >= limit:
                    return found
    return found


def all_caps_ratio(text: str) -> float:
    """Fraction of alphabetic characters that are uppercase (0-1)."""
    letters = [ch for ch in text if ch.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for ch in letters if ch.isupper()) / len(letters)


def requestive_ratio(context: "AnalysisContext") -> float:
    """Share of sentences that are questions or imperatives (0-1)."""
    total = context.semantic.semantic_features.sentence_count or 1
    return clamp(
        (
            context.semantic.semantic_features.question_count
            + context.semantic.semantic_features.imperative_count
        )
        / total
    )


def entity_values(context: "AnalysisContext", etype: str) -> list[str]:
    return [e.value for e in context.semantic.entities if e.type == etype]


def entity_types(context: "AnalysisContext") -> set[str]:
    return {e.type for e in context.semantic.entities}


def topic_names(context: "AnalysisContext") -> set[str]:
    return {t.topic for t in context.semantic.topics}


def domain_names(context: "AnalysisContext") -> set[str]:
    return {c.domain for c in context.semantic.contexts}


def has_token(tokens: set[str], lexicon: Iterable[str]) -> bool:
    return bool(tokens & set(lexicon))


# ------------------------------------------------------------ context


@dataclass
class AnalysisContext:
    """Everything a detector may read.

    Built once per message by the pipeline; detectors are pure functions
    of this object, which makes them independently testable and
    replaceable by future model-based strategies.
    """

    raw_text: str
    normalized: str
    message_type: str
    semantic: SemanticAnalysisResult
    sentences: list[str] = field(default_factory=list)
    tokens: set[str] = field(default_factory=set)
    lowercase: str = field(default="")

    def __post_init__(self) -> None:
        if not self.sentences:
            self.sentences = list(self.semantic.sentences)
        if not self.tokens:
            self.tokens = {
                token.lower()
                for token in re.findall(
                    r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*", self.normalized
                )
            }
        if not self.lowercase:
            self.lowercase = self.normalized.lower()


def build_context(
    message: str = "",
    *,
    message_type: str = "text",
    subject: str | None = None,
    sender: str | None = None,
    body: str | None = None,
    email_raw: str | None = None,
    semantic_result: SemanticAnalysisResult | None = None,
    semantic_pipeline: SemanticPipeline | None = None,
) -> AnalysisContext:
    """Build an analysis context.

    Reuses the Semantic Understanding Engine when no pre-computed result
    is supplied — the semantic engine stays the single source of truth
    for preprocessing; intent never re-implements it.
    """
    if semantic_result is None:
        pipeline = semantic_pipeline or SemanticPipeline()
        semantic_result = pipeline.analyze(
            message=message,
            message_type=message_type,
            subject=subject,
            sender=sender,
            body=body,
            email_raw=email_raw,
            include_embeddings=False,
        )
    return AnalysisContext(
        raw_text=message or body or subject or "",
        normalized=semantic_result.normalized_text,
        message_type=message_type,
        semantic=semantic_result,
        sentences=[],
        tokens=set(),
        lowercase="",
    )
