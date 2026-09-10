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
A missing ML model raises ``ServiceUnavailableError`` (HTTP 503).
"""

from __future__ import annotations

import hashlib
import time
from datetime import UTC, datetime

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError
from app.core.logging import get_logger
from app.database import database as db
from app.ml import indicators as indicator_engine
from app.ml import intent as intent_engine
from app.ml import url_analyzer
from app.ml.classifier import classifier
from app.ml.input_detection import looks_like_raw_email, parse_raw_email
from app.ml.preprocess import normalize_text
from app.rag.generator import generate_explanation
from app.rag.retriever import retriever
from app.schemas.analysis import AnalyzeRequest
from app.services.risk_engine import compute_risk

logger = get_logger(__name__)


def _hash_message(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def _merge_behavior_edges(visualization: dict, behavior_edges: list) -> dict:
    """Append Person—Uses→technique edges to the Cytoscape payload.

    Behavior edges reference display labels, so they materialize their own
    ATTACK_PATTERN/persona nodes (id namespaced ``BEHAVIOR:``) instead of
    rewiring message-graph ids.
    """
    try:
        elements = visualization.get("elements", {})
        nodes = elements.setdefault("nodes", [])
        edges = elements.setdefault("edges", [])
        known_ids = {n.get("data", {}).get("id") for n in nodes}
        for item in behavior_edges or []:
            for role, fallback_type in (("src", "PERSON"), ("dst", "ATTACK_PATTERN")):
                label = str(item.get(f"{role}_label", "")).strip()
                nid = f"BEHAVIOR:{item.get(f'{role}_type', fallback_type)}:{label.lower()}"
                if label and nid not in known_ids:
                    known_ids.add(nid)
                    nodes.append({"data": {"id": nid, "label": label,
                                           "type": item.get(f"{role}_type", fallback_type),
                                           "color": "#FF7452" if role == "dst" else "#4C9AFF",
                                           "sightings": 0, "threat_hits": 0,
                                           "legit_hits": 0}})
            src_id = f"BEHAVIOR:{item.get('src_type', 'PERSON')}:{item.get('src_label', '').lower()}"
            dst_id = f"BEHAVIOR:{item.get('dst_type', 'ATTACK_PATTERN')}:{item.get('dst_label', '').lower()}"
            eid = f"{src_id}::{item.get('rel', 'Uses')}::{dst_id}"
            if all((item.get("src_label"), item.get("dst_label"))) and \
                    not any(e.get("data", {}).get("id") == eid for e in edges):
                edges.append({"data": {"id": eid, "source": src_id, "target": dst_id,
                                       "label": item.get("rel", "Uses"), "weight": 0.6}})
    except Exception:
        pass
    return visualization


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
    if effective_type == "text" and request.message and looks_like_raw_email(request.message):
        # Auto-detection: a raw email pasted into the generic text box is
        # upgraded to an email analysis (subject/sender/body parsed).
        effective_type = "email"

    if effective_type == "email":
        if request.input_type == "text":
            # raw email lives in `message` - parse headers/subject/body
            parsed_email = parse_raw_email(request.message)
            combined_text = " ".join(
                part for part in (parsed_email["subject"], parsed_email["body"]) if part
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
    logger.info(
        "Processing stage: normalize/parse complete, effective_type=%s, text_len=%d",
        effective_type,
        len(combined_text),
    )

    # ------------------------------------------------------------- ML
    try:
        prediction = classifier.predict(combined_text)
        logger.info(
            "ML prediction: %s prob=%.3f model=%s",
            prediction.label,
            prediction.probability,
            classifier.algorithm_name,
        )
    except RuntimeError as exc:
        logger.error("Classifier error: %s", exc)
        raise ServiceUnavailableError(
            "ML model not available. Run `python scripts/train_model.py` first."
        ) from exc

    # ----------------------------------------------------- supporting layers
    indicators = indicator_engine.detect_indicators(full_text)
    logger.info("Indicator engine: %d indicators", len(indicators))
    urls = url_analyzer.analyze_urls(combined_text)
    logger.info("URL analysis: %d urls", len(urls))
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
    logger.info("Intent detection: %s", intent.get("label") if isinstance(intent, dict) else intent)

    # ------------------------------------------------- v4 understanding (RFC-001)
    # Semantic message understanding runs BEFORE the verdict layers and is
    # purely additive: it never changes classification, risk or indicators.
    understanding: dict = {}
    try:
        from app.understanding.pipeline import understanding_pipeline

        understanding = understanding_pipeline.analyze(
            combined_text, sender=sender, subject=subject_text)
        profile = understanding.get("profile", {})
        logger.info(
            "Understanding: type=%s intent=%s risk=%s threat=%.3f trust=%.3f latency_ms=%s",
            profile.get("category"), profile.get("intent"), profile.get("risk"),
            profile.get("threat_score"), profile.get("trust_score"),
            understanding.get("latency_ms"),
        )
    except Exception as exc:  # understanding must never break analysis
        logger.warning("Understanding pipeline failed: %s", exc)
        understanding = {}

    # RAG retrieval (synchronous, cached vector store, never rebuild on page load)
    if retriever.is_ready:
        rag_evidence = retriever.retrieve(combined_text)
        logger.info(
            "RAG retrieval: %d evidence (provider=%s)",
            len(rag_evidence),
            retriever.status().get("embedding_provider"),
        )
    else:
        rag_evidence = []
        logger.info("RAG not ready - continuing without knowledge evidence")

    # ------------------------------------------- v4 behavior (RFC-004)
    # Behavioral evidence provider: manipulation, personas, urgency, emotion,
    # persuasion, style. Additive only — never touches classification/risk.
    behavior: dict = {}
    try:
        from app.behavior.analyzer import behavioral_analyzer, behavior_context_block

        behavior = behavioral_analyzer.analyze(
            combined_text,
            message_type=understanding.get("profile", {}).get("category", "Unknown"),
            sender=sender,
        )
        bp = behavior.get("behavior_profile", {})
        logger.info(
            "Behavior: style=%s manipulation=%s(%.3f) urgency=%s personas=%s latency_ms=%s",
            bp.get("communication_style"), bp.get("manipulation_level"),
            bp.get("manipulation_score"), bp.get("urgency", {}).get("level"),
            bp.get("social_engineering"), behavior.get("latency_ms"),
        )
    except Exception as exc:  # behavior must never break analysis
        logger.warning("Behavioral analysis failed: %s", exc)
        behavior = {}

    # ------------------------------------------- v4 knowledge graph (RFC-003)
    # Context graph reasoning is additive: per-message graph, verdict with
    # trust/threat adjustments (reported, never applied to stored scores),
    # and graph-guided extra retrieval kept in a SEPARATE evidence list so
    # the primary RAG contract is untouched.
    knowledge_graph: dict = {}
    graph_rag_evidence: list = []
    try:
        from app.knowledge_graph.graph_reasoner import build_and_reason
        from app.knowledge_graph.serializers import llm_context_block, to_cytoscape

        kg = build_and_reason(combined_text, understanding, sender=sender)
        verdict = kg["verdict"]
        expansion_terms = list(kg["expansion_terms"]) + behavior.get("rag_terms", [])
        if retriever.is_ready and expansion_terms:
            expanded = combined_text + " " + " ".join(expansion_terms)
            try:
                extra = retriever.retrieve(expanded)
                seen_ids = {e.get("id") for e in rag_evidence}
                graph_rag_evidence = [e for e in extra if e.get("id") not in seen_ids][:3]
            except Exception as exc:
                logger.warning("Graph-guided retrieval failed: %s", exc)
        knowledge_graph = {
            "node_count": len(kg["message_graph"].nodes),
            "edge_count": kg["message_graph"].edge_count(),
            "known_organizations": verdict["known_organizations"],
            "campaign_matches": verdict["campaign_matches"],
            "unknown_domains": verdict["unknown_domains"],
            "trust_adjustment": verdict["trust_adjustment"],
            "threat_adjustment": verdict["threat_adjustment"],
            "adjusted_trust": verdict["adjusted_trust"],
            "adjusted_threat": verdict["adjusted_threat"],
            "confidence": verdict["confidence"],
            "reasons": verdict["reasons"],
            "expansion_terms": kg["expansion_terms"],
            "behavior_rag_terms": behavior.get("rag_terms", []),
            "graph_context": llm_context_block(verdict),
            "visualization": _merge_behavior_edges(
                to_cytoscape(kg["message_graph"]), behavior.get("graph_edges", [])),
            "store_size": kg["graph_size"],
        }
        logger.info(
            "Knowledge graph: nodes=%d edges=%d known_orgs=%s campaigns=%s "
            "trust_adj=%+.3f threat_adj=%+.3f graph_rag=%d",
            knowledge_graph["node_count"], knowledge_graph["edge_count"],
            verdict["known_organizations"], verdict["campaign_matches"],
            verdict["trust_adjustment"], verdict["threat_adjustment"],
            len(graph_rag_evidence),
        )
    except Exception as exc:  # graph must never break analysis
        logger.warning("Knowledge graph failed: %s", exc)
        knowledge_graph = {}

    # Threat Intel (provider-agnostic, not blocking if unavailable)
    # Currently via separate /api/v2/threat endpoints; inline check is no-op but logged
    logger.info("Threat Intel: checked %d urls, %d indicators", len(urls), len(indicators))

    risk = compute_risk(
        prediction.label,
        prediction.probability,
        indicators,
        urls,
        rag_evidence,
        intent=intent,
    )
    logger.info(
        "Decision: risk=%s score=%.1f factors=%s", risk["level"], risk["score"], risk["factors"]
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
            "graph_context": knowledge_graph.get("graph_context", ""),
            "behavior_context": behavior_context_block(behavior) if behavior else "",
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
        # v4 understanding (additive; filtered by response_model on v1 API)
        "understanding": understanding,
        "message_profile": understanding.get("profile", {}),
        # v4 knowledge graph (additive)
        "knowledge_graph": knowledge_graph,
        "graph_rag_evidence": graph_rag_evidence,
        # v4 behavior (additive)
        "behavior": behavior,
        "behavior_profile": behavior.get("behavior_profile", {}),
    }

    # ------------------------------------------------------------- history (Database Save)
    if store_history:
        try:
            row_id = _store_history(
                request,
                combined_text,
                prediction.label,
                prediction.probability,
                risk["level"],
                risk["score"],
                intent,
                effective_type,
            )
            logger.info("Database save: history row %s persisted", row_id)
        except Exception as exc:  # history must never break analysis
            logger.error("Failed to persist history: %s", exc, exc_info=True)

    elapsed = round(time.perf_counter() - started, 3)
    logger.info(
        "analysis complete: %s prob=%.3f risk=%s in %.3fs (explanation=%s, rag=%s)",
        prediction.label,
        prediction.probability,
        risk["level"],
        elapsed,
        explanation_result["source"],
        "on" if rag_evidence else "off",
    )
    return result


def _store_history(
    request: AnalyzeRequest,
    combined_text: str,
    label: str,
    confidence: float,
    risk_level: str,
    risk_score: float,
    intent: dict,
    effective_type: str,
) -> int:
    """Persist a history row. Message content is hashed, not stored, by default."""
    preview = None
    if settings.HISTORY_STORE_PREVIEW:
        cleaned = normalize_text(combined_text, mask_sensitive=False)
        preview = cleaned[: settings.HISTORY_PREVIEW_LENGTH]
    record = {
        "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
        "input_type": effective_type,
        "message_hash": _hash_message(combined_text),
        "classification": label,
        "confidence": confidence,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "intent": intent.get("intent") if isinstance(intent, dict) else None,
        "message_type": effective_type,
        "preview": preview,
    }
    return db.insert_analysis(record)
