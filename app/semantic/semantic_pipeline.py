"""Semantic Understanding Engine — analysis pipeline.

Stages (all deterministic; no classification):

1. input resolution (sms / text / chat / email / raw email)
2. preprocessing (unicode, whitespace, emoji preservation, case)
3. language detection + confidence
4. sentence segmentation
5. context detection (domain keywords -> confidence)
6. topic extraction (topic lexicon -> confidence)
7. entity extraction (regex + heuristic patterns -> structured entities)
8. semantic features (counts + boolean surface indicators)
9. embeddings (message / sentences / subject / body)
10. confidence estimation (language / context / topic / entity)
11. structured :class:`SemanticAnalysisResult`

Graceful degradation: empty or malformed inputs produce a valid result
with ``unknown``/empty fields — never an exception.
"""
from __future__ import annotations

import re
from typing import Any

from app.core.logging import get_logger
from app.semantic.embedding_service import EmbeddingService, embedding_service
from app.semantic.semantic_models import (
    SemanticAnalysisResult,
    SemanticConfidence,
    SemanticContext,
    SemanticEntity,
    SemanticFeatures,
    SemanticTopic,
)
from app.semantic.semantic_utils import (
    detect_language,
    extract_emojis,
    is_imperative_sentence,
    is_question_sentence,
    parse_raw_email,
    preprocess_text,
    segment_sentences,
)

logger = get_logger(__name__)

_UNKNOWN = "unknown"

# ================================================================= contexts
_CONTEXT_LEXICONS: dict[str, list[str]] = {
    "banking": [
        "bank", "bank account", "account balance", "savings", "atm", "debit card",
        "credit card", "upi", "neft", "imps", "rtgs", "otp", "pin", "kyc",
        "balance", "branch", "ifsc", "cheque", "statement", "transaction",
        "bank details", "netbanking",
    ],
    "finance": [
        "loan", "emi", "interest", "invest", "mutual fund", "sip", "insurance",
        "credit score", "tax", "refund", "salary", "mortgage", "wallet",
        "payment", "pay", "money transfer", "finance", "pre-approved", "crypto",
    ],
    "shopping": [
        "order", "delivery", "shipped", "track order", "discount", "coupon",
        "cart", "checkout", "return", "refund", "invoice", "purchase", "buy",
        "deal", "gift card", "out for delivery", "cod", "cash on delivery",
    ],
    "education": [
        "exam", "admit card", "result", "college", "university", "school",
        "course", "assignment", "scholarship", "fees", "syllabus", "hostel",
        "attendance", "marks", "semester", "tuition",
    ],
    "employment": [
        "job", "hiring", "interview", "resume", "cv", "offer letter", "hr",
        "recruitment", "internship", "work from home", "vacancy", "salary",
        "appointment", "employer", "candidate",
    ],
    "government": [
        "aadhaar", "pan", "tax", "gst", "passport", "voter id", "government",
        "subsidy", "election", "police", "court", "ration", "scheme", "epfo",
        "ministry", "department",
    ],
    "healthcare": [
        "hospital", "doctor", "appointment", "prescription", "medicine",
        "clinic", "insurance claim", "ambulance", "lab report", "blood",
        "vaccine", "covid", "diagnostic", "pharmacy", "health",
    ],
    "technology": [
        "app", "software", "update", "download", "login", "password",
        "verification code", "device", "account access", "browser", "version",
        "patch", "link", "security alert", "session", "two-factor",
    ],
    "personal_communication": [
        "hello", "hi", "how are you", "talk", "meeting", "lunch", "family",
        "friend", "party", "birthday", "miss you", "call me", "message",
        "chat", "catching up", "good morning", "good evening",
    ],
    "business": [
        "invoice", "contract", "proposal", "client", "vendor", "purchase order",
        "payment due", "business", "partnership", "agreement", "tender",
        "meeting", "conference", "stakeholder", "revenue",
    ],
    "social_media": [
        "instagram", "facebook", "whatsapp", "telegram", "follow", "like",
        "subscribe", "channel", "viral", "dm", "tweet", "post", "hashtag",
        "influencer", "reel", "story",
    ],
}

_CONTEXT_RE: dict[str, re.Pattern] = {
    domain: re.compile(
        r"\b(" + "|".join(sorted(phrases, key=len, reverse=True)) + r")\b",
        re.IGNORECASE,
    )
    for domain, phrases in _CONTEXT_LEXICONS.items()
}

# ================================================================== topics
_TOPIC_LEXICONS: dict[str, list[str]] = {
    "Payment": [
        "pay", "payment", "transfer", "send money", "upi", "neft", "imps",
        "wallet", "due", "outstanding", "remit", "credited", "received money",
        "paid", "settlement",
    ],
    "Prize": [
        "win", "won", "prize", "lottery", "lucky draw", "reward", "cash prize",
        "jackpot", "winner",
    ],
    "Investment": [
        "invest", "investment", "mutual fund", "stock", "trading", "sip",
        "returns", "profit", "crypto", "bitcoin", "nft", "shares", "dividend",
    ],
    "Loan": [
        "loan", "emi", "credit", "borrow", "interest rate", "sanction",
        "lender", "mortgage", "personal loan", "pre-approved",
    ],
    "Delivery": [
        "delivery", "shipped", "dispatch", "courier", "parcel", "package",
        "tracking", "delivered", "out for delivery", "delivery failed",
        "delivery date",
    ],
    "Verification": [
        "verify", "verification", "otp", "confirm", "kyc", "validate",
        "account confirm", "one-time password", "authenticate", "security code",
    ],
    "Account": [
        "account", "login", "sign in", "password reset", "account blocked",
        "account suspended", "credentials", "user id", "recover account",
        "access restored",
    ],
    "Promotion": [
        "offer", "discount", "sale", "deal", "promo", "coupon", "exclusive",
        "limited period", "festive sale", "clearance", "special price",
    ],
    "Meeting": [
        "meeting", "call", "schedule", "appointment", "conference", "webinar",
        "sync up", "reschedule", "agenda", "catch up", "connect",
    ],
    "Education": [
        "exam", "admit card", "result", "course", "class", "tutorial",
        "assignment", "study", "syllabus", "marks", "scholarship", "lecture",
    ],
    "Support": [
        "help", "support", "assistance", "query", "complaint", "ticket",
        "troubleshooting", "customer care", "helpline", "issue resolved",
    ],
    "Travel": [
        "flight", "booking", "ticket", "trip", "hotel", "boarding pass",
        "itinerary", "reservation", "cancellation", "cab", "travel",
    ],
    "Communication": [
        "message", "chat", "reply", "call", "contact", "talk", "conversation",
        "dm", "ping", "message received", "missed call",
    ],
}

_TOPIC_RE: dict[str, re.Pattern] = {
    topic: re.compile(
        r"\b(" + "|".join(sorted(phrases, key=len, reverse=True)) + r")\b",
        re.IGNORECASE,
    )
    for topic, phrases in _TOPIC_LEXICONS.items()
}

# ================================================================= entities
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_URL_RE = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
_PHONE_RE = re.compile(r"(?<![A-Za-z0-9])(?:\+?\d[\d\s\-().]{7,}\d)(?![A-Za-z0-9])")
_MONEY_RE = re.compile(
    r"(?:Rs\.?|INR|USD|EUR|GBP|JPY|\$|€|£|₹)\s?\d[\d,]*(?:\.\d+)?"
    r"|\d[\d,]*\.?\d*\s?(?:rs\.?|inr|usd|euros?|pounds?|dollars?|rupees?)",
    re.IGNORECASE,
)
_MONTH_NAMES = (
    r"jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?|ember)?|oct(?:ober)?|"
    r"nov(?:ember)?|dec(?:ember)?"
)
_DATE_RE = re.compile(
    r"\b\d{4}-\d{2}-\d{2}\b"
    r"|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"
    r"|\b\d{1,2}(?:st|nd|rd|th)?\s+(?:" + _MONTH_NAMES + r")\s+\d{2,4}\b"
    r"|\b(?:" + _MONTH_NAMES + r")\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{2,4}\b"
    r"|\b\d{1,2}(?:st|nd|rd|th)?\s+(?:" + _MONTH_NAMES + r")\b"
    r"|\b(?:" + _MONTH_NAMES + r")\s+\d{1,2}(?:st|nd|rd|th)?\b",
    re.IGNORECASE,
)
_TIME_RE = re.compile(
    r"\b(?:[01]?\d|2[0-3]):[0-5]\d(?:\s?(?:am|pm|hrs))?\b"
    r"|\b(?:[01]?\d|2[0-3]):[0-5]\d:[0-5]\d\b"
    r"|\b\d{1,2}\s?(?:am|pm)\b",
    re.IGNORECASE,
)
_ACCOUNT_RE = re.compile(
    r"(?:account|acc|a/c|acct)(?:\s*(?:no\.?|number|num))?\s*[:#]?\s*"
    r"([A-Z0-9]{4,20})",
    re.IGNORECASE,
)
_TRACKING_RE = re.compile(
    r"(?:tracking|awb|waybill|track)(?:\s*(?:no\.?|number|num))?\s*[:#]?\s*"
    r"([A-Z0-9]{6,24})",
    re.IGNORECASE,
)
_UPS_TRACKING_RE = re.compile(r"\b1Z[A-Z0-9]{16}\b", re.IGNORECASE)
_FEDEX_TRACKING_RE = re.compile(r"\b\d{12}\b")
_ORG_RE = re.compile(
    r"\b(?:[A-Z][A-Za-z0-9&.'-]*\s+)+(?:Bank|Banks|Ltd|Limited|Corp|Corporation|"
    r"Inc|Pvt|Pvt\.\s*Ltd|Company|Foundation|University|Hospital|Group|"
    r"Industries|Technologies|Systems|Services)\b"
)
_PERSON_RE = re.compile(
    r"\b(?:Mr|Mrs|Ms|Dr|Prof|Sri|Shri|Smt|Er|Capt|Col)\.?\s+"
    r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b"
)
_GREETING_NAME_RE = re.compile(
    r"\b(?:Dear|Hi|Hello)\s+([A-Z][a-zA-Z'-]+(?:\s+[A-Z][a-zA-Z'-]+)?)\b"
)
_LOCATION_SUFFIX_RE = re.compile(
    r"\b(?:[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\s+"
    r"(?:Street|St|Road|Rd|Avenue|Ave|Nagar|City|Colony|Town|Village|"
    r"Basti|Chowk|Marg)\b"
)
_CITY_GAZETTEER = [
    "mumbai", "delhi", "new delhi", "bengaluru", "bangalore", "hyderabad",
    "chennai", "kolkata", "pune", "ahmedabad", "jaipur", "lucknow", "noida",
    "gurugram", "gurgaon", "chandigarh", "bhopal", "indore", "patna",
    "kathmandu", "dhaka", "colombo", "london", "new york", "san francisco",
    "los angeles", "chicago", "singapore", "dubai", "toronto", "sydney",
    "berlin", "paris", "tokyo", "seoul", "mexico city", "sao paulo", "nairobi",
]
_CITY_RE = re.compile(
    r"\b(" + "|".join(sorted(_CITY_GAZETTEER, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)

_ENTITY_TYPES: tuple[str, ...] = (
    "email", "url", "phone", "money", "date", "time",
    "account_number", "tracking_number", "organization", "bank", "company",
    "person", "location",
)

_BANK_WORDS = {"bank", "banks"}
_COMPANY_WORDS = {
    "ltd", "limited", "corp", "corporation", "inc", "pvt", "company",
    "industries", "technologies", "systems", "group",
}


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


# ================================================================ pipeline
class SemanticPipeline:
    """Orchestrates the semantic understanding stages."""

    def __init__(self, embeddings: EmbeddingService | None = None) -> None:
        self.embeddings = embeddings or embedding_service

    # -------------------------------------------------------------- input
    def _resolve_input(
        self,
        *,
        message: str | None,
        message_type: str,
        subject: str | None,
        sender: str | None,
        body: str | None,
        email_raw: str | None,
    ) -> dict[str, str]:
        message_type = (message_type or "text").lower()
        if email_raw:
            parsed = parse_raw_email(email_raw)
            combined = " ".join(
                p for p in (parsed["subject"], parsed["body"]) if p
            ).strip()
            return {
                "full_text": combined,
                "subject": parsed["subject"],
                "sender": parsed["sender"],
                "body": parsed["body"],
                "message_type": "email",
            }
        if message_type == "email":
            subject = subject or ""
            body = body or ""
            combined = " ".join(p for p in (subject, body) if p).strip()
            return {
                "full_text": combined,
                "subject": subject,
                "sender": sender or "",
                "body": body,
                "message_type": "email",
            }
        text = message or ""
        return {
            "full_text": text,
            "subject": "",
            "sender": "",
            "body": "",
            "message_type": message_type or "text",
        }

    # ------------------------------------------------------------ contexts
    def detect_contexts(self, text: str) -> list[SemanticContext]:
        hits: dict[str, int] = {}
        for domain, pattern in _CONTEXT_RE.items():
            count = len(pattern.findall(text))
            if count:
                hits[domain] = count
        if not hits:
            return [SemanticContext(domain=_UNKNOWN, confidence=0.8)]
        ranked = sorted(hits.items(), key=lambda item: item[1], reverse=True)
        best = ranked[0][1]
        contexts = []
        for domain, count in ranked[:4]:
            confidence = _clamp(0.45 + 0.12 * count / max(best, 1))
            contexts.append(SemanticContext(domain=domain, confidence=confidence))
        return contexts

    # -------------------------------------------------------------- topics
    def extract_topics(self, text: str) -> list[SemanticTopic]:
        hits: dict[str, int] = {}
        for topic, pattern in _TOPIC_RE.items():
            count = len(pattern.findall(text))
            if count:
                hits[topic] = count
        if not hits:
            return []
        ranked = sorted(hits.items(), key=lambda item: item[1], reverse=True)
        best = ranked[0][1]
        topics = []
        for topic, count in ranked[:4]:
            confidence = _clamp(0.45 + 0.12 * count / max(best, 1))
            topics.append(SemanticTopic(topic=topic, confidence=confidence))
        return topics

    # ------------------------------------------------------------ entities
    def _add_entity(
        self,
        entities: list[SemanticEntity],
        *,
        etype: str,
        value: str,
        confidence: float,
        normalized: str | None = None,
        attributes: dict | None = None,
    ) -> None:
        value = value.strip()
        if not value:
            return
        for existing in entities:
            if existing.type == etype and existing.value.lower() == value.lower():
                return
        entities.append(
            SemanticEntity(
                type=etype,
                value=value,
                normalized=normalized or value,
                confidence=_clamp(confidence),
                attributes=attributes or {},
            )
        )

    def extract_entities(self, text: str, sender: str = "") -> list[SemanticEntity]:
        entities: list[SemanticEntity] = []
        # exact patterns (high confidence)
        for match in _EMAIL_RE.finditer(text):
            self._add_entity(
                entities, etype="email", value=match.group(0),
                normalized=match.group(0).lower(), confidence=0.95,
            )
        for match in _URL_RE.finditer(text):
            raw = match.group(0).rstrip(".,;:!?)>]}")
            self._add_entity(
                entities, etype="url", value=raw,
                normalized=raw.rstrip("/").lower(), confidence=0.95,
            )
        for match in _PHONE_RE.finditer(text):
            raw = match.group(0)
            digits = re.sub(r"\D", "", raw)
            if len(digits) < 7:
                continue
            self._add_entity(
                entities, etype="phone", value=raw, normalized=digits,
                confidence=0.92,
            )
        for match in _MONEY_RE.finditer(text):
            self._add_entity(
                entities, etype="money", value=match.group(0),
                normalized=re.sub(r"\s+", "", match.group(0).lower()),
                confidence=0.93,
            )
        for match in _DATE_RE.finditer(text):
            self._add_entity(entities, etype="date", value=match.group(0),
                             confidence=0.9)
        for match in _TIME_RE.finditer(text):
            self._add_entity(entities, etype="time", value=match.group(0),
                             confidence=0.9)
        for match in _ACCOUNT_RE.finditer(text):
            code = match.group(1)
            if re.fullmatch(r"[A-Za-z0-9]{6,20}", code) and not re.fullmatch(
                r"[0-9]{6,20}", code
            ) or (code.isdigit() and len(code) >= 8):
                self._add_entity(
                    entities, etype="account_number", value=match.group(0),
                    normalized=code.upper(), confidence=0.88,
                )
        for match in _TRACKING_RE.finditer(text):
            code = match.group(1)
            if re.fullmatch(r"[A-Za-z0-9]{6,24}", code):
                self._add_entity(
                    entities, etype="tracking_number", value=match.group(0),
                    normalized=code.upper(), confidence=0.88,
                )
        for match in _UPS_TRACKING_RE.finditer(text):
            self._add_entity(
                entities, etype="tracking_number", value=match.group(0),
                normalized=match.group(0).upper(), confidence=0.92,
            )
        for match in _FEDEX_TRACKING_RE.finditer(text):
            self._add_entity(
                entities, etype="tracking_number", value=match.group(0),
                normalized=match.group(0), confidence=0.85,
            )
        # organization-like entities (medium confidence, case-sensitive)
        for match in _ORG_RE.finditer(text):
            name = match.group(0).strip()
            lower = name.lower()
            if any(w in lower for w in _BANK_WORDS):
                self._add_entity(
                    entities, etype="bank", value=name, normalized=lower,
                    confidence=0.8,
                )
            elif any(w in lower for w in _COMPANY_WORDS):
                self._add_entity(
                    entities, etype="company", value=name, normalized=lower,
                    confidence=0.75,
                )
            else:
                self._add_entity(
                    entities, etype="organization", value=name,
                    normalized=lower, confidence=0.7,
                )
        # people (medium confidence)
        for match in _PERSON_RE.finditer(text):
            self._add_entity(
                entities, etype="person", value=match.group(0).strip(),
                normalized=match.group(0).strip().lower(), confidence=0.6,
            )
        for match in _GREETING_NAME_RE.finditer(text):
            self._add_entity(
                entities, etype="person", value=match.group(1),
                normalized=match.group(1).lower(), confidence=0.55,
            )
        # locations (medium confidence)
        for match in _LOCATION_SUFFIX_RE.finditer(text):
            self._add_entity(
                entities, etype="location", value=match.group(0).strip(),
                normalized=match.group(0).strip().lower(), confidence=0.55,
            )
        for match in _CITY_RE.finditer(text):
            self._add_entity(
                entities, etype="location", value=match.group(1),
                normalized=match.group(1).lower(), confidence=0.65,
            )
        # sender address may carry an organization/person
        if sender:
            email_match = _EMAIL_RE.search(sender)
            if email_match:
                self._add_entity(
                    entities, etype="email", value=email_match.group(0),
                    normalized=email_match.group(0).lower(), confidence=0.9,
                )
            name_part = _EMAIL_RE.sub("", sender).strip(" <>\"").strip()
            if name_part and re.search(r"[A-Za-z]", name_part):
                self._add_entity(
                    entities, etype="organization", value=name_part,
                    normalized=name_part.lower(), confidence=0.5,
                )
        self._dedupe_phones(entities)
        return entities

    @staticmethod
    def _dedupe_phones(entities: list[SemanticEntity]) -> None:
        """Drop phone entities that are digit-substrings of account or
        tracking numbers (those patterns are more specific)."""
        coded_values = [
            re.sub(r"\D", "", e.normalized or e.value)
            for e in entities
            if e.type in {"account_number", "tracking_number", "date"}
            and re.sub(r"\D", "", e.normalized or e.value)
        ]
        if not coded_values:
            return
        kept: list[SemanticEntity] = []
        for entity in entities:
            if entity.type == "phone":
                digits = re.sub(r"\D", "", entity.value)
                if any(digits and digits in code for code in coded_values):
                    continue
            kept.append(entity)
        entities[:] = kept

    # ------------------------------------------------------------ features
    def compute_features(
        self,
        text: str,
        sentences: list[str],
        entities: list[SemanticEntity],
    ) -> SemanticFeatures:
        lowered = text.lower()
        counts = {t: sum(1 for e in entities if e.type == t) for t in (
            "url", "email", "phone", "money", "date", "time",
        )}
        return SemanticFeatures(
            message_length=len(text),
            word_count=len(text.split()),
            sentence_count=len(sentences),
            question_count=sum(1 for s in sentences if is_question_sentence(s)),
            imperative_count=sum(1 for s in sentences if is_imperative_sentence(s)),
            emoji_count=len(extract_emojis(text)),
            url_count=counts["url"],
            email_count=counts["email"],
            phone_count=counts["phone"],
            money_count=counts["money"],
            date_count=counts["date"],
            time_count=counts["time"],
            has_request=bool(re.search(r"\b(please|kindly|request|need you to|"
                                       r"require|asking you|urge)\b", lowered)),
            has_offer=bool(re.search(r"\b(free|win|won|prize|offer|discount|"
                                     r"exclusive|gift|reward|bonus|cashback)\b",
                                     lowered)),
            has_urgency=bool(re.search(r"\b(urgent|immediately|asap|hurry|"
                                       r"deadline|expires?|final notice|"
                                       r"within \d+ hours|act now)\b", lowered)),
            has_financial_reference=bool(re.search(r"\b(bank|account|balance|"
                                                   r"transfer|payment|loan|"
                                                   r"emi|upi|wallet|refund|"
                                                   r"invoice|salary|tax)\b",
                                                   lowered)),
            has_credential_request=bool(re.search(r"\b(password|passcode|otp|"
                                                  r"pin|credential|login|"
                                                  r"verify|verification|"
                                                  r"aadhaar|ssn|pan)\b",
                                                  lowered)),
            has_personal_information_request=bool(
                re.search(r"\b(dob|date of birth|address|cvv|cvc|"
                          r"card number|bank details|mother'?s name)\b",
                          lowered)
            ),
        )

    # --------------------------------------------------------- confidence
    def _estimate_confidence(
        self,
        language_confidence: float,
        contexts: list[SemanticContext],
        topics: list[SemanticTopic],
        entities: list[SemanticEntity],
    ) -> SemanticConfidence:
        context_conf = max((c.confidence for c in contexts), default=0.0)
        topic_conf = max((t.confidence for t in topics), default=0.0)
        if entities:
            entity_conf = max((e.confidence for e in entities), default=0.0)
        else:
            entity_conf = 0.0
        return SemanticConfidence(
            language=language_confidence,
            context=context_conf,
            topic=topic_conf,
            entity=entity_conf,
        )

    # ------------------------------------------------------------- embeddings
    def _embed(self, text: str, sentences: list[str], subject: str, body: str) -> dict[str, list]:
        payload: dict[str, list] = {}
        payload["message"] = self.embeddings.embed_one(text)
        payload["sentences"] = self.embeddings.embed(
            [s for s in sentences if s.strip()]
        )
        if subject:
            payload["subject"] = self.embeddings.embed_one(subject)
        if body:
            payload["body"] = self.embeddings.embed_one(body)
        return payload

    # -------------------------------------------------------------- analyze
    def analyze(
        self,
        *,
        message: str | None = None,
        message_type: str = "text",
        subject: str | None = None,
        sender: str | None = None,
        body: str | None = None,
        email_raw: str | None = None,
        include_embeddings: bool = True,
    ) -> SemanticAnalysisResult:
        resolved = self._resolve_input(
            message=message,
            message_type=message_type,
            subject=subject,
            sender=sender,
            body=body,
            email_raw=email_raw,
        )
        full_text = resolved["full_text"].strip()
        normalized = preprocess_text(full_text)

        language, language_conf = detect_language(normalized)
        sentences = segment_sentences(full_text)
        contexts = self.detect_contexts(full_text)
        topics = self.extract_topics(full_text)
        entities = self.extract_entities(full_text, sender=resolved["sender"])
        features = self.compute_features(full_text, sentences, entities)
        confidence = self._estimate_confidence(language_conf, contexts, topics, entities)

        embeddings: dict[str, list] = {}
        dimension = self.embeddings.dimension if include_embeddings else 0
        if include_embeddings:
            embeddings = self._embed(normalized, sentences, resolved["subject"], resolved["body"])

        return SemanticAnalysisResult(
            language=language,
            contexts=contexts,
            topics=topics,
            entities=entities,
            embedding_dimension=dimension,
            embeddings=embeddings,
            semantic_features=features,
            confidence=confidence,
            embedding_provider=self.embeddings.provider,
            message_preview=(normalized or full_text)[:80],
        )
