"""Intent & Behavior Analysis Engine (Phase 6).

Consumes the Semantic Understanding Engine's structured output and
produces a behavioral profile: sender intents, requested actions,
behaviors, psychological manipulation techniques, urgency, trust
signals, conversation style and communication goal — with confidence
for every prediction.

The engine describes what the sender is trying to achieve; it NEVER
classifies (no spam/risk determination) and depends only on the
semantic module. Detectors implement the ``DetectorStrategy`` contract
so future model-based strategies can replace the rule-based defaults.
"""

from app.intent.pipeline import IntentPipeline, intent_pipeline

__all__ = ["IntentPipeline", "intent_pipeline"]
