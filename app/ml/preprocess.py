"""Text preprocessing for spam/ham detection.

Design notes
------------
Spam-relevant information is *preserved* rather than destroyed:
URLs, emails, phone numbers and money amounts are replaced with stable
placeholder tokens (e.g. ``[URL]``) so the classifier can learn that
their *presence* is meaningful, while the original strings remain
available to the URL analyzer and indicator engine.

The cleaning is intentionally conservative:
* lowercase
* whitespace normalization
* placeholder substitution for URLs / emails / phones / money
* keep '!', '?', digits, currency symbols (strong spam signals)
"""
from __future__ import annotations

import re

# ---------------------------------------------------------------- regexes
URL_PATTERN = re.compile(
    r"(?:https?://|www\.)\S+",
    re.IGNORECASE,
)
EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
)
PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+?\d[\d\s\-().]{7,}\d)(?!\d)"
)
MONEY_PATTERN = re.compile(
    r"(?:₹|rs\.?|inr|usd|eur|\$|€|£|pounds?|dollars?)\s?\d[\d,]*(?:\.\d+)?"
    r"|\d[\d,]*\.?\d*\s?(?:rs\.?|inr|usd|lakh|lakhs|crore|crores|k|grand|bucks)",
    re.IGNORECASE,
)

_URL_TOKEN = "[URL]"
_EMAIL_TOKEN = "[EMAIL]"
_PHONE_TOKEN = "[PHONE]"
_MONEY_TOKEN = "[MONEY]"

_WS_PATTERN = re.compile(r"\s+")
_REPEATED_PUNCT = re.compile(r"([!?])\1{2,}")

# Optional stop-word set for experiments with stopword removal.
# NOT applied by default (see tokenize()).
STOPWORDS = frozenset(
    {
        "a", "an", "the", "and", "or", "but", "if", "then", "else", "for",
        "nor", "so", "yet", "in", "on", "at", "to", "of", "by", "with",
        "from", "as", "into", "through", "is", "are", "was", "were", "be",
        "been", "being", "am", "do", "does", "did", "have", "has", "had",
        "will", "would", "can", "could", "may", "might", "shall", "should",
        "this", "that", "these", "those", "it", "its", "you", "your", "we",
        "our", "they", "their", "he", "she", "him", "her", "not", "no",
        "yes", "get", "got", "just", "like", "please",
    }
)


def extract_urls(text: str) -> list[str]:
    """Return all URLs found in the text (deduplicated, in order)."""
    seen: set[str] = set()
    urls: list[str] = []
    for match in URL_PATTERN.finditer(text):
        url = match.group(0).rstrip(".,;:!?)>]}")
        if url not in seen:
            seen.add(url)
            urls.append(url)
    return urls


def extract_emails(text: str) -> list[str]:
    """Return all email addresses found in the text."""
    seen: set[str] = set()
    emails: list[str] = []
    for match in EMAIL_PATTERN.finditer(text):
        email = match.group(0)
        if email not in seen:
            seen.add(email)
            emails.append(email)
    return emails


def extract_phones(text: str) -> list[str]:
    """Return all phone numbers found in the text."""
    return list(dict.fromkeys(PHONE_PATTERN.findall(text)))


def placeholder(text: str) -> str:
    """Replace URLs, emails, phones and money amounts with stable tokens."""
    masked = URL_PATTERN.sub(_URL_TOKEN, text)
    masked = EMAIL_PATTERN.sub(_EMAIL_TOKEN, masked)
    masked = PHONE_PATTERN.sub(_PHONE_TOKEN, masked)
    masked = MONEY_PATTERN.sub(_MONEY_TOKEN, masked)
    return masked


def normalize_text(raw_text: str, mask_sensitive: bool = True) -> str:
    """Normalize raw text for the ML pipeline.

    Parameters
    ----------
    raw_text : str
        Input message.
    mask_sensitive : bool
        Replace URLs/emails/phones/money with placeholder tokens.
    """
    if not raw_text:
        return ""
    text = raw_text.lower()
    if mask_sensitive:
        text = placeholder(text)
    text = _REPEATED_PUNCT.sub(r"\1\1", text)
    text = _WS_PATTERN.sub(" ", text).strip()
    return text


def tokenize(text: str, remove_stopwords: bool = False) -> list[str]:
    """Whitespace tokenization.

    ``remove_stopwords`` is an OPTIONAL flag (spec: "optional stop-word
    handling"). It is off by default: the TF-IDF min_df/max_df bounds
    already neutralize corpus-common words, and keeping stopwords lets
    the bigrams (e.g. "do not", "will be") remain informative.
    """
    tokens = normalize_text(text, mask_sensitive=False).split()
    if remove_stopwords:
        tokens = [t for t in tokens if t not in STOPWORDS]
    return tokens


# ----------------------------------------------------------- manual features
def basic_feature_counts(text: str) -> dict[str, int | float]:
    """Lightweight manual features complementary to TF-IDF.

    These are mainly used for reporting/debugging; the ML classifier
    itself learns on TF-IDF vectors.
    """
    raw = text or ""
    counts: dict[str, int | float] = {
        "num_urls": len(extract_urls(raw)),
        "num_emails": len(extract_emails(raw)),
        "num_phones": len(extract_phones(raw)),
        "num_money": len(MONEY_PATTERN.findall(raw)),
        "num_exclamations": raw.count("!"),
        "num_question_marks": raw.count("?"),
        "length": len(raw),
        "caps_ratio": _caps_ratio(raw),
    }
    return counts


def _caps_ratio(text: str) -> float:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if c.isupper()) / len(letters)