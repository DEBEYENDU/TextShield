"""Evidence validation: reject evidence that fails quality checks.

Rejects evidence if:
- Similarity is below threshold
- Metadata is invalid
- Document version is obsolete
- Knowledge source is untrusted
- Chunk is incomplete
"""

from __future__ import annotations

from typing import List, Dict, Any, Tuple, Optional

from app.rag.config import RAG_SIMILARITY_THRESHOLD, RAG_MIN_METADATA_FIELDS


def validate_evidence(
    chunks: List[Dict[str, Any]],
    semantic_features,
    min_similarity: Optional[float] = None,
    validate_metadata: bool = True,
    validate_trust: bool = True,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], float]:
    """Validate retrieved evidence and reject invalid chunks.

    Args:
        chunks: List of retrieved chunks to validate.
        semantic_features: Features from the semantic engine for context.
        min_similarity: Minimum similarity threshold (uses config default if None).
        validate_metadata: Whether to validate metadata fields.
        validate_trust: Whether to validate trust level.

    Returns:
        Tuple of (valid_chunks, rejected_chunks, overall_confidence).
    """
    if min_similarity is None:
        from app.rag.config import RAG_SIMILARITY_THRESHOLD

        min_similarity = RAG_SIMILARITY_THRESHOLD

    valid_chunks: List[Dict[str, Any]] = []
    rejected_chunks: List[Dict[str, Any]] = []
    total_score = 0.0

    for chunk in chunks:
        score = 0.0
        rejection_reasons: List[str] = []

        # 1. Check similarity threshold
        similarity = chunk.get("score", chunk.get("similarity", 0.0))
        if similarity < min_similarity:
            rejection_reasons.append(
                f"Similarity {similarity:.4f} below threshold {min_similarity}"
            )
            total_score += 0.0
        else:
            score += 1.0
            total_score += 1.0

        # 2. Validate metadata
        if validate_metadata:
            metadata_valid, metadata_reasons = _validate_chunk_metadata(chunk)
            if not metadata_valid:
                rejection_reasons.extend(metadata_reasons)
            else:
                score += 0.3

        # 3. Validate trust level
        if validate_trust:
            trust_valid, trust_reasons = _validate_trust(chunk)
            if not trust_valid:
                rejection_reasons.extend(trust_reasons)
            else:
                score += 0.2

        # 4. Check for incomplete chunks
        if _is_chunk_incomplete(chunk):
            rejection_reasons.append("Chunk is incomplete (missing document text)")
            score *= 0.5  # Heavy penalty

        # 5. Check document version obsolescence
        if _check_version_obsolete(chunk):
            rejection_reasons.append("Document version is obsolete")
            score *= 0.7  # Heavy penalty

        # Add weighted score
        if rejection_reasons:
            # Rejected chunk
            chunk["validation_status"] = "rejected"
            chunk["validation_reasons"] = rejection_reasons
            rejected_chunks.append(chunk)
        else:
            # Valid chunk
            chunk["validation_status"] = "valid"
            chunk["validation_reasons"] = []
            valid_chunks.append(chunk)
            total_score += score

    # Compute overall confidence based on valid chunks ratio
    total = len(chunks) if chunks else 1
    valid_ratio = len(valid_chunks) / total
    overall_confidence = valid_ratio * (total_score / (total * 2.0))

    return valid_chunks, rejected_chunks, overall_confidence


def _validate_chunk_metadata(chunk: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate that chunk has required metadata fields."""
    metadata = chunk.get("metadata", {})
    missing: List[str] = []

    # Check required fields from config
    required_fields = ["source", "category", "version", "last_updated"]
    for field in required_fields:
        if field not in metadata or not metadata[field]:
            missing.append(field)

    # Check tags exist and are non-empty
    if "tags" not in metadata or not metadata["tags"]:
        missing.append("tags")

    return len(missing) == 0, [f"missing {m}" for m in missing]


def _validate_trust(chunk: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate that chunk has acceptable trust level."""
    metadata = chunk.get("metadata", {})
    trust_level = metadata.get("trust_level", "medium")

    valid_levels = ("high", "medium", "low")
    if trust_level not in valid_levels:
        return False, [f"invalid trust level: {trust_level}"]

    # Even "low" trust is acceptable; we just validate it's set
    return True, []


def _is_chunk_incomplete(chunk: Dict[str, Any]) -> bool:
    """Check if a chunk is incomplete (missing essential content)."""
    # Check both "document" and "content" keys for compatibility
    document = chunk.get("document", chunk.get("content", ""))
    if not document or document.strip() == "":
        return True

    # Check if document has minimum content
    if len(document) < 20:
        return True

    # Check metadata has source
    metadata = chunk.get("metadata", {})
    if not metadata.get("source"):
        return True

    return False


def _check_version_obsolete(chunk: Dict[str, Any]) -> bool:
    """Check if the document version is obsolete."""
    metadata = chunk.get("metadata", {})
    version = metadata.get("version", "1.0")

    # Simple version check: if version is "1.0" or higher, consider current
    # If version is less than "1.0", consider obsolete
    if not version:
        return True  # No version considered potentially obsolete

    # Parse version number
    try:
        version_num = float(version.split("-")[0])  # Handle versions like "1.0", "2.1"
        # Version "1.0" or higher is considered current (not obsolete)
        # Return True if obsolete (version < 1.0), False if acceptable
        return version_num < 1.0
    except (ValueError, IndexError):
        return True  # Can't determine, assume potentially obsolete
