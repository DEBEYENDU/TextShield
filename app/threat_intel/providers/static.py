"""Static provider: enhanced offline URL/domain analysis, no network.

Wraps the existing static URL analyzer (app.ml.url_analyzer — preserved)
and adds punycode, typosquatting similarity, subdomain depth, IP hosts,
shorteners, credential-like paths, suspicious query params and encoded
payloads. Never fetches the URL.
"""

from __future__ import annotations

import re
from urllib.parse import parse_qsl, unquote, urlparse

from app.threat_intel.models import ProviderResult
from app.threat_intel.provider import ThreatIntelProvider

_SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd",
               "cutt.ly", "shorturl.at", "ow.ly", "buff.ly", "rebrand.ly"}
_SUSPICIOUS_TLDS = {"tk", "ml", "ga", "cf", "gq", "top", "xyz", "buzz",
                    "country", "stream", "download", "review", "trade"}
_CRED_PATH = re.compile(
    r"(login|signin|verify|secure|account|update|confirm|banking|password)",
    re.IGNORECASE)
_SUSPICIOUS_PARAM = re.compile(
    r"(token|session|auth|password|card|cvv|otp|ssn|aadhaar)", re.IGNORECASE)
_ENCODED = re.compile(r"%[0-9a-fA-F]{2}")
_PUNY = re.compile(r"xn--", re.IGNORECASE)

_TRUSTED = {"google.com", "microsoft.com", "apple.com", "amazon.com",
            "rbi.org.in", "gov.in", "nic.in", "hdfcbank.com", "sbi.co.in",
            "icicibank.com", "uidai.gov.in", "incometax.gov.in"}

_BIG_BRANDS = ["google", "microsoft", "apple", "amazon", "paypal", "hdfc",
               "sbi", "icici", "rbi", "facebook", "instagram", "whatsapp"]


def _typosquat_score(host: str) -> tuple[bool, str]:
    labels = host.lower().split(".")
    for label in labels:
        if label in ("www",):
            continue
        for brand in _BIG_BRANDS:
            if label == brand:
                continue
            if brand in label and len(label) <= len(brand) + 6:
                return True, f"lookalike of {brand}: {label}"
            if len(label) >= 5 and _edit_distance(label, brand) == 1:
                return True, f"one-char variant of {brand}: {label}"
    return False, ""


def _edit_distance(a: str, b: str) -> int:
    if abs(len(a) - len(b)) > 1:
        return 2
    if len(a) == len(b):
        return sum(c1 != c2 for c1, c2 in zip(a, b))
    short, long = (a, b) if len(a) < len(b) else (b, a)
    for i in range(len(long)):
        if short == long[:i] + long[i + 1:]:
            return 1
    return 2


def static_assess_url(url: str) -> tuple[str, float, list[str]]:
    """Return (verdict, confidence, evidence) without network access."""
    evidence: list[str] = []
    score = 0.0
    text = url if "://" in url else "http://" + url
    try:
        host = (urlparse(text).hostname or "").lower()
    except Exception:
        return ("unknown", 0.0, ["unparseable url"])
    if not host:
        return ("unknown", 0.0, ["empty host"])
    if any(host == t or host.endswith("." + t) for t in _TRUSTED):
        return ("benign", 0.75, ["trusted domain"])
    if re.fullmatch(r"(?:\d{1,3}\.){3}\d{1,3}", host):
        evidence.append("raw IP host")
        score += 0.5
    if _PUNY.search(host):
        evidence.append("punycode (possible homograph)")
        score += 0.6
    typo, why = _typosquat_score(host)
    if typo:
        evidence.append(why)
        score += 0.55
    if host in _SHORTENERS:
        evidence.append("URL shortener hides destination")
        score += 0.3
    tld = host.rsplit(".", 1)[-1]
    if tld in _SUSPICIOUS_TLDS:
        evidence.append(f"suspicious TLD .{tld}")
        score += 0.25
    if host.count(".") >= 3:
        evidence.append("deep subdomain nesting")
        score += 0.2
    try:
        path = urlparse(text).path or ""
        query = urlparse(text).query or ""
    except Exception:
        path, query = "", ""
    if _CRED_PATH.search(path):
        evidence.append("credential-like URL path")
        score += 0.35
    params = [k.lower() for k, _ in parse_qsl(query)]
    if any(_SUSPICIOUS_PARAM.search(p) for p in params):
        evidence.append("suspicious query parameters")
        score += 0.4
    if _ENCODED.search(path + query):
        evidence.append("percent-encoded payload")
        score += 0.2
    # existing static analyzer corroboration (preserved, never replaced)
    try:
        from app.ml.url_analyzer import analyze_urls

        for finding in analyze_urls(url):
            for warning in finding.get("warnings", []):
                if str(warning) not in evidence:
                    evidence.append(f"static: {warning}")
                    score += 0.15
    except Exception:
        pass
    if score >= 0.8:
        return ("known_malicious", min(0.9, score), evidence)
    if score >= 0.4:
        return ("suspicious", round(min(0.75, score), 3), evidence)
    if evidence:
        return ("suspicious", round(score, 3), evidence)
    return ("unknown", 0.0, ["no static signals"])


class StaticProvider(ThreatIntelProvider):
    """Offline static analysis provider (always configured)."""

    name = "static"
    version = "1.0.0"

    @property
    def capabilities(self) -> list[str]:
        return ["url", "domain"]

    def lookup_url(self, url: str) -> ProviderResult:
        verdict, confidence, evidence = static_assess_url(url)
        return ProviderResult(ioc=url, ioc_type="url", provider=self.name,
                              verdict=verdict, confidence=confidence,
                              categories=["static-analysis"],
                              sources=["static-heuristics-v1"],
                              raw_summary="; ".join(evidence)[:200])

    def lookup_domain(self, domain: str) -> ProviderResult:
        return self.lookup_url("http://" + domain)
