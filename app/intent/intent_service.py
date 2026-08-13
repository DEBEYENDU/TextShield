"""Sender intent detection.

Identifies one or more probable sender intentions with confidence and
supporting evidence. Detection is rule-based (deterministic) but not
keyword-only: every detector combines marker hits with structural gates
drawn from the semantic features (requestive ratio, entities, topics,
language, style signals), so a keyword alone rarely fires a detection.

The service implements the :class:`DetectorStrategy` contract so a future
model-based detector can be swapped in without touching the pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from app.intent.models import DetectedItem
from app.intent.utils import (
    AnalysisContext,
    all_caps_ratio,
    clamp,
    compile_word_patterns,
    entity_types,
    hit_confidence,
    requestive_ratio,
    round_conf,
    topic_names,
)
from app.semantic.semantic_models import SemanticFeatures

MARKETING_TOKENS = {
    "offer", "offers", "deal", "deals", "discount", "sale", "coupon",
    "promo", "promotion", "promotions", "shop", "buy", "purchase",
    "exclusive", "limited", "free", "prize", "win", "won", "cashback",
    "reward", "rewards", "gift", "voucher",
}
PROMOTION_TOKENS = {
    "contest", "campaign", "event", "sponsor", "subscribe", "follow",
    "featured", "hurry", "join", "launch", "unveil", "new",
}
INFORMAL_TOKENS = {
    "hi", "hey", "yo", "lol", "haha", "gonna", "wanna", "gotta", "pls",
    "u ", "r u", "ur", "thx", "ttyl", "btw", "idk", "omg", "cool", "nice",
}
FORMAL_TOKENS = {
    "kindly", "regarding", "pursuant", "herewith", "compliance",
    "regulations", "department", "official", "authorities", "accordingly",
    "therefore", "furthermore", "sincerely", "regards", "as per",
}
ACCOUNT_TOKENS = {
    "account", "acc", "a/c", "acct", "savings", "current", "balance",
    "card", "netbanking", "wallet",
}
APP_TOKENS = {
    "app", "application", "apk", "software", "plugin", "extension",
    "browser", "update", "installer", "setup",
}


@dataclass(frozen=True)
class IntentSpec:
    name: str
    patterns: tuple[re.Pattern, ...]
    gate: Callable[[AnalysisContext], bool] | None = None
    boost: Callable[[AnalysisContext], float] | None = None


def _any_pat(*words: str) -> tuple[re.Pattern, ...]:
    return compile_word_patterns(*words)


# ------------------------------------------------------------ gates

def _requestive(ctx: AnalysisContext) -> bool:
    feats: SemanticFeatures = ctx.semantic.semantic_features
    return bool(feats.has_request) or requestive_ratio(ctx) > 0.15


def _has_credential_feature(ctx: AnalysisContext) -> bool:
    return bool(ctx.semantic.semantic_features.has_credential_request)


def _has_pii_feature(ctx: AnalysisContext) -> bool:
    return bool(ctx.semantic.semantic_features.has_personal_information_request)


def _has_financial(ctx: AnalysisContext) -> bool:
    feats: SemanticFeatures = ctx.semantic.semantic_features
    return bool(feats.has_financial_reference or feats.money_count)


def _has_phone_or_email(ctx: AnalysisContext) -> bool:
    types = entity_types(ctx)
    return bool({"phone", "email"} & types)


def _has_url(ctx: AnalysisContext) -> bool:
    return "url" in entity_types(ctx)


def _has_account(ctx: AnalysisContext) -> bool:
    return bool(ctx.tokens & ACCOUNT_TOKENS) or "Account" in topic_names(ctx)


def _has_app(ctx: AnalysisContext) -> bool:
    return bool(ctx.tokens & APP_TOKENS)


def _informational(ctx: AnalysisContext) -> bool:
    return not _requestive(ctx)


# ------------------------------------------------------------ boosts

def _urgency_boost(ctx: AnalysisContext) -> float:
    feats: SemanticFeatures = ctx.semantic.semantic_features
    boost = all_caps_ratio(ctx.normalized) * 0.06
    if ctx.normalized.count("!") >= 2:
        boost += 0.05
    if feats.has_urgency:
        boost += 0.05
    return clamp(boost)


def _excitement_boost(ctx: AnalysisContext) -> float:
    feats: SemanticFeatures = ctx.semantic.semantic_features
    return clamp(feats.emoji_count * 0.04 + (0.05 if "!" in ctx.normalized else 0))


def _conversational_boost(ctx: AnalysisContext) -> float:
    feats: SemanticFeatures = ctx.semantic.semantic_features
    return clamp(feats.question_count * 0.05 + feats.emoji_count * 0.02)


def _marketing_boost(ctx: AnalysisContext) -> float:
    if ctx.tokens & MARKETING_TOKENS:
        return 0.04
    return 0.0


def _social_gate(ctx: AnalysisContext) -> bool:
    feats: SemanticFeatures = ctx.semantic.semantic_features
    return bool(feats.question_count) or bool(ctx.tokens & INFORMAL_TOKENS)


# ------------------------------------------------------------ specs

INTENT_SPECS: tuple[IntentSpec, ...] = (
    IntentSpec("Inform", _any_pat(
        r"inform\w*", r"information", r"notice", r"update\w*", r"status",
        r"regarding", r"about your", r"schedule", r"timings", r"available",
        r"details of", r"in case of",
    ), gate=_informational),
    IntentSpec("Notify", _any_pat(
        r"your (?:order|payment|shipment|delivery|account|appointment|subscription|"
        r"booking|application|request|parcel|card)",
        r"has been (?:shipped|delivered|approved|received|scheduled|confirmed|"
        r"updated|processed|dispatched|accepted|rejected)",
        r"transaction (?:successful|failed|declined|approved)",
        r"credited|debited", r"missed call", r"intimation",
        r"due (?:date|payment|amount)", r"reminder:", r"status:",
        r"will be delivered", r"out for delivery", r"auto-?debit",
        r"your (?:otp|verification code|code) (?:is|for)",
    )),
    IntentSpec("Advertise", _any_pat(
        r"introducing", r"discover", r"new (?:product|arrival|collection|range|"
        r"model|launch)", r"exclusive", r"launch(?:ed|ing)?", r"unveil\w*",
        r"check out (?:our|the)", r"visit our (?:website|store|showroom)",
        r"our brand", r"limited edition",
    ), boost=_marketing_boost),
    IntentSpec("Promote", _any_pat(
        r"promotion\w*", r"contest", r"event", r"campaign", r"sponsor\w*",
        r"featured", r"follow us", r"subscribe", r"like (?:and|&) share",
        r"tag a friend", r"join (?:us|our|the)", r"share with",
        r"spread the word",
    ), boost=_marketing_boost),
    IntentSpec("Sell", _any_pat(
        r"buy\w*", r"purchase", r"order (?:now|today|yours)", r"shop\w*",
        r"pre-?order", r"add to cart", r"book (?:your )?(?:slot|seat|ticket|"
        r"now)", r"checkout", r"on sale", r"get yours", r"for sale",
    ), boost=_marketing_boost),
    IntentSpec("Request Payment", _any_pat(
        r"pay\w*", r"payment", r"remit", r"transfer (?:money|funds)", r"send money",
        r"upi|neft|imps|rtgs", r"bank transfer", r"settle (?:the )?(?:amount|"
        r"dues|bill)", r"outstanding", r"due amount", r"payable", r"recharge",
        r"contribute", r"donate",
    ), gate=lambda ctx: _has_financial(ctx) or _requestive(ctx),
       boost=_urgency_boost),
    IntentSpec("Request Credentials", _any_pat(
        r"password", r"passcode", r"credentials?", r"login (?:details|id)",
        r"log in details", r"sign-?in", r"sign in", r"username",
        r"reset (?:your )?password", r"re-?authenticate",
    ), gate=lambda ctx: _has_credential_feature(ctx) or _requestive(ctx)),
    IntentSpec("Request OTP", _any_pat(
        r"share (?:the|your|this)? ?(?:otp|code)", r"send (?:me|us|the|your)? ?"
        r"(?:otp|code)", r"enter (?:the )?(?:otp|code)", r"provide (?:the|your) "
        r"(?:otp|code)", r"what is your (?:otp|code)", r"forward (?:the|your) "
        r"(?:otp|code)", r"give (?:me|us) (?:the|your)? ?(?:otp|code)",
        r"tell (?:me|us) the (?:otp|code)", r"confirm (?:the )?(?:otp|code)",
        r"reply with (?:your|the)? ?(?:otp|code)",
    ), gate=_requestive,
       boost=lambda ctx: 0.05 if "otp" in ctx.tokens else 0.0),
    IntentSpec("Request Personal Information", _any_pat(
        r"aadha?ar", r"pan card", r"date of birth", r"\bdob\b", r"address proof",
        r"identity proof", r"\bkyc\b", r"personal details", r"bank statement",
        r"upload (?:your )?(?:photo|selfie|id|documents)", r"voter id",
        r"passport", r"gstin", r"contact details", r"family details",
    ), gate=lambda ctx: _has_pii_feature(ctx) or _requestive(ctx)),
    IntentSpec("Request Verification", _any_pat(
        r"verify\w*", r"verification", r"confirm (?:your|the) (?:account|"
        r"identity|details)", r"validate", r"authenticate", r"complete (?:your )?"
        r"kyc", r"activate (?:your )?account", r"security check", r"identity check",
    ), gate=_requestive),
    IntentSpec("Request Contact", _any_pat(
        r"call (?:us|now|me|this number)", r"contact (?:us|me|our)",
        r"contact number", r"reach (?:us|out)", r"whatsapp",
        r"text (?:us|me)", r"reply (?:yes|stop|1|2|\bno\b)", r"toll-?free",
        r"helpline", r"support (?:line|desk)", r"send (?:us )?(?:an? )?(?:email|"
        r"message)", r"inbox us", r"dm us", r"\bcall\b",
    ), gate=lambda ctx: _has_phone_or_email(ctx) or _requestive(ctx),
       boost=lambda ctx: 0.05 if _has_phone_or_email(ctx) else 0.0),
    IntentSpec("Request Download", _any_pat(
        r"download (?:the|our|this)? ?(?:app|file|document|pdf|report|apk|"
        r"update|brochure)", r"get the app", r"download now",
    ), gate=lambda ctx: _has_url(ctx) or "download" in ctx.tokens),
    IntentSpec("Request Installation", _any_pat(
        r"install\w*", r"installation", r"set up (?:the )?app",
        r"enable (?:app|plugin|extension)", r"update (?:your )?app",
        r"run the (?:setup|installer)",
    ), gate=_has_app),
    IntentSpec("Request Account Update", _any_pat(
        r"update (?:your )?(?:account|details|profile|information|address|"
        r"phone number|email)", r"renew (?:your )?(?:subscription|policy|plan)",
        r"upgrade (?:your )?account", r"your account (?:has|is) (?:been )?"
        r"(?:suspended|blocked|locked|expiring)",
        r"your (?:bank )?account (?:will|has|is) (?:be )?(?:blocked|suspended|"
        r"locked|expiring|reactivated)", r"reactivate (?:your )?account",
        r"keep your account (?:active|safe)",
    ), gate=_has_account),
    IntentSpec("Offer Reward", _any_pat(
        r"you (?:have )?won", r"congratulations?", r"prize", r"gift (?:card|"
        r"voucher)", r"cashback", r"reward\w*", r"bonus", r"lucky (?:winner|"
        r"draw)", r"raffle", r"jackpot", r"free (?:gift|trip|iphone|laptop|"
        r"prize|voucher)", r"win\w* (?:a|an|the) (?:prize|reward|gift)",
    ), boost=_excitement_boost),
    IntentSpec("Offer Discount", _any_pat(
        r"discount", r"offers?", r"deal\w*", r"sale", r"coupon", r"promo code",
        r"flat \d+\s?%", r"\d+\s?% off", r"bogo", r"buy one get one",
        r"clearance", r"reduced", r"special (?:price|offer)",
    ), boost=_marketing_boost),
    IntentSpec("Offer Job", _any_pat(
        r"job", r"vacanc\w*", r"hiring", r"recruit\w*", r"position (?:open|"
        r"available)", r"salary", r"work from home", r"part-?time",
        r"full-?time", r"internship", r"career", r"fresher", r"job opening",
        r"we are (?:hiring|looking for)",
    )),
    IntentSpec("Threaten", _any_pat(
        r"will be (?:blocked|suspended|cancelled|deactivated|terminated|seized|"
        r"frozen)", r"legal action", r"court", r"arrest", r"prosecut\w*",
        r"police (?:case|complaint)", r"recovery (?:agent|team)", r"blacklist",
        r"your (?:account|card) (?:will|has|is|has been|was)? ?(?:be )?"
        r"(?:blocked|suspended|cancelled|deactivated|terminated|seized|frozen|"
        r"locked|at risk)", r"action will be taken",
        r"non-?compliance", r"compulsory", r"mandatory", r"fine of",
        r"penalty", r"imprisonment",
    ), boost=_urgency_boost),
    IntentSpec("Warn", _any_pat(
        r"warning", r"caution", r"alert", r"security (?:risk|threat|warning|"
        r"breach|alert)", r"fraud (?:alert|warning)", r"be careful", r"beware",
        r"do not share", r"unauthorized", r"suspicious", r"compromised",
        r"phishing", r"do not (?:click|respond|share|reveal)", r"scam\w*",
    )),
    IntentSpec("Create Curiosity", _any_pat(
        r"guess what", r"you won't believe", r"secret", r"surprise",
        r"find out", r"click (?:here )?to (?:find out|see|know)", r"don't miss",
        r"curious\b", r"what's inside", r"open (?:this|the|me)", r"shocking",
        r"unbelievable", r"too good to be true", r"you'll never guess",
    ), boost=_conversational_boost),
    IntentSpec("Create Urgency", _any_pat(
        r"urgent\w*", r"immediately", r"immediate", r"\basap\b", r"right now",
        r"now only", r"today only", r"only today", r"deadline", r"expires?",
        r"expiring", r"last chance", r"final (?:call|warning|reminder)",
        r"limited (?:time|period|offer)", r"act now", r"hurry", r"do not delay",
        r"before (?:midnight|tomorrow|end of day)", r"within 24 (?:hours|hrs)",
        r"expire\w*", r"ending (?:soon|today|tonight)",
    ), boost=_urgency_boost),
    IntentSpec("Social Conversation", _any_pat(
        r"how are you", r"how's it going", r"how have you been", r"what's up",
        r"\bhey\b", r"\bhi\b", r"\bhello\b", r"long time", r"miss you",
        r"let's meet", r"catch up", r"\blol\b", r"\bhaha\b", r"family",
        r"weekend plans", r"how is (?:your|the) (?:day|week|family)",
        r"hope you are (?:doing|feeling)",
    ), gate=_social_gate, boost=_conversational_boost),
    IntentSpec("Business Communication", _any_pat(
        r"meeting", r"agenda", r"client", r"invoice", r"proposal", r"contract",
        r"quarterly", r"project", r"conference call", r"business hours",
        r"office", r"colleague\w*", r"stakeholder\w*", r"minutes of",
        r"business (?:meeting|discussion)", r"partnership", r"vendor",
    )),
    IntentSpec("Education", _any_pat(
        r"class\w*", r"course\w*", r"lecture", r"admission\w*", r"exam\b",
        r"exams\b", r"examination\w*", r"test series", r"syllabus",
        r"assignment", r"homework", r"tuition", r"scholarship", r"webinar",
        r"seminar", r"workshop", r"study (?:group|material)", r"enrollment",
        r"academy", r"institute", r"learning", r"certification",
        r"student\w*", r"faculty",
    )),
    IntentSpec("Support", _any_pat(
        r"support", r"customer care", r"help desk", r"helpdesk",
        r"ticket (?:id|number)", r"issue with", r"problem with", r"not working",
        r"\berror\b", r"facing (?:an? )?issue", r"service request",
        r"complaint", r"troubleshoot", r"how do i", r"can you help",
        r"assist me", r"technical (?:support|assistance)", r"we are here to help",
        r"reach out to us", r"we apologize", r"resolve\w*",
    )),
)

_INTENT_ORDER = {spec.name: index for index, spec in enumerate(INTENT_SPECS)}


class IntentService:
    """Deterministic sender-intent detector (implements DetectorStrategy)."""

    name = "intent"

    def detect(
        self,
        ctx: AnalysisContext,
        *,
        threshold: float = 0.35,
        max_intents: int = 4,
    ) -> list[DetectedItem]:
        results: list[DetectedItem] = []
        for spec in INTENT_SPECS:
            hits = 0
            evidence: list[str] = []
            for pattern in spec.patterns:
                for match in pattern.finditer(ctx.lowercase):
                    hits += 1
                    snippet = match.group(0).strip()[:64]
                    if snippet and snippet not in evidence:
                        evidence.append(snippet)
                    if len(evidence) >= 3:
                        break
                if len(evidence) >= 3:
                    break
            if hits == 0:
                continue
            if spec.gate and not spec.gate(ctx):
                continue
            confidence = hit_confidence(hits, len(spec.patterns))
            if spec.boost:
                confidence += spec.boost(ctx)
            confidence = round_conf(confidence)
            if confidence < threshold:
                continue
            results.append(DetectedItem(name=spec.name, confidence=confidence, evidence=evidence[:3]))

        if not results:
            results.append(DetectedItem(name="Unknown", confidence=0.55, evidence=[]))

        results.sort(key=lambda item: (-item.confidence, _INTENT_ORDER.get(item.name, 99)))
        return results[:max_intents]


intent_service = IntentService()

__all__ = ["IntentService", "intent_service", "INTENT_SPECS", "IntentSpec"]
