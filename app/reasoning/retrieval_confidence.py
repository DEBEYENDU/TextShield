"""Retrieval Confidence Estimation for Reasoning Engine.

Estimates confidence in the reasoning output based on multiple factors:
- Similarity of retrieved chunks to the query
- Agreement between different evidence sources
- Metadata quality and completeness
- Trust level of evidence sources
- Coverage of detected topics/entities by retrieved knowledge

This estimates confidence in the reasoning process, NOT final spam probability.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

from app.core.config import settings

# ---------------------------------------------------------------------------
# Confidence factor computation
# ---------------------------------------------------------------------------


def compute_similarity_confidence(retrieved_chunks: List[Dict[str, Any]]) -> float:
    """Compute confidence based on retrieved chunk similarities.

    Higher similarity scores indicate more relevant evidence,
    increasing overall confidence.

    Args:
        retrieved_chunks: List of retrieved chunks with "similarity" keys.

    Returns:
        Confidence score in [0.0, 1.0].
    """
    if not retrieved_chunks:
        return 0.0

    similarities: List[float] = []
    for chunk in retrieved_chunks:
        sim = chunk.get("similarity", 0.0)
        # Clamp to [0, 1]
        sim = max(0.0, min(1.0, float(sim)))
        similarities.append(sim)

    # Use median similarity as robust central tendency
    sorted_sims = sorted(similarities)
    n = len(sorted_sims)
    if n % 2 == 1:
        median = sorted_sims[n // 2]
    else:
        median = (sorted_sims[n // 2 - 1] + sorted_sims[n // 2]) / 2

    return round(median, 4)


def compute_agreement_confidence(
    claim_validation_results: List[Any],
) -> float:
    """Compute confidence based on how well claims agree with evidence.

    Args:
        claim_validation_results: List of ClaimValidationResult objects
                                 from the EvidenceValidator.

    Returns:
        Agreement confidence score in [0.0, 1.0].
    """
    if not claim_validation_results:
        return 0.5  # Neutral when no claims to evaluate

    supported_count = sum(1 for r in claim_validation_results if r.is_supported)
    total_count = len(claim_validation_results)

    # Ratio of supported claims to total claims
    ratio = supported_count / total_count

    # Apply a weighting: full agreement = 1.0, no agreement = 0.0
    # Use square root to avoid over-penalizing small numbers
    agreement = ratio**0.5

    return round(min(1.0, agreement), 4)


def compute_metadata_confidence(
    claim_validation_results: List[Any],
) -> float:
    """Compute confidence based on metadata quality of evidence sources.

    Checks whether validated claims have proper source metadata
    (source name, category, version, similarity score).

    Args:
        claim_validation_results: List of ClaimValidationResult objects.

    Returns:
        Metadata confidence score in [0.0, 1.0].
    """
    if not claim_validation_results:
        return 0.5

    total = len(claim_validation_results)
    supported_with_metadata = 0

    for result in claim_validation_results:
        if result.is_supported and result.supporting_sources:
            # Check if indexed sources have proper metadata
            for source_key in result.supporting_sources:
                if (
                    source_key in validator._indexed_sources
                    if "validator" in dir()
                    else {}
                ):
                    supported_with_metadata += 1
                    break
        elif result.is_supported:
            supported_with_metadata += 1

    if total == 0:
        return 0.5

    ratio = supported_with_metadata / total
    return round(ratio, 4)


def compute_trust_confidence(
    claim_validation_results: List[Any],
    validator: Any,
) -> float:
    """Compute confidence based on trust level of evidence sources.

    Args:
        claim_validation_results: List of ClaimValidationResult objects.
        validator: EvidenceValidator instance with indexed sources.

    Returns:
        Trust confidence score in [0.0, 1.0].
    """
    if not claim_validation_results:
        return 0.5

    total = len(claim_validation_results)
    if total == 0:
        return 0.5

    trusted_count = 0
    for result in claim_validation_results:
        if result.is_supported and result.supporting_sources:
            for source_key in result.supporting_sources:
                if source_key in validator._indexed_sources:
                    source_info = validator._indexed_sources[source_key]
                    # Check if source has a version field (indicates proper metadata)
                    if source_info.get("version") not in (None, "", "unknown"):
                        trusted_count += 1
                        break
                        break

    ratio = trusted_count / total if total > 0 else 0.5
    return round(ratio, 4)


def compute_coverage_confidence(
    claim_validation_results: List[Any],
    semantic_features: Dict[str, Any],
) -> float:
    """Compute confidence based on how well retrieved knowledge covers
    detected topics and entities.

    Args:
        claim_validation_results: List of ClaimValidationResult objects.
        semantic_features: Output from the Semantic Engine.

    Returns:
        Coverage confidence score in [0.0, 1.0].
    """
    if not claim_validation_results:
        return 0.0

    total = len(claim_validation_results)
    covered = 0

    # Get detected topics and entities from semantic features
    detected_topics: Set[str] = set(semantic_features.get("topic_names", []))
    detected_entities: Set[str] = set(semantic_features.get("entities", []))

    for result in claim_validation_results:
        if result.is_supported and result.supporting_sources:
            # Check if any supporting source covers detected topics/entities
            for source_key in result.supporting_sources:
                if (
                    source_key in validator._indexed_sources
                    if "validator" in dir()
                    else {}
                ):
                    source_info = validator._indexed_sources[source_key]
                    content = source_info.get("content", "").lower()
                    # Check topic coverage
                    for topic in detected_topics:
                        if topic.lower() in content:
                            covered += 1
                            break
                    # Check entity coverage
                    for entity in detected_entities:
                        if entity.lower() in content:
                            covered += 1
                            break

    if total == 0:
        return 0.5

    ratio = covered / (total * max(len(detected_topics) + len(detected_entities), 1))
    return round(min(1.0, ratio), 4)


# ---------------------------------------------------------------------------
# Main confidence estimation function
# ---------------------------------------------------------------------------

# Weight constants for the composite confidence score
# These are configurable via settings in a production deployment
RAG_AGREEMENT_WEIGHTS: Dict[str, float] = {
    "similarity": 0.30,
    "agreement": 0.25,
    "metadata": 0.20,
    "trust": 0.15,
    "coverage": 0.10,
}


def estimate_confidence(
    claim_validation_results: List[Any],
    semantic_features: Dict[str, Any],
    retrieved_chunks: Optional[List[Dict[str, Any]]] = None,
    validator: Optional[Any] = None,
) -> Dict[str, float]:
    """Estimate overall reasoning confidence based on multiple factors.

    This estimates confidence in the reasoning process based on evidence
    quality, not final spam probability (per Phase 10 guidelines).

    Args:
        claim_validation_results: List of ClaimValidationResult objects
                                  from the EvidenceValidator.
        semantic_features: Output from the Semantic Engine.
        retrieved_chunks: Optional list of retrieved chunks from RAG pipeline.
        validator: Optional EvidenceValidator instance.

    Returns:
        Dict mapping factor names to confidence scores in [0.0, 1.0],
        plus an "overall" key with the weighted composite score.
    """
    # Compute individual factor scores
    similarity_conf = compute_similarity_confidence(retrieved_chunks or [])

    agreement_conf = compute_agreement_confidence(claim_validation_results)

    metadata_conf = compute_metadata_confidence(claim_validation_results)

    trust_conf = (
        compute_trust_confidence(claim_validation_results, validator)
        if validator
        else 0.5
    )

    coverage_conf = compute_coverage_confidence(
        claim_validation_results, semantic_features
    )

    # Weighted composite score
    weights = RAG_AGREEMENT_WEIGHTS
    overall_confidence = round(
        (
            weights.get("similarity", 0.30) * similarity_conf
            + weights.get("agreement", 0.25) * agreement_conf
            + weights.get("metadata", 0.20) * metadata_conf
            + weights.get("trust", 0.15) * trust_conf
            + weights.get("coverage", 0.10) * coverage_conf
        ),
        4,
    )

    return {
        "similarity": similarity_conf,
        "agreement": agreement_conf,
        "metadata": metadata_conf,
        "trust": trust_conf,
        "coverage": coverage_conf,
        "overall": overall_confidence,
    }


# ---------------------------------------------------------------------------
# Global convenience function
# ---------------------------------------------------------------------------


def quick_estimate_confidence(
    claim_validation_results: List[Any],
    semantic_features: Dict[str, Any],
    retrieved_chunks: Optional[List[Dict[str, Any]]] = None,
) -> float:
    """Quick convenience function: returns only the overall confidence score.

    Args:
        claim_validation_results: List of ClaimValidationResult objects.
        semantic_features: Semantic Engine output.
        retrieved_chunks: Optional retrieved chunks from RAG pipeline.

    Returns:
        Overall confidence score in [0.0, 1.0].
    """
    result = estimate_confidence(
        claim_validation_results, semantic_features, retrieved_chunks
    )
    return result["overall"]
