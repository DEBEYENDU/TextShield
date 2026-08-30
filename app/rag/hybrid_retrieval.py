"""Hybrid retrieval: combine dense vector search with metadata filtering.

Combines dense vector similarity search with category, tag, language, and trust
level filtering for improved precision and recall.
"""

from __future__ import annotations

from typing import List, Dict, Set, Tuple, Any, Optional

from app.rag.query_builder import build_queries_from_semantic
from app.rag.vector_store import open_vector_store
from app.rag.embeddings import create_embedding_provider


def retrieve_hybrid(
    semantic_features,
    top_k: int = 5,
    category_filter: Optional[List[str]] = None,
    tag_filter: Optional[List[str]] = None,
    language_filter: Optional[str] = None,
    trust_filter: Optional[float] = None,
    use_reranking: bool = True,
) -> Dict[str, Any]:
    """Retrieve documents using hybrid search (vector + metadata filtering).

    Args:
        semantic_features: Features from the semantic engine.
        top_k: Number of final results to return.
        category_filter: Optional list of allowed categories.
        tag_filter: Optional list of required tags.
        language_filter: Optional language code filter (e.g., "en-US").
        trust_filter: Minimum trust level (0.0-1.0, mapped to high/medium/low).
        use_reranking: Whether to apply re-ranking after retrieval.

    Returns:
        Dict with retrieved documents and metadata.
    """
    # Build queries from semantic features
    query_result = build_queries_from_semantic(semantic_features)

    # Start with vector search using the primary query
    store = open_vector_store()
    embedding = create_embedding_provider().embed_one(query_result.primary.query)
    vector_hits = store.query(embedding, top_k=top_k * 2)  # Get more before filtering

    # Apply metadata filtering to vector hits
    filtered_hits = _apply_metadata_filter(
        vector_hits,
        category_filter=category_filter,
        tag_filter=tag_filter,
        language_filter=language_filter,
        trust_filter=trust_filter,
    )

    # If we don't have enough results, supplement with intent-based search
    if len(filtered_hits) < top_k:
        # Build intent query
        intent_query = semantic_features.intent or "scam phishing fraud"
        intent_embedding = create_embedding_provider().embed_one(intent_query)
        intent_hits = store.query(intent_embedding, top_k=top_k)
        intent_filtered = _apply_metadata_filter(
            intent_hits,
            category_filter=category_filter,
            tag_filter=tag_filter,
            language_filter=language_filter,
            trust_filter=trust_filter,
        )
        # Combine results
        all_results = filtered_hits + intent_filtered
    else:
        all_results = filtered_hits

    # Deduplicate by source document
    deduped = _deduplicate_by_source(all_results)

    # Sort by score descending
    deduped.sort(key=lambda x: x.get("score", 0.0), reverse=True)

    # Return top_k results
    final_results = deduped[:top_k]

    # Apply optional re-ranking
    if use_reranking and final_results:
        from app.rag.reranker import rerank_chunks

        final_results = rerank_chunks(
            final_results,
            semantic_features=semantic_features,
            top_k=top_k,
        )

    return {
        "queries": {
            "primary": query_result.primary.query,
        },
        "retrieved_documents": final_results,
        "total_before_filtering": len(vector_hits),
        "after_metadata_filtering": len(filtered_hits),
        "after_deduplication": len(deduped),
        "final_count": len(final_results),
    }


def _apply_metadata_filter(
    hits: List[Dict[str, Any]],
    category_filter: Optional[List[str]],
    tag_filter: Optional[List[str]],
    language_filter: Optional[str],
    trust_filter: Optional[float],
) -> List[Dict[str, Any]]:
    """Apply metadata-based filtering to retrieval hits."""
    filtered = []

    for hit in hits:
        metadata = hit.get("metadata", {})

        # Category filter
        if category_filter:
            category = metadata.get("category", "")
            if category not in category_filter:
                continue

        # Tag filter
        if tag_filter:
            hit_tags = metadata.get("tags", [])
            if not any(tag in hit_tags for tag in tag_filter):
                continue

        # Language filter
        if language_filter:
            hit_language = metadata.get("language", "en-US")
            if hit_language != language_filter:
                continue

        # Trust level filter
        if trust_filter is not None:
            # Map trust_filter (0-1) to trust levels
            # 0.0-0.3 = low, 0.3-0.7 = medium, 0.7-1.0 = high
            trust_score = metadata.get("trust_level", 0.5)
            if trust_score < trust_filter:
                continue

        filtered.append(hit)

    return filtered


def _deduplicate_by_source(hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate chunks, keeping the highest-scoring version."""
    seen: Dict[str, Dict[str, Any]] = {}

    for hit in hits:
        source = hit.get("source", "unknown")
        score = hit.get("score", 0.0)

        if source not in seen:
            seen[source] = hit
        else:
            # Keep the higher-scoring version
            if score > seen[source].get("score", 0.0):
                seen[source] = hit

    return list(seen.values())
