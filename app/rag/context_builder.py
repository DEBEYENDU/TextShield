"""Context construction: build the final context for the future LLM.

Builds comprehensive context from validated, reranked, and deduplicated chunks,
including relevant knowledge, behavioral explanations, manipulation explanations,
examples, counter-examples, references, and metadata.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional, Set

from app.rag.evidence_validator import validate_evidence
from app.rag.duplicate_removal import remove_duplicates


def build_context(
    retrieved_chunks: List[Dict[str, Any]],
    semantic_features,
    include_behavioral: bool = True,
    include_examples: bool = True,
    include_counter_examples: bool = True,
    max_chunks: int = 5,
    max_token_limit: int = 2000,
) -> Dict[str, Any]:
    """Build the final context for the future LLM from retrieved chunks.

    Args:
        retrieved_chunks: List of validated, reranked chunks from the retrieval pipeline.
        semantic_features: Features from the semantic engine for context enrichment.
        include_behavioral: Whether to include behavioral explanations.
        include_examples: Whether to include example messages.
        include_counter_examples: Whether to include counter-examples.
        max_chunks: Maximum number of chunks to include in context.
        max_token_limit: Maximum estimated token limit for the context.

    Returns:
        Dict with constructed context including all required elements.
    """
    # Step 1: Validate evidence
    valid_chunks, rejected_chunks, confidence = validate_evidence(
        retrieved_chunks, semantic_features
    )

    # Step 2: Remove duplicates
    deduped_chunks, dup_removed, kept = remove_duplicates(valid_chunks)

    # Step 3: Limit to max_chunks
    final_chunks = deduped_chunks[:max_chunks]

    # Step 4: Build context components
    context_parts: Dict[str, Any] = {
        "relevant_knowledge": _extract_knowledge(final_chunks),
        "behavioral_explanations": (
            _extract_behavioral_explanations(final_chunks, semantic_features)
            if include_behavioral
            else []
        ),
        "manipulation_explanations": _extract_manipulation_explanations(
            final_chunks, semantic_features
        ),
        "examples": _extract_examples(final_chunks) if include_examples else [],
        "counter_examples": (
            _extract_counter_examples(final_chunks, semantic_features)
            if include_counter_examples
            else []
        ),
        "references": _extract_references(final_chunks),
        "metadata": _extract_metadata(final_chunks),
    }

    # Step 5: Estimate token count and compress if needed
    token_estimate = _estimate_token_count(context_parts)
    if token_estimate > max_token_limit and max_chunks > 1:
        context_parts = _compress_context(
            context_parts, max_chunks - 1, max_token_limit
        )

    # Final token estimate
    context_parts["token_estimate"] = _estimate_token_count(context_parts)

    # Overall confidence
    context_parts["retrieval_confidence"] = confidence

    return context_parts


def _extract_knowledge(chunks: List[Dict[str, Any]]) -> str:
    """Extract relevant knowledge text from chunks."""
    knowledge_parts: List[str] = []
    for chunk in chunks:
        document = chunk.get("document", "")
        if document:
            knowledge_parts.append(document)
    return " ".join(knowledge_parts) if knowledge_parts else ""


def _extract_behavioral_explanations(
    chunks: List[Dict[str, Any]],
    semantic_features,
) -> List[Dict[str, Any]]:
    """Extract behavioral explanations from chunks."""
    explanations: List[Dict[str, Any]] = []
    for chunk in chunks:
        behavioral_patterns = chunk.get("metadata", {}).get("behavioral_patterns", [])
        if behavioral_patterns:
            explanations.append(
                {
                    "pattern": behavioral_patterns[0] if behavioral_patterns else "",
                    "description": _get_behavior_description(behavioral_patterns[0]),
                    "source": chunk.get("source", ""),
                    "category": chunk.get("category", ""),
                }
            )
    return explanations


def _extract_manipulation_explanations(
    chunks: List[Dict[str, Any]],
    semantic_features,
) -> List[Dict[str, Any]]:
    """Extract manipulation technique explanations from chunks."""
    explanations: List[Dict[str, Any]] = []
    for chunk in chunks:
        manipulation_techniques = chunk.get("manipulation_techniques", [])
        if manipulation_techniques:
            explanations.append(
                {
                    "techniques": manipulation_techniques,
                    "description": _get_manipulation_description(
                        manipulation_techniques
                    ),
                    "source": chunk.get("source", ""),
                }
            )
    return explanations


def _extract_examples(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract example messages from chunks."""
    examples: List[Dict[str, Any]] = []
    for chunk in chunks:
        # Check if this is an example chunk (is_example flag)
        if chunk.get("is_example", False):
            examples.append(
                {
                    "message": (
                        chunk.get("document", "")[:200] if chunk.get("document") else ""
                    ),
                    "intent": chunk.get("category", ""),
                    "source": chunk.get("source", ""),
                }
            )
        # Also look for examples in metadata
        metadata_examples = chunk.get("metadata", {}).get("examples", [])
        for ex in metadata_examples:
            examples.append(
                {
                    "message": ex[:200] if isinstance(ex, str) else "",
                    "intent": chunk.get("category", ""),
                    "source": chunk.get("source", ""),
                }
            )
    # Deduplicate by message content
    seen: Set[str] = set()
    deduped: List[Dict[str, Any]] = []
    for ex in examples:
        msg_key = ex.get("message", "")[:100] if ex.get("message") else ""
        if msg_key not in seen:
            seen.add(msg_key)
            deduped.append(ex)
    return deduped


def _extract_counter_examples(
    chunks: List[Dict[str, Any]],
    semantic_features,
) -> List[Dict[str, Any]]:
    """Extract counter-examples (legitimate/communication patterns) from chunks."""
    counter_examples: List[Dict[str, Any]] = []
    for chunk in chunks:
        category = chunk.get("category", "")
        # Add legitimate communication patterns as counter-examples
        if category in {"legitimate", "safety_guidelines"}:
            counter_examples.append(
                {
                    "message": (
                        chunk.get("document", "")[:200] if chunk.get("document") else ""
                    ),
                    "type": "legitimate_communication",
                    "source": chunk.get("source", ""),
                }
            )
        # Also add examples from legitimate categories
        if chunk.get("is_example", False) and category == "examples":
            # Find corresponding legitimate pattern
            counter_examples.append(
                {
                    "message": (
                        chunk.get("document", "")[:200] if chunk.get("document") else ""
                    ),
                    "type": "legitimate_alternative",
                    "source": chunk.get("source", ""),
                }
            )
    return counter_examples


def _extract_references(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract references/citations from chunks."""
    references: List[Dict[str, Any]] = []
    for chunk in chunks:
        metadata = chunk.get("metadata", {})
        source = metadata.get("source", "")
        version = metadata.get("version", "")
        references.append(
            {
                "source": source,
                "version": version,
                "category": metadata.get("category", ""),
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


def _extract_metadata(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract consolidated metadata from chunks."""
    metadata: Dict[str, Any] = {
        "total_chunks": len(chunks),
        "valid_chunks": len(chunks),  # Will be updated after validation
        "categories": set(),
        "trust_levels": set(),
        "sources": set(),
    }

    for chunk in chunks:
        md = chunk.get("metadata", {})
        if md.get("category"):
            metadata["categories"].add(md["category"])
        if md.get("trust_level"):
            metadata["trust_levels"].add(md["trust_level"])
        if md.get("source"):
            metadata["sources"].add(md["source"])

    # Convert sets to lists for JSON serialization
    metadata["categories"] = list(metadata["categories"])
    metadata["trust_levels"] = list(metadata["trust_levels"])
    metadata["sources"] = list(metadata["sources"])

    return metadata


def _estimate_token_count(context: Dict[str, Any]) -> int:
    """Estimate the token count of the context dictionary."""
    import json

    context_json = json.dumps(context, separators=(",", ":"))
    # Rough estimate: 1 character ≈ 0.25 tokens for English text
    return max(1, int(len(context_json) * 0.25))


def _compress_context(
    context: Dict[str, Any], max_chunks: int, max_token_limit: int
) -> Dict[str, Any]:
    """Compress context by reducing chunks and deduplicating content.

    Preserves references and metadata while reducing overall size.
    """
    # Reduce the number of knowledge chunks
    if "relevant_knowledge" in context:
        knowledge = context["relevant_knowledge"]
        # Keep only the most relevant parts
        words = knowledge.split()
        if len(words) > max_token_limit:
            # Keep the first part and add summary note
            keep_words = int(max_token_limit * 0.8)
            context["relevant_knowledge"] = (
                " ".join(words[:keep_words]) + " ... [truncated]"
            )

    # Remove least important example/counter-example entries
    if "examples" in context:
        context["examples"] = context["examples"][: max(1, max_chunks // 2)]
    if "counter_examples" in context:
        context["counter_examples"] = context["counter_examples"][
            : max(1, max_chunks // 2)
        ]

    return context


def _get_behavior_description(pattern: str) -> str:
    """Get human-readable description of a behavioral pattern."""
    descriptions: Dict[str, str] = {
        "urgency": "Creates artificial time pressure to prompt immediate action without proper verification",
        "authority": "Exploits deference to perceived authority figures or institutions",
        "fear": "Exploits anxiety, dread, or panic to prompt immediate action",
        "reward": "Promises benefits or gains to prompt desired actions",
        "curiosity": "Exploits the human desire for new information or resolution of uncertainty",
        "scarcity": "Creates artificial shortage to prompt immediate action",
        "reciprocity": "Exploits the social norm of returning favors or benefits",
        "trust_building": "Establishes false trust over time to lower victim resistance",
        "social_proof": "Exploits the tendency to follow the actions or decisions of others",
        "pressure": "Applies continuous coercion to force compliance",
        "personalization": "Uses personal information to appear legitimate and increase compliance",
    }
    return descriptions.get(pattern, "Behavioral manipulation technique")


def _get_manipulation_description(
    techniques: List[str],
) -> str:
    """Get human-readable description of manipulation techniques."""
    if not techniques:
        return ""

    descriptions: Dict[str, str] = {
        "urgency": "Creates artificial time pressure",
        "authority": "Exploits perceived authority",
        "fear": "Uses threats and intimidation",
        "reward": "Promises benefits or gains",
        "curiosity": "Exploits information gap",
        "scarcity": "Creates artificial shortage",
        "reciprocity": "Exploits social obligation to return favors",
        "trust_building": "Establishes false trust relationship",
        "social_proof": "Uses perceived majority behavior to influence",
        "pressure": "Applies persistent coercion",
        "personalization": "Uses personal details to appear credible",
    }

    relevant = [descriptions.get(t, t) for t in techniques if t in descriptions]
    return " ".join(relevant[:3])  # Top 3 techniques
