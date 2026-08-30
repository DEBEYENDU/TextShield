"""Multi-query retrieval: support primary, intent, behavior, entity, and context queries.

Retrieves results independently for each query type, then merges intelligently.
"""

from __future__ import annotations

from typing import List, Dict, Set, Tuple, Any

from app.rag.query_builder import build_queries_from_semantic, QueryBuilderResult
from app.rag.vector_store import open_vector_store


def retrieve_multi_query(
    semantic_features,
    top_k: int = 5,
    use_hybrid: bool = True,
) -> Dict[str, Any]:
    """Retrieve documents using multiple query types independently.

    Args:
        semantic_features: Features from the semantic engine used to build queries.
        top_k: Number of results to retrieve per query type.
        use_hybrid: Whether to use hybrid retrieval (vector + metadata filtering).

    Returns:
        Dict mapping query type to list of retrieved documents with scores.
    """
    # Build all query types
    query_result: QueryBuilderResult = build_queries_from_semantic(semantic_features)

    # Retrieve results for each query type
    retrievals: Dict[str, List[Dict[str, Any]]] = {}

    # Primary query retrieval
    primary_hits = _retrieve_single_query(query_result.primary.query, top_k, "primary")
    retrievals["primary"] = primary_hits

    # Intent query retrieval
    intent_hits = _retrieve_single_query(query_result.intent.query, top_k, "intent")
    retrievals["intent"] = intent_hits

    # Behavior query retrieval
    behavior_hits = _retrieve_single_query(
        query_result.behavior.query, top_k, "behavior"
    )
    retrievals["behavior"] = behavior_hits

    # Entity query retrieval
    entity_hits = _retrieve_single_query(query_result.entity.query, top_k, "entity")
    retrievals["entity"] = entity_hits

    # Context query retrieval
    context_hits = _retrieve_single_query(query_result.context.query, top_k, "context")
    retrievals["context"] = context_hits

    # Merge results intelligently
    merged = _merge_retrieval_results(retrievals, top_k)

    return {
        "queries": {
            "primary": query_result.primary.query,
            "intent": query_result.intent.query,
            "behavior": query_result.behavior.query,
            "entity": query_result.entity.query,
            "context": query_result.context.query,
        },
        "retrieved_documents": merged,
        "per_type": retrievals,
    }


def _retrieve_single_query(
    query: str, top_k: int, query_type: str
) -> List[Dict[str, Any]]:
    """Retrieve documents for a single query using the vector store."""
    try:
        store = open_vector_store()
        embedding = store.provider.embed_one(query)
        hits = store.query(embedding, top_k=top_k)

        results = []
        for hit in hits:
            metadata = hit.get("metadata", {})
            results.append(
                {
                    "document": hit.get("document", ""),
                    "source": metadata.get("source", "unknown"),
                    "category": metadata.get("category", "general"),
                    "chunk_id": hit.get("id", ""),
                    "score": float(hit.get("score", 0.0)),
                    "query_type": query_type,
                    "is_example": bool(metadata.get("is_example", False)),
                }
            )
        return results
    except Exception as e:
        # Log and return empty results rather than failing
        return []


def _merge_retrieval_results(
    retrievals: Dict[str, List[Dict[str, Any]]], top_k: int
) -> List[Dict[str, Any]]:
    """Merge results from multiple query types, deduplicating and ranking by quality.

    Strategy:
    1. Collect all results from all query types
    2. Group by source document
    3. For each document, keep the highest score across query types
    4. Sort by score (highest first)
    5. Return top_k results
    """
    # Track documents by source, keeping best score and query types
    document_scores: Dict[str, Dict[str, Any]] = {}

    for query_type, hits in retrievals.items():
        for hit in hits:
            source = hit.get("source", "unknown")
            score = hit.get("score", 0.0)

            if source not in document_scores:
                document_scores[source] = {
                    "score": score,
                    "query_types": [query_type],
                    "document": hit.get("document", ""),
                    "category": hit.get("category", "general"),
                    "is_example": hit.get("is_example", False),
                }
            else:
                # Update if this score is higher
                if score > document_scores[source]["score"]:
                    document_scores[source]["score"] = score
                # Add query type if not already present
                if query_type not in document_scores[source]["query_types"]:
                    document_scores[source]["query_types"].append(query_type)

    # Sort by score descending and return top_k
    sorted_docs = sorted(
        document_scores.values(), key=lambda x: x["score"], reverse=True
    )

    return sorted_docs[:top_k]
