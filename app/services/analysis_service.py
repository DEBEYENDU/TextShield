"""Analysis orchestration service.

Pipeline (as executed here):

    input        -> normalize / parse email
    -> preprocess + URL/email/phone extraction
    -> ML classifier (SPAM / HAM + probability)
    -> indicator engine (rule-based evidence)
    -> URL analysis (static pattern checks)
    -> risk engine (transparent score + factors)
    -> RAG retrieval (evidence from the knowledge base)
    -> explanation (LLM if available, template otherwise)
    -> history record (SQLite, hashed content by default)
    -> structured response

Failure policy: if RAG or LLM are unavailable the analysis still
completes with basic classification, confidence and indicators.
A missing ML model raises ``ClassifierUnavailableError`` (HTTP 503).
"""
from __future__ import annotations

import hashlib
import time
from datetime import datetime, timezone

from app.core.config import settings
from app.core.logging import get_logger
from app.database import database as db
from app.ml.classifier import SpamClassifier, classifier
from app.ml import indicators as indicator_engine
from app.ml import url_analyzer
from app.ml import intent as intent_engine
from app.ml.input_detection import looks_like_raw_email, parse_raw_email
from app.ml.preprocess import normalize_text
from app.rag.generator import generate_explanation
from app.rag.retriever import retriever
from app.schemas.analysis import AnalyzeRequest, AnalysisResult
from app.services.risk_engine import compute_risk

logger = get_logger(__name__)


class ClassifierUnavailableError(RuntimeError):
    """Raised when the ML model files are missing."""


def _hash_message(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def _combine_email_fields(request: AnalyzeRequest) -> dict:
    """Return {subject, sender, body, combined} for email input."""
    subject = (request.subject or "").strip()
    sender = (request.sender or "").strip()
    body = (request.body or "").strip()
    if request.email_raw:
        if looks_like_raw_email(request.email_raw):
            parsed = parse_raw_email(request.email_raw)
            subject = parsed["subject"]
            sender = parsed["sender"]
            body = parsed["body"]
        else:
            body = request.email_raw.strip()
    combined = " ".join(part for part in (subject, body) if part).strip()
    return {"subject": subject, "sender": sender, "body": body, "combined": combined}


def analyze(request: AnalyzeRequest, store_history: bool = True) -> dict:
    """Run the full analysis pipeline and return the structured payload."""
    started = time.perf_counter()
    logger.info(
        "analyze requested: input_type=%s, has_message=%s, has_body=%s, raw_email=%s",
        request.input_type,
        bool(request.message),
        bool(request.body),
        bool(request.email_raw),
    )

    # ------------------------------------------------------------- inputs
    effective_type = request.input_type
    if (
        effective_type == "text"
        and request.message
        and looks_like_raw_email(request.message)
    ):
        # Auto-detection: a raw email pasted into the generic text box is
        # upgraded to an email analysis (subject/sender/body parsed).
        effective_type = "email"

    if effective_type == "email":
        if request.input_type == "text":
            # raw email lives in `message` - parse headers/subject/body
            parsed_email = parse_raw_email(request.message)
            combined_text = " ".join(
                part for part in (parsed_email["subject"], parsed_email["body"])
                if part
            ).strip()
            subject_text = parsed_email["subject"]
            sender = parsed_email["sender"]
        else:
            parsed = _combine_email_fields(request)
            combined_text = parsed["combined"]
            subject_text = parsed["subject"]
            sender = parsed["sender"]
    else:
        combined_text = (request.message or "").strip()
        subject_text = ""
        sender = ""

    if not combined_text:
        raise ValueError("Message content is empty after parsing.")

    full_text = combined_text
    if sender:
        full_text = f"{full_text}\n{sender}"

    # ------------------------------------------------------------- ML
    try:
        prediction = classifier.predict(combined_text)
    except RuntimeError as exc:
        logger.error("Classifier error: %s", exc)
        raise ClassifierUnavailableError(
            "ML model not available. Run `python scripts/train_model.py` first."
        ) from exc

    # ----------------------------------------------------- supporting layers
    indicators = indicator_engine.detect_indicators(full_text)
    urls = url_analyzer.analyze_urls(combined_text)
    if sender:
        domain_info = url_analyzer.analyze_domain(sender.split("@")[-1])
        if domain_info["suspicious"]:
            indicators.append(
                {
                    "indicator": "Suspicious sender domain",
                    "severity": "high",
                    "category": "phishing",
                    "evidence": domain_info["host"],
                }
            )
            urls.append(
                {
                    "url": f"mailto:{sender}",
                    "host": domain_info["host"],
                    "warnings": domain_info["warnings"],
                    "flag_count": domain_info["flag_count"],
                }
            )

    intent = intent_engine.detect_intent(full_text)

    rag_evidence = retriever.retrieve(combined_text) if retriever.is_ready else []
    if not retriever.is_ready:
        logger.info("RAG not ready - continuing without knowledge evidence")

    risk = compute_risk(
        prediction.label, prediction.probability, indicators, urls, rag_evidence,
        intent=intent,
    )

    mention_subject = " (subject: " + subject_text + ")" if subject_text else ""
    explanation_result = generate_explanation(
        {
            "message": combined_text[:1200] + mention_subject,
            "classification": prediction.label,
            "confidence": prediction.probability,
            "indicators": indicators,
            "urls": urls,
            "rag_evidence": rag_evidence,
            "risk_level": risk["level"],
            "message_type": effective_type,
            "intent": intent,
        }
    )

    # ------------------------------------------------------------- mapping
    result = {
        "classification": prediction.label,
        "confidence": prediction.probability,
        "risk_score": risk["score"],
        "risk_level": risk["level"],
        "message_type": effective_type,
        "intent": intent,
        "indicators": indicators,
        "urls": urls,
        "rag_evidence": rag_evidence,
        "explanation": explanation_result["text"],
        "explanation_source": explanation_result["source"],
        "recommended_action": explanation_result["recommendation"],
        "risk_factors": risk["factors"],
        "model_used": classifier.algorithm_name or "unknown",
        "rag_status": retriever.status(),
    }

    # ------------------------------------------------------------- history
    if store_history:
        try:
            _store_history(request, combined_text, prediction.label,
                           prediction.probability, risk["level"])
        except Exception as exc:  # history must never break analysis
            logger.error("Failed to persist history: %s", exc)

    elapsed = round(time.perf_counter() - started, 3)
    logger.info(
        "analysis complete: %s prob=%.3f risk=%s in %.3fs (explanation=%s, rag=%s)",
        prediction.label, prediction.probability, risk["level"],
        elapsed, explanation_result["source"],
        "on" if rag_evidence else "off",
    )
    return result


def _store_history(
    request: AnalyzeRequest, combined_text: str, label: str, confidence: float,
    risk_level: str,
) -> int:
    """Persist a history row. Message content is hashed, not stored, by default."""
    preview = None
    if settings.HISTORY_STORE_PREVIEW:
        cleaned = normalize_text(combined_text, mask_sensitive=False)
        preview = cleaned[: settings.HISTORY_PREVIEW_LENGTH]
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "input_type": request.input_type,
        "message_hash": _hash_message(combined_text),
        "classification": label,
        "confidence": confidence,
        "risk_level": risk_level,
        "preview": preview,
    }
    return db.insert_analysis(record)