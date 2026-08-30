"""RAG system: Retrieval-Augmented Generation pipeline.

Modular, deterministic, and configurable retrieval pipeline for cybersecurity
knowledge. Supports multi-query retrieval, hybrid search, re-ranking, duplicate
removal, evidence validation, context construction, and confidence estimation.

DO NOT connect to LLM for final reasoning - this pipeline returns evidence only.
"""

from __future__ import annotations

from app.rag.query_builder import build_queries_from_semantic
from app.rag.multi_query_retrieval import retrieve_multi_query
from app.rag.hybrid_retrieval import retrieve_hybrid
from app.rag.reranker import rerank_chunks
from app.rag.duplicate_removal import remove_duplicates
from app.rag.evidence_validator import validate_evidence
from app.rag.context_builder import build_context
from app.rag.output_schema import RetrievalOutput, build_retrieval_output
from app.rag.retrieval_confidence import estimate_confidence
from app.rag.config import RagConfig, get_config
from app.rag.retrieval_pipeline import RetrievalPipeline, run_pipeline

__all__ = [
    "RetrievalPipeline",
    "RetrievalOutput",
    "build_retrieval_output",
    "run_pipeline",
    "estimate_confidence",
    "get_config",
    "RagConfig",
    "build_queries_from_semantic",
    "retrieve_multi_query",
    "retrieve_hybrid",
    "rerank_chunks",
    "remove_duplicates",
    "validate_evidence",
    "build_context",
]
