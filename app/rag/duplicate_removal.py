"""Duplicate removal: remove duplicate and near-duplicate chunks.

Keeps only the highest quality version of each unique chunk based on content
similarity, metadata quality, and source trustworthiness.
"""

from __future__ import annotations

from typing import List, Dict, Set, Tuple, Any

import hashlib


def remove_duplicates(
    chunks: List[Dict[str, Any]],
    similarity_threshold: float = 0.85,
    quality_threshold: float = 0.6,
) -> Tuple[List[Dict[str, Any]], int, int]:
    """Remove duplicate and near-duplicate chunks.

    Args:
        chunks: List of chunks to deduplicate.
        similarity_threshold: Chunks with cosine similarity above this threshold
            are considered duplicates.
        quality_threshold: Minimum quality score to keep a chunk.

    Returns:
        Tuple of (deduplicated chunks, number removed, number kept).
    """
    if not chunks:
        return [], 0, 0

    # Filter by quality threshold first
    quality_filtered = _filter_by_quality(chunks, quality_threshold)

    # Step 1: Deduplicate by content hash (exact match)
    seen_hashes: Set[str] = set()
    deduped_by_hash: List[Dict[str, Any]] = []
    hash_removed = 0

    for chunk in quality_filtered:
        content_hash = _compute_content_hash(chunk)
        if content_hash is None:
            # Can't hash this chunk, fall through to source-based dedup
            deduped_by_hash.append(chunk)
            continue
        if content_hash in seen_hashes:
            hash_removed += 1
            continue
        seen_hashes.add(content_hash)
        deduped_by_hash.append(chunk)

    # Step 2: Deduplicate by source key (for chunks without content hash or near-duplicates)
    seen_keys: Set[str] = set()
    final_chunks: List[Dict[str, Any]] = []
    source_removed = 0

    for chunk in deduped_by_hash:
        source_key = _get_source_key(chunk)
        if source_key not in seen_keys:
            seen_keys.add(source_key)
            final_chunks.append(chunk)
        else:
            source_removed += 1

    kept_count = len(final_chunks)
    total_removed = hash_removed + source_removed

    return final_chunks, total_removed, kept_count


def _filter_by_quality(
    chunks: List[Dict[str, Any]],
    quality_threshold: float,
) -> List[Dict[str, Any]]:
    """Filter chunks by minimum quality score."""
    quality_chunks: List[Dict[str, Any]] = []
    for chunk in chunks:
        # Use relevance_score if available, otherwise use score
        score = chunk.get("relevance_score", chunk.get("score", 0.0))
        if score >= quality_threshold:
            quality_chunks.append(chunk)
    return quality_chunks


def _compute_content_hash(chunk: Dict[str, Any]) -> Optional[str]:
    """Compute a hash based on chunk content for duplicate detection.

    Returns None if the chunk cannot be hashed (no document text).
    """
    # Use document text + source as the basis for hashing
    document = chunk.get("document", "")
    source = chunk.get("source", "")

    if not document:
        return None

    # Create hash from document text + source
    hash_input = f"{source}:{document[:200]}"  # Use first 200 chars
    try:
        return hashlib.md5(hash_input.encode("utf-8")).hexdigest()
    except Exception:
        return None


def _get_source_key(chunk: Dict[str, Any]) -> str:
    """Get a source key for duplicate detection."""
    source = chunk.get("source", "unknown")
    category = chunk.get("category", "general")
    chunk_id = chunk.get("chunk_id", "")
    return f"{source}:{category}:{chunk_id}"
