"""Rule-based spam indicator engine.

Purpose
-------
Indicators are *supporting evidence* only. The ML classifier is the
primary decision maker; this engine enriches the analysis with
interpretable, transparent signal such as:

    {"indicator": "Urgency language", "severity": "high",
     "evidence": "act immediately", "category": "urgency"}

Each rule detects a pattern class (financial request, OTP scam,
job scam, ...) and returns structured evidence including the matched
text snippet so the explanation layer can quote it.
"""
from __future__ import annotations

import re

from app.ml.preprocess import extract_emails, extract_phones, extract_urls

# ------------------------------------------------------------------ patterns
_PATTERNS: list[dict] = [
    # --- urgency ----------------------------------------------------------
    {
        "indicator": "Excessive urgency",
        "severity": "high",
        "category": "urgency",
        "regex": re.compile(
            r"\b(act now|act immediately|immediately|urgent|asap|right away|"
            r"limited (time|period)|expires? (today|soon|in \d+ (hours?|minutes?))|"
            r"last (chance|warning|notice)|don'?t (delay|wait)|hurry|"
            r"only \d+ (hours?|minutes?|days?))\b",
            re.IGNORECASE,
        ),
    },
    # --- prizes / lotteries ----------------------------------------------
    {
        "indicator": "Prize / lottery claim",
        "severity": "high",
        "category": "prize",
        "regex": re.compile(
            r"\b(winner|you('ve| have) won|won (a|the)? ?(prize|amount|money|gift)|"
            r"lottery|lucky draw|jackpot|claim (your|the) (prize|reward)|"
            r"congratulations!? you|free (gift|reward)|gift (card|voucher) worth)\b",
            re.IGNORECASE,
        ),
    },
    # --- financial reward / money ------------------------------------------
    {
        "indicator": "Financial reward promise",
        "severity": "high",
        "category": "reward",
        "regex": re.compile(
            r"\b(cash (prize|reward|bonus)|reward|you have been (selected|chosen)|"
            r"earn (easy|extra|free)? ?money|make money (fast|quickly|online)|"
            r"get rich|double your money|guaranteed (income|returns|profit)|"
            r"passive income|money (back|making) opportunity)\b",
            re.IGNORECASE,
        ),
    },
    # --- account verification / phishing -----------------------------------
    {
        "indicator": "Account verification request",
        "severity": "high",
        "category": "phishing",
        "regex": re.compile(
            r"\b(verify (your|the) account|account (will be|has been) (blocked|disabled|"
            r"suspended|locked|deactivated)|update your (account|details|information)|"
            r"confirm your (account|identity|details)|k\s?y\s?c\s? ?(update|verification)|"
            r"unusual (activity|login)|unauthorized (access|login|transaction)|"
            r"immediate (action|attention) (required|needed)?)\b",
            re.IGNORECASE,
        ),
    },
    # --- password / OTP -----------------------------------------------------
    {
        "indicator": "Password or credential request",
        "severity": "high",
        "category": "credentials",
        "regex": re.compile(
            r"\b(enter|provide|send|share|confirm|verify)? ?(your |the )?(password|pin|"
            r"security (code|question)|login (id|details)|credentials|mpin)\b",
            re.IGNORECASE,
        ),
    },
    {
        "indicator": "OTP request",
        "severity": "high",
        "category": "credentials",
        "regex": re.compile(
            r"\b(otp|one[- ]?time[- ]?(password|pin|code|pass)?|verification code|"
            r"share (this|the) (otp|code|pin))\b",
            re.IGNORECASE,
        ),
    },
    # --- payments / fees ------------------------------------------------------
    {
        "indicator": "Suspicious payment request",
        "severity": "high",
        "category": "payment",
        "regex": re.compile(
            r"\b(pay (a|the|this) (fee|amount|registration|processing|shipping|"
            r"delivery|tax|insurance)|processing fee|registration fee|advance (fee|payment)|"
            r"money (transfer|order|request)|wire (money|transfer)|western union|"
            r"pay (now|today|immediately)|payment (required|needed)|"
            r"receive (money|payment|amount)|refund (processing|fee))\b",
            re.IGNORECASE,
        ),
    },
    # --- jobs ----------------------------------------------------------------
    {
        "indicator": "Job scam pattern",
        "severity": "high",
        "category": "job_scam",
        "regex": re.compile(
            r"\b(work from home|earn (up to )?(rs\.? ?\d+|up to ?\d+|₹\d+|\d+) per "
            r"(day|month|week|monthly)|(monthly|daily) (income|salary|earning)|"
            r"part[- ]?time (job|work|opportunity)|no experience (needed|required)|"
            r"apply (now|today|immediately)|data entry (job|work)|freelance (job|work|"
            r"opportunity)|online (job|work|task)|job (offer|opportunity|vacancy)|"
            r"hiring (now|immediately|today)|placement (fee|charge)|"
            r"registration (fee|charge|amount))\b",
            re.IGNORECASE,
        ),
    },
    # --- investment / crypto ----------------------------------------------------
    {
        "indicator": "Investment scheme pattern",
        "severity": "high",
        "category": "investment",
        "regex": re.compile(
            r"\b(invest (now|today|only)|high returns|guaranteed (returns|profit|income)|"
            r"double (your )?(money|investment|deposit)|crypto(curency)? (investment|trading)|"
            r"bitcoin|trading (platform|signals|tips)|forex|stock (tips|recommendation)|"
            r"profit (guaranteed|assured)|risk[- ]?free (investment|returns)|"
            r"mutual fund (scam|guarantee)|p\s?2\s?p\s? ?(lending|investment))\b",
            re.IGNORECASE,
        ),
    },
    # --- loans ------------------------------------------------------------------
    {
        "indicator": "Loan scam pattern",
        "severity": "medium",
        "category": "loan_scam",
        "regex": re.compile(
            r"\b(instant loan|loan (approved|sanctioned|released|sanction)|"
            r"pre[- ]?approved loan|loan (offer|facility) (up to )?\d+|"
            r"personal loan (without|no )? (documents|collateral|guarantor|income)|"
            r"low interest (loan|emi)|loan (processing|disbursal) fee|"
            r"easy emis?|no (credit|cibil) (check|score|history))\b",
            re.IGNORECASE,
        ),
    },
    # --- delivery ------------------------------------------------------------------
    {
        "indicator": "Delivery / parcel scam pattern",
        "severity": "medium",
        "category": "delivery",
        "regex": re.compile(
            r"\b(your (parcel|package|shipment|order|courier)|package (held|pending|"
            r"delayed|awaiting)|delivery (failed|pending|attempt)|"
            r"re-?schedule (your )?(delivery|parcel)|update (your )?(delivery|shipping) (address)|"
            r"pay (the )?(small )?(delivery|shipping) (fee|charge|amount)|"
            r"(undelivered|undeliverable) (parcel|package)|customs (fee|charge|clearance))\b",
            re.IGNORECASE,
        ),
    },
    # --- phishing language -----------------------------------------------------------
    {
        "indicator": "Phishing link language",
        "severity": "high",
        "category": "phishing",
        "regex": re.compile(
            r"\b(click (here|this|the|the link|link)|tap (here|this|the link)|"
            r"login (here|via|through)|sign in (here|via)|"
            r"(follow|open|visit) (this|the) (link|url|website|page)|"
            r"http\S*|link (below|attached)|update (payment|billing) info)\b",
            re.IGNORECASE,
        ),
    },
    # --- bank / card ------------------------------------------------------------------
    {
        "indicator": "Bank or card warning",
        "severity": "high",
        "category": "banking",
        "regex": re.compile(
            r"\b(debit card|credit card|atm card|bank account|account number|"
            r"cvv|card (will be|has been) (blocked|suspended|deactivated)|"
            r"card (expiry|expires) today|add (your|the) card|"
            r"net ?banking (blocked|disabled|suspended)|"
            r"aadhaar (number|seeded|link|update)|pan (card )?(verification|update|link))\b",
            re.IGNORECASE,
        ),
    },
    # --- free offers / promotions ---------------------------------------------------------
    {
        "indicator": "Promotional language",
        "severity": "low",
        "category": "promotion",
        "regex": re.compile(
            r"\b(free (gift|prize|membership|access|trial|offer)|exclusive offer|"
            r"limited (period|time) offer|hurry!?|discount|spend and (win|earn)|"
            r"special (offer|discount|deal)|buy one get one|flat \d+% off|"
            r"season (sale|offer)|clearance (sale|offer)|festive (sale|offer))\b",
            re.IGNORECASE,
        ),
    },
    # --- general financial urgency keywords ------------------------------------------------
    {
        "indicator": "Financial request",
        "severity": "medium",
        "category": "financial",
        "regex": re.compile(
            r"\b(send (money|cash|amount)|transfer (money|cash)|"
            r"deposit (money|cash|amount)|withdraw (money|cash)|"
            r"borrow (money|cash)|need (money|cash) (urgently|now)|"
            r"funds (needed|required|transfer)|payment (due|pending|required))\b",
            re.IGNORECASE,
        ),
    },
]

# Extra patterns evaluated separately (regex-free helpers)
_FREE_OFFER_WORDS = {
    "free", "gift", "win", "won", "prize", "bonus", "reward", "lucky",
    "discount", "offer", "cashback", "reward points",
}
_URGENCY_WORDS = {
    "urgent", "immediately", "now", "today", "soon", "hurry", "asap",
    "fast", "quick", "limited", "expired", "expires",
}

_SEVERITY_ORDER = {"high": 3, "medium": 2, "low": 1}


def _find_evidence(text: str, pattern: re.Pattern) -> str | None:
    """Return a short matched snippet (~40 chars) for evidence display."""
    match = pattern.search(text)
    if not match:
        return None
    snippet = match.group(0).strip()
    if len(snippet) > 40:
        snippet = snippet[:40] + "..."
    return snippet


def detect_indicators(raw_text: str) -> list[dict]:
    """Run all rules against raw text; return structured indicator dicts."""
    if not raw_text or not raw_text.strip():
        return []
    indicators: list[dict] = []
    seen: set[str] = set()
    text = raw_text.lower()

    for rule in _PATTERNS:
        evidence = _find_evidence(text, rule["regex"])
        if evidence:
            key = rule["indicator"]
            if key in seen:
                continue
            seen.add(key)
            indicators.append(
                {
                    "indicator": rule["indicator"],
                    "severity": rule["severity"],
                    "category": rule["category"],
                    "evidence": evidence,
                }
            )

    # word-frequency based checks
    words = set(re.findall(r"[a-z]+", text))
    if words & _FREE_OFFER_WORDS and not any(
        i["category"] == "promotion" for i in indicators
    ):
        indicators.append(
            {
                "indicator": "Promotional language",
                "severity": "low",
                "category": "promotion",
                "evidence": ", ".join(sorted(words & _FREE_OFFER_WORDS))[:40],
            }
        )
    if len(words & _URGENCY_WORDS) >= 2 and not any(
        i["category"] == "urgency" for i in indicators
    ):
        indicators.append(
            {
                "indicator": "Excessive urgency",
                "severity": "high",
                "category": "urgency",
                "evidence": ", ".join(sorted(words & _URGENCY_WORDS))[:40],
            }
        )

    # structural checks
    if raw_text.count("!") >= 3:
        indicators.append(
            {
                "indicator": "Repeated exclamations",
                "severity": "low",
                "category": "promotion",
                "evidence": raw_text[-80:] if len(raw_text) > 80 else raw_text,
            }
        )
    if extract_urls(raw_text):
        indicators.append(
            {
                "indicator": "Contains link(s)",
                "severity": "low",
                "category": "url",
                "evidence": extract_urls(raw_text)[0][:60],
            }
        )
    if extract_emails(raw_text):
        indicators.append(
            {
                "indicator": "Contains email address",
                "severity": "low",
                "category": "contact",
                "evidence": extract_emails(raw_text)[0][:40],
            }
        )
    if extract_phones(raw_text):
        indicators.append(
            {
                "indicator": "Contains phone number",
                "severity": "low",
                "category": "contact",
                "evidence": extract_phones(raw_text)[0][:30],
            }
        )

    # ALL-CAPS signalling
    letters = [c for c in raw_text if c.isalpha()]
    if letters:
        caps_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
        if caps_ratio > 0.7 and len(letters) > 15:
            indicators.append(
                {
                    "indicator": "Excessive ALL-CAPS text",
                    "severity": "medium",
                    "category": "promotion",
                    "evidence": ">70% uppercase",
                }
            )

    indicators.sort(
        key=lambda i: (_SEVERITY_ORDER.get(i["severity"], 0), i["indicator"]),
        reverse=True,
    )
    return indicators


def count_severity(indicators: list[dict], severity: str) -> int:
    return sum(1 for i in indicators if i["severity"] == severity)