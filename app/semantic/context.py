"""Context detection with transformer augmentation.

Extends existing lexicon-based context detection with transformer-based
confidence boosting.
"""

from __future__ import annotations

from app.semantic.semantic_pipeline import SemanticPipeline
from app.semantic.semantic_models import SemanticContext
from app.semantic.config import config
from app.semantic.transformer import similarity_score


_CONTEXT_DESCRIPTORS = {
    "banking": "bank account balance transfer OTP PIN KYC",
    "finance": "loan EMI investment mutual fund tax refund",
    "shopping": "order delivery tracking invoice purchase refund",
    "education": "exam admit card result college university scholarship",
    "employment": "job hiring interview resume offer letter recruitment",
    "government": "Aadhaar PAN passport voter ID tax subsidy scheme",
    "healthcare": "hospital doctor appointment prescription medicine clinic",
    "technology": "app software update download login password verification",
    "personal_communication": "hello hi meeting lunch family friend birthday",
    "business": "invoice contract proposal client vendor purchase order",
    "social_media": "instagram facebook whatsapp telegram follow like subscribe",
}


class ContextEngine:
    def __init__(self, pipeline: SemanticPipeline | None = None):
        self.pipeline = pipeline or SemanticPipeline()

    def detect(self, text: str) -> list[SemanticContext]:
        base_contexts = self.pipeline.detect_contexts(text)
        if not config.context.use_transformer_logits:
            return base_contexts[:config.context.max_contexts]
        boosted = []
        for ctx in base_contexts:
            descriptor = _CONTEXT_DESCRIPTORS.get(ctx.domain, "")
            if descriptor:
                try:
                    sim = similarity_score(text, descriptor)
                    ctx_conf = ctx.confidence + (sim * config.context.confidence_boost)
                    ctx_conf = max(0.0, min(1.0, ctx_conf))
                    boosted.append(SemanticContext(domain=ctx.domain, confidence=ctx_conf))
                    continue
                except Exception:
                    pass
            boosted.append(ctx)
        return boosted[:config.context.max_contexts]
