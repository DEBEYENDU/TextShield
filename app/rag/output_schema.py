"""Output schema: return structured object from the retrieval pipeline.

Returns a structured object similar to:
{
  "queries": [],
  "retrieved_documents": [],
  "ranked_chunks": [],
  "supporting_examples": [],
  "counter_examples": [],
  "references": [],
  "retrieval_confidence": 0.93,
  "coverage_score": 0.91,
  "context": "..."
}
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional

from app.rag.context_builder import build_context
from app.rag.evidence_validator import validate_evidence
from app.rag.duplicate_removal import remove_duplicates


class RetrievalOutput:
    """Structured output object from the RAG retrieval pipeline."""

    def __init__(
        self,
        query: Optional[str] = None,
        queries: Optional[List[str]] = None,
        chunks: Optional[List[Dict[str, Any]]] = None,
        retrieved_documents: Optional[List[Dict[str, Any]]] = None,
        total_chunks: Optional[int] = None,
        confidence_score: Optional[float] = None,
        retrieval_confidence: Optional[float] = None,
        evidence_chain: Optional[List[Dict[str, Any]]] = None,
        trust_level: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ranked_chunks: Optional[List[Dict[str, Any]]] = None,
        supporting_examples: Optional[List[Dict[str, Any]]] = None,
        counter_examples: Optional[List[Dict[str, Any]]] = None,
        references: Optional[List[Dict[str, Any]]] = None,
        coverage_score: Optional[float] = None,
        context: Optional[str] = None,
    ):
        self.queries = queries or [query] if query else []
        self.query = query
        self.retrieved_documents = retrieved_documents or []
        self.total_chunks = total_chunks or (len(chunks) if chunks else 0)
        self.chunks = chunks or []
        self.confidence_score = confidence_score
        self.retrieval_confidence = retrieval_confidence
        self.evidence_chain = evidence_chain or []
        self.trust_level = trust_level
        self.metadata = metadata or {}
        self.ranked_chunks = ranked_chunks or []
        self.supporting_examples = supporting_examples or []
        self.counter_examples = counter_examples or []
        self.references = references or []
        self.coverage_score = coverage_score
        self.context = context
        self.context = context

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "queries": self.queries,
            "retrieved_documents": self.retrieved_documents,
            "ranked_chunks": self.ranked_chunks,
            "supporting_examples": self.supporting_examples,
            "counter_examples": self.counter_examples,
            "references": self.references,
            "retrieval_confidence": self.retrieval_confidence,
            "coverage_score": self.coverage_score,
            "context": self.context,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        import json

        return json.dumps(self.to_dict(), indent=2)


def build_retrieval_output(
    semantic_features,
    top_k: int = 5,
    max_token_limit: int = 2000,
    include_context: bool = True,
    include_examples: bool = True,
    include_counter_examples: bool = True,
) -> RetrievalOutput:
    """Build the complete retrieval output object.

    This is the main entry point that orchestrates the entire retrieval pipeline:
    1. Build queries from semantic features
    2. Multi-query retrieval
    3. Hybrid retrieval with metadata filtering
    4. Re-ranking
    5. Duplicate removal
    6. Evidence validation
    7. Context construction
    8. Output schema assembly
    """
    # Step 1: Build queries
    from app.rag.query_builder import build_queries_from_semantic

    query_result = build_queries_from_semantic(semantic_features)

    # Step 2: Multi-query retrieval
    from app.rag.multi_query_retrieval import retrieve_multi_query

    multi_result = retrieve_multi_query(semantic_features, top_k=top_k * 2)

    # Step 3: Hybrid retrieval
    from app.rag.hybrid_retrieval import retrieve_hybrid

    hybrid_result = retrieve_hybrid(
        semantic_features,
        top_k=top_k * 2,
        category_filter=None,
        tag_filter=None,
        language_filter=None,
        trust_filter=None,
    )

    # Combine results from both approaches
    all_retrieved = multi_result.get("retrieved_documents", []) + hybrid_result.get(
        "retrieved_documents", []
    )

    # Step 4: Remove duplicates
    deduped_chunks, dup_removed, kept = remove_duplicates(all_retrieved)

    # Step 5: Validate evidence
    valid_chunks, rejected_chunks, confidence = validate_evidence(
        deduped_chunks, semantic_features
    )

    # Step 6: Rerank chunks
    from app.rag.reranker import rerank_chunks

    ranked_chunks = rerank_chunks(valid_chunks, semantic_features, top_k=top_k)

    # Step 7: Build context (if requested)
    context_str = ""
    if include_context:
        context_build_result = build_context(
            ranked_chunks,
            semantic_features,
            include_behavioral=True,
            include_examples=include_examples,
            include_counter_examples=include_counter_examples,
            max_chunks=min(top_k, 5),
            max_token_limit=max_token_limit,
        )
        context_str = context_build_result.get("relevant_knowledge", "")
        # Also include behavioral and manipulation explanations
        context_parts = []
        if context_build_result.get("behavioral_explanations"):
            for_beh = context_build_result["behavioral_explanations"]
            for_beh_str = " ".join([_get_beh_descr(b) for b in for_beh])
            context_parts.append(for_beh_str)
        if context_build_result.get("manipulation_explanations"):
            for_man = context_build_result["manipulation_explanations"]
            for_man_str = " ".join([_get_man_descr(m) for m in for_man])
            context_parts.append(for_man_str)
        context_str = (
            " | ".join([context_str] + context_parts)
            if context_str
            else " | ".join(context_parts)
        )

    # Step 8: Extract supporting examples
    supporting_examples = _extract_output_examples(ranked_chunks, include_examples)

    # Step 9: Extract counter-examples
    counter_examples = _extract_output_counter_examples(
        ranked_chunks, semantic_features
    )

    # Step 10: Extract references
    references = _extract_output_references(ranked_chunks)

    # Step 11: Compute coverage score
    # Coverage: how many detected topics are covered by retrieved chunks
    coverage_score = _compute_coverage_score(ranked_chunks, semantic_features)

    # Step 12: Final output object
    output = RetrievalOutput(
        queries=[
            query_result.primary.query,
            query_result.intent.query,
            query_result.behavior.query,
            query_result.entity.query,
            query_result.context.query,
        ],
        retrieved_documents=deduped_chunks,
        ranked_chunks=ranked_chunks,
        supporting_examples=supporting_examples,
        counter_examples=counter_examples,
        references=references,
        retrieval_confidence=round(confidence, 4) if confidence else 0.0,
        coverage_score=round(coverage_score, 4),
        context=context_str if context_str else None,
    )

    return output


def _extract_output_examples(
    chunks: List[Dict[str, Any]], include: bool
) -> List[Dict[str, Any]]:
    """Extract supporting examples from ranked chunks."""
    if not include:
        return []

    examples: List[Dict[str, Any]] = []
    for chunk in chunks:
        if chunk.get("is_example", False):
            examples.append(
                {
                    "message": (
                        chunk.get("document", "")[:200] if chunk.get("document") else ""
                    ),
                    "category": chunk.get("category", ""),
                    "source": chunk.get("source", ""),
                    "relevance": chunk.get("score", 0.0),
                }
            )
    return examples


def _extract_output_counter_examples(
    chunks: List[Dict[str, Any]], semantic_features
) -> List[Dict[str, Any]]:
    """Extract counter-examples from ranked chunks and semantic features."""
    counter: List[Dict[str, Any]] = []

    for chunk in chunks:
        category = chunk.get("category", "")
        # Add legitimate communication as counter-example
        if category in {"legitimate", "safety_guidelines"}:
            counter.append(
                {
                    "message": (
                        chunk.get("document", "")[:200] if chunk.get("document") else ""
                    ),
                    "type": "legitimate_communication",
                    "source": chunk.get("source", ""),
                }
            )

    # Also add from semantic features if available
    if (
        semantic_features
        and hasattr(semantic_features, "intent")
        and semantic_features.intent
    ):
        counter.append(
            {
                "message": f"Legitimate communication with {semantic_features.intent} intent",
                "type": "intent_based_counter",
                "source": "semantic_features",
            }
        )

    return counter


def _extract_output_references(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract references from ranked chunks."""
    references: List[Dict[str, Any]] = []
    for chunk in chunks:
        metadata = chunk.get("metadata", {})
        references.append(
            {
                "source": metadata.get("source", "unknown"),
                "version": metadata.get("version", "1.0"),
                "category": metadata.get("category", "general"),
                "trust_level": metadata.get("trust_level", "medium"),
            }
        )
    # Deduplicate by source
    seen: Set[str] = set()
    deduped: List[Dict[str, Any]] = []
    for ref in references:
        source_key = ref.get("source", "")
        if source_key not in seen:
            seen.add(source_key)
            deduped.append(ref)
    return deduped


def _get_beh_descr(beh: Dict[str, Any]) -> str:
    """Get behavioral description for context output."""
    return f"Behavior: {beh.get('pattern', '')}" if beh else ""


def _get_man_descr(man: Dict[str, Any]) -> str:
    """Get manipulation description for context output."""
    techniques = man.get("techniques", [])
    return f"Manipulation: {', '.join(techniques)}" if techniques else ""


def _compute_coverage_score(
    ranked_chunks: List[Dict[str, Any]],
    semantic_features: Dict[str, Any],
) -> float:
    """Compute coverage score: how many detected topics are covered by retrieved chunks.

    Args:
        ranked_chunks: Ranked list of retrieved chunks.
        semantic_features: Features from the semantic engine containing detected topics.

    Returns:
        Coverage score between 0.0 and 1.0.
    """
    detected_topics = set(semantic_features.get("topic_names", []))
    detected_entities = set(semantic_features.get("entities", []))

    covered_topics = set()
    covered_entities = set()

    for chunk in ranked_chunks:
        chunk_metadata = chunk.get("metadata", {})
        chunk_topics = chunk_metadata.get("topic_names", []) or []
        chunk_entities = chunk_metadata.get("entities", []) or []

        covered_topics.update(chunk_topics)
        covered_entities.update(chunk_entities)

    topic_coverage = len(covered_topics & detected_topics) / max(
        len(detected_topics), 1
    )
    entity_coverage = len(covered_entities & detected_entities) / max(
        len(detected_entities), 1
    )

    return (topic_coverage + entity_coverage) / 2
