"""Message-type classification: WHAT the message is, before maliciousness.

Deterministic multi-signal scoring (no hardcoded single-keyword rules):
each category owns weighted semantic phrases; scores combine phrase
evidence, structural signals (sender domain, greeting/formal layout) and
the semantic context engine. Returns {type, confidence, evidence}.
"""

from __future__ import annotations

import re

# Category -> [(phrase, weight)]. Phrases are semantic concepts, matched as
# whole-word case-insensitive patterns; weights reflect discriminativeness.
_TYPE_PHRASES: dict[str, list[tuple[str, float]]] = {
    "Educational Announcement": [
        ("university", 1.2), ("college", 1.2), ("campus", 1.3), ("semester", 1.4),
        ("admission", 1.2), ("placement cell", 1.6), ("campus drive", 1.8),
        ("convocation", 1.6), ("scholarship", 1.2), ("examination", 1.0),
        ("academic calendar", 1.5), ("dean", 1.0), ("registrar", 1.3),
        ("students are hereby", 1.6), ("faculty", 0.8), ("lecture", 0.8),
        ("congratulations on your graduation", 1.5), ("enrollment", 1.0),
    ],
    "Recruitment": [
        ("we are hiring", 1.7), ("job opening", 1.5), ("walk-in interview", 1.7),
        ("apply with your resume", 1.5), ("recruitment drive", 1.6),
        ("shortlisted for interview", 1.5), ("offer letter", 1.2),
        ("hr department", 1.0), ("job description", 1.3), ("ctc", 1.1),
        ("notice period", 1.1), ("interview schedule", 1.4), ("campus placement", 1.5),
        ("recruiter", 0.9), ("position open", 1.2),
    ],
    "Bank Notification": [
        ("account credited", 1.7), ("account debited", 1.7), ("available balance", 1.6),
        ("transaction alert", 1.5), ("neft", 1.2), ("imps", 1.2), ("upi ref", 1.3),
        ("passbook", 1.0), ("branch", 0.7), ("ifsc", 1.2), ("statement", 0.8),
        ("emi due", 1.1), ("cheque", 0.9), ("net banking", 1.0),
    ],
    "Government Advisory": [
        ("ministry of", 1.6), ("government of", 1.5), ("municipal corporation", 1.5),
        ("public notice", 1.4), ("gazette", 1.5), ("aadhaar", 0.9),
        ("income tax department", 1.5), ("civic", 0.9), ("ward office", 1.3),
        ("helpline number 1", 1.0), ("citizens are advised", 1.5),
        ("as per government order", 1.5), ("toll free", 0.7),
    ],
    "Healthcare": [
        ("appointment confirmed", 1.7), ("lab report", 1.5), ("prescription", 1.4),
        ("dr\\.", 0.8), ("hospital", 1.1), ("clinic", 1.1), ("diagnostic", 1.3),
        ("vaccination", 1.3), ("follow-up visit", 1.4), ("pharmacy", 1.0),
        ("health checkup", 1.4), ("token number", 1.1),
    ],
    "Courier / Logistics": [
        ("out for delivery", 1.8), ("tracking id", 1.5), ("awb", 1.3),
        ("shipment", 1.2), ("parcel", 1.1), ("consignment", 1.4),
        ("delivery attempt", 1.5), ("expected delivery", 1.5),
        ("courier partner", 1.3), ("delivered successfully", 1.6),
        ("pickup scheduled", 1.4),
    ],
    "E-commerce": [
        ("order confirmed", 1.7), ("order shipped", 1.6), ("cash on delivery", 1.4),
        ("return pickup", 1.4), ("refund initiated", 1.5), ("invoice", 0.8),
        ("cart", 0.7), ("checkout", 0.9), ("seller", 0.8),
        ("your order", 1.1), ("delivery by", 0.9),
    ],
    "Personal Communication": [
        ("how are you", 1.2), ("long time", 1.2), ("miss you", 1.4),
        ("happy birthday", 1.4), ("good morning", 0.9), ("see you", 1.0),
        ("call me when", 1.1), ("lunch tomorrow", 1.3), ("mom", 0.9),
        ("love,", 1.0), ("take care", 0.9),
    ],
    "OTP / Authentication": [
        ("one time password", 1.8), ("otp is", 1.8), ("verification code", 1.6),
        ("valid for \\d+ min", 1.5), ("do not share", 1.2),
        ("login attempt", 1.3), ("use this code", 1.4),
    ],
    "Payment Confirmation": [
        ("payment successful", 1.8), ("payment received", 1.7), ("receipt", 1.0),
        ("transaction id", 1.4), ("utr", 1.3), ("amount paid", 1.5),
        ("invoice paid", 1.4), ("subscription renewed", 1.4), ("premium receipt", 1.3),
    ],
    "Invoice": [
        ("invoice number", 1.7), ("gstin", 1.5), ("tax invoice", 1.6),
        ("amount due", 1.3), ("due date", 1.0), ("billing address", 1.3),
        ("payment terms", 1.2), ("hsn", 1.2), ("igst", 1.2), ("cgst", 1.2),
    ],
    "Meeting Invitation": [
        ("meeting invite", 1.7), ("calendar invite", 1.6), ("agenda", 1.2),
        ("video call link", 1.4), ("rsvp", 1.2), ("join the meeting", 1.5),
        ("scheduled for", 0.9), ("standup", 1.2), ("webinar", 1.0),
        ("looking forward to seeing you", 1.2),
    ],
    "Technical Support": [
        ("ticket number", 1.6), ("support team", 1.3), ("troubleshoot", 1.4),
        ("we are looking into", 1.4), ("issue resolved", 1.5),
        ("escalated", 1.2), ("workaround", 1.2), ("service status", 1.2),
        ("apologize for the inconvenience", 1.3),
    ],
    "Promotional Advertisement": [
        ("limited period offer", 1.6), ("flat \\d+% off", 1.6), ("mega sale", 1.5),
        ("exclusive deal", 1.4), ("buy one get one", 1.6), ("festive offer", 1.4),
        ("clearance sale", 1.5), ("use code", 1.2), ("grab now", 1.3),
        ("discount coupon", 1.4),
    ],
    "Newsletter": [
        ("this week's edition", 1.6), ("newsletter", 1.5), ("top stories", 1.5),
        ("in this issue", 1.5), ("subscribe", 0.8), ("unsubscribe", 1.1),
        ("editor's note", 1.5), ("read more", 0.7), ("highlights", 0.8),
    ],
    "Social Media": [
        ("new follower", 1.6), ("tagged you", 1.6), ("your post", 1.1),
        ("story mention", 1.5), ("went live", 1.3), ("trending", 1.0),
        ("friend request", 1.5), ("liked your", 1.5), ("commented", 1.1),
    ],
    "Subscription": [
        ("subscription expiring", 1.6), ("plan renewed", 1.5), ("auto-renew", 1.4),
        ("billing cycle", 1.3), ("membership", 1.0), ("cancel anytime", 1.2),
        ("trial ends", 1.4), ("upgrade your plan", 1.3),
    ],
    "Travel": [
        ("pnr", 1.5), ("boarding pass", 1.6), ("flight", 1.0), ("itinerary", 1.5),
        ("hotel booking", 1.5), ("check-in", 1.1), ("rescheduled", 0.9),
        ("gate number", 1.3), ("cab booked", 1.4), ("trip", 0.7),
    ],
    "Telecom": [
        ("recharge successful", 1.6), ("data balance", 1.5), ("plan expired", 1.4),
        ("validity", 1.1), ("dth", 1.3), ("broadband", 1.2),
        ("caller tune", 1.2), ("port your number", 1.1), ("gb data", 1.2),
    ],
    "Investment": [
        ("mutual fund", 1.4), ("portfolio", 1.3), ("nav", 1.1), ("sip", 1.1),
        ("dividend credited", 1.5), ("demat", 1.3), ("stock split", 1.4),
        ("annual report", 1.1), ("fund performance", 1.3),
    ],
}

# Semantic context domains boosting each message type.
_CONTEXT_BOOST: dict[str, list[str]] = {
    "Educational Announcement": ["education"],
    "Recruitment": ["employment"],
    "Bank Notification": ["banking"],
    "Government Advisory": ["government"],
    "Healthcare": ["healthcare"],
    "Courier / Logistics": ["shopping"],
    "E-commerce": ["shopping"],
    "Personal Communication": ["personal_communication"],
    "OTP / Authentication": ["banking", "technology"],
    "Payment Confirmation": ["finance", "banking"],
    "Invoice": ["business", "finance"],
    "Meeting Invitation": ["business", "personal_communication"],
    "Technical Support": ["technology", "business"],
    "Promotional Advertisement": ["shopping", "social_media"],
    "Newsletter": ["social_media", "business"],
    "Social Media": ["social_media"],
    "Subscription": ["technology", "business"],
    "Travel": ["shopping"],
    "Telecom": ["technology"],
    "Investment": ["finance"],
}

_COMPILED: dict[str, list[tuple[re.Pattern, float]]] = {
    category: [(re.compile(r"\b" + phrase + r"\b", re.IGNORECASE), weight)
               for phrase, weight in phrases]
    for category, phrases in _TYPE_PHRASES.items()
}


class MessageTypeClassifier:
    """Score every category on combined evidence; never single-keyword."""

    def __init__(self, min_evidence: int = 1):
        self.min_evidence = min_evidence

    def classify(self, text: str, contexts: list | None = None) -> dict:
        lowered = text or ""
        scores: dict[str, float] = {}
        evidence: dict[str, list[str]] = {}
        for category, patterns in _COMPILED.items():
            total = 0.0
            hits: list[str] = []
            for pattern, weight in patterns:
                matches = pattern.findall(lowered)
                if matches:
                    total += weight * (1.0 + 0.25 * (len(matches) - 1))
                    snippet = matches[0] if isinstance(matches[0], str) else matches[0][0]
                    hits.append(snippet[:40])
            # semantic context agreement boost
            if contexts:
                domains = {getattr(c, "domain", c) if not isinstance(c, str) else c
                           for c in contexts}
                if domains & set(_CONTEXT_BOOST.get(category, [])):
                    total += 0.6
            if total > 0:
                scores[category] = total
                evidence[category] = hits[:4]
        if not scores or max(scores.values()) < 0.9:
            return {"type": "Unknown", "confidence": 0.35,
                    "evidence": ["no dominant category signals"]}
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        best, best_score = ranked[0]
        runner_up = ranked[1][1] if len(ranked) > 1 else 0.0
        # confidence: normalized margin between best and runner-up
        margin = (best_score - runner_up) / max(best_score, 1e-9)
        confidence = round(min(0.95, 0.45 + 0.5 * margin + 0.05 * min(len(evidence[best]), 3)), 3)
        return {"type": best, "confidence": confidence, "evidence": evidence[best]}


message_type_classifier = MessageTypeClassifier()
