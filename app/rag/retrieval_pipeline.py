"""Main retrieval pipeline: orchestrates the complete RAG retrieval process.

Connects the Semantic Engine, Intent Engine, Knowledge Loader, and Vector Store
without connecting to the LLM. Responsible for retrieving, ranking, validating,
and assembling evidence for later reasoning.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional, Tuple

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


class RetrievalPipeline:
    """Main pipeline for RAG retrieval, validation, and context construction."""

    def __init__(self, semantic_features=None, knowledge_loader=None):
        self.semantic_features = semantic_features or {}
        self.knowledge_loader = knowledge_loader
        self.config = get_config()
        self._cache: Dict[str, Any] = {}

    def retrieve(self, text: str, top_k: Optional[int] = None) -> RetrievalOutput:
        """Execute the complete retrieval pipeline for a given message text.

        Args:
            text: The input message/text to retrieve knowledge for.
            top_k: Number of final ranked chunks to return (uses config default if None).

        Returns:
            RetrievalOutput with all pipeline results.
        """
        if top_k is None:
            top_k = self.config.RAG_TOP_K

        # Step 1: If semantic features not provided, build minimal ones
        if not self.semantic_features:
            self.semantic_features = self._build_semantic_features(text)

        # Step 2: Build queries from semantic features
        query_result = build_queries_from_semantic(self.semantic_features)

        # Step 3: Multi-query retrieval
        multi_result = retrieve_multi_query(self.semantic_features, top_k=top_k)

        # Step 4: Hybrid retrieval (vector + metadata filtering)
        hybrid_result = retrieve_hybrid(
            self.semantic_features,
            top_k=top_k,
            category_filter=None,
            tag_filter=None,
            language_filter=None,
            trust_filter=None,
        )

        # Step 5: Combine results from multi and hybrid retrieval
        all_retrieved = multi_result.get("retrieved_documents", []) + hybrid_result.get(
            "retrieved_documents", []
        )

        # Step 6: Remove duplicates
        deduped_chunks, dup_removed, kept = remove_duplicates(all_retrieved)

        # Step 7: Validate evidence
        valid_chunks, rejected_chunks, confidence = validate_evidence(
            deduped_chunks, self.semantic_features
        )

        # Step 8: Rerank chunks using multiple relevance factors
        ranked_chunks = rerank_chunks(valid_chunks, self.semantic_features, top_k=top_k)

        # Step 9: Build context for future LLM
        context_build_result = build_context(
            ranked_chunks,
            self.semantic_features,
            include_behavioral=self.config.RAG_INCLUDE_BEHAVIORAL,
            include_examples=self.config.RAG_INCLUDE_EXAMPLES,
            include_counter_examples=self.config.RAG_INCLUDE_COUNTER_EXAMPLES,
            max_chunks=self.config.RAG_MAX_CONTEXT_CHUNKS,
            max_token_limit=self.config.RAG_MAX_TOKEN_LIMIT,
        )

        # Step 10: Estimate retrieval confidence
        output = build_retrieval_output(
            self.semantic_features,
            top_k=top_k,
            max_token_limit=self.config.RAG_MAX_TOKEN_LIMIT,
            include_context=True,
            include_examples=self.config.RAG_INCLUDE_EXAMPLES,
            include_counter_examples=self.config.RAG_INCLUDE_COUNTER_EXAMPLES,
        )

        # Step 10.5: Add confidence estimate
        output.retrieval_confidence = confidence

        # Store pipeline state for debugging/analysis
        self._cache = {
            "query": text,
            "chunks_before_dedup": len(all_retrieved),
            "chunks_after_dedup": kept,
            "chunks_valid": len(valid_chunks),
            "chunks_rejected": len(rejected_chunks),
            "similarity_confidence": confidence,
        }

        return output

    def _build_semantic_features(self, text: str) -> Dict[str, Any]:
        """Build minimal semantic features from input text.

        In a full implementation, this would connect to the Semantic Engine.
        For now, extracts basic keywords, topics, and intent patterns.
        """
        import re

        # Basic keyword extraction
        words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())

        # Remove common stop words
        stop_words = {
            "the",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "a",
            "an",
            "was",
            "were",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "you",
            "your",
            "i",
            "he",
            "she",
            "it",
            "we",
            "they",
            "them",
            "this",
            "that",
            "what",
            "which",
            "who",
            "when",
            "where",
            "why",
        }
        filtered_words = [w for w in words if w not in stop_words]

        # Build semantic features dict
        semantic_features: Dict[str, Any] = {
            "keywords": filtered_words[:20],  # Top 20 keywords
            "topic_names": self._extract_topics(filtered_words),
            "entities": self._extract_entities(text),
            "language": "en-US",
        }

        # Try to detect intent-related keywords
        intent_keywords = [
            "urgent",
            "immediately",
            "warning",
            "alert",
            "verify",
            "confirm",
            "update",
            "password",
            "OTP",
            "code",
            "payment",
            "transfer",
        ]
        detected_intent = None
        for kw in filtered_words:
            if kw in intent_keywords:
                detected_intent = kw
                break
        if detected_intent:
            semantic_features["intent"] = detected_intent

        # Detect behavioral patterns
        behavior_patterns = []
        urgency_keywords = ["urgent", "immediately", "now", "expire", "expires"]
        if any(kw in filtered_words for kw in urgency_keywords):
            behavior_patterns.append("urgency")
        if any(kw in filtered_words for kw in ["guarantee", "guaranteed", "risk-free"]):
            behavior_patterns.append("reward")

        if behavior_patterns:
            semantic_features["behavioral_patterns"] = behavior_patterns

        return semantic_features

    @staticmethod
    def _extract_topics(words: List[str]) -> List[str]:
        """Extract topic labels from keyword list."""
        topic_keywords = {
            "phishing": ["verify", "account", "login", "password", "credential"],
            "scam": ["payment", "transfer", "fee", "refund", "winnings"],
            "fraud": ["guarantee", "guaranteed", "risk-free", "investment", "return"],
            "smishing": ["sms", "text", "message", "phone", "call"],
            "malware": ["virus", "malware", "infected", "security", "warning"],
        }

        topics: List[str] = []
        for topic, keywords in topic_keywords.items():
            if any(kw in words for kw in keywords):
                topics.append(topic)

        return topics if topics else ["general"]

    @staticmethod
    def _extract_entities(text: str) -> List[str]:
        """Extract simple entities from text (e.g., bank names, amounts)."""
        import re

        entities: Set[str] = set()

        # Bank/financial entity patterns
        bank_patterns = [
            r"\b\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars|USD|rupees|Rs)\b",
            r"\b(?:bank|banking|financial|account)\b",
        ]
        for pattern in bank_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.update(matches)

        # Shortened URL / domain patterns
        url_patterns = re.findall(
            r"https?://[^\s]+|[a-zA-Z0-9]+\.[a-zA-Z]{2,}[/]?", text
        )
        entities.update(url_patterns[:5])  # Limit to 5 URL-related entities

        return list(entities)[:10]


def run_pipeline(text: str, top_k: Optional[int] = None) -> Dict[str, Any]:
    """Convenience function to run the full retrieval pipeline.

    Args:
        text: The input message/text to analyze.
        top_k: Number of final ranked chunks (uses config default if None).

    Returns:
        Dict with pipeline results including all output schema fields.
    """
    pipeline = RetrievalPipeline(semantic_features={})
    output = pipeline.retrieve(text, top_k=top_k)

    return output.to_dict()
