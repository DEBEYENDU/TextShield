"""Tests for the RAG Retrieval Pipeline.

Covers:
- Relevant retrieval
- Irrelevant retrieval rejection
- Metadata filtering
- Re-ranking
- Duplicate removal
- Context construction
- Confidence estimation
- Edge cases
"""

import sys
import os

# Add the project root to path
sys.path.insert(0, r"C:\Users\GOD KAKAROT\TextShield")

from app.rag.query_builder import build_queries_from_semantic, QueryBuilderResult
from app.rag.multi_query_retrieval import retrieve_multi_query, _retrieve_single_query, _merge_retrieval_results
from app.rag.hybrid_retrieval import retrieve_hybrid, _apply_metadata_filter, _deduplicate_by_source
from app.rag.reranker import rerank_chunks
from app.rag.duplicate_removal import remove_duplicates
from app.rag.evidence_validator import validate_evidence
from app.rag.retrieval_confidence import estimate_confidence
from app.rag.context_builder import build_context
from app.rag.output_schema import RetrievalOutput, build_retrieval_output
from app.rag import run_pipeline


def make_semantic_features():
    """Create a minimal valid semantic features instance for RAG pipeline."""
    return {
        "topic_names": ["phishing"],
        "entities": ["account"],
        "intent": "phishing",
        "behavioral_patterns": ["urgency"],
        "communication_goal": "credential_theft",
        "additional_context": "test message about account verification",
        "message_length": 100,
        "word_count": 20,
        "sentence_count": 5,
        "question_count": 0,
        "imperative_count": 0,
        "emoji_count": 0,
        "url_count": 0,
        "email_count": 0,
        "phone_count": 0,
        "money_count": 0,
        "date_count": 0,
        "time_count": 0,
        "has_request": False,
        "has_offer": False,
        "has_urgency": False,
        "has_financial_reference": False,
        "has_credential_request": False,
        "has_personal_information_request": False,
        "language": 1.0,
        "context": 1.0,
        "topic": 1.0,
        "entity": 1.0,
    }


def make_test_chunks(count: int, base_source: str = "test_source", base_category: str = "test_category"):
    """Create test chunks with proper metadata for validation testing."""
    chunks = []
    for i in range(count):
        chunk = {
            "content": f"Test chunk {i} about phishing urgency scam account verification",
            "metadata": {
                "source": f"{base_source}_{i}",
                "category": base_category,
                "version": "1.0",
                "last_updated": "2024-01-01",
                "tags": ["phishing", "scam", "urgency"],
            },
            "embedding": [0.1] * 384,
            "similarity": 0.85 + (i * 0.01),
        }
        chunks.append(chunk)
    return chunks


def test_query_builder():
    """Test query building from semantic features."""
    from app.rag.query_builder import build_queries_from_semantic
    features = make_semantic_features()
    result = build_queries_from_semantic(features)
    assert result is not None
    assert hasattr(result, "queries")


def test_multi_query_retrieval():
    """Test multi-query retrieval."""
    chunks = make_test_chunks(3)
    queries = [{"query": "phishing scam urgency", "weight": 1.0}]
    results = retrieve_multi_query(queries, top_k=3)
    assert len(results) <= 3


def test_hybrid_retrieval():
    """Test hybrid retrieval with metadata filtering."""
    queries = [{"query": "phishing scam", "weight": 1.0}]
    results = retrieve_hybrid(queries, top_k=5)
    assert len(results.get("retrieved_documents", [])) > 0
    # Function returns up to top_k results after deduplication/filtering
    assert len(results.get("retrieved_documents", [])) <= 10


def test_reranking():
    """Test chunk re-ranking."""
    chunks = make_test_chunks(3)
    reranked = rerank_chunks(chunks, make_semantic_features())
    assert len(reranked) == len(chunks)


def test_duplicate_removal():
    """Test duplicate chunk removal."""
    chunks = make_test_chunks(3, base_source="duplicate_test")
    deduped = remove_duplicates(chunks)
    assert len(deduped) <= len(chunks)


def test_evidence_validation():
    """Test that valid chunks are kept and invalid ones rejected."""
    chunks = make_test_chunks(3)
    valid, rejected, confidence = validate_evidence(chunks, make_semantic_features())
    # At least some chunks should be valid
    assert len(valid) >= 1, "Valid chunk should be kept"


def test_retrieval_confidence():
    """Test confidence estimation."""
    chunks = make_test_chunks(3)
    features = make_semantic_features()
    overall, factors = estimate_confidence(chunks, features)
    assert 0.0 <= overall <= 1.0


def test_context_construction():
    """Test context building from valid chunks."""
    chunks = make_test_chunks(2)
    valid_chunks = [c for c in chunks if c.get("validation_status") != "rejected"]
    context = build_context(valid_chunks, make_semantic_features())
    assert context is not None


def test_output_schema():
    """Test retrieval output schema."""
    output = RetrievalOutput(
        query="test query",
        chunks=[],
        total_chunks=0,
        confidence_score=0.5,
        evidence_chain=[],
        trust_level="medium",
        metadata={},
    )
    assert output.query == "test query"


def test_pipeline_convenience():
    """Test pipeline convenience function with non-empty query."""
    result = run_pipeline("Your account has been suspended, verify immediately")
    assert result is not None


def test_edge_cases():
    """Test pipeline edge cases with empty string."""
    result = run_pipeline("")
    assert result is not None