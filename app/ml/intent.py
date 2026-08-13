"""Sender intent extraction (V2.0).

Purpose
-------
Intent analysis answers the question a statistical filter never asks:
*what does the sender want the recipient to do?* The requested action is
one of the strongest signals in social engineering: legitimate services
never ask for passwords, OTPs, or advance payments through messages.

The detector assigns one of eight machine-readable intent classes:

    credential_request    - asks for passwords, PINs, OTPs, verification codes
    money_transfer        - asks the user to pay, send, or transfer money
    download_install      - asks the user to download/install an app or file
    personal_data         - asks for identity/financial personal data
    prize_claim           - claims a prize/lottery and asks the user to claim it
    confirmation_request  - asks the user to verify/confirm account details
    engagement            - benign conversational/transactional engagement
    other                 - no recognizable request pattern

The output is ``{"label", "description", "evidence"}`` where ``evidence``
is the matched text snippet, so intent remains auditable like indicators.
"""
from __future__ import annotations

import re

# ------------------------------------------------------------------ patterns
# Ordered by risk: dangerous requests are matched first so a message asking
# for both credentials and money resolves to the most dangerous intent.
_PATTERNS: list[dict] = [
    {
        "label": "credential_request",
        "description": "The sender asks for passwords, PINs, OTPs or verification codes.",
        "regex": re.compile(
            r"\b(enter|provide|send|share|confirm|verify|re[- ]?enter|submit)\b.{0,40}?"
            r"\b(password|pin|otp|one[- ]?time[- ]?(password|pin|code|pass)?|"
            r"security (code|question|answer)|login (id|details|credentials)|mpin|"
            r"verification (code|number|otp)|net ?banking (id|password)|card (pin|cvv))\b",
            re.IGNORECASE | re.DOTALL,
        ),
    },
    {
        "label": "credential_request",
        "description": "The sender asks for passwords, PINs, OTPs or verification codes.",
        "regex": re.compile(
            r"\b(share|send|text|reply (with|me))\b.{0,30}?(otp|code|pin)\b",
            re.IGNORECASE | re.DOTALL,
        ),
    },
    {
        "label": "money_transfer",
        "description": "The sender asks the recipient to pay, send or transfer money.",
        "regex": re.compile(
            r"\b(pay|send|transfer|deposit|wire|release)\b.{0,40}?"
            r"\b(money|cash|amount|fee|funds?|payment|rs\.? ?\d+|\$\d+|€\d+|₹\d+|"
            r"advance|processing fee|registration fee)\b",
            re.IGNORECASE | re.DOTALL,
        ),
    },
    {
        "label": "download_install",
        "description": "The sender asks the recipient to download or install an app or file.",
        "regex": re.compile(
            r"\b(download|install|update (your )?app|install now)\b.{0,50}?"
            r"\b(app|application|apk|file|software|update|tool)\b",
            re.IGNORECASE | re.DOTALL,
        ),
    },
    {
        "label": "personal_data",
        "description": "The sender asks for identity or financial personal details.",
        "regex": re.compile(
            r"\b(provide|enter|share|send|update|confirm|give)\b.{0,40}?"
            r"\b(aadhaar|pan (card )?number|ssn|social security|date of birth|"
            r"bank (account|details)|account number|card (number|details)|cvv|"
            r"address|full name|id proof|passport|driver'?s? license)\b",
            re.IGNORECASE | re.DOTALL,
        ),
    },
    {
        "label": "prize_claim",
        "description": "The sender claims a prize or lottery and asks the recipient to claim it.",
        "regex": re.compile(
            r"\b(winner|won|jackpot|lottery|lucky draw)\b.{0,60}?"
            r"\b(claim|collect|receive|contact|register|congratulations)\b",
            re.IGNORECASE | re.DOTALL,
        ),
    },
    {
        "label": "confirmation_request",
        "description": "The sender asks the recipient to verify or confirm account information.",
        "regex": re.compile(
            r"\b(verify|confirm|update|reactivate|renew|unlock)\b.{0,40}?"
            r"\b(account|profile|details|information|membership|subscription|wallet|"
            r"login|identity)\b",
            re.IGNORECASE | re.DOTALL,
        ),
    },
    {
        "label": "engagement",
        "description": "The sender invites benign interaction: meetings, replies, purchases or appointments.",
        "regex": re.compile(
            r"\b(please\b.*\b(reply|call|let me know|confirm your (attendance|seat|order|"
            r"appointment))|rsvp|book (your )?(slot|appointment|ticket)|"
            r"call (us|me|our)|visit (us|our (store|website))|reply (to )?this"
            r"|order (now|today)|reserve|schedule (a )?(meeting|call|demo))\b",
            re.IGNORECASE,
        ),
    },
]

_INTENT_ORDER = [
    "credential_request",
    "money_transfer",
    "download_install",
    "personal_data",
    "prize_claim",
    "confirmation_request",
    "engagement",
    "other",
]

_DESCRIPTIONS: dict[str, str] = {
    "credential_request": "The sender asks for passwords, PINs, OTPs or verification codes.",
    "money_transfer": "The sender asks the recipient to pay, send or transfer money.",
    "download_install": "The sender asks the recipient to download or install an app or file.",
    "personal_data": "The sender asks for identity or financial personal details.",
    "prize_claim": "The sender claims a prize or lottery and asks the recipient to claim it.",
    "confirmation_request": "The sender asks the recipient to verify or confirm account information.",
    "engagement": "The sender invites benign interaction: meetings, replies, purchases or appointments.",
    "other": "No recognizable request pattern was detected.",
}


def _evidence(text: str, pattern: re.Pattern, limit: int = 60) -> str:
    match = pattern.search(text)
    if not match:
        return ""
    snippet = " ".join(match.group(0).split())
    if len(snippet) > limit:
        snippet = snippet[: limit - 3] + "..."
    return snippet


def detect_intent(raw_text: str) -> dict:
    """Return the sender's intended action: {"label", "description", "evidence"}.

    Rules are evaluated in the module order (most dangerous first); the
    first match wins. Messages with no recognizable request pattern are
    labeled "other".
    """
    text = (raw_text or "").lower()
    if not text.strip():
        return {"label": "other", "description": _DESCRIPTIONS["other"], "evidence": ""}

    for rule in _PATTERNS:
        evidence = _evidence(text, rule["regex"])
        if evidence:
            return {
                "label": rule["label"],
                "description": rule["description"],
                "evidence": evidence,
            }
    return {"label": "other", "description": _DESCRIPTIONS["other"], "evidence": ""}


def is_malicious_intent(label: str) -> bool:
    """True for intents that typically accompany social engineering."""
    return label in {
        "credential_request",
        "money_transfer",
        "download_install",
        "personal_data",
        "prize_claim",
    }
