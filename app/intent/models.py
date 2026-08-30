"""Intent & Behavior Analysis Engine — data models and vocabularies.

The engine describes *what the sender is trying to achieve* and the
behavioral characteristics of a message. It never determines whether a
message is spam.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------- vocab

SENDER_INTENTS: tuple[str, ...] = (
    "Inform",
    "Notify",
    "Advertise",
    "Promote",
    "Sell",
    "Request Payment",
    "Request Credentials",
    "Request OTP",
    "Request Personal Information",
    "Request Verification",
    "Request Contact",
    "Request Download",
    "Request Installation",
    "Request Account Update",
    "Offer Reward",
    "Offer Discount",
    "Offer Job",
    "Threaten",
    "Warn",
    "Create Curiosity",
    "Create Urgency",
    "Social Conversation",
    "Business Communication",
    "Education",
    "Support",
    "Unknown",
)

REQUESTED_ACTIONS: tuple[str, ...] = (
    "Click Link",
    "Reply",
    "Call Number",
    "Open Attachment",
    "Visit Website",
    "Download File",
    "Install Application",
    "Transfer Money",
    "Verify Identity",
    "Provide OTP",
    "Provide Password",
    "Provide Banking Information",
    "Provide Personal Information",
    "Purchase Product",
    "Ignore",
    "No Action",
)

BEHAVIORS: tuple[str, ...] = (
    "Financial Request",
    "Credential Request",
    "Authentication Request",
    "Identity Verification",
    "External Redirection",
    "Information Collection",
    "Conversation Continuation",
    "Marketing",
    "Advertisement",
    "Promotion",
    "Appointment",
    "Reminder",
    "Support Conversation",
    "Customer Service",
    "Personal Discussion",
)

MANIPULATION_TECHNIQUES: tuple[str, ...] = (
    "Urgency",
    "Fear",
    "Reward",
    "Greed",
    "Authority",
    "Scarcity",
    "Curiosity",
    "Trust",
    "Familiarity",
    "Friendliness",
    "Pressure",
    "Social Obligation",
    "Reciprocity",
    "Guilt",
    "Hope",
    "Excitement",
)

URGENCY_LEVELS: tuple[str, ...] = ("none", "low", "medium", "high", "critical")

TRUST_SIGNAL_TYPES: tuple[str, ...] = (
    "Official language",
    "Brand references",
    "Government references",
    "Bank references",
    "Professional tone",
    "Formal formatting",
    "Personal greetings",
)

CONVERSATION_STYLES: tuple[str, ...] = (
    "Formal",
    "Informal",
    "Marketing",
    "Customer Support",
    "Educational",
    "Transactional",
    "Personal",
    "Corporate",
    "Promotional",
    "Unknown",
)

COMMUNICATION_GOALS: tuple[str, ...] = (
    "Share Information",
    "Collect Information",
    "Complete Transaction",
    "Obtain Credentials",
    "Drive Website Traffic",
    "Build Trust",
    "Create Fear",
    "Offer Opportunity",
    "Continue Conversation",
)

# ---------------------------------------------------------------- schema


class DetectedItem(BaseModel):
    """A detected signal with supporting evidence snippets."""

    name: str = Field(description="Detected item (intent/action/behavior/...)")
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(
        default_factory=list,
        description="Short textual snippets that support the detection",
    )


class UrgencyEstimate(BaseModel):
    level: Literal["none", "low", "medium", "high", "critical"]
    score: float = Field(ge=0.0, le=100.0, description="0-100 urgency score")
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)


class ConversationStyle(BaseModel):
    style: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)


class CommunicationGoal(BaseModel):
    goal: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)


class IntentAnalysisResult(BaseModel):
    """Structured behavioral profile of a single message.

    The engine only describes intent/behavior; it performs no
    classification and assigns no risk or spam probability.
    """

    intents: list[DetectedItem] = Field(default_factory=list)
    requested_actions: list[DetectedItem] = Field(default_factory=list)
    behaviors: list[DetectedItem] = Field(default_factory=list)
    manipulation: list[DetectedItem] = Field(default_factory=list)
    urgency: UrgencyEstimate = Field(
        default_factory=lambda: UrgencyEstimate(level="none", score=0.0, confidence=0.0)
    )
    trust_signals: list[DetectedItem] = Field(default_factory=list)
    conversation_style: ConversationStyle = Field(
        default_factory=lambda: ConversationStyle(style="Unknown", confidence=0.0)
    )
    communication_goal: CommunicationGoal = Field(
        default_factory=lambda: CommunicationGoal(
            goal="Share Information", confidence=0.0
        )
    )
    confidence: dict[str, float] = Field(
        default_factory=dict,
        description="Aggregate confidence per category (deterministic)",
    )
    language: str = Field(default="unknown")
    engine_version: str = Field(default="1.0.0")
    message_preview: str = Field(default="", description="First 80 chars of input")


# ---------------------------------------------------------- strategies


class DetectorStrategy:
    """Interface for a detector.

    Rule-based detectors are the default implementation; a future ML or
    LLM-based detector can replace a service by implementing the same
    ``detect(ctx)`` contract without touching the rest of the pipeline.
    """

    name: str = "base"

    def detect(self, ctx: "AnalysisContext") -> list[DetectedItem]:  # noqa: F821
        raise NotImplementedError
