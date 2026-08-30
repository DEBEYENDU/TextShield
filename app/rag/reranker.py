"""Re-ranking: rank retrieved chunks using multiple relevance factors.

Reranks retrieved chunks using: semantic similarity, intent relevance,
behavior relevance, metadata quality, trust level, freshness, and category
relevance.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional, Tuple

from app.rag.query_builder import build_queries_from_semantic


def rerank_chunks(
    chunks: List[Dict[str, Any]],
    semantic_features,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """Rerank retrieved chunks using multiple relevance factors.

    Args:
        chunks: List of retrieved chunks from hybrid retrieval.
        semantic_features: Features from the semantic engine for relevance scoring.
        top_k: Return top k reranked chunks.

    Returns:
        Reranked list of chunks sorted by composite relevance score.
    """
    if not chunks:
        return []

    # Compute relevance score for each chunk
    for chunk in chunks:
        chunk["relevance_score"] = _compute_relevance_score(chunk, semantic_features)

    # Sort by relevance score descending
    chunks.sort(key=lambda x: x.get("relevance_score", 0.0), reverse=True)

    # Return top_k
    return chunks[:top_k]


def _compute_relevance_score(
    chunk: Dict[str, Any],
    semantic_features,
) -> float:
    """Compute composite relevance score for a chunk.

    Factors:
    - Semantic similarity (from vector search score)
    - Intent relevance
    - Behavior relevance
    - Metadata quality
    - Trust level
    - Category relevance
    - Freshness (recency)
    """
    # Base score from vector search (0-1 range)
    base_score = chunk.get("score", 0.0)

    # Intent relevance
    intent_relevance = _compute_intent_relevance(chunk, semantic_features)

    # Behavior relevance
    behavior_relevance = _compute_behavior_relevance(chunk, semantic_features)

    # Metadata quality
    metadata_quality = _compute_metadata_quality(chunk)

    # Trust level
    trust_score = _compute_trust_score(chunk)

    # Category relevance
    category_relevance = _compute_category_relevance(chunk, semantic_features)

    # Freshness (based on last_updated in metadata)
    freshness = _compute_freshness(chunk)

    # Weighted composite score
    # Weights can be configured; these are defaults
    weights = {
        "base": 0.30,
        "intent": 0.20,
        "behavior": 0.15,
        "metadata": 0.15,
        "trust": 0.10,
        "category": 0.10,
        "freshness": 0.0,
    }

    composite = (
        weights["base"] * base_score
        + weights["intent"] * intent_relevance
        + weights["behavior"] * behavior_relevance
        + weights["metadata"] * metadata_quality
        + weights["trust"] * trust_score
        + weights["category"] * category_relevance
        + weights["freshness"] * freshness
    )

    # Normalize to 0-1 range
    return min(max(composite, 0.0), 1.0)


def _compute_intent_relevance(chunk: Dict[str, Any], semantic_features) -> float:
    """Compute how well the chunk matches the detected intent."""
    chunk_category = chunk.get("category", "")
    detected_intent = getattr(semantic_features, "intent", None)

    if not detected_intent:
        return 0.5  # Neutral if no intent detected

    # Higher score if chunk category matches intent-related categories
    intent_categories = {
        "phishing": ["phishing", "email_scams", "banking_scams"],
        "fraud": ["investment_scams", "loan_scams", "banking_scams"],
        "scam": ["scams", "banking_scams", "investment_scams"],
    }

    if chunk_category in intent_categories.get(detected_intent, []):
        return 1.0
    elif chunk_category in ["examples", "legitimate", "safety_guidelines"]:
        # Examples and legitimate communications have lower intent relevance for scam detection
        return 0.3
    else:
        return 0.5


def _compute_behavior_relevance(chunk: Dict[str, Any], semantic_features) -> float:
    """Compute how well the chunk matches the detected behavioral patterns."""
    behavioral_patterns = getattr(semantic_features, "behavioral_patterns", [])
    chunk_category = chunk.get("category", "")

    if not behavioral_patterns:
        return 0.5  # Neutral if no patterns detected

    # Score based on category match with behavioral patterns
    pattern_category_map = {
        "urgency": ["spam_patterns", "examples"],
        "authority": ["phishing", "banking_scams"],
        "fear": ["phishing", "sms_scams"],
        "reward": ["sms_scams", "examples"],
        "curiosity": ["examples", "spam_patterns"],
        "scarcity": ["examples", "sms_scams"],
        "reciprocity": ["examples", "spam_patterns"],
        "trust_building": ["examples", "legitimate"],
        "social_proof": ["examples", "spam_patterns"],
        "pressure": ["sms_scams", "phishing"],
        "personalization": ["examples", "phishing"],
    }

    total_relevance = 0.0
    for pattern in behavioral_patterns:
        mapped_categories = pattern_category_map.get(pattern, [])
        if chunk_category in mapped_categories:
            total_relevance += 1.0 / len(behavioral_patterns)

    return min(total_relevance, 1.0)


def _compute_metadata_quality(chunk: Dict[str, Any]) -> float:
    """Compute metadata quality score for a chunk."""
    metadata = chunk.get("metadata", {})
    score = 0.0

    # Presence of required fields
    required_fields = ["source", "category", "version", "last_updated"]
    for field in required_fields:
        if field in metadata and metadata[field]:
            score += 1.0 / len(required_fields)

    # Trust level presence and validity
    trust = metadata.get("trust_level", "")
    if trust in ("high", "medium", "low"):
        score += 0.1

    # Version presence
    if metadata.get("version"):
        score += 0.1

    # Last updated recency (newer is better)
    last_updated = metadata.get("last_updated", "")
    if last_updated:
        try:
            from datetime import datetime

            updated_date = datetime.strptime(last_updated, "%Y-%m-%d")
            age_years = (datetime.now() - updated_date).days / 365.0
            # Decay: fresher documents get higher scores
            if age_years <= 1:
                score += 0.2
            elif age_years <= 2:
                score += 0.1
            elif age_years <= 5:
                score += 0.05
        except ValueError:
            score += 0.0  # Invalid date format

    return min(score, 1.0)


def _compute_trust_score(chunk: Dict[str, Any]) -> float:
    """Compute trust level score for a chunk."""
    metadata = chunk.get("metadata", {})
    trust_level = metadata.get("trust_level", "medium")

    trust_map = {"high": 1.0, "medium": 0.7, "low": 0.3}
    return trust_map.get(trust_level, 0.5)


def _compute_category_relevance(chunk: Dict[str, Any], semantic_features) -> float:
    """Compute category relevance based on semantic features."""
    chunk_category = chunk.get("category", "general")
    detected_intent = getattr(semantic_features, "intent", None)

    # If we have a detected intent, check category alignment
    if detected_intent:
        intent_category_map = {
            "phishing": "phishing",
            "fraud": "investment_scams",
            "scam": "banking_scams",
        }
        target_category = intent_category_map.get(detected_intent, chunk_category)
        if chunk_category == target_category:
            return 1.0
        elif chunk_category == "examples":
            # Examples are always somewhat relevant
            return 0.7
        else:
            return 0.5
    else:
        # No specific intent, check if it's a known scam category
        known_scams = {
            "banking_scams",
            "phishing",
            "investment_scams",
            "sms_scams",
            "email_scams",
        }
        if chunk_category in known_scams:
            return 0.8
        elif chunk_category in {"examples", "legitimate", "safety_guidelines"}:
            return 0.6
        else:
            return 0.5


def _compute_freshness(chunk: Dict[str, Any]) -> float:
    """Compute freshness score based on last_updated date."""
    from datetime import datetime

    metadata = chunk.get("metadata", {})
    last_updated = metadata.get("last_updated", "")

    if not last_updated:
        return 0.5  # Neutral if no date

    try:
        updated_date = datetime.strptime(last_updated, "%Y-%m-%d")
        age_days = (datetime.now() - updated_date).days

        # Decay: fresher is better
        if age_days <= 30:
            return 1.0
        elif age_days <= 90:
            return 0.8
        elif age_days <= 180:
            return 0.6
        elif age_days <= 365:
            return 0.4
        else:
            return 0.2
    except ValueError:
        return 0.5
