"""Structured JSON Response Parsing and Validation for Reasoning Engine.

Parses LLM responses, extracts JSON objects (handling prose, markdown
formatting, code blocks), and validates against the ReasoningResponse
schema. Ensures every reasoning output is well-structured and valid.

Phase 10 requirements:
- Output MUST be valid JSON matching the ReasoningResponse schema
- No prose outside JSON structure
- Every claim must be traceable to evidence
- Uncertainty must be explicitly stated when evidence is insufficient
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, get_type_hints

from app.reasoning.evidence_validator import ClaimValidationResult, EvidenceValidator

# ---------------------------------------------------------------------------
# ReasoningResponse schema definition
# ---------------------------------------------------------------------------


class ReasoningResponse:
    """Structured response schema from the LLM Reasoning Engine.

    This is the exact schema the LLM must output. All fields are required
    (some may be empty/default lists/null) to ensure consistent downstream
    processing by the Decision Engine (future phase).

    Fields:
        summary: Overall summary of the analysis
        observed_intents: List of detected intent(s)
        behaviors: List of observed behaviors
        requested_actions: List of actions requested by the message
        manipulation: List of manipulation techniques detected
        supporting_evidence: List of evidence supporting the analysis
        conflicting_evidence: List of evidence contradicting the analysis
        reasoning_steps: List of logical reasoning steps taken
        limitations: List of known limitations/uncertainties
        confidence: Float confidence score in [0.0, 1.0]
        uncertainty: Description of remaining uncertainty
        references: List of source references
    """

    #: Schema field names for validation
    REQUIRED_FIELDS = {
        "summary",
        "observed_intents",
        "behaviors",
        "requested_actions",
        "manipulation",
        "supporting_evidence",
        "conflicting_evidence",
        "reasoning_steps",
        "limitations",
        "confidence",
        "uncertainty",
        "references",
    }

    #: Expected types for each field
    FIELD_TYPES: Dict[str, type] = {
        "summary": str,
        "observed_intents": list,
        "behaviors": list,
        "requested_actions": list,
        "manipulation": list,
        "supporting_evidence": list,
        "conflicting_evidence": list,
        "reasoning_steps": list,
        "limitations": list,
        "confidence": (int, float),
        "uncertainty": str,
        "references": list,
    }

    def __init__(
        self,
        summary: str = "",
        observed_intents: List[str] = None,
        behaviors: List[str] = None,
        requested_actions: List[str] = None,
        manipulation: List[str] = None,
        supporting_evidence: List[Dict[str, Any]] = None,
        conflicting_evidence: List[Dict[str, Any]] = None,
        reasoning_steps: List[str] = None,
        limitations: List[str] = None,
        confidence: float = 0.0,
        uncertainty: str = "",
        references: List[str] = None,
    ):
        self.summary = summary
        self.observed_intents = observed_intents or []
        self.behaviors = behaviors or []
        self.requested_actions = requested_actions or []
        self.manipulation = manipulation or []
        self.supporting_evidence = supporting_evidence or []
        self.conflicting_evidence = conflicting_evidence or []
        self.reasoning_steps = reasoning_steps or []
        self.limitations = limitations or []
        self.confidence = round(float(confidence), 4)
        self.uncertainty = uncertainty
        self.references = references or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict, ensuring all schema fields are present."""
        return {
            "summary": self.summary,
            "observed_intents": self.observed_intents,
            "behaviors": self.behaviors,
            "requested_actions": self.requested_actions,
            "manipulation": self.manipulation,
            "supporting_evidence": self.supporting_evidence,
            "conflicting_evidence": self.conflicting_evidence,
            "reasoning_steps": self.reasoning_steps,
            "limitations": self.limitations,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
            "references": self.references,
        }

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate the response against the schema.

        Returns:
            (is_valid, errors) tuple where errors is a list of
            human-readable validation error messages.
        """
        errors: List[str] = []

        # Check all required fields exist
        for field in self.REQUIRED_FIELDS:
            if not hasattr(self, field):
                errors.append(f"Missing required field: {field}")
                continue

            value = getattr(self, field)
            expected_type = self.FIELD_TYPES.get(field)

            # Type checking
            if expected_type and not isinstance(value, expected_type):
                # Allow list types to be None/empty
                if not (expected_type is list and (value is None or value == [])):
                    errors.append(
                        f"Field '{field}' expected {expected_type.__name__}, "
                        f"got {type(value).__name__}: {value}"
                    )

        return len(errors) == 0, errors


# ---------------------------------------------------------------------------
# JSON extraction from LLM response
# ---------------------------------------------------------------------------


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Extract a JSON object from LLM response text.

    Handles multiple formats:
    1. Pure JSON text
    2. JSON wrapped in markdown code blocks (```json ... ```)
    3. JSON embedded in prose with surrounding text
    4. JSON with trailing/leading whitespace

    Args:
        text: The raw LLM response text.

    Returns:
        Parsed JSON dict if found, None otherwise.
    """
    if not text:
        return None

    # Strip code block markers if present
    cleaned = text.strip()

    # Remove ```json ``` or ``` ``` blocks
    code_block_pattern = r"^```(?:json)?\s*\n(.*?)\n```$"
    match = re.match(code_block_pattern, cleaned, re.DOTALL)
    if match:
        cleaned = match.group(1).strip()

    # Try direct JSON parse
    try:
        result = json.loads(cleaned)
        if isinstance(result, dict):
            return result
    except (json.JSONDecodeError, ValueError):
        pass

    # Search for JSON object within text using regex
    # Look for the outermost balanced braces approach
    # Find the first { and last }
    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start >= 0 and end > start:
        candidate = cleaned[start : end + 1]
        try:
            result = json.loads(candidate)
            if isinstance(result, dict):
                return result
        except (json.JSONDecodeError, ValueError):
            pass

    return None


# ---------------------------------------------------------------------------
# Response parser: parse and validate LLM output
# ---------------------------------------------------------------------------


class ResponseParser:
    """Parses and validates LLM reasoning responses.

    Responsibilities:
    1. Extract JSON from LLM response text (prose, markdown, code blocks)
    2. Validate against ReasoningResponse schema
    3. Fill in default values for missing fields
    4. Cross-validate with evidence (optionally using EvidenceValidator)
    5. Return a validated ReasoningResponse object
    """

    def __init__(self, evidence_validator: Optional[EvidenceValidator] = None):
        self.evidence_validator = evidence_validator

    def parse(self, text: str) -> Optional[ReasoningResponse]:
        """Parse an LLM response text into a validated ReasoningResponse.

        Args:
            text: Raw LLM response text.

        Returns:
            ReasoningResponse object if parsing and validation succeed,
            None if the response cannot be parsed or is invalid.
        """
        # Step 1: Extract JSON from text
        json_dict = extract_json_from_text(text)
        if json_dict is None:
            return None

        # Step 2: Fill in ReasoningResponse with extracted values
        response = self._dict_to_response(json_dict)

        # Step 3: Validate schema
        is_valid, errors = response.validate()
        if not is_valid:
            # Try to fix common issues; if unresolvable, return None
            if not self._fix_common_issues(response, errors):
                return None

        # Step 4: Cross-validate with evidence (optional)
        if self.evidence_validator and hasattr(response, "supporting_evidence"):
            self._cross_validate_with_evidence(response)

        return response

    def _dict_to_response(self, data: Dict[str, Any]) -> ReasoningResponse:
        """Convert a JSON dict to a ReasoningResponse object.

        Uses .get() with defaults for all fields to handle missing keys.
        """
        return ReasoningResponse(
            summary=data.get("summary", ""),
            observed_intents=data.get("observed_intents", []),
            behaviors=data.get("behaviors", []),
            requested_actions=data.get("requested_actions", []),
            manipulation=data.get("manipulation", []),
            supporting_evidence=data.get("supporting_evidence", []),
            conflicting_evidence=data.get("conflicting_evidence", []),
            reasoning_steps=data.get("reasoning_steps", []),
            limitations=data.get("limitations", []),
            confidence=data.get("confidence", 0.0),
            uncertainty=data.get("uncertainty", ""),
            references=data.get("references", []),
        )

    def _fix_common_issues(
        self, response: ReasoningResponse, errors: List[str]
    ) -> bool:
        """Attempt to fix common schema validation issues.

        Returns True if issues were fixed, False if the response is
        beyond repair.
        """
        fixed = False

        for error in errors:
            if "Missing required field" in error:
                field = error.replace("Missing required field: ", "")
                # Add default based on field name
                defaults = {
                    "summary": "",
                    "observed_intents": [],
                    "behaviors": [],
                    "requested_actions": [],
                    "manipulation": [],
                    "supporting_evidence": [],
                    "conflicting_evidence": [],
                    "reasoning_steps": [],
                    "limitations": [],
                    "uncertainty": "",
                }
                if field in defaults:
                    setattr(response, field, defaults[field])
                    fixed = True

        # Re-validate after fixes
        is_valid, _ = response.validate()
        return is_valid

    def _cross_validate_with_evidence(self, response: ReasoningResponse) -> None:
        """Cross-validate response claims with available evidence.

        This updates the response's supporting_evidence and confidence
        based on what the EvidenceValidator can verify.

        Note: This is a best-effort operation; if the evidence validator
        is not configured, this method is a no-op.
        """
        if not self.evidence_validator:
            return

        # Collect claims from the response to validate
        claims: List[str] = []

        # Extract claims from reasoning_steps
        for step in response.reasoning_steps:
            claims.append(step)

        # Extract claims from supporting_evidence summaries
        for ev in response.supporting_evidence:
            if isinstance(ev, dict) and "reasoning" in ev:
                claims.append(str(ev["reasoning"]))
            elif isinstance(ev, str):
                claims.append(ev)

        # Validate claims
        if claims:
            validation_results = self.evidence_validator.validate_claims(claims)

            # Update confidence based on validation
            supported_count = sum(1 for r in validation_results if r.is_supported)
            total_count = len(validation_results)

            if total_count > 0:
                ratio = supported_count / total_count
                # Adjust confidence downward if claims are unsupported
                current_conf = response.confidence
                adjustment = (1.0 - current_conf) * (1.0 - ratio)
                response.confidence = round(max(0.0, current_conf - adjustment), 4)

            # Add uncertainty if many claims are unsupported
            if supported_count / total_count < 0.5 if total_count > 0 else True:
                if not response.uncertainty:
                    response.uncertainty = (
                        f"{total_count - supported_count} of "
                        f"{total_count} claims not fully supported by evidence"
                    )

    # --------------------------------------------------------------------------
    # Batch parsing
    # --------------------------------------------------------------------------

    def parse_batch(self, texts: List[str]) -> List[Optional[ReasoningResponse]]:
        """Parse multiple LLM response texts.

        Args:
            texts: List of raw LLM response texts.

        Returns:
            List of ReasoningResponse objects (None for failed parses).
        """
        return [self.parse(text) for text in texts]


# ---------------------------------------------------------------------------
# Global convenience functions
# ---------------------------------------------------------------------------


def parse_llm_response(
    text: str, evidence_validator: Optional[EvidenceValidator] = None
) -> Optional[ReasoningResponse]:
    """Quick convenience function: parse an LLM response text.

    Args:
        text: Raw LLM response text.
        evidence_validator: Optional EvidenceValidator for cross-validation.

    Returns:
        ReasoningResponse object or None if parsing fails.
    """
    parser = ResponseParser(evidence_validator=evidence_validator)
    return parser.parse(text)


def parse_and_validate_llm_output(
    text: str,
    rag_chunks: Optional[List[Dict[str, Any]]] = None,
    semantic_features: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Parse, validate, and cross-validate an LLM response.

    Full pipeline: extract JSON -> validate schema -> cross-check with
    evidence -> return enriched dict.

    Args:
        text: Raw LLM response text.
        rag_chunks: Retrieved chunks from RAG pipeline.
        semantic_features: Semantic Engine output.

    Returns:
        Dict with "reasoning_response" (ReasoningResponse object or None)
        and "metadata" (validation info, hallucination analysis, etc.).
    """
    from app.reasoning.evidence_validator import validate_evidence_for_response

    # Parse the response
    parser = ResponseParser(evidence_validator=None)
    reasoning_response = parser.parse(text)

    # Build metadata dict
    metadata: Dict[str, Any] = {
        "parsing_success": reasoning_response is not None,
        "schema_valid": (
            reasoning_response is not None and reasoning_response.validate()[0]
            if reasoning_response
            else False
        ),
    }

    # Cross-validate with evidence if we have a response and evidence inputs
    if reasoning_response and (rag_chunks or semantic_features):
        ev = EvidenceValidator(
            rag_chunks=rag_chunks,
            semantic_features=semantic_features,
        )
        validation_result = validate_evidence_for_response(
            reasoning_response.to_dict(),
            rag_chunks=rag_chunks,
            semantic_features=semantic_features,
        )
        metadata["hallucination_analysis"] = validation_result.get("metadata", {}).get(
            "hallucination_analysis", {}
        )
        # Update confidence based on evidence
        if "confidence" in reasoning_response.to_dict():
            base_conf = reasoning_response.confidence
            evidence_conf = metadata.get("hallucination_analysis", {}).get(
                "supported_claims", []
            )
            # Simple confidence adjustment
            if evidence_conf:
                supported_ratio = len(evidence_conf) / max(
                    len(
                        validation_result.get("hallucination_analysis", {}).get(
                            "hallucinated_claims", []
                        )
                    )
                    + len(evidence_conf),
                    1,
                )
                adjusted_conf = round(base_conf * supported_ratio, 4)
                reasoning_response.confidence = adjusted_conf

    return {
        "reasoning_response": reasoning_response,
        "metadata": metadata,
    }
