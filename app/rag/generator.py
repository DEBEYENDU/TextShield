"""Explanation generator: LLM-first, template fallback.

The generator turns structured analysis data (ML prediction, confidence,
indicators, URL findings, RAG evidence) into a concise human-readable
explanation plus a recommended action.

Pipeline rules
--------------
* The LLM explains the ML result. It is explicitly instructed NOT to
  change the classification.
* No chain-of-thought is exposed; the LLM returns a short JSON object.
* If the LLM is unavailable or returns garbage, a deterministic
  template-based explanation is used instead, and the response flags
  ``explanation_source == "template"``.
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.rag import llm as llm_mod
from app.rag.llm import extract_json

logger = get_logger(__name__)

_SYSTEM_PROMPT = (
    "You are TextShield, a spam-detection explanation assistant. "
    "You are given an ML classification result together with supporting evidence "
    "(rule-based indicators, URL analysis and retrieved knowledge-base documents). "
    "You must EXPLAIN the result, never override it. "
    "Do not output chain-of-thought. Respond with valid JSON only, in this shape:\n"
    '{"summary": "one short sentence", '
    '"explanation": "2-4 sentences explaining why the message was classified '
    'this way, referencing concrete evidence", '
    '"recommended_action": "concise practical guidance for the user"}'
)


def _user_prompt(data: dict) -> str:
    return f"""
ORIGINAL MESSAGE:
{data.get("message", "")}

ML CLASSIFICATION: {data.get("classification")}
ML CONFIDENCE: {data.get("confidence")}

DETECTED INDICATORS:
{_format_indicators(data.get("indicators", []))}

URL ANALYSIS:
{_format_urls(data.get("urls", []))}

RETRIEVED KNOWLEDGE (RAG evidence, may be partial):
{_format_rag(data.get("rag_evidence", []))}

RISK LEVEL: {data.get("risk_level")}
MESSAGE TYPE: {data.get("message_type")}

Respond with the JSON object only.
"""


def _format_indicators(indicators: list[dict]) -> str:
    if not indicators:
        return "(none detected)"
    return "\n".join(
        f"- {item['indicator']} ({item['severity']}): {item.get('evidence', '')}"
        for item in indicators[:8]
    )


def _format_urls(urls: list[dict]) -> str:
    if not urls:
        return "(none detected)"
    lines = []
    for url in urls:
        warnings = "; ".join(url.get("warnings", [])) or "no pattern warnings"
        lines.append(f"- {url.get('url')}: {warnings}")
    return "\n".join(lines)


def _format_rag(evidence: list[dict]) -> str:
    if not evidence:
        return "(no retrieved knowledge)"
    return "\n".join(
        f"- [{item.get('category')}] ({item.get('source')}) {item.get('document', '')[:400]}"
        for item in evidence[:4]
    )


def generate_explanation(analysis: dict) -> dict:
    """Return {'text': ..., 'recommendation': ..., 'source': 'llm'|'template'}."""
    client = llm_mod.create_llm_client()
    if client is not None:
        try:
            raw = client.complete(_SYSTEM_PROMPT, _user_prompt(analysis))
            payload = extract_json(raw)
            if payload and payload.get("explanation"):
                return {
                    "text": str(payload["explanation"]).strip(),
                    "summary": str(payload.get("summary", "")).strip(),
                    "recommendation": str(payload.get("recommended_action", "")).strip(),
                    "source": "llm",
                }
        except Exception as exc:
            logger.warning("LLM explanation failed, using template: %s", exc)
    return template_explanation(analysis)


def template_explanation(analysis: dict) -> dict:
    """Deterministic, evidence-grounded explanation (no LLM involved)."""
    classification = analysis.get("classification", "HAM")
    confidence = analysis.get("confidence", 0.0)
    risk = analysis.get("risk_level", "LOW")
    indicators = analysis.get("indicators", [])
    urls = analysis.get("urls", [])
    evidence = analysis.get("rag_evidence", [])

    parts = [
        f"This message was classified as {classification} with {confidence * 100:.0f}% "
        f"confidence by the machine-learning model, and the overall risk is {risk}."
    ]

    if classification == "SPAM":
        parts.append(
            "The message matches patterns characteristic of unsolicited or fraudulent "
            "communication."
        )
    else:
        parts.append(
            "The message content is consistent with normal personal or transactional "
            "communication."
        )

    if indicators:
        names = ", ".join(
            f"{item['indicator'].lower()} ({item['severity']})" for item in indicators[:6]
        )
        parts.append(f"Rule-based indicators detected: {names}.")
    else:
        parts.append("No significant rule-based spam indicators were detected.")

    if urls:
        flagged = [u for u in urls if u.get("warnings")]
        if flagged:
            parts.append(
                f"Of {len(urls)} link(s) found, {len(flagged)} show potentially "
                "suspicious URL patterns (static analysis only)."
            )
        else:
            parts.append(f"{len(urls)} link(s) were found; none triggered pattern warnings.")

    if evidence:
        top = evidence[0]
        parts.append(
            f"Retrieved knowledge matches '{top.get('category', 'general').replace('_', ' ')}' "
            f"patterns described in {top.get('source', 'knowledge base')}."
        )

    if classification == "SPAM" and "credentials" in {
        ind.get("category") for ind in indicators
    }:
        parts.append("The message requests passwords, PINs or OTPs, which legitimate "
                     "organizations never do.")

    explanation = " ".join(parts)

    recommendation = _recommendation(analysis)
    summary = f"{classification} content detected at {confidence * 100:.0f}% confidence."
    return {
        "text": explanation,
        "summary": summary,
        "recommendation": recommendation,
        "source": "template",
    }


def _recommendation(analysis: dict) -> str:
    if analysis.get("classification") == "HAM":
        if analysis.get("risk_level") == "LOW":
            return "No major spam indicators were detected. This message looks legitimate, " \
                   "but avoid clicking links from unknown senders as a general habit."
        return "The message looks like normal content but contains a few caution-worthy " \
               "signals; verify the sender before acting on anything financial."

    categories = {item.get("category") for item in analysis.get("indicators", [])}
    has_urls = bool(analysis.get("urls"))
    advice = ["Do not click any links or open attachments in this message."]
    if "credentials" in categories:
        advice.append("Never share your password, PIN, OTP or card details.")
    if "payment" in categories or "financial" in categories:
        advice.append("Do not send money or pay any fee.")
    if "urgency" in categories or "banking" in categories:
        advice.append("Ignore urgent threats like account blocking; verify through the "
                      "official app or website instead.")
    if has_urls:
        advice.append("Report the message to the impersonated brand's official helpline "
                      "if it claims to be a known service.")
    advice.append("If you already shared details, contact your bank or cyber cell over "
                  "the official channel immediately.")
    return " ".join(advice)