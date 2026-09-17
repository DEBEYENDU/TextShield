"""Entity linking: normalize names, merge duplicates, resolve aliases.

Example: "SBI" / "State Bank" / "State Bank of India" -> single entity.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

_LEGAL_SUFFIXES = re.compile(
    r"\s+(ltd\.?|limited|inc\.?|corp\.?|corporation|pvt\.?|pvtltd|llp|llc|co\.?|company|group|bank|banks)$",
    re.IGNORECASE,
)
_PUNCT = re.compile(r"[^\w\s.&@+:/?=-]")
_WS = re.compile(r"\s+")

# canonical -> aliases (all compared in normalized form)
_ALIAS_TABLE: dict[str, set[str]] = {
    "state bank of india": {"sbi", "state bank", "state bank of india", "sb of india"},
    "hdfc bank": {"hdfc", "hdfc bank", "hdfcbank"},
    "icici bank": {"icici", "icici bank", "icicibank"},
    "punjab national bank": {"pnb", "punjab national bank"},
    "bank of baroda": {"bob", "bank of baroda"},
    "reserve bank of india": {"rbi", "reserve bank", "reserve bank of india"},
    "income tax department": {"income tax", "income tax department", "it department"},
    "unique identification authority of india": {"uidai", "aadhaar", "aadhar"},
    "unified payments interface": {"upi"},
    "whatsapp": {"whatsapp", "wa"},
    "telegram": {"telegram", "tg"},
}

_CANONICAL_LOOKUP: dict[str, str] = {}
for canonical, aliases in _ALIAS_TABLE.items():
    for alias in aliases:
        _CANONICAL_LOOKUP[alias] = canonical


def normalize_text_value(value: str) -> str:
    text = (value or "").strip().lower()
    text = _PUNCT.sub(" ", text)
    text = _WS.sub(" ", text).strip(" .")
    return text


def normalize_org(value: str) -> str:
    text = normalize_text_value(value)
    if text in _CANONICAL_LOOKUP:  # aliases first: "State Bank" must not lose "bank"
        return _CANONICAL_LOOKUP[text]
    stripped = _LEGAL_SUFFIXES.sub("", text).strip()
    if stripped in _CANONICAL_LOOKUP:
        return _CANONICAL_LOOKUP[stripped]
    return _CANONICAL_LOOKUP.get(text, stripped or text)


def normalize_domain(value: str) -> str:
    host = (value or "").strip().lower()
    if "://" in host or "/" in host:
        try:
            host = urlparse(host if "://" in host else "http://" + host).hostname or host
        except Exception:
            pass
    if host.startswith("www."):
        host = host[4:]
    return host.strip(".")


def normalize_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    if len(digits) > 10 and digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    if len(digits) > 10 and digits.startswith("0"):
        digits = digits[1:]
    return digits


def normalize_email(value: str) -> str:
    return (value or "").strip().lower()


def canonical_label(normalized: str, surface: str) -> str:
    """Human label: title-cased canonical unless surface looks more official."""
    if not normalized:
        return (surface or "").strip()
    if len(surface or "") > len(normalized) + 12:
        return (surface or "").strip()
    return " ".join(w.capitalize() for w in normalized.split())


class EntityLinker:
    """Link a raw (group, value) pair to a canonical (type, normalized, label)."""

    def link(self, group: str, value: str) -> tuple[str, str, str]:
        """Return (entity_type, normalized, label)."""
        from app.knowledge_graph import GROUP_TO_TYPE

        entity_type = GROUP_TO_TYPE.get(group, "ORGANIZATION")
        surface = (value or "").strip()
        if group in {"domains", "websites"}:
            normalized = normalize_domain(surface)
        elif group == "urls":
            normalized = normalize_domain(surface)
            if not normalized:
                normalized = normalize_text_value(surface)
        elif group == "phone_numbers":
            normalized = normalize_phone(surface)
        elif group == "email_addresses":
            normalized = normalize_email(surface)
        elif group in {"banks", "companies", "organizations", "universities",
                       "recruiters", "people"}:
            normalized = normalize_org(surface)
        else:
            normalized = normalize_text_value(surface)
        if not normalized:
            normalized = normalize_text_value(surface) or "unknown"
        return entity_type, normalized, canonical_label(normalized, surface)

    @staticmethod
    def node_id(entity_type: str, normalized: str) -> str:
        return f"{entity_type}:{normalized}"
