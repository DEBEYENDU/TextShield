"""Contextual analysis: urgency, trust signals, conversation style and
communication goal.

These detectors read the semantic context (entities, topics, features,
sentences) in addition to marker words, keeping them structural rather
than purely keyword-driven.
"""

from __future__ import annotations

import re
from typing import Iterable

from app.intent.models import (
    CommunicationGoal,
    ConversationStyle,
    DetectedItem,
    UrgencyEstimate,
)
from app.intent.utils import (
    AnalysisContext,
    all_caps_ratio,
    clamp,
    compile_word_patterns,
    entity_types,
    hit_confidence,
    round_conf,
)


def _any_pat(*words: str) -> tuple[re.Pattern, ...]:
    return compile_word_patterns(*words)


def _hits(ctx: AnalysisContext, patterns: Iterable[re.Pattern], cap: int = 6) -> int:
    hits = 0
    for pattern in patterns:
        hits += sum(1 for _ in pattern.finditer(ctx.lowercase))
    return min(hits, cap)


def _evidence(
    ctx: AnalysisContext, patterns: Iterable[re.Pattern], limit: int = 3
) -> list[str]:
    found: list[str] = []
    for pattern in patterns:
        for match in pattern.finditer(ctx.lowercase):
            snippet = match.group(0).strip()[:64]
            if snippet and snippet not in found:
                found.append(snippet)
            if len(found) >= limit:
                return found
    return found


# ------------------------------------------------------------ urgency

URGENCY_PATTERNS = _any_pat(
    r"urgent\w*",
    r"immediately",
    r"immediate",
    r"\basap\b",
    r"right away",
    r"right now",
    r"act now",
    r"hurry\w*",
    r"today only",
    r"now only",
    r"last chance",
    r"expires?",
    r"expiring",
    r"deadline",
    r"final (?:call|" r"warning|notice|reminder)",
    r"limited (?:time|period|offer)",
    r"before (?:midnight|tomorrow|end of day)",
    r"within (?:24|48) (?:hours|hrs)",
    r"do not delay",
    r"emergency",
    r"as soon as possible",
    r"no delay",
    r"at once",
    r"time sensitive",
    r"must respond",
)
PRESSURE_PATTERNS = _any_pat(
    r"must (?:act|pay|respond|complete)",
    r"mandatory",
    r"compulsory",
    r"required\b",
    r"otherwise\b",
    r"or (?:else|your)",
    r"failure to",
    r"you need to (?:act|do)",
    r"no other option",
    r"will be (?:blocked|suspended|cancelled|deactivated|terminated|seized)",
    r"legal action",
    r"fine of",
    r"penalty",
    r"action will be taken",
)


def _urgency_score(ctx: AnalysisContext) -> tuple[float, list[str]]:
    """Raw urgency score 0-100 plus evidence snippets.

    Exclamation marks and ALL-CAPS text only count once genuine urgency
    language is present (or the message is overwhelmingly caps), so a
    single "!" in a friendly note never inflates urgency.
    """
    text = ctx.normalized
    hits = _hits(ctx, URGENCY_PATTERNS)
    evidence = _evidence(ctx, URGENCY_PATTERNS)
    pressure = _hits(ctx, PRESSURE_PATTERNS)
    caps = all_caps_ratio(text)
    exclaim = text.count("!")
    score = hits * 16 + pressure * 8
    if hits or caps > 0.5:
        score += exclaim * 4 + caps * 25
    score = min(100.0, score)
    if not evidence and pressure:
        evidence = _evidence(ctx, PRESSURE_PATTERNS, 2)
    return score, evidence


# ------------------------------------------------------- trust signals

TRUST_SIGNAL_SPECS: dict[str, tuple[re.Pattern, ...]] = {
    "Official language": _any_pat(
        r"official\w*",
        r"kindly\b",
        r"regarding\b",
        r"regulations?",
        r"pursuant",
        r"herewith",
        r"compliance",
        r"department\b",
        r"authorities?",
        r"notified\b",
        r"as per (?:rules|regulations|policy)",
    ),
    "Government references": _any_pat(
        r"government\b",
        r"\brbi\b",
        r"income tax",
        r"ministry\b",
        r"police\b",
        r"election commission",
        r"municipal\b",
        r"tax (?:department|authority)",
        r"\bgst\b",
        r"central bank",
        r"statutory",
    ),
    "Bank references": _any_pat(
        r"your bank",
        r"bank\b",
        r"\bsbi\b",
        r"\bhdfc\b",
        r"\bicici\b",
        r"\baxis\b",
        r"\bpnb\b",
        r"\bcanara\b",
        r"\bbob\b",
        r"union bank",
        r"kotak",
        r"yes bank",
        r"banking\b",
        r"your (?:savings|current) account",
    ),
    "Professional tone": _any_pat(
        r"kindly\b",
        r"sincerely",
        r"regards\b",
        r"yours (?:faithfully|truly)",
        r"please be (?:informed|advised)",
        r"we (?:would|will|are) (?:like to|" r"be|glad)",
        r"appreciate\w*",
        r"courtesy",
    ),
    "Formal formatting": _any_pat(
        r"subject:",
        r"from:",
        r"dear\b",
        r"to whom it may concern",
        r"reference(?:s)?:?",
        r"no\.?:?",
        r"attachment\w*",
    ),
    "Personal greetings": _any_pat(
        r"dear (?:valued )?(?:customer|member|user|sir|madam)",
        r"dear mr",
        r"dear ms",
        r"dear dr",
        r"dear\s+[A-Z][a-z]+",
    ),
}
BRAND_TOKENS = {
    "amazon",
    "flipkart",
    "myntra",
    "ajio",
    "swiggy",
    "zomato",
    "uber",
    "ola",
    "netflix",
    "jio",
    "airtel",
    "vodafone",
    "vi ",
    "mtn",
    "samsung",
    "apple",
    "oneplus",
    "mi ",
    "realme",
    "nike",
    "adidas",
    "puma",
    "croma",
    "reliance",
    "tata",
    "infosys",
    "wipro",
    "google",
    "microsoft",
    "paytm",
    "phonepe",
    "google pay",
    "gpay",
}


class ContextService:
    """Urgency, trust signals, conversation style and communication goal."""

    name = "context"

    # ------------------------------------------------------- urgency

    def urgency(
        self, ctx: AnalysisContext, *, threshold: float = 0.30
    ) -> UrgencyEstimate:
        score, evidence = _urgency_score(ctx)
        confidence = round_conf(
            clamp(0.3 + score / 200.0 + (0.15 if evidence else 0.0))
        )
        if score > 0 and confidence < threshold:
            confidence = threshold
        if score <= 0:
            level = "none"
        elif score < 25:
            level = "low"
        elif score < 50:
            level = "medium"
        elif score < 75:
            level = "high"
        else:
            level = "critical"
        return UrgencyEstimate(
            level=level,
            score=round(score, 2),
            confidence=confidence,
            evidence=evidence[:4],
        )

    # ------------------------------------------------- trust signals

    def trust_signals(
        self, ctx: AnalysisContext, *, threshold: float = 0.30
    ) -> list[DetectedItem]:
        results: list[DetectedItem] = []
        types = entity_types(ctx)
        text_lower = ctx.lowercase

        if "bank" in types and "Bank references" not in results:
            results.append(
                DetectedItem(name="Bank references", confidence=0.85, evidence=[])
            )

        for name, patterns in TRUST_SIGNAL_SPECS.items():
            hits = _hits(ctx, patterns)
            if hits == 0:
                continue
            confidence = round_conf(
                hit_confidence(hits, len(patterns), base=0.38, boost=0.15)
            )
            if confidence < threshold:
                continue
            results.append(
                DetectedItem(
                    name=name, confidence=confidence, evidence=_evidence(ctx, patterns)
                )
            )

        brands_hit = [
            token for token in BRAND_TOKENS if f" {token.strip()} " in f" {text_lower} "
        ]
        if brands_hit and not any(s.name == "Brand references" for s in results):
            results.append(
                DetectedItem(
                    name="Brand references",
                    confidence=round_conf(0.6 + 0.05 * min(len(brands_hit), 3)),
                    evidence=brands_hit[:3],
                )
            )
        if "company" in types or "organization" in types:
            if not any(s.name == "Brand references" for s in results):
                results.append(
                    DetectedItem(name="Brand references", confidence=0.55, evidence=[])
                )

        if "person" in types and not any(
            s.name == "Personal greetings" for s in results
        ):
            results.append(
                DetectedItem(name="Personal greetings", confidence=0.6, evidence=[])
            )

        results.sort(key=lambda item: (-item.confidence, item.name))
        return results[:6]

    # ---------------------------------------------------------- style

    STYLE_SPECS: dict[str, tuple[re.Pattern, ...]] = {
        "Formal": _any_pat(
            r"kindly\b",
            r"regarding\b",
            r"pursuant",
            r"herewith",
            r"compliance",
            r"sincerely",
            r"regards\b",
            r"accordingly",
            r"therefore",
            r"furthermore",
            r"please be (?:informed|advised)",
        ),
        "Informal": _any_pat(
            r"\bhi\b",
            r"\bhey\b",
            r"\byo\b",
            r"\blol\b",
            r"\bhaha\b",
            r"gonna",
            r"wanna",
            r"gotta",
            r"\bpls\b",
            r"\bthx\b",
            r"\bomg\b",
            r"\bidk\b",
            r"\bbtw\b",
            r"what's up",
            r"how are you",
        ),
        "Marketing": _any_pat(
            r"offer\w*",
            r"deal\w*",
            r"discount",
            r"sale\b",
            r"coupon",
            r"cashback",
            r"exclusive",
            r"limited (?:time|offer)",
            r"shop now",
            r"buy now",
            r"don't miss",
        ),
        "Customer Support": _any_pat(
            r"support",
            r"customer care",
            r"help desk",
            r"how can we help",
            r"we apologize",
            r"resolve\w*",
            r"ticket\b",
            r"your (?:issue|" r"concern|complaint)",
            r"we are here to help",
        ),
        "Educational": _any_pat(
            r"course\w*",
            r"class\w*",
            r"admission\w*",
            r"exam\b",
            r"exams\b",
            r"examination\w*",
            r"webinar",
            r"seminar",
            r"workshop",
            r"lecture",
            r"study\b",
            r"assignment",
            r"tuition",
            r"scholarship",
            r"learn\w*",
        ),
        "Transactional": _any_pat(
            r"payment",
            r"transaction",
            r"order\b",
            r"invoice",
            r"receipt",
            r"bill\b",
            r"amount",
            r"balance",
            r"credited",
            r"debited",
            r"due date",
            r"statement",
        ),
        "Personal": _any_pat(
            r"how are you",
            r"family\b",
            r"your weekend",
            r"weekend (?:plans|" r"trip|party)",
            r"let's (?:meet|catch up)",
            r"how have you been",
            r"miss you",
            r"how's (?:life|it|your)",
        ),
        "Corporate": _any_pat(
            r"meeting\b",
            r"agenda\b",
            r"client\b",
            r"proposal\b",
            r"contract\b",
            r"quarterly",
            r"project\b",
            r"stakeholder",
            r"office\b",
            r"colleague",
            r"business hours",
        ),
        "Promotional": _any_pat(
            r"promotion\w*",
            r"contest\b",
            r"campaign\b",
            r"event\b",
            r"follow " r"us",
            r"subscribe",
            r"giveaway",
            r"featured\b",
            r"join us",
        ),
    }
    STYLE_PRIORITY: tuple[str, ...] = (
        "Formal",
        "Informal",
        "Marketing",
        "Customer Support",
        "Educational",
        "Transactional",
        "Personal",
        "Corporate",
        "Promotional",
    )

    def conversation_style(self, ctx: AnalysisContext) -> ConversationStyle:
        scores: dict[str, float] = {}
        evidence_map: dict[str, list[str]] = {}
        for style, patterns in self.STYLE_SPECS.items():
            hits = _hits(ctx, patterns)
            if hits:
                evidence_map[style] = _evidence(ctx, patterns)
            if style == "Informal":
                hits += ctx.semantic.semantic_features.emoji_count
            scores[style] = 0.25 + 0.12 * min(hits, 5)
        if ctx.semantic.semantic_features.emoji_count >= 2 and "Informal" in scores:
            scores["Informal"] += 0.08
        if scores.get("Formal", 0) > 0.25 and scores.get("Informal", 0) > 0.25:
            if scores["Formal"] >= scores["Informal"]:
                scores["Formal"] += 0.1
        best = max(
            self.STYLE_PRIORITY,
            key=lambda s: (scores.get(s, 0.0), -self.STYLE_PRIORITY.index(s)),
        )
        confidence = round_conf(clamp(scores[best], 0.25, 0.95))
        if confidence < 0.3:
            best = "Unknown"
            confidence = 0.35
        return ConversationStyle(
            style=best, confidence=confidence, evidence=evidence_map.get(best, [])[:3]
        )

    # ------------------------------------------------------------ goal

    def communication_goal(
        self,
        ctx: AnalysisContext,
        intents: list[DetectedItem],
        behaviors: list[DetectedItem],
        trust_signals: list[DetectedItem],
        manipulation: list[DetectedItem] | None = None,
    ) -> CommunicationGoal:
        manipulation = manipulation or []
        intent_names = {item.name for item in intents}
        behavior_names = {item.name for item in behaviors}

        def candidates() -> list[tuple[str, float, list[str]]]:
            cred = intent_names & {
                "Request Credentials",
                "Request OTP",
                "Request Personal Information",
                "Request Verification",
                "Request Account Update",
            }
            if cred:
                conf = max(
                    (i.confidence for i in intents if i.name in cred), default=0.6
                )
                yield "Obtain Credentials", conf, sorted(cred)[:3]
            if intent_names & {"Request Payment", "Sell"} or behavior_names & {
                "Financial Request"
            }:
                conf = max(
                    [
                        i.confidence
                        for i in intents
                        if i.name in {"Request Payment", "Sell"}
                    ]
                    + [
                        b.confidence for b in behaviors if b.name == "Financial Request"
                    ],
                    default=0.6,
                )
                yield "Complete Transaction", conf, []
            if (
                intent_names & {"Request Personal Information"}
                or "Information Collection" in behavior_names
            ):
                conf = max(
                    [
                        i.confidence
                        for i in intents
                        if i.name == "Request Personal Information"
                    ]
                    + [
                        b.confidence
                        for b in behaviors
                        if b.name == "Information Collection"
                    ],
                    default=0.6,
                )
                yield "Collect Information", conf, []
            if (
                intent_names & {"Request Download", "Create Curiosity"}
                or "External Redirection" in behavior_names
            ):
                conf = max(
                    [
                        i.confidence
                        for i in intents
                        if i.name in {"Request Download", "Create Curiosity"}
                    ]
                    + [
                        b.confidence
                        for b in behaviors
                        if b.name == "External Redirection"
                    ],
                    default=0.6,
                )
                yield "Drive Website Traffic", conf, []
            if len(trust_signals) >= 2 and any(
                s.name
                in {
                    "Official language",
                    "Bank references",
                    "Brand references",
                    "Professional tone",
                }
                for s in trust_signals
            ):
                yield "Build Trust", round_conf(
                    max(s.confidence for s in trust_signals) * 0.9
                ), [s.name for s in trust_signals[:3]]
            if "Threaten" in intent_names or any(
                t.name == "Fear" for t in manipulation
            ):
                conf = max(
                    [i.confidence for i in intents if i.name in {"Threaten", "Warn"}]
                    + [m.confidence for m in manipulation if m.name == "Fear"],
                    default=0.7,
                )
                yield "Create Fear", conf, []
            if intent_names & {"Offer Reward", "Offer Discount", "Offer Job"}:
                conf = max(
                    (
                        i.confidence
                        for i in intents
                        if i.name in {"Offer Reward", "Offer Discount", "Offer Job"}
                    ),
                    default=0.6,
                )
                yield "Offer Opportunity", conf, []
            if intent_names & {"Social Conversation", "Create Curiosity"} and (
                ctx.semantic.semantic_features.question_count
            ):
                conf = max(
                    (
                        i.confidence
                        for i in intents
                        if i.name in {"Social Conversation", "Create Curiosity"}
                    ),
                    default=0.5,
                )
                yield "Continue Conversation", conf, []

        best = None
        for goal, conf, evidence in candidates():
            if best is None or conf > best[1]:
                best = (goal, conf, evidence)
        if best is None:
            return CommunicationGoal(
                goal="Share Information", confidence=0.5, evidence=[]
            )
        goal, conf, evidence = best
        return CommunicationGoal(
            goal=goal,
            confidence=round_conf(clamp(conf * 0.92, 0.35, 0.95)),
            evidence=evidence,
        )


context_service = ContextService()

__all__ = ["ContextService", "context_service"]
