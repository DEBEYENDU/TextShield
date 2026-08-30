"""Psychological manipulation technique detection.

Detects techniques such as urgency, fear, reward, authority, scarcity,
pressure, social obligation and others — with confidence and supporting
evidence. Detection is descriptive: it reports the technique present,
never a judgment about the message's legitimacy.
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
    round_conf,
)


def _any_pat(*words: str) -> tuple[re.Pattern, ...]:
    return compile_word_patterns(*words)


@dataclass(frozen=True)
class TechniqueSpec:
    name: str
    patterns: tuple[re.Pattern, ...]
    boost: Callable[[AnalysisContext], float] | None = None


def _caps_boost(ctx: AnalysisContext) -> float:
    return clamp(all_caps_ratio(ctx.normalized) * 0.08)


def _emoji_boost(ctx: AnalysisContext) -> float:
    return clamp(ctx.semantic.semantic_features.emoji_count * 0.04)


def _has_url(ctx: AnalysisContext) -> bool:
    return "url" in entity_types(ctx)


TECHNIQUE_SPECS: tuple[TechniqueSpec, ...] = (
    TechniqueSpec(
        "Urgency",
        _any_pat(
            r"urgent\w*",
            r"immediately",
            r"asap",
            r"right now",
            r"act now",
            r"hurry",
            r"today only",
            r"last chance",
            r"expires?",
            r"deadline",
            r"do not delay",
            r"limited (?:time|offer)",
            r"before (?:midnight|" r"tomorrow)",
            r"within 24",
            r"final (?:call|warning)",
            r"now only",
        ),
        boost=lambda ctx: _caps_boost(ctx)
        + (0.05 if ctx.normalized.count("!") >= 2 else 0),
    ),
    TechniqueSpec(
        "Fear",
        _any_pat(
            r"will be (?:blocked|suspended|deactivated|terminated|cancelled|seized)",
            r"legal action",
            r"arrest",
            r"prosecut\w*",
            r"police case",
            r"court",
            r"fine of",
            r"penalty",
            r"lose (?:your|all)",
            r"risk (?:of )?(?:losing|" r"fraud|blocking)",
            r"your account (?:will|is|has|was|has been)? ?(?:be )?"
            r"(?:blocked|suspended|cancelled|frozen|seized|locked|compromised|at "
            r"risk)",
            r"compromised",
            r"breach\w*",
            r"blacklist\w*",
            r"imprisonment",
            r"seizure",
        ),
    ),
    TechniqueSpec(
        "Reward",
        _any_pat(
            r"you (?:have )?won",
            r"congratulations?",
            r"prize",
            r"gift\b",
            r"cashback",
            r"reward\w*",
            r"bonus",
            r"jackpot",
            r"lucky (?:winner|draw)",
            r"free (?:gift|trip|iphone|laptop)",
            r"voucher",
        ),
        boost=_emoji_boost,
    ),
    TechniqueSpec(
        "Greed",
        _any_pat(
            r"double (?:your|the) (?:money|income|returns)",
            r"earn (?:fast|" r"quick|easy) money",
            r"high returns",
            r"guaranteed (?:profit|returns)",
            r"passive income",
            r"millionaire",
            r"get rich",
            r"\d+% (?:interest|" r"returns)",
            r"multiply your",
            r"instant (?:cash|money)",
        ),
    ),
    TechniqueSpec(
        "Authority",
        _any_pat(
            r"official\w*",
            r"government",
            r"rbi\b",
            r"income tax",
            r"ministry",
            r"police\b",
            r"court\b",
            r"tax (?:department|authority)",
            r"regulatory",
            r"legal\b",
            r"bank (?:of india|headquarters)",
            r"authorized",
            r"election commission",
            r"municipal\b",
        ),
        boost=lambda ctx: (
            0.05 if ctx.semantic.semantic_features.has_financial_reference else 0.0
        ),
    ),
    TechniqueSpec(
        "Scarcity",
        _any_pat(
            r"limited (?:time|stock|offer|seats|slots)",
            r"only (?:a )?\d+ (?:left|" r"remaining|spots)",
            r"last (?:chance|day|few)",
            r"while stocks last",
            r"few (?:seats|slots|units) left",
            r"almost gone",
            r"selling fast",
            r"only (?:today|now)",
            r"closing (?:soon|tonight)",
        ),
    ),
    TechniqueSpec(
        "Curiosity",
        _any_pat(
            r"guess what",
            r"you won't believe",
            r"secret\b",
            r"surprise\b",
            r"find out",
            r"don't miss",
            r"shocking\b",
            r"unbelievable",
            r"too good to be true",
            r"you'll never guess",
            r"what's (?:inside|" r"behind)",
            r"click (?:here )?to (?:see|find out)",
        ),
    ),
    TechniqueSpec(
        "Trust",
        _any_pat(
            r"genuine\b",
            r"verified\b",
            r"trusted\b",
            r"trustworthy",
            r"secure\b",
            r"100% (?:safe|secure|genuine)",
            r"legitimate",
            r"official (?:bank|" r"partner)",
            r"registered\b",
            r"encrypted\b",
            r"guaranteed\b",
        ),
        boost=lambda ctx: 0.05 if "bank" in entity_types(ctx) else 0.0,
    ),
    TechniqueSpec(
        "Familiarity",
        _any_pat(
            r"your account",
            r"our records",
            r"as (?:you|we) know",
            r"your (?:card|" r"policy|subscription|loan)",
            r"dear (?:valued )?(?:customer|member)",
            r"you are (?:a|an) (?:valued|important)",
            r"we have your",
            r"your recent (?:purchase|transaction|order)",
        ),
    ),
    TechniqueSpec(
        "Friendliness",
        _any_pat(
            r"hi\b",
            r"hello\b",
            r"hey\b",
            r"hope you're (?:doing|having)",
            r"warm (?:greetings|wishes)",
            r"cheers\b",
            r"best wishes",
            r"have a (?:great|nice|good) (?:day|weekend)",
            r"lots of love",
            r"take care",
        ),
        boost=_emoji_boost,
    ),
    TechniqueSpec(
        "Pressure",
        _any_pat(
            r"must (?:act|pay|respond|complete)",
            r"required\b",
            r"mandatory",
            r"compulsory",
            r"otherwise\b",
            r"or (?:else|your)",
            r"no other option",
            r"you need to (?:act|do)",
            r"expected to",
            r"will (?:be|not) (?:able|" r"allowed) to",
            r"failure to (?:act|comply|respond)",
        ),
    ),
    TechniqueSpec(
        "Social Obligation",
        _any_pat(
            r"everyone (?:is|has)",
            r"as a (?:citizen|member|user)",
            r"your (?:" r"family|children|community) needs",
            r"help (?:us|your|the)",
            r"join " r"(?:everyone|others)",
            r"you (?:also )?have a responsibility",
            r"be a (?:part|member)",
            r"our (?:community|society) needs",
        ),
    ),
    TechniqueSpec(
        "Reciprocity",
        _any_pat(
            r"as a thank you",
            r"in return",
            r"because you (?:are|have)",
            r"we " r"appreciate",
            r"to thank (?:you|our)",
            r"for being (?:a|our)",
            r"in appreciation",
            r"you deserve",
            r"rewards for (?:you|being)",
        ),
    ),
    TechniqueSpec(
        "Guilt",
        _any_pat(
            r"you missed",
            r"you owe",
            r"you're (?:responsible|to blame)",
            r"you " r"haven't (?:paid|responded|replied)",
            r"your fault",
            r"don't let us " r"down",
            r"you failed",
            r"why haven't you",
        ),
    ),
    TechniqueSpec(
        "Hope",
        _any_pat(
            r"could be yours",
            r"your (?:chance|opportunity)",
            r"chance to (?:win|" r"earn|get)",
            r"opportunity of a lifetime",
            r"dream come true",
            r"imagine (?:your|having)",
            r"this could change",
            r"your future",
            r"finally (?:yours|your)",
            r"achieve your (?:dreams|goals)",
        ),
    ),
    TechniqueSpec(
        "Excitement",
        _any_pat(
            r"amazing\b",
            r"awesome\b",
            r"incredible\b",
            r"fantastic\b",
            r"wow\b",
            r"spectacular",
            r"mind[- ]blowing",
            r"thrilling",
            r"biggest\b",
            r"greatest\b",
            r"once-?in-?a-?lifetime",
        ),
        boost=lambda ctx: _emoji_boost(ctx) + (0.05 if "!" in ctx.normalized else 0),
    ),
)


class ManipulationService:
    """Deterministic psychological-manipulation technique detector."""

    name = "manipulation"

    def detect(
        self, ctx: AnalysisContext, *, threshold: float = 0.30
    ) -> list[DetectedItem]:
        results: list[DetectedItem] = []
        for spec in TECHNIQUE_SPECS:
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

        results.sort(key=lambda item: (-item.confidence, item.name))
        return results[:8]


manipulation_service = ManipulationService()

__all__ = ["ManipulationService", "manipulation_service"]
