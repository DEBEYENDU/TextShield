"""Application-wide constants.

Central location for the fixed values that used to be scattered across
modules (risk levels, intent labels, severity ordering, limits). Risk
engine *weights* remain in settings; these are structural constants.
"""

from __future__ import annotations

# ------------------------------------------------------------- classification
SPAM = "SPAM"
HAM = "HAM"
CLASSIFICATION_VALUES = (SPAM, HAM)

# ------------------------------------------------------------- message types
MESSAGE_TYPES = ("sms", "text", "email")
DETECTED_TYPES = ("email", "text")

# ------------------------------------------------------------- risk levels
RISK_LOW = "LOW"
RISK_MEDIUM = "MEDIUM"
RISK_HIGH = "HIGH"
RISK_CRITICAL = "CRITICAL"
RISK_UNCERTAIN = "UNCERTAIN"
RISK_LEVELS = (RISK_LOW, RISK_MEDIUM, RISK_HIGH, RISK_CRITICAL, RISK_UNCERTAIN)

# ------------------------------------------------------------- severities
SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW = "low"
SEVERITY_ORDER = {SEVERITY_HIGH: 3, SEVERITY_MEDIUM: 2, SEVERITY_LOW: 1}

# ------------------------------------------------------------- intent labels
INTENT_CREDENTIAL_REQUEST = "credential_request"
INTENT_MONEY_TRANSFER = "money_transfer"
INTENT_DOWNLOAD_INSTALL = "download_install"
INTENT_PERSONAL_DATA = "personal_data"
INTENT_PRIZE_CLAIM = "prize_claim"
INTENT_CONFIRMATION_REQUEST = "confirmation_request"
INTENT_ENGAGEMENT = "engagement"
INTENT_OTHER = "other"
INTENT_LABELS = (
    INTENT_CREDENTIAL_REQUEST,
    INTENT_MONEY_TRANSFER,
    INTENT_DOWNLOAD_INSTALL,
    INTENT_PERSONAL_DATA,
    INTENT_PRIZE_CLAIM,
    INTENT_CONFIRMATION_REQUEST,
    INTENT_ENGAGEMENT,
    INTENT_OTHER,
)
# Intents that typically accompany social engineering (risk engine uses this).
MALICIOUS_INTENTS = {
    INTENT_CREDENTIAL_REQUEST,
    INTENT_MONEY_TRANSFER,
    INTENT_DOWNLOAD_INSTALL,
    INTENT_PERSONAL_DATA,
    INTENT_PRIZE_CLAIM,
}
# Intents severe enough to escalate SPAM verdicts to CRITICAL (PRD RZ-03).
CRITICAL_INTENTS = {
    INTENT_CREDENTIAL_REQUEST,
    INTENT_MONEY_TRANSFER,
    INTENT_DOWNLOAD_INSTALL,
}

# ------------------------------------------------------------- RAG categories
HIGH_RISK_RAG_CATEGORIES = {"banking_scams", "phishing", "investment_scams"}

# ------------------------------------------------------------- placeholders
PLACEHOLDER_PHONE = "[PHONE]"
PLACEHOLDER_EMAIL = "[EMAIL]"
PLACEHOLDER_URL = "[URL]"
PLACEHOLDER_MONEY = "[MONEY]"

# ------------------------------------------------------------- explanation
EXPLANATION_SOURCE_LLM = "llm"
EXPLANATION_SOURCE_TEMPLATE = "template"

# ------------------------------------------------------------- default limits
DEFAULT_MAX_MESSAGE_LENGTH = 10_000
DEFAULT_EMAIL_MAX_LENGTH = 20_000
DEFAULT_HISTORY_PREVIEW_LENGTH = 120
DEFAULT_PAGE_SIZE = 50

# ------------------------------------------------------------- health
STATUS_OK = "ok"
STATUS_DEGRADED = "degraded"
STATUS_READY = "ready"
STATUS_NOT_READY = "not_ready"
