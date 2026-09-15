"""Frontend helpers for semantic visualization."""

from __future__ import annotations


def format_semantic_result(result):
    return {
        "language": result.language,
        "contexts": [{"domain": c.domain, "confidence": c.confidence} for c in result.contexts],
        "topics": [{"topic": t.topic, "confidence": t.confidence} for t in result.topics],
        "entity_count": len(result.entities),
        "features": result.semantic_features.dict() if hasattr(result.semantic_features, "dict") else result.semantic_features,
    }
