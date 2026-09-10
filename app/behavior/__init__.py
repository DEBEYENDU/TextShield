"""Behavioral Analysis & Social Engineering Engine (v4.0 / RFC-004).

Detects HOW a message attempts to influence the recipient: psychological
manipulation, social-engineering personas, persuasion techniques, emotional
triggers, communication style and conversation patterns.

Another evidence provider — it never replaces existing components and never
classifies. Output feeds trust/threat scoring, RAG retrieval and the graph.
"""

from __future__ import annotations

__version__ = "4.0.0"
__rfc__ = "RFC-004"

PSYCHOLOGICAL_TECHNIQUES = [
    "Authority Bias",
    "Urgency",
    "Fear",
    "Scarcity",
    "Greed",
    "Curiosity",
    "Reciprocity",
    "Commitment",
    "Social Proof",
    "Loss Aversion",
    "Reward Seeking",
    "FOMO",
    "Sympathy",
    "Empathy Exploitation",
    "Trust Building",
    "Guilt",
    "Pressure",
    "Time Constraints",
]

SOCIAL_ENGINEERING_PERSONAS = [
    "Impersonation",
    "CEO Fraud",
    "Bank Representative",
    "Courier Executive",
    "Government Official",
    "Police",
    "Income Tax",
    "Customer Support",
    "HR",
    "Recruiter",
    "Friend",
    "Family",
    "Tech Support",
    "Marketplace Buyer",
    "Marketplace Seller",
]

COMMUNICATION_STYLES = [
    "Formal",
    "Informal",
    "Professional",
    "Corporate",
    "Academic",
    "Government",
    "Marketing",
    "Conversational",
    "Transactional",
    "Aggressive",
    "Manipulative",
    "Emotional",
    "Neutral",
]

EMOTIONS = [
    "Fear",
    "Excitement",
    "Happiness",
    "Curiosity",
    "Stress",
    "Pressure",
    "Trust",
    "Hope",
    "Greed",
    "Confusion",
    "Urgency",
    "Panic",
]
