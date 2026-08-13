"""Semantic Understanding Engine — preprocessing utilities.

Deterministic text utilities shared by the pipeline stages:

* unicode normalization (NFC + confusable folding)
* whitespace cleanup
* emoji preservation (extract + count, never discarded)
* case normalization
* email / SMS parsing (stdlib only)
* sentence segmentation
* language detection (script heuristic — deterministic)
* token normalization
* special-character handling
"""
from __future__ import annotations

import re
import unicodedata
from email import message_from_string

# ----------------------------------------------------------------- unicode
_SMART_CHARS = {
    "\u201c": '"', "\u201d": '"', "\u2018": "'", "\u2019": "'",
    "\u2013": "-", "\u2014": "-", "\u00a0": " ", "\u200b": "",
    "\u2026": "...", "\u20b9": "Rs", "\u00a9": "(c)", "\u00ae": "(r)",
}

_WS_RUN = re.compile(r"\s+")
_SPECIAL_KEEP = frozenset(
    "!?.,;:%$€£₹&@#()[]{}/*+=-_\"'<>\\|~^"
)

# ----------------------------------------------------------------- emoji
# Comprehensive-enough emoji ranges (deterministic extraction).
_EMOJI_PATTERN = re.compile(
    "["
    "\U0001F000-\U0001FAFF"      # misc symbols, emoticons, etc.
    "\U00002600-\U000027BF"      # misc symbols, dingbats
    "\U0001F1E6-\U0001F1FF"      # flags
    "\U0000FE00-\U0000FE0F"      # variation selectors
    "\U00002700-\U000027BF"      # dingbats
    "\U0001F900-\U0001F9FF"      # supplemental symbols
    "\U00002300-\U000023FF"      # technical symbols
    "\U0000FE20-\U0000FE2F"      # combining half marks
    "]"
)

# ----------------------------------------------------------------- parsing
_EMAIL_HEADER_RE = re.compile(
    r"^(from|sender|to|subject|date|cc|bcc|reply-to):\s*(.*)$",
    re.IGNORECASE | re.MULTILINE,
)

# ----------------------------------------------------------------- language
_SCRIPT_RANGES: list[tuple[str, str, int, int]] = [
    ("en", "latin", 0x0041, 0x024F),
    ("hi", "devanagari", 0x0900, 0x097F),
    ("bn", "bengali", 0x0980, 0x09FF),
    ("ta", "tamil", 0x0B80, 0x0BFF),
    ("te", "telugu", 0x0C00, 0x0C7F),
    ("mr", "devanagari", 0x0900, 0x097F),
    ("ar", "arabic", 0x0600, 0x06FF),
    ("ru", "cyrillic", 0x0400, 0x04FF),
    ("zh", "cjk", 0x4E00, 0x9FFF),
    ("ja", "cjk", 0x3040, 0x30FF),
    ("ko", "hangul", 0xAC00, 0xD7AF),
    ("el", "greek", 0x0370, 0x03FF),
    ("he", "hebrew", 0x0590, 0x05FF),
    ("th", "thai", 0x0E00, 0x0E7F),
]

_ABBREVIATIONS = frozenset(
    {
        "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st", "vs", "etc",
        "rs", "no", "nos", "fig", "inc", "ltd", "co", "dept", "u", "s",
    }
)

_SENTENCE_BOUNDARY = re.compile(
    r"[.!?][\"'\u201d\u2019]?\s+(?=[\"'A-Z0-9\u201c\u2018])"
)

_QUESTION_WORD = re.compile(
    r"^(who|what|when|where|why|how|which|whose|whom|can|could|will|would|"
    r"do|does|did|is|are|was|were|have|has|had|should|shall|may|might|"
    r"are you|is it)\b",
    re.IGNORECASE,
)

_IMPERATIVE_VERBS = frozenset(
    {
        "click", "enter", "verify", "submit", "update", "confirm", "download",
        "open", "press", "call", "send", "reply", "visit", "register", "login",
        "log", "check", "scan", "reply", "contact", "provide", "share", "pay",
        "transfer", "enable", "disable", "add", "remove", "select", "choose",
        "visit", "follow", "read", "attach", "upload", "tell", "ask", "join",
        "redeem", "claim", "activate", "deactivate", "set", "reset",
    }
)

_REQUEST_MARKERS = re.compile(
    r"\b(please|kindly|request|require|need|must|we ask|asking|urge|"
    r"could you|can you|would you|do you need to)\b",
    re.IGNORECASE,
)

_OFFER_MARKERS = re.compile(
    r"\b(free|win|won|prize|offer|discount|exclusive|gift|reward|bonus|"
    r"cashback|giveaway|coupon|deal|limited time|claim now)\b",
    re.IGNORECASE,
)

_URGENCY_MARKERS = re.compile(
    r"\b(urgent|immediately|asap|now|today only|expires?|deadline|hurry|"
    r"final|last chance|within 24 hours|act now|don't miss)\b",
    re.IGNORECASE,
)

_FINANCIAL_MARKERS = re.compile(
    r"\b(bank|account|balance|transfer|payment|pay|credit|debit|loan|"
    r"interest|emi|wallet|upi|neft|imps|rtgs|charge|fee|refund|salary|"
    r"invest|withdraw|deposit|invoice|billing|statement|transaction)\b",
    re.IGNORECASE,
)

_CREDENTIAL_MARKERS = re.compile(
    r"\b(password|passcode|otp|pin|credential|login|sign[ -]?in|"
    r"verify|verification|aadhaar|ssn|pan card|identity|id proof|"
    r"security question|secret code|2fa|mfa)\b",
    re.IGNORECASE,
)

_PERSONAL_INFO_MARKERS = re.compile(
    r"\b(birth date|dob|date of birth|address|mother's name|maiden name|"
    r"cvv|cvc|card number|atm|debit card|credit card|bank details)\b",
    re.IGNORECASE,
)


# ------------------------------------------------------------ public API
def normalize_unicode(text: str) -> str:
    """NFC normalization + fold a small safe set of confusables."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    return "".join(_SMART_CHARS.get(ch, ch) for ch in text)


def clean_whitespace(text: str) -> str:
    """Collapse whitespace runs, strip edges, keep one space."""
    return _WS_RUN.sub(" ", text or "").strip()


def case_normalize(text: str) -> str:
    """Lowercase for matching; display text uses the original."""
    return (text or "").lower()


def extract_emojis(text: str) -> list[str]:
    """All emoji codepoints/clusters present, in order (never dropped)."""
    return _EMOJI_PATTERN.findall(text or "")


def normalize_special_characters(text: str) -> str:
    """Normalize special characters: keep common punctuation, drop control
    chars, replace exotic quotes/dashes, keep emoji intact."""
    if not text:
        return ""
    out = []
    for ch in text:
        category = unicodedata.category(ch)
        if category.startswith("C") and ch not in "\n\t":
            continue  # control characters removed
        if ch == "\n":
            out.append(" ")  # newline -> space
            continue
        if category == "Zs":
            out.append(" ")
            continue
        out.append(ch)
    return "".join(out)


def preprocess_text(text: str) -> str:
    """Canonical pipeline: unicode -> special chars -> whitespace fold."""
    return clean_whitespace(normalize_special_characters(normalize_unicode(text)))


# ------------------------------------------------------------- input kinds
def parse_raw_email(raw: str) -> dict[str, str]:
    """Parse a raw pasted email into {subject, sender, body}.

    Uses the stdlib ``email`` package; malformed input degrades to the
    raw text as body. Never raises.
    """
    if not raw:
        return {"subject": "", "sender": "", "body": ""}
    try:
        parsed = message_from_string(raw)
        subject = parsed.get("Subject", "") or ""
        sender = parsed.get("From", "") or ""
        body = parsed.get_payload()
        if isinstance(body, list):
            body = " ".join(str(part) for part in body)
        return {
            "subject": subject.strip(),
            "sender": sender.strip(),
            "body": (body or "").strip(),
        }
    except Exception:
        return {"subject": "", "sender": "", "body": raw.strip()}


def parse_sms(text: str) -> dict[str, str]:
    """SMS normalization: single message, no headers."""
    return {"message": preprocess_text(text)}


def decompose_email(subject: str, sender: str, body: str) -> dict[str, str]:
    """Structured email input -> combined text + parts."""
    subject = preprocess_text(subject)
    sender = preprocess_text(sender)
    body = preprocess_text(body)
    combined = " ".join(part for part in (subject, body) if part).strip()
    return {"subject": subject, "sender": sender, "body": body, "combined": combined}


# ------------------------------------------------------------ segmentation
def segment_sentences(text: str) -> list[str]:
    """Deterministic sentence segmentation with abbreviation guards.

    Splits on sentence-ending punctuation followed by whitespace and an
    uppercase letter/digit/quote. Boundaries after abbreviations
    (Mr., Dr., Rs., ...) or single letters are skipped. Sentences keep
    their ending punctuation.
    """
    cleaned = preprocess_text(text)
    if not cleaned:
        return []
    sentences: list[str] = []
    start = 0
    for match in _SENTENCE_BOUNDARY.finditer(cleaned):
        sentence = cleaned[start : match.end()].rstrip()
        words = re.findall(r"[A-Za-z]+", sentence)
        previous_word = words[-1].lower() if words else ""
        if previous_word in _ABBREVIATIONS or len(previous_word) == 1:
            continue
        sentences.append(sentence)
        start = match.end()
    tail = cleaned[start:].strip()
    if tail:
        sentences.append(tail)
    return [s for s in sentences if s]


def is_question_sentence(sentence: str) -> bool:
    """True when a sentence is a question (ending ? or question-leading)."""
    s = sentence.strip()
    if not s:
        return False
    if s.endswith("?"):
        return True
    return bool(_QUESTION_WORD.match(s))


def is_imperative_sentence(sentence: str) -> bool:
    """Approximate imperative detection: leading verb / request keyword."""
    s = sentence.strip().lstrip("\"'").lower()
    if not s:
        return False
    words = s.split()
    if not words:
        return False
    head = words[0].rstrip("!.,")
    if head in _IMPERATIVE_VERBS:
        return True
    if head in {"please", "kindly", "don't", "do not", "never", "always"}:
        return True
    return False


# ---------------------------------------------------------------- language
def detect_language(text: str) -> tuple[str, float]:
    """Script-heuristic language detection.

    Returns ``(iso_label, confidence)``. Deterministic. ``unknown`` with
    confidence 0.0 when no script evidence is present.
    """
    if not text:
        return "unknown", 0.0
    script_counts: dict[str, int] = {}
    letter_count = 0
    for ch in text:
        code = ord(ch)
        if not ch.isalpha() and not unicodedata.category(ch).startswith("L"):
            continue
        letter_count += 1
        for label, _script, low, high in _SCRIPT_RANGES:
            if low <= code <= high:
                script_counts[label] = script_counts.get(label, 0) + 1
                break
    if not script_counts:
        return "unknown", 0.0
    dominant = max(script_counts, key=script_counts.get)
    share = script_counts[dominant] / letter_count
    confidence = min(0.95, 0.35 + 0.6 * share)
    if letter_count < 3:
        confidence *= 0.5
    return dominant, round(confidence, 3)


# ---------------------------------------------------------------- tokens
def tokenize_words(text: str) -> list[str]:
    """Whitespace tokenization on the normalized text."""
    return preprocess_text(text).split()


def normalize_token(word: str) -> str:
    """Lowercase + strip wrapping punctuation from a token."""
    return word.strip(".,;:!?()[]{}\"'<>-").lower()


def has_special_characters(text: str) -> bool:
    """True when text contains punctuation/symbols outside words."""
    return any(ch in _SPECIAL_KEEP for ch in text or "")
