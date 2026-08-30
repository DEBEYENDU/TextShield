"""Prompt Builder for Reasoning Engine.

Constructs LLM prompts from structured inputs derived by the TextShield
pipeline: Semantic Engine, Intent & Behavior Analysis, and RAG Retrieval
Pipeline.

Prompt requirements (per Phase 10):
- Require evidence-based reasoning: every claim must trace to retrieved
  documents or semantic analysis
- Require uncertainty when evidence is insufficient
- Require structured JSON output (never free-form classification)
- Never ask the model to simply classify the message as "spam" or "ham"
- Support prompt injection protection (STEP 9)
- Support hallucination mitigation (STEP 8)

The prompt is designed so the LLM acts as an analyst, not the final judge.
The Decision Engine (future phase) makes the final classification.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.reasoning.llm_provider import create_llm_client, LLMProvider

# ---------------------------------------------------------------------------
# Prompt builder: assembles structured inputs into a single LLM prompt
# ---------------------------------------------------------------------------


class PromptBuilder:
    """Builds LLM prompts for reasoning about message characteristics.

    Takes structured inputs from the pipeline and produces a prompt that
    directs the LLM to perform evidence-based analysis with structured
    JSON output.
    """

    # Prompt template parts (kept as class constants for maintainability)
    SYSTEM_PROMPT = """You are TextShield, a cybersecurity analysis assistant.
You examine messages and retrieved cybersecurity knowledge to identify
patterns characteristic of spam, phishing, fraud, or legitimate
communication.

ROLE: You are an ANALYST, not the final decision-maker.
- Your job is to interpret evidence and produce structured analysis.
- The final classification is made by a separate Decision Engine.
- Do NOT simply label the message as "spam" or "phishing" without
  providing detailed reasoning.

REQUIREMENTS:
1. EVERY claim must be traceable to specific retrieved documents or
   semantic analysis results. Cite sources by source name or chunk ID.
2. If evidence is insufficient or contradictory, explicitly state
   uncertainty. Do not invent or fabricate information.
3. OUTPUT MUST BE valid JSON matching the ReasoningResponse schema
   (see below). Do not include surrounding prose or analysis text
   outside the JSON structure.

4. Analyze these aspects:
   - Message summary and likely sender objective
   - Observed behaviors (urgency, authority, fear, etc.)
   - Requested actions (click link, provide credentials, etc.)
   - Manipulation techniques (if any)
   - Supporting evidence from retrieved knowledge
   - Conflicting evidence
   - Remaining uncertainty

5. If the LLM cannot determine a answer with reasonable confidence,
   set confidence to a low value and describe uncertainty in the
   "limitations" field.
"""

    USER_PROMPT_TEMPLATE = """ORIGINAL MESSAGE:
{original_message}

SEMANTIC ANALYSIS:
- Detected intent: {intent}
- Detected entities: {entities}
- Behavioral patterns: {behavioral_patterns}
- Communication goal: {communication_goal}
- Topic names: {topic_names}
- Extracted keywords: {keywords}

INTENT & BEHAVIOR ANALYSIS:
- Primary intent: {primary_intent}
- Secondary intents: {secondary_intents}
- Behavioral patterns detected: {behavior_patterns}
- Communication style: {communication_style}
- Urgency level: {urgency_level}

RAG RETRIEVAL EVIDENCE:
{evidence_section}

INSTRUCTION:
Provide a structured analysis of whether this message exhibits characteristics
of spam, phishing, fraud, or legitimate communication. Base your analysis
exclusively on the provided evidence. Cite specific sources.

Output ONLY a JSON object matching the ReasoningResponse schema. Do not
include any reasoning text outside the JSON.
"""

    # ------------------------------------------------------------------
    # Core builder method
    # ------------------------------------------------------------------

    @classmethod
    def build(
        cls,
        *,
        original_message: str,
        semantic_features: Dict[str, Any],
        intent_analysis: Optional[Dict[str, Any]] = None,
        behavior_analysis: Optional[Dict[str, Any]] = None,
        rag_results: Optional[List[Dict[str, Any]]] = None,
        provider: Optional[LLMProvider] = None,
    ) -> Dict[str, Any]:
        """Build a structured prompt dict for the LLM.

        Args:
            original_message: The incoming message text.
            semantic_features: Output from the Semantic Engine.
            intent_analysis: Output from the Intent Analysis Engine.
            behavior_analysis: Output from the Behavior Analysis Engine.
            rag_results: List of retrieved chunks from the RAG pipeline.
            provider: Optional LLMProvider instance (uses configured default
                      if None).

        Returns:
            Dict with "system" and "user" keys ready for LLM completion.
        """
        # Extract fields from semantic features
        intent = semantic_features.get("intent", "unknown")
        entities = semantic_features.get("entities", [])
        behavioral_patterns = semantic_features.get("behavioral_patterns", [])
        communication_goal = semantic_features.get("communication_goal", "")
        topic_names = semantic_features.get("topic_names", [])
        keywords = semantic_features.get("keywords", [])

        # Intent analysis
        if intent_analysis is None:
            primary_intent = intent
            secondary_intents = []
        else:
            primary_intent = intent_analysis.get("primary_intent", intent)
            secondary_intents = intent_analysis.get("secondary_intents", [])

        # Behavior analysis
        if behavior_analysis is None:
            behavior_patterns_list = behavioral_patterns if behavioral_patterns else []
            communication_style = ""
            urgency_level = "medium"
        else:
            behavior_patterns_list = behavior_analysis.get(
                "behavioral_patterns", behavioral_patterns or []
            )
            communication_style = behavior_analysis.get("communication_style", "")
            urgency_level = behavior_analysis.get("urgency_level", "medium")

        # Build evidence section from RAG results
        evidence_section = cls._build_evidence_section(rag_results or [])

        # Render the user prompt
        user_prompt = cls.USER_PROMPT_TEMPLATE.format(
            original_message=original_message,
            intent=intent,
            entities=json.dumps(entities, ensure_ascii=False),
            behavioral_patterns=json.dumps(behavior_patterns_list, ensure_ascii=False),
            communication_goal=communication_goal,
            topic_names=json.dumps(topic_names, ensure_ascii=False),
            keywords=json.dumps(keywords, ensure_ascii=False),
            primary_intent=primary_intent,
            secondary_intents=json.dumps(secondary_intents, ensure_ascii=False),
            behavior_patterns=json.dumps(behavior_patterns_list, ensure_ascii=False),
            communication_style=communication_style,
            urgency_level=urgency_level,
            evidence_section=evidence_section,
        )

        # Determine which provider to use
        if provider is None:
            provider = create_llm_client()

        return {
            "system": cls.SYSTEM_PROMPT,
            "user": user_prompt,
            "provider": provider,
        }

    # ------------------------------------------------------------------
    # Evidence section builder
    # ------------------------------------------------------------------

    @classmethod
    def _build_evidence_section(cls, rag_results: List[Dict[str, Any]]) -> str:
        """Build the evidence section of the prompt from RAG results.

        Each chunk is formatted with its content, source, similarity score,
        and relevance notes. If no chunks are provided, a statement that
        no retrieval evidence is available is included.

        This ensures every claim the LLM makes can be traced to a source.
        """
        if not rag_results:
            return "No retrieved evidence available. Analyze based on semantic/intent/behavior features only."

        parts: List[str] = []
        for i, chunk in enumerate(rag_results, start=1):
            content = chunk.get("content", "")
            metadata = chunk.get("metadata", {})
            source = metadata.get("source", f"chunk_{i}")
            category = metadata.get("category", "unknown")
            similarity = chunk.get("similarity", 0.0)
            # Extract a relevance snippet (first 80 chars if content is long)
            snippet = content[:80] + ("..." if len(content) > 80 else "")
            parts.append(
                f"--- Evidence {i} ---\n"
                f"Source: {source} (category: {category})\n"
                f"Similarity: {similarity:.4f}\n"
                f"Content: {snippet}\n"
            )
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Completion helper (optional, used by ReasoningService)
    # ------------------------------------------------------------------

    @classmethod
    def complete_with_provider(
        cls,
        *,
        original_message: str,
        semantic_features: Dict[str, Any],
        intent_analysis: Optional[Dict[str, Any]] = None,
        behavior_analysis: Optional[Dict[str, Any]] = None,
        rag_results: Optional[List[Dict[str, Any]]] = None,
        provider: Optional[LLMProvider] = None,
    ) -> Optional[Dict[str, Any]]:
        """Build prompt and request completion from the LLM.

        Returns the raw JSON dict if the LLM responds successfully, or None
        if the LLM is disabled/unavailable.
        """
        prompt_dict = cls.build(
            original_message=original_message,
            semantic_features=semantic_features,
            intent_analysis=intent_analysis,
            behavior_analysis=behavior_analysis,
            rag_results=rag_results,
            provider=provider,
        )

        provider = prompt_dict["provider"]
        if provider is None:
            from app.core.logging import get_logger

            logger = get_logger(__name__)
            logger.warning("LLM provider unavailable - returning None")
            return None

        try:
            system = prompt_dict["system"]
            user = prompt_dict["user"]
            response_text = provider.complete(system=system, user=user)
            return cls._parse_response(response_text)
        except Exception as exc:
            from app.core.logging import get_logger

            logger = get_logger(__name__)
            logger.error("LLM completion failed: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Response parser: extracts and validates JSON from LLM output
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_response(text: Optional[str]) -> Optional[Dict[str, Any]]:
        """Parse the LLM response, extracting the best-effort JSON object.

        Uses the extract_json utility from the LLM provider module.
        Returns None if no valid JSON can be extracted.

        This is a safeguard against LLMs that include prose around the
        JSON or fail to format strictly.
        """
        from app.reasoning.llm_provider import extract_json

        if not text:
            return None

        result = extract_json(text)
        if result is not None:
            # Basic schema validation: ensure essential keys exist
            essential = {
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
                "references",
            }
            if essential.isubset(result.keys()) or _minimal_schema_ok(result):
                return result

        # Fallback: try to extract JSON from within the text
        # (LLM may wrap it in markdown code blocks or prose)
        try:
            import re

            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                candidate = json.loads(match.group(0))
                essential = {
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
                    "references",
                }
                if essential.isubset(candidate.keys()) or _minimal_schema_ok(candidate):
                    return candidate
        except (json.JSONDecodeError, TypeError):
            pass

        return None


def _minimal_schema_ok(data: Dict[str, Any]) -> bool:
    """Check if the JSON has the minimal required fields for a reasoning response.

    Not all fields may be populated (e.g., no evidence may be available),
    but the core structure must exist.
    """
    required_groups = {
        "summary": str,
        "confidence": (int, float),
        "observed_intents": list,
        "behaviors": list,
        "requested_actions": list,
        "manipulation": list,
        "supporting_evidence": list,
        "conflicting_evidence": list,
        "reasoning_steps": list,
        "limitations": list,
        "references": list,
    }

    for key, expected_type in required_groups.items():
        if key not in data:
            return False
        if not isinstance(data[key], expected_type):
            # Allow empty lists as valid
            if not (expected_type is list and isinstance(data[key], list)):
                return False
    return True
