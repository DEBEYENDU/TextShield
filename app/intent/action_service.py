"""Requested-action detection.

Determines what the recipient is expected to do (click a link, reply,
call, transfer money, provide an OTP, ...). Actions combine marker hits
with semantic entities (urls, phones, money) so that e.g. "call" alone
does not fire unless a callable channel exists.
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
class ActionSpec:
    name: str
    patterns: tuple[re.Pattern, ...]
    gate: Callable[[AnalysisContext], bool] | None = None
    boost: Callable[[AnalysisContext], float] | None = None


def _requestive(ctx: AnalysisContext) -> bool:
    return (
        bool(ctx.semantic.semantic_features.has_request) or requestive_ratio(ctx) > 0.15
    )


def _has_url(ctx: AnalysisContext) -> bool:
    return "url" in entity_types(ctx)


def _has_phone(ctx: AnalysisContext) -> bool:
    return "phone" in entity_types(ctx)


def _has_money(ctx: AnalysisContext) -> bool:
    return "money" in entity_types(ctx) or bool(
        ctx.semantic.semantic_features.has_financial_reference
    )


ACTION_SPECS: tuple[ActionSpec, ...] = (
    ActionSpec(
        "Click Link",
        _any_pat(
            r"click (?:here|on|this|the link)",
            r"tap (?:here|on|this)",
            r"open (?:this|the) link",
            r"follow this link",
            r"go to",
            r"press (?:here|the button)",
            r"click the button",
            r"via (?:this|the|our|following)? ?link",
            r"through (?:this|the|our)" r"? ?link",
            r"link:",
        ),
        gate=_has_url,
        boost=lambda ctx: 0.06 if _has_url(ctx) else 0.0,
    ),
    ActionSpec(
        "Visit Website",
        _any_pat(
            r"visit (?:our|the|this)? ?(?:website|site|portal|page)",
            r"check (?:our|the)? ?(?:website|site|portal)",
            r"see our",
            r"browse",
            r"view (?:our|the) site",
            r"go to our website",
        ),
        gate=_has_url,
    ),
    ActionSpec(
        "Reply",
        _any_pat(
            r"reply",
            r"respond",
            r"text back",
            r"reply (?:yes|stop|start|\bno\b|\d+)",
            r"answer (?:us|this|the)",
            r"type (?:yes|stop|\bno\b)",
            r"send (?:us )?(?:a )?reply",
            r"write back",
        ),
    ),
    ActionSpec(
        "Call Number",
        _any_pat(
            r"call (?:us|now|me|this number|the number)",
            r"phone (?:us|now)",
            r"ring (?:us|this number)",
            r"contact (?:us|me) (?:on|at)",
            r"reach us (?:at|on)",
            r"dial",
            r"\bcall\b",
        ),
        gate=_has_phone,
        boost=lambda ctx: 0.08 if _has_phone(ctx) else 0.0,
    ),
    ActionSpec(
        "Open Attachment",
        _any_pat(
            r"open (?:the )?(?:attachment|attached|enclosed)",
            r"attachment",
            r"attached (?:file|document|pdf|invoice)",
            r"see (?:the )?attachment",
            r"please find (?:the )?attachment",
            r"enclosed (?:file|document)",
        ),
    ),
    ActionSpec(
        "Download File",
        _any_pat(
            r"download (?:the )?(?:file|document|pdf|report|receipt|statement|app)",
            r"download now",
            r"get the (?:file|document|pdf)",
            r"save the (?:file|pdf)",
            r"download (?:your )?(?:receipt|statement|invoice)",
        ),
    ),
    ActionSpec(
        "Install Application",
        _any_pat(
            r"install (?:the |our )?(?:app|application|apk|software|update)",
            r"install now",
            r"set up (?:the )?app",
            r"enable (?:the )?app",
            r"update (?:your|the) app",
            r"install (?:our )?application",
        ),
    ),
    ActionSpec(
        "Transfer Money",
        _any_pat(
            r"transfer (?:money|funds|amount)",
            r"send (?:money|funds|the amount)",
            r"pay (?:now|today|the amount|us)",
            r"make a payment",
            r"pay the due",
            r"settle (?:the )?(?:amount|dues)",
            r"pay via (?:upi|neft|imps)",
            r"pay your (?:bill|fee|rent|installment)",
            r"recharge",
            r"\bpay\b",
        ),
        gate=_has_money,
        boost=lambda ctx: 0.06 if _has_money(ctx) else 0.0,
    ),
    ActionSpec(
        "Verify Identity",
        _any_pat(
            r"verify (?:your|the) (?:identity|id|account|details|phone|number)",
            r"complete (?:your )?kyc",
            r"confirm (?:your )?identity",
            r"update (?:your )?kyc",
            r"re-?verify",
            r"identity verification",
            r"validate (?:your|the) account",
        ),
    ),
    ActionSpec(
        "Provide OTP",
        _any_pat(
            r"share (?:the|your|this)? ?(?:otp|code|number)",
            r"send (?:the|your)? ?" r"(?:otp|code)",
            r"provide (?:the|your)? ?(?:otp|code)",
            r"enter (?:the )?" r"(?:otp|code)",
            r"tell (?:me|us) the (?:otp|code)",
            r"what is your otp",
            r"forward the (?:otp|code)",
            r"reply with (?:your|the)? ?(?:otp|code)",
            r"give (?:me|us) (?:the|your)? ?(?:otp|code)",
        ),
        boost=lambda ctx: 0.05 if "otp" in ctx.tokens else 0.0,
    ),
    ActionSpec(
        "Provide Password",
        _any_pat(
            r"share (?:your )?(?:password|pin|passcode|credentials)",
            r"enter (?:your )?" r"(?:password|pin|passcode)",
            r"send (?:your )?(?:password|pin)",
            r"provide (?:your )?(?:password|pin)",
            r"what is your (?:password|pin)",
            r"confirm (?:your )?password",
        ),
    ),
    ActionSpec(
        "Provide Banking Information",
        _any_pat(
            r"share (?:your )?(?:bank|card|account) details",
            r"enter (?:your )?" r"(?:card|cvv|bank) (?:number|details)",
            r"provide (?:your )?banking " r"(?:details|information)",
            r"send (?:your )?(?:card|account) details",
            r"confirm (?:your )?(?:card|account|bank) (?:details|number)",
        ),
    ),
    ActionSpec(
        "Provide Personal Information",
        _any_pat(
            r"share (?:your )?(?:aadhaar|pan|name|address|date of birth|details)",
            r"enter (?:your )?(?:name|address|aadhaar|pan|details)",
            r"provide (?:your )?" r"(?:details|aadhaar|pan|address)",
            r"upload (?:your )?(?:id|photo|" r"documents|proof)",
            r"send (?:your )?(?:aadhaar|pan|details)",
        ),
        gate=_requestive,
    ),
    ActionSpec(
        "Purchase Product",
        _any_pat(
            r"buy (?:now|it|this|one|the product)",
            r"purchase (?:now|it|this)",
            r"order (?:now|today|yours)",
            r"add to cart",
            r"book (?:now|your slot)",
            r"get (?:yours|it) (?:now|today)",
            r"shop now",
            r"checkout",
        ),
    ),
    ActionSpec(
        "Ignore",
        _any_pat(
            r"ignore",
            r"ignore this",
            r"disregard",
            r"delete (?:this|the) message",
            r"no action needed",
            r"do not respond",
        ),
    ),
)


class ActionService:
    """Deterministic requested-action detector."""

    name = "requested_action"

    def detect(
        self, ctx: AnalysisContext, *, threshold: float = 0.35
    ) -> list[DetectedItem]:
        results: list[DetectedItem] = []
        for spec in ACTION_SPECS:
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
            results.append(
                DetectedItem(
                    name=spec.name, confidence=confidence, evidence=evidence[:3]
                )
            )

        if not results:
            results.append(DetectedItem(name="No Action", confidence=0.6, evidence=[]))

        results.sort(key=lambda item: -item.confidence)
        return results[:6]


action_service = ActionService()

__all__ = ["ActionService", "action_service"]
