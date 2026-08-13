"""Intent & Behavior Analysis Engine — orchestration pipeline.

Consumes the Semantic Understanding Engine's structured output and
produces a single behavioral profile (intents, requested actions,
behaviors, manipulation techniques, urgency, trust signals, style,
communication goal) with per-category confidence.

The semantic engine stays independent: intent only reads its result or
reuses its pipeline for preprocessing — it never re-implements it and
never classifies.
"""

from __future__ import annotations

from typing import Any, Sequence

from app.intent.action_service import ActionService, action_service
from app.intent.behavior_service import BehaviorService, behavior_service
from app.intent.context_service import ContextService, context_service
from app.intent.intent_service import IntentService, intent_service
from app.intent.manipulation_service import ManipulationService, manipulation_service
from app.intent.models import IntentAnalysisResult
from app.intent.utils import build_context
from app.semantic.semantic_models import SemanticAnalysisResult
from app.semantic.semantic_pipeline import SemanticPipeline


def _average(items: Sequence[Any]) -> float:
    if not items:
        return 0.0
    return round(sum(item.confidence for item in items) / len(items), 4)


class IntentPipeline:
    """Deterministic orchestrator of the intent & behavior services."""

    engine_version = "1.0.0"

    def __init__(
        self,
        intents: IntentService | None = None,
        actions: ActionService | None = None,
        behaviors: BehaviorService | None = None,
        manipulation: ManipulationService | None = None,
        context: ContextService | None = None,
        semantic_pipeline: SemanticPipeline | None = None,
    ) -> None:
        self.intents = intents or intent_service
        self.actions = actions or action_service
        self.behaviors = behaviors or behavior_service
        self.manipulation = manipulation or manipulation_service
        self.context = context or context_service
        self.semantic_pipeline = semantic_pipeline or SemanticPipeline()

    def analyze(
        self,
        message: str = "",
        *,
        message_type: str = "text",
        subject: str | None = None,
        sender: str | None = None,
        body: str | None = None,
        email_raw: str | None = None,
        semantic_result: SemanticAnalysisResult | None = None,
        intent_threshold: float | None = None,
        behavior_threshold: float | None = None,
        urgency_threshold: float | None = None,
        max_intents: int | None = None,
        **_: Any,
    ) -> IntentAnalysisResult:
        """Analyze a single message.

        ``semantic_result`` may be supplied from a previous semantic pass;
        otherwise the semantic pipeline is invoked internally (with
        embeddings disabled for throughput).
        """
        ctx = build_context(
            message=message,
            message_type=message_type,
            subject=subject,
            sender=sender,
            body=body,
            email_raw=email_raw,
            semantic_result=semantic_result,
            semantic_pipeline=self.semantic_pipeline,
        )

        from app.core.settings import settings

        threshold = intent_threshold if intent_threshold is not None else settings.INTENT_CONFIDENCE_THRESHOLD
        b_threshold = behavior_threshold if behavior_threshold is not None else settings.INTENT_BEHAVIOR_THRESHOLD
        u_threshold = urgency_threshold if urgency_threshold is not None else settings.INTENT_URGENCY_THRESHOLD
        max_n = max_intents if max_intents is not None else settings.INTENT_MAX_INTENTS

        intents = self.intents.detect(ctx, threshold=threshold, max_intents=max_n)
        actions = self.actions.detect(ctx, threshold=threshold)
        behaviors = self.behaviors.detect(ctx, threshold=b_threshold)
        manipulation = self.manipulation.detect(ctx, threshold=b_threshold)
        urgency = self.context.urgency(ctx, threshold=u_threshold)
        trust_signals = self.context.trust_signals(ctx, threshold=b_threshold)
        style = self.context.conversation_style(ctx)
        goal = self.context.communication_goal(ctx, intents, behaviors, trust_signals, manipulation)

        confidence: dict[str, float] = {
            "intents": _average(intents),
            "requested_actions": _average(actions),
            "behaviors": _average(behaviors),
            "manipulation": _average(manipulation),
            "urgency": urgency.confidence,
            "trust_signals": _average(trust_signals),
            "conversation_style": style.confidence,
            "communication_goal": goal.confidence,
        }

        return IntentAnalysisResult(
            intents=intents,
            requested_actions=actions,
            behaviors=behaviors,
            manipulation=manipulation,
            urgency=urgency,
            trust_signals=trust_signals,
            conversation_style=style,
            communication_goal=goal,
            confidence=confidence,
            language=ctx.semantic.language,
            engine_version=self.engine_version,
            message_preview=(ctx.semantic.message_preview or ctx.raw_text)[:80],
        )


intent_pipeline = IntentPipeline()

__all__ = ["IntentPipeline", "intent_pipeline"]
