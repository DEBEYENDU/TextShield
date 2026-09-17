"""Intent & Message Understanding Engine (v4.0 / RFC-001).

Semantic message understanding that runs BEFORE classification: language
detection, message-type classification, intent detection, entity extraction,
legitimacy + threat indicator engines, evidence summary and a structured
message profile.

The legacy Spam/Ham classifier is untouched and remains the backward
compatible prediction authority; this package only adds understanding.
"""

from __future__ import annotations

__version__ = "4.0.0"
__rfc__ = "RFC-001"

MESSAGE_TYPES = [
    "Educational Announcement",
    "Recruitment",
    "Bank Notification",
    "Government Advisory",
    "Healthcare",
    "Courier / Logistics",
    "E-commerce",
    "Personal Communication",
    "OTP / Authentication",
    "Payment Confirmation",
    "Invoice",
    "Meeting Invitation",
    "Technical Support",
    "Promotional Advertisement",
    "Newsletter",
    "Social Media",
    "Subscription",
    "Travel",
    "Telecom",
    "Investment",
    "Unknown",
]

INTENTS = [
    "Inform",
    "Notify",
    "Authenticate",
    "Promote",
    "Request Action",
    "Collect Information",
    "Verify Identity",
    "Warn",
    "Congratulate",
    "Recruit",
    "Advertise",
    "Sell",
    "Support",
    "Survey",
    "Reminder",
    "Update",
]
