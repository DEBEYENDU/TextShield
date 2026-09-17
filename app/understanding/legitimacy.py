"""Legitimacy indicator engine — evidence supporting that a message is benign.

Each indicator contributes positive trust with a weight and quoted evidence.
Trust score in 0..1 = weighted positives / (weighted positives + 1).
"""

from __future__ import annotations

import re

# (name, weight, [patterns])
_TRUST_PATTERNS: list[tuple[str, float, list[str]]] = [
    ("named_organization", 1.2, [r"(?:from|at|team)\s+[A-Z][A-Za-z&., ]{2,40}"]),
    ("formal_greeting", 0.6, [r"^(?:dear|respected|hello)\s+[A-Z]", r"^dear\s+(customer|user|student|employee|valued)"]),
    ("formal_closing", 0.7, [r"(?:regards|sincerely|best regards|thank you|warm regards)[,.]?\s*$", r"customer care|helpdesk|support team"]),
    ("institutional_language", 1.0, [r"this is to inform", r"please be advised", r"as per", r"in accordance with", r"reference number", r"circular number"]),
    ("official_terminology", 0.8, [r"transaction id|utr|invoice number|gstin|acknowledgement|reference id|ticket number|token number"]),
    ("academic_announcement", 1.3, [r"university|college|campus|semester|convocation|placement cell"]),
    ("recruitment_notice", 1.2, [r"walk-in interview|interview schedule|offer letter|hr department|shortlisted"]),
    ("government_advisory", 1.3, [r"ministry of|government of|public notice|toll free|helpline"]),
    ("delivery_notification", 1.1, [r"out for delivery|tracking id|expected delivery|delivered successfully"]),
    ("appointment_reminder", 1.1, [r"appointment (confirmed|scheduled|reminder)|token number|visit us on"]),
    ("bank_transaction_record", 1.2, [r"account (credited|debited)|available balance|upi ref|transaction alert"]),
    ("payment_confirmation", 1.1, [r"payment (successful|received)|receipt|amount paid"]),
    ("expected_workflow", 0.9, [r"as requested|per your request|following up on|thank you for contacting|in response to your"]),
    ("unsubscribe_option", 0.7, [r"unsubscribe|manage preferences|opt out"]),
    ("no_credential_request", 0.8, []),  # structural (absence) — evaluated below
    ("no_payment_demand", 0.8, []),      # structural (absence) — evaluated below
    ("no_urgency", 0.7, []),             # structural (absence) — evaluated below
]

_CREDENTIAL_DEMAND = re.compile(
    r"\b(share|send|enter|provide|reveal).{0,30}?(otp|password|pin|cvv|credentials)\b"
    r"|\b(otp|password|pin).{0,20}?(required|needed|share|send)\b", re.IGNORECASE)
_PAYMENT_DEMAND = re.compile(
    r"\b(pay|transfer|deposit|wire).{0,30}?(fee|immediately|now|advance|processing)\b",
    re.IGNORECASE)
_URGENCY_DEMAND = re.compile(
    r"\b(urgent|immediately|act now|last warning|blocked within|expires today)\b",
    re.IGNORECASE)

_COMPILED = [(n, w, [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in ps])
             for n, w, ps in _TRUST_PATTERNS]


class LegitimacyEngine:
    """Detect trust indicators; absence-of-harm signals included."""

    def analyze(self, text: str) -> dict:
        lowered = text or ""
        found: list[dict] = []
        weight_sum = 0.0
        for name, weight, patterns in _COMPILED:
            if name == "no_credential_request":
                if not _CREDENTIAL_DEMAND.search(lowered):
                    found.append({"indicator": name, "weight": weight, "evidence": "no credential request"})
                    weight_sum += weight
                continue
            if name == "no_payment_demand":
                if not _PAYMENT_DEMAND.search(lowered):
                    found.append({"indicator": name, "weight": weight, "evidence": "no payment demand"})
                    weight_sum += weight
                continue
            if name == "no_urgency":
                if not _URGENCY_DEMAND.search(lowered):
                    found.append({"indicator": name, "weight": weight, "evidence": "no urgency language"})
                    weight_sum += weight
                continue
            for pattern in patterns:
                match = pattern.search(lowered)
                if match:
                    snippet = " ".join(match.group(0).split())[:60]
                    found.append({"indicator": name, "weight": weight, "evidence": snippet})
                    weight_sum += weight
                    break
        trust = round(weight_sum / (weight_sum + 2.5), 3)
        return {"trust_score": trust, "indicators": found,
                "count": len(found), "weight_sum": round(weight_sum, 2)}


legitimacy_engine = LegitimacyEngine()
