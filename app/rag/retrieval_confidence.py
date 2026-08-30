"""Retrieval confidence: estimate confidence in the retrieval results.

Factors include:
- Similarity between query and retrieved chunks
- Agreement between multiple query types (primary, intent, behavior, entity, context)
- Metadata quality and trust level
- Coverage of detected topics/entities/intents
"""

from __future__ import annotations

from typing import List, Dict, Any, Tuple, Optional

from app.rag.config import RAG_SIMILARITY_THRESHOLD, RAG_AGREEMENT_WEIGHTS


def estimate_confidence(
    retrieved_chunks: List[Dict[str, Any]],
    semantic_features,
    query_result: Optional[Any] = None,
) -> Tuple[float, Dict[str, float]]:  # (overall_confidence, factor_breakdown)
    """Estimate retrieval confidence based on multiple factors.

    Args:
        retrieved_chunks: List of validated, reranked chunks.
        semantic_features: Features from the semantic engine.
        query_result: The QueryBuilderResult from query building (optional).

    Returns:
        Tuple of (overall_confidence, dict of factor scores).
    """
    if not retrieved_chunks:
        return 0.0, {}

    # Factor 1: Similarity-based confidence
    similarity_conf = _compute_similarity_confidence(retrieved_chunks)

    # Factor 2: Agreement between query types
    if query_result is not None:
        agreement_conf = _compute_agreement_confidence(retrieved_chunks, query_result)
    else:
        agreement_conf = 0.5  # Default agreement score when no query result

    # Factor 3: Metadata quality confidence
    metadata_conf = _compute_metadata_confidence(retrieved_chunks)

    # Factor 4: Trust level confidence
    trust_conf = _compute_trust_confidence(retrieved_chunks)

    # Factor 5: Coverage confidence (how well topics are covered)
    coverage_conf = _compute_coverage_confidence(retrieved_chunks, semantic_features)

    # Weighted composite score
    weights = RAG_AGREEMENT_WEIGHTS
    overall_confidence = (
        weights.get("similarity", 0.30) * similarity_conf
        + weights.get("agreement", 0.25) * agreement_conf
        + weights.get("metadata", 0.20) * metadata_conf
        + weights.get("trust", 0.15) * trust_conf
        + weights.get("coverage", 0.10) * coverage_conf
    )

    # Normalize to 0-1 range
    overall_confidence = min(max(overall_confidence, 0.0), 1.0)

    # Build factor breakdown
    factors: Dict[str, float] = {
        "similarity": round(similarity_conf, 4),
        "agreement": round(agreement_conf, 4),
        "metadata": round(metadata_conf, 4),
        "trust": round(trust_conf, 4),
        "coverage": round(coverage_conf, 4),
        "overall": round(overall_confidence, 4),
    }

    return overall_confidence, factors


def _compute_similarity_confidence(chunks: List[Dict[str, Any]]) -> float:
    """Compute confidence based on retrieval similarity scores."""
    if not chunks:
        return 0.0

    scores = [chunk.get("score", 0.0) for chunk in chunks]
    avg_score = sum(scores) / len(scores)
    # Normalize: if all scores are above threshold, high confidence
    if avg_score >= RAG_SIMILARITY_THRESHOLD:
        # Also consider how spread out the scores are
        score_range = max(scores) - min(scores)
        if score_range < 0.3:
            # Tight cluster of high scores = high confidence
            return min(avg_score, 1.0)
        else:
            # Varied scores = moderate confidence
            return (avg_score + 0.5) / 2.0
    else:
        # Below threshold = low confidence
        return avg_score


def _compute_agreement_confidence(chunks: List[Dict[str, Any]], query_result) -> float:
    """Compute confidence based on agreement between query types."""
    if not chunks or not query_result:
        return 0.5

    # Check how many query types contributed to each chunk
    contributing_types: Set[str] = set()
    for chunk in chunks:
        chunk_query_types = chunk.get("query_types", [])
        contributing_types.update(chunk_query_types)

    # Count how many query types we have total
    total_query_types = len(query_result.all_queries) if query_result.all_queries else 1

    # Agreement ratio: what fraction of possible types are represented
    agreement_ratio = len(contributing_types) / total_query_types

    # Also check if chunks agree on category
    chunk_categories = {chunk.get("category", "") for chunk in chunks}
    category_agreement = len(chunk_categories) <= 2  # High agreement if few categories

    # Combined confidence
    base_agreement = agreement_ratio * 1.0 + (0.5 if category_agreement else 0.0)
    return min(base_agreement, 1.0)


def _compute_metadata_confidence(chunks: List[Dict[str, Any]]) -> float:
    """Compute confidence based on metadata quality."""
    if not chunks:
        return 0.5

    valid_count = 0
    for chunk in chunks:
        metadata = chunk.get("metadata", {})
        # Check required fields
        required = ["source", "category", "version", "last_updated"]
        if all(metadata.get(f) for f in required):
            valid_count += 1

    return valid_count / len(chunks)


def _compute_trust_confidence(chunks: List[Dict[str, Any]]) -> float:
    """Compute confidence based on trust levels of chunks."""
    if not chunks:
        return 0.5

    trust_levels = {"high": 1.0, "medium": 0.7, "low": 0.3, "": 0.5}
    total = 0.0
    for chunk in chunks:
        metadata = chunk.get("metadata", {})
        trust = metadata.get("trust_level", "medium")
        total += trust_levels.get(trust, 0.5)

    return total / len(chunks)


def _compute_coverage_confidence(
    chunks: List[Dict[str, Any]], semantic_features
) -> float:
    """Compute confidence based on how well topics/entities are covered."""
    if not chunks or not semantic_features:
        return 0.5

    # Check which detected features are covered by chunk categories
    detected_topics = (
        set(semantic_features.topic_names)
        if hasattr(semantic_features, "topic_names")
        else set()
    )
    chunk_categories = {chunk.get("category", "") for chunk in chunks}

    # Coverage: what fraction of detected topics are represented in chunk categories
    if not detected_topics:
        return 0.7  # Neutral if no topics detected

    covered_topics = sum(
        1
        for topic in detected_topics
        if any(topic.lower() in cat.lower() for cat in chunk_categories)
    )

    coverage_ratio = covered_topics / len(detected_topics)
    return coverage_ratio
