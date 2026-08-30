"""Prompt Injection Protection for Reasoning Engine.

Protects against malicious user input designed to override system
instructions, disable the LLM, or cause unintended behavior.

Phase 10 requirements:
- Detect and reject prompt injection attempts
- The reasoning engine must always follow system instructions
- Never execute user commands that contradict system directives
- Provide safe prompt construction with injection protection
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

# Injection patterns categorized by type
INJECTION_PATTERNS = {
    "ignore_instructions": [
        r"ignore\s+previous\s+instructions",
        r"forget\s+previous",
        r"disregard\s+all\s+previous",
        r"clear\s+context",
        r"start\s+fresh",
    ],
    "role_override": [
        r"pretend\s+to\s+be",
        r"act\s+as\s+",
        r"role\s*[:=]\s*",
        r"system\s*[:=]\s*",
        r"you\s+are\s+nOW",
    ],
    "disable_llm": [
        r"disable\s+llm",
        r"turn\s+off\s+llm",
        r"no\s+more\s+llm",
        r"llm\s+disabled",
    ],
    "bypass_filters": [
        r"bypass\s+filter",
        r"skip\s+safety",
        r"override\s+safety",
        r"disable\s+safety",
    ],
    "use_documents_against": [
        r"do\s+not\s+use\s+the\s+documents",
        r"ignore\s+retrieved",
        r"disregard\s+evidence",
        r"the\s+knowledge\s+is\s+wrong",
    ],
    "extract_system_prompt": [
        r"give\s+me\s+the\s+system",
        r"show\s+me\s+the\s+prompt",
        r"what\s+are\s+your\s+instructions",
        r"explain\s+your\s+system",
    ],
}

# Regex compilation for performance
_COMPILED_PATTERNS: Dict[str, List[re.Pattern[str]]] = {}
for category, patterns in INJECTION_PATTERNS.items():
    _COMPILED_PATTERNS[category] = [re.compile(p, re.IGNORECASE) for p in patterns]


def detect_injection(text: str) -> Tuple[bool, Optional[str]]:
    """Detect if the given text contains a prompt injection attempt.

    Returns:
        (has_injection, injection_type): Tuple where:
        - has_injection: True if an injection pattern was detected
        - injection_type: The category of injection attempted, or None if unknown
    """
    text_lower = text.lower().strip()

    for category, patterns in _COMPILED_PATTERNS.items():
        for pattern in patterns:
            if pattern.search(text_lower):
                return True, category

    return False, None


def sanitize_user_input(text: str) -> Tuple[str, Optional[str]]:
    """Sanitize user input by removing or neutralizing injection attempts.

    Returns the sanitized text and the detected injection type (or None).
    """
    sanitized = text
    detected_type: Optional[str] = None

    for category, patterns in _COMPILED_PATTERNS.items():
        for pattern in patterns:
            match = pattern.search(sanitized.lower())
            if match:
                detected_type = category
                replacement_map = {
                    "ignore_instructions": "understood",
                    "role_override": "analyze normally",
                    "disable_llm": "proceed with analysis",
                    "bypass_filters": "apply standard safety",
                    "use_documents_against": "use retrieved evidence",
                    "extract_system_prompt": "analysis in progress",
                }
                replacement = replacement_map.get(category, " [neutralized] ")
                sanitized = pattern.sub(replacement, sanitized)

    return sanitized, detected_type


class PromptInjectionProtector:
    """Protector that ensures the LLM reasoning engine always follows system instructions."""

    SYSTEM_DIRECTIVE = (
        "YOU ARE TextShield ANALYST. Your role is to interpret evidence "
        "and produce structured analysis. The final classification is made "
        "by a separate Decision Engine. DO NOT simply label the message. "
        "OUTPUT MUST BE valid JSON matching the ReasoningResponse schema. "
        "EVERY claim must trace to specific retrieved documents or semantic "
        "analysis results. Cite sources by source name or chunk ID. If "
        "evidence is insufficient, explicitly state uncertainty. DO NOT "
        "fabricate information. DO NOT classify the message as spam/phishing "
        "without detailed reasoning."
    )

    @classmethod
    def verify_system_directive_compliance(
        cls, response_text: str
    ) -> Tuple[bool, List[str]]:
        """Verify that an LLM response complies with the system directive.

        Args:
            response_text: The LLM's raw response text.

        Returns:
            (compliant, violations): Tuple where:
            - compliant: True if the response complies with the system directive
            - violations: List of violation descriptions found
        """
        violations: List[str] = []

        if not re.search(r"\{.*\}", response_text, re.DOTALL):
            violations.append("No JSON output found in response")

        disobedience_patterns = [
            r"i.*just\s+(?:label|classify|say)\s+(?:spam|phishing|ham)",
            r"(?:no|never)\s+(?:provide|give|produce)\s+json",
            r"i.*(?:cannot|unable)\s+(?:produce|output)\s+json",
        ]

        text_lower = response_text.lower()
        for pattern in disobedience_patterns:
            if re.search(pattern, text_lower):
                violations.append(f"Direct disobedience detected: {pattern.pattern}")

        requirements_met: List[str] = []

        if any(
            kw in text_lower
            for kw in ["uncertain", "insufficient evidence", "not sure"]
        ):
            requirements_met.append("uncertainty stated when needed")

        if re.search(r"reasoning|reasoning.s*steps", text_lower):
            requirements_met.append("reasoning steps present")

        if not requirements_met:
            violations.append("None of the core requirements met")

        compliant = len(violations) == 0
        return compliant, violations

    @classmethod
    def build_safe_prompt(
        cls, system_prompt: str, user_prompt: str, user_input: str
    ) -> Dict[str, Any]:
        """Build a safe prompt by sanitizing user input.

        Args:
            system_prompt: The base system prompt/directive.
            user_prompt: The structured prompt built from analysis inputs.
            user_input: The raw user message/text.

        Returns:
            Dict with "safe_system_prompt", "safe_user_prompt", and
            "injection_detected" flags.
        """
        sanitized_input, injection_type = sanitize_user_input(user_input)

        injection_in_prompt, prompt_type = (
            detect_injection(user_prompt) if user_prompt else (False, None)
        )

        full_system_prompt = cls.SYSTEM_DIRECTIVE

        injection_reminder = ""
        if injection_type:
            injection_reminder = (
                "\n\nIMPORTANT: User input contained a "
                + injection_type
                + " attempt that has been neutralized. Proceed with analysis as normal."
            )

        safe_user_prompt = user_prompt.replace(user_input, sanitized_input)

        return {
            "safe_system_prompt": full_system_prompt,
            "safe_user_prompt": safe_user_prompt,
            "injection_detected": injection_type is not None or prompt_type is not None,
            "injection_type": injection_type or prompt_type,
            "sanitized_input": sanitized_input,
        }
