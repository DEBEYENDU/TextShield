"""Behavior analysis.

Describes the behavioral characteristics of a message: financial
requests, credential requests, external redirection, information
collection, conversation continuation, marketing activity, etc.

Behaviors are descriptive — the engine never labels a behavior as
"good" or "bad".
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from app.intent.models import DetectedItem
from app.intent.utils import (
    AnalysisContext,
    compile_word_patterns,
    entity_types,
    hit_confidence,
    requestive_ratio,
    round_conf,
)


def _any_pat(*words: str) -> tuple[re.Pattern, ...]:
    return compile_word_patterns(*words)


@dataclass(frozen=True)
class BehaviorSpec:
    name: str
    patterns: tuple[re.Pattern, ...]
    gate: Callable[[AnalysisContext], bool] | None = None
    boost: Callable[[AnalysisContext], float] | None = None


def _requestive(ctx: AnalysisContext) -> bool:
    return bool(ctx.semantic.semantic_features.has_request) or requestive_ratio(ctx) > 0.15


def _has_money(ctx: AnalysisContext) -> bool:
    return "money" in entity_types(ctx) or bool(ctx.semantic.semantic_features.has_financial_reference)


def _has_url(ctx: AnalysisContext) -> bool:
    return "url" in entity_types(ctx)


def _has_questions(ctx: AnalysisContext) -> bool:
    return ctx.semantic.semantic_features.question_count >= 2


def _has_date(ctx: AnalysisContext) -> bool:
    return bool({"date", "time"} & entity_types(ctx))


BEHAVIOR_SPECS: tuple[BehaviorSpec, ...] = (
    BehaviorSpec("Financial Request", _any_pat(
        r"pay\w*", r"payment", r"transfer (?:money|funds)", r"send money",
        r"upi|neft|imps|rtgs", r"bank details", r"account number",
        r"card (?:number|details|cvv)", r"due amount", r"outstanding",
        r"bill", r"fee", r"recharge", r"donation",
    ), gate=lambda ctx: _has_money(ctx) or _requestive(ctx),
       boost=lambda ctx: 0.06 if _has_money(ctx) else 0.0),
    BehaviorSpec("Credential Request", _any_pat(
        r"share (?:your|the|this|me)? ?(?:password|passcode|pin|otp|code|"
        r"credentials)", r"enter (?:your|the)? ?(?:password|passcode|pin|otp|"
        r"code|credentials)", r"send (?:me|us|your|the)? ?(?:password|passcode|"
        r"pin|otp|code)", r"provide (?:your|the)? ?(?:password|passcode|pin|"
        r"otp|code|credentials)", r"tell (?:me|us) (?:your|the)? ?(?:otp|"
        r"password|code|pin)", r"what is your (?:otp|password|code|pin)",
        r"forward (?:me|the|this|your)? ?(?:otp|code)", r"give (?:me|us) "
        r"(?:the|your)? ?(?:otp|code|password)", r"confirm (?:your )?password",
        r"verify your (?:otp|password)", r"re-?enter your (?:otp|code)",
        r"one[- ]?time password",
    ), gate=_requestive,
       boost=lambda ctx: 0.05 if ctx.semantic.semantic_features.has_credential_request else 0.0),
    BehaviorSpec("Authentication Request", _any_pat(
        r"login to (?:your|the)", r"log in (?:to|with|using)", r"sign-?in to",
        r"sign in to", r"login here", r"authenticate (?:yourself|your)",
        r"enter (?:your )?credentials", r"verify (?:your )?(?:login|"
        r"credentials|identity)", r"session (?:expired|timed out)",
        r"two-?factor", r"2[- ]?fa\b", r"biometric",
    ), gate=_requestive),
    BehaviorSpec("Identity Verification", _any_pat(
        r"kyc\b", r"identity (?:verification|proof)", r"verify (?:your )?"
        r"(?:identity|id)", r"aadhaar", r"pan card", r"proof of (?:identity|"
        r"address)", r"selfie", r"document verification", r"e-?kyc",
    )),
    BehaviorSpec("External Redirection", _any_pat(
        r"click", r"tap (?:here|this)", r"open (?:the|this|our)? ?(?:link|url|"
        r"website|page)", r"visit (?:our|the)? ?(?:website|site|link)",
        r"follow (?:the|this) link", r"go to (?:our|this|the)",
        r"redirect", r"scanned? (?:this )?qr",
    ), gate=_has_url, boost=lambda ctx: 0.08 if _has_url(ctx) else 0.0),
    BehaviorSpec("Information Collection", _any_pat(
        r"share (?:your|some|more) (?:details|information)", r"tell (?:us|me)"
        r" (?:about|your)", r"enter (?:your )?(?:details|information)",
        r"fill (?:out|in)? (?:the|this)? ?(?:form|details)", r"provide (?:your )?"
        r"details", r"update (?:your )?details", r"what is your",
        r"your (?:name|age|address|number)",
    ), gate=lambda ctx: _has_questions(ctx) or _requestive(ctx),
       boost=lambda ctx: 0.05 if ctx.semantic.semantic_features.question_count else 0.0),
    BehaviorSpec("Conversation Continuation", _any_pat(
        r"how are you", r"what's up", r"how have you been", r"let me know",
        r"get back to (?:me|us)", r"will you be", r"are you (?:free|available|"
        r"coming|interested)", r"want to (?:meet|talk|chat)", r"let's (?:meet|"
        r"talk|catch up|chat)", r"reply (?:back )?(?:soon|asap|to this)",
    ), gate=lambda ctx: _has_questions(ctx) or _requestive(ctx)),
    BehaviorSpec("Marketing", _any_pat(
        r"offer\w*", r"deal\w*", r"discount", r"sale", r"coupon", r"cashback",
        r"reward\w*", r"promo\w*", r"free (?:gift|trial|sample|shipping)",
        r"limited (?:time|offer|stock)", r"don't miss (?:out|this)",
        r"exclusive (?:offer|deal)", r"buy (?:now|one)", r"shop (?:now|today)",
    )),
    BehaviorSpec("Advertisement", _any_pat(
        r"introducing", r"discover", r"new (?:product|arrival|launch|range)",
        r"our (?:product|brand|collection)", r"visit our (?:website|store)",
        r"showroom", r"book (?:your|a)? ?(?:demo|slot|consultation)",
        r"featured", r"our latest", r"launch\w*",
    )),
    BehaviorSpec("Promotion", _any_pat(
        r"contest", r"campaign", r"event", r"sponsor", r"giveaway",
        r"follow us", r"subscribe", r"share (?:this|our) (?:post|page)",
        r"tag a friend", r"join (?:our|the|us)", r"stand a chance",
    )),
    BehaviorSpec("Appointment", _any_pat(
        r"appointment", r"book(?:ing)?", r"schedule", r"visit (?:us|our "
        r"(?:clinic|office|store))", r"consultation", r"check-?up", r"slot",
        r"reschedule", r"confirm (?:your )?(?:appointment|visit)",
        r"meeting (?:scheduled|booked)",
    ), gate=lambda ctx: _has_date(ctx) or "appointment" in ctx.tokens),
    BehaviorSpec("Reminder", _any_pat(
        r"reminder", r"due (?:date|payment|amount|tomorrow)", r"renewal",
        r"expir\w*", r"overdue", r"coming (?:due|up)", r"auto-?debit",
        r"payable (?:on|by|before)", r"valid (?:until|till|upto)",
        r"last (?:date|day) to", r"don't forget",
    )),
    BehaviorSpec("Support Conversation", _any_pat(
        r"support", r"help (?:me|us|with|desk)", r"customer care", r"issue",
        r"problem", r"not working", r"\berror\b", r"complaint", r"ticket",
        r"how do i", r"can you (?:help|assist)", r"technical (?:issue|support)",
        r"troubleshoot", r"refund (?:request|issue)", r"unable to",
    )),
    BehaviorSpec("Customer Service", _any_pat(
        r"customer (?:care|service|support)", r"helpline", r"toll-?free",
        r"service (?:center|centre|desk)", r"executive", r"our team",
        r"care team", r"complaint (?:number|cell)", r"we value (?:you|our "
        r"customers)", r"your satisfaction",
    )),
    BehaviorSpec("Personal Discussion", _any_pat(
        r"how are you", r"how's (?:your|it)", r"family", r"your weekend",
        r"weekend (?:plans|trip|party|hangout)", r"met (?:you|him|her)",
        r"let's (?:meet|catch up|hang out)", r"how have you been",
        r"how is life", r"miss(?:ed)? you", r"wanted to (?:talk|chat)",
    )),
)


class BehaviorService:
    """Deterministic behavior analyzer."""

    name = "behavior"

    def detect(self, ctx: AnalysisContext, *, threshold: float = 0.30) -> list[DetectedItem]:
        results: list[DetectedItem] = []
        for spec in BEHAVIOR_SPECS:
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

        results.sort(key=lambda item: (-item.confidence, item.name))
        return results[:8]


behavior_service = BehaviorService()

__all__ = ["BehaviorService", "behavior_service"]
