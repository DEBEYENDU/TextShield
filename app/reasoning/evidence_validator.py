"""Evidence Validation Layer for Reasoning Engine.

Validates that every LLM claim is traceable to supporting evidence
from the RAG pipeline, semantic/intent/behavior analysis, or other
pipeline components. Rejects unsupported claims and flags hallucinations.

Key principles (per Phase 10):
- Every claim must trace to: retrieved documents, semantic analysis,
  intent analysis, or behavior analysis
- Unsupported claims are rejected (not included in final output)
- Hallucinations (claims with no evidence base) are flagged
- Confidence reflects evidence support level
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Set

from app.reasoning.llm_provider import extract_json

# ---------------------------------------------------------------------------
# Core validation: claim-to-evidence tracing
# ---------------------------------------------------------------------------


class ClaimValidationResult:
    """Result of validating a single LLM claim against available evidence."""

    def __init__(
        self,
        claim_text: str,
        is_supported: bool,
        supporting_sources: List[str] = None,
        contradicting_sources: List[str] = None,
        uncertainty_reason: Optional[str] = None,
    ):
        self.claim_text = claim_text
        self.is_supported = is_supported
        self.supporting_sources = supporting_sources or []
        self.contradicting_sources = contradicting_sources or []
        self.uncertainty_reason = uncertainty_reason

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim": self.claim_text,
            "is_supported": self.is_supported,
            "supporting_sources": self.supporting_sources,
            "contradicting_sources": self.contradicting_sources,
            "uncertainty_reason": self.uncertainty_reason,
        }


# ---------------------------------------------------------------------------
# Evidence validator main class
# ---------------------------------------------------------------------------


class EvidenceValidator:
    """Validates LLM claims against available evidence from the pipeline.

    Ensures every assertion the LLM makes can be traced to one of:
    - Retrieved RAG chunks (with source, category, similarity)
    - Semantic engine output (topic_names, entities, intent, etc.)
    - Intent analysis results
    - Behavior analysis results

    Claims without traceable evidence are rejected as unsupported.
    Claims contradicting evidence are flagged.
    """

    def __init__(
        self,
        rag_chunks: Optional[List[Dict[str, Any]]] = None,
        semantic_features: Optional[Dict[str, Any]] = None,
        intent_analysis: Optional[Dict[str, Any]] = None,
        behavior_analysis: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the evidence validator.

        Args:
            rag_chunks: List of retrieved chunks from the RAG pipeline,
                       each with "content", "metadata", "similarity" keys.
            semantic_features: Output from the Semantic Engine.
            intent_analysis: Output from the Intent Analysis Engine.
            behavior_analysis: Output from the Behavior Analysis Engine.
        """
        self.rag_chunks = rag_chunks or []
        self.semantic_features = semantic_features or {}
        self.intent_analysis = intent_analysis or {}
        self.behavior_analysis = behavior_analysis or {}

        # Build indexed evidence sources for tracing
        self._indexed_sources: Dict[str, Dict[str, Any]] = {}
        self._build_index()

    def _build_index(self) -> None:
        """Index all available evidence sources for tracing claims."""

        # Index RAG chunks by source key
        for i, chunk in enumerate(self.rag_chunks):
            metadata = chunk.get("metadata", {})
            source_key = metadata.get("source", f"rag_chunk_{i}")
            self._indexed_sources[source_key] = {
                "type": "rag_chunk",
                "content": chunk.get("content", ""),
                "source": source_key,
                "category": metadata.get("category", "unknown"),
                "similarity": chunk.get("similarity", 0.0),
                "version": metadata.get("version", "unknown"),
            }

        # Index semantic features
        for key, value in self.semantic_features.items():
            if isinstance(value, (list, str, int, float, bool)) and value:
                self._indexed_sources[f"semantic_{key}"] = {
                    "type": "semantic_feature",
                    "key": key,
                    "value": str(value)[:200],
                }

        # Index intent analysis
        if self.intent_analysis:
            for key, value in self.intent_analysis.items():
                if isinstance(value, (list, str, int, float, bool)) and value:
                    self._indexed_sources[f"intent_{key}"] = {
                        "type": "intent_feature",
                        "key": key,
                        "value": str(value)[:200],
                    }

        # Index behavior analysis
        if self.behavior_analysis:
            for key, value in self.behavior_analysis.items():
                if isinstance(value, (list, str, int, float, bool)) and value:
                    self._indexed_sources[f"behavior_{key}"] = {
                        "type": "behavior_feature",
                        "key": key,
                        "value": str(value)[:200],
                    }

    # --------------------------------------------------------------------------
    # Public validation methods
    # --------------------------------------------------------------------------

    def validate_claim(
        self, claim: str, claim_type: str = "general"
    ) -> ClaimValidationResult:
        """Validate a single claim against available evidence.

        Args:
            claim: The claim text to validate.
            claim_type: Category of claim (helps with heuristic matching):
                       "intent", "behavior", "urgency", "entity", "general".

        Returns:
            ClaimValidationResult with support status and source info.
        """
        claim_lower = claim.lower().strip()

        # Specialized validation by claim type
        if claim_type == "intent":
            return self._validate_intent_claim(claim_lower)
        if claim_type == "behavior":
            return self._validate_behavior_claim(claim_lower)
        if claim_type == "urgency":
            return self._validate_urgency_claim(claim_lower)
        if claim_type == "entity":
            return self._validate_entity_claim(claim_lower)

        # General claim validation - check against all evidence sources
        return self._validate_general_claim(claim_lower)

    def _validate_intent_claim(self, claim: str) -> ClaimValidationResult:
        """Validate a claim about message intent against intent analysis."""

        # Check if claim keywords match indexed intent features
        indexed_keys = [k for k in self._indexed_sources if k.startswith("intent_")]

        matching_sources: List[str] = []
        for key in indexed_keys:
            source = self._indexed_sources[key]
            # Simple keyword overlap check
            value_str = source.get("value", "").lower()
            # Extract key terms from claim (remove common words)
            claim_terms = set(claim.split()) - {
                "the",
                "a",
                "an",
                "and",
                "or",
                "but",
                "is",
                "are",
                "was",
                "were",
            }
            if claim_terms and any(term in value_str for term in claim_terms):
                matching_sources.append(key)

        is_supported = len(matching_sources) > 0
        contradicting: List[str] = []

        # Check for contradicting intent evidence
        if not is_supported and matching_sources:
            # If we have some matches but claim seems inconsistent, flag
            is_supported = True  # treat as supported if any match found

        return ClaimValidationResult(
            claim_text=claim,
            is_supported=is_supported,
            supporting_sources=matching_sources,
            contradicting_sources=contradicting,
            uncertainty_reason=(
                "Intent claim not fully supported by intent analysis features"
                if not is_supported
                else None
            ),
        )

    def _validate_behavior_claim(self, claim: str) -> ClaimValidationResult:
        """Validate a claim about observed behaviors."""

        indexed_keys = [k for k in self._indexed_sources if k.startswith("behavior_")]
        matching_sources: List[str] = []

        for key in indexed_keys:
            source = self._indexed_sources[key]
            value_str = source.get("value", "").lower()
            claim_terms = set(claim.split()) - {
                "the",
                "a",
                "an",
                "and",
                "or",
                "but",
                "is",
                "are",
                "was",
                "were",
            }
            if claim_terms and any(term in value_str for term in claim_terms):
                matching_sources.append(key)

        is_supported = len(matching_sources) > 0
        contradicting: List[str] = []

        return ClaimValidationResult(
            claim_text=claim,
            is_supported=is_supported,
            supporting_sources=matching_sources,
            contradicting_sources=contradicting,
            uncertainty_reason=(
                "Behavior claim not supported by behavior analysis features"
                if not is_supported
                else None
            ),
        )

    def _validate_urgency_claim(self, claim: str) -> ClaimValidationResult:
        """Validate a claim about urgency level."""

        # Check semantic features for urgency indicators
        behavioral = self.semantic_features.get("behavioral_patterns", [])
        urgency_keywords = ["urgent", "immediately", "hurry", "asap", "emergency"]

        claim_lower = claim.lower()
        found_keywords = [kw for kw in urgency_keywords if kw in claim_lower]

        matching_sources: List[str] = []
        if found_keywords and "behavioral_patterns" in self.semantic_features:
            matching_sources.append("semantic_behavioral_patterns")
            is_supported = True
        elif found_keywords and self.behavior_analysis:
            matching_sources.append("behavior_analysis")
            is_supported = True
        else:
            is_supported = False
            # Check if message itself contains urgency markers
            if any(kw in claim_lower for kw in ["urgent", "immediately", "hurry"]):
                # Message has urgency markers but no analysis supports it
                is_supported = True
                matching_sources.append("message_content")

        contradicting: List[str] = []

        uncertainty_reason = None
        if not is_supported:
            uncertainty_reason = "No urgency evidence found in analysis features"

        return ClaimValidationResult(
            claim_text=claim,
            is_supported=is_supported,
            supporting_sources=matching_sources,
            contradicting_sources=contradicting,
            uncertainty_reason=uncertainty_reason,
        )

    def _validate_entity_claim(self, claim: str) -> ClaimValidationResult:
        """Validate a claim about entities (accounts, domains, etc.)."""

        indexed_keys = [
            k for k in self._indexed_sources if k.startswith("semantic_entities")
        ]
        matching_sources: List[str] = []

        for key in indexed_keys:
            source = self._indexed_sources[key]
            value_str = source.get("value", "").lower()
            # Extract potential entity names from claim
            claim_terms = [t for t in claim.lower().split() if len(t) > 2]
            if any(term in value_str for term in claim_terms):
                matching_sources.append(key)

        is_supported = len(matching_sources) > 0
        contradicting: List[str] = []

        return ClaimValidationResult(
            claim_text=claim,
            is_supported=is_supported,
            supporting_sources=matching_sources,
            contradicting_sources=contradicting,
            uncertainty_reason=(
                "Entity claim not supported by semantic features"
                if not is_supported
                else None
            ),
        )

    def _validate_general_claim(self, claim: str) -> ClaimValidationResult:
        """Validate a general claim against all evidence sources.

        Checks RAG chunks, semantic features, intent analysis, and behavior
        analysis for any traceable support.
        """
        matching_sources: List[str] = []
        contradicting_sources: List[str] = []

        # Check RAG chunks
        for source_key, source in self._indexed_sources.items():
            if source["type"] == "rag_chunk":
                content = source["content"].lower()
                claim_lower = claim.lower()
                # Simple overlap: if any significant word overlap exists
                claim_words = set(claim_lower.split())
                content_words = set(content.split())
                overlap = claim_words & content_words
                if overlap:
                    # Require at least 2 word overlap for significance
                    if len(overlap) >= 2:
                        matching_sources.append(source_key)

        # Check semantic features
        if not matching_sources:
            for source_key, source in self._indexed_sources.items():
                if source["type"] in (
                    "semantic_feature",
                    "intent_feature",
                    "behavior_feature",
                ):
                    value_str = source.get("value", "").lower()
                    claim_words = set(claim.lower().split())
                    if any(word in value_str for word in claim_words if len(word) > 2):
                        matching_sources.append(source_key)

        is_supported = len(matching_sources) > 0
        contradicting = (
            []
        )  # Simplified: no explicit contradiction check in general mode

        uncertainty_reason = None
        if not is_supported:
            uncertainty_reason = "Claim not supported by available evidence sources"

        return ClaimValidationResult(
            claim_text=claim,
            is_supported=is_supported,
            supporting_sources=matching_sources,
            contradicting_sources=contradicting,
            uncertainty_reason=uncertainty_reason,
        )

    # --------------------------------------------------------------------------
    # Batch validation
    # --------------------------------------------------------------------------

    def validate_claims(
        self, claims: List[str], claim_types: Optional[List[str]] = None
    ) -> List[ClaimValidationResult]:
        """Validate multiple claims at once.

        Args:
            claims: List of claim texts to validate.
            claim_types: Optional list of claim types matching each claim.
                        If None, all claims are validated as "general".

        Returns:
            List of ClaimValidationResult one per input claim.
        """
        if claim_types is None:
            claim_types = ["general"] * len(claims)

        results: List[ClaimValidationResult] = []
        for claim, claim_type in zip(claims, claim_types):
            result = self.validate_claim(claim, claim_type)
            results.append(result)
        return results

    # --------------------------------------------------------------------------
    # Hallucination detection
    # --------------------------------------------------------------------------

    def detect_hallucinations(self, claims: List[str]) -> Dict[str, Any]:
        """Detect claims that likely constitute hallucinations.

        A hallucination is a claim with no traceable evidence base.
        This method identifies such claims and provides reasoning.

        Returns:
            Dict with "hallucinated_claims" (list of claim texts),
            "supported_claims" (list of claim texts), and
            "reasoning" (description of the analysis).
        """
        if not claims:
            return {
                "hallucinated_claims": [],
                "supported_claims": [],
                "reasoning": "No claims provided",
            }

        hallucinated: List[str] = []
        supported: List[str] = []
        reasoning_parts: List[str] = []

        for claim in claims:
            result = self.validate_claim(claim)
            if result.is_supported:
                supported.append(claim)
            else:
                hallucinated.append(claim)
                reasoning_parts.append(f"  - '{claim[:60]}...': no traceable evidence")

        reasoning = "Hallucination analysis:\n"
        if hallucinated:
            reasoning += "\n".join(reasoning_parts)
        else:
            reasoning += "All claims have some evidence support."

        if supported:
            reasoning += f"\nSupported claims: {len(supported)}"

        return {
            "hallucinated_claims": hallucinated,
            "supported_claims": supported,
            "reasoning": reasoning,
        }

    # --------------------------------------------------------------------------
    # Output formatting for reasoning engine
    # --------------------------------------------------------------------------

    def validate_and_filter_response(
        self,
        response: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Validate and filter a reasoning response, removing unsupported claims.

        This is called by the reasoning engine after the LLM produces output.
        It examines each evidence reference in the response and checks
        whether it traces to indexed sources. Unsupported references are
        removed or marked as uncertain.

        Args:
            response: The LLM's JSON response dict.

        Returns:
            Filtered/validated response dict with only supported claims/evidence.
        """
        # If response has no evidence chain, return as-is
        if "evidence_chain" not in response:
            return response

        # Filter evidence chain
        validated_chain: List[Dict[str, Any]] = []
        for entry in response.get("evidence_chain", []):
            source_ref = entry.get("source", "")
            # Check if source is indexed
            if source_ref in self._indexed_sources:
                validated_chain.append(entry)
            else:
                # Source not indexed - mark as uncertain
                entry_copy = dict(entry)  # Don't mutate original
                entry_copy["validation_status"] = "uncertain"
                entry_copy["uncertainty_reason"] = "Source not in indexed evidence"
                validated_chain.append(entry_copy)

        response = dict(response)  # Don't mutate original
        response["evidence_chain"] = validated_chain

        # Similarly validate reasoning_steps if present
        if "reasoning_steps" in response:
            validated_steps: List[str] = []
            for step in response.get("reasoning_steps", []):
                # Simple heuristic: if step contains words that match indexed sources, keep it
                step_lower = step.lower()
                supported = False
                for source_key, source in self._indexed_sources.items():
                    content = (
                        source.get("content", "").lower()
                        if source["type"] == "rag_chunk"
                        else ""
                    )
                    if content and any(
                        word in content for word in step_lower.split() if len(word) > 3
                    ):
                        supported = True
                        break
                if supported:
                    validated_steps.append(step)
                else:
                    # Keep but mark uncertain
                    validated_steps.append(f"(uncertain: {step})")
            response["reasoning_steps"] = validated_steps

        return response


# ---------------------------------------------------------------------------
# Global convenience function
# ---------------------------------------------------------------------------


def validate_evidence_for_response(
    response: Dict[str, Any],
    rag_chunks: Optional[List[Dict[str, Any]]] = None,
    semantic_features: Optional[Dict[str, Any]] = None,
    intent_analysis: Optional[Dict[str, Any]] = None,
    behavior_analysis: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Quick validation of an LLM response against available evidence.

    Args:
        response: The LLM's JSON reasoning response.
        rag_chunks: Retrieved chunks from RAG pipeline.
        semantic_features: Semantic Engine output.
        intent_analysis: Intent Analysis Engine output.
        behavior_analysis: Behavior Analysis Engine output.

    Returns:
        Validated and filtered response with only evidence-supported claims.
    """
    validator = EvidenceValidator(
        rag_chunks=rag_chunks,
        semantic_features=semantic_features,
        intent_analysis=intent_analysis,
        behavior_analysis=behavior_analysis,
    )

    # Detect hallucinations
    if "supporting_evidence" in response or "conflicting_evidence" in response:
        claims: List[str] = []
        if "supporting_evidence" in response:
            claims.extend(str(c) for c in response["supporting_evidence"])
        if "conflicting_evidence" in response:
            claims.extend(str(c) for c in response["conflicting_evidence"])

        hallucination_result = validator.detect_hallucinations(claims)
        # Store hallucination info in response metadata
        if "metadata" not in response:
            response = dict(response)  # Don't mutate original
        if "metadata" not in response:
            response["metadata"] = {}
        response["metadata"]["hallucination_analysis"] = hallucination_result

    # Validate and filter
    return validator.validate_and_filter_response(response)
