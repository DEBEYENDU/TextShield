"""Safe, pattern-based URL analysis.

Security principles
-------------------
* Only static pattern analysis: scheme, host structure, shortening
  services, suspicious TLDs, path keywords, obfuscation characters.
* No HTTP requests, no DNS lookups, no content fetching of arbitrary URLs.
* Language is deliberately cautious: "potentially suspicious pattern"
  rather than claims of maliciousness.
"""

from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlparse

from app.ml.preprocess import extract_urls

SHORTENERS = {
    "bit.ly",
    "tinyurl.com",
    "goo.gl",
    "t.co",
    "is.gd",
    "ow.ly",
    "buff.ly",
    "rebrand.ly",
    "cutt.ly",
    "shorturl.at",
    "rb.gy",
    "s.id",
    "short.gy",
    "zv.gd",
    "chilp.it",
    "tny.im",
}

SUSPICIOUS_TLDS = {
    "xyz",
    "top",
    "click",
    "link",
    "gift",
    "zip",
    "win",
    "men",
    "loan",
    "download",
    "review",
    "country",
    "kim",
    "icu",
    "cyou",
    "work",
    "party",
    "buzz",
    "live",
    "press",
    "site",
    "online",
    "tech",
    "club",
    "tk",
    "ga",
    "ml",
    "cf",
    "gq",
    "buzz",
    "rest",
    "monster",
}

# Brand and trust words commonly borrowed by lookalike domains.
BRAND_WORDS = {
    "paypal",
    "icici",
    "hdfc",
    "sbi",
    "axis",
    "kotak",
    "yesbank",
    "amazon",
    "flipkart",
    "google",
    "microsoft",
    "netflix",
    "gmail",
    "apple",
    "facebook",
    "instagram",
    "whatsapp",
    "paytm",
    "phonepe",
    "airtel",
    "jio",
    "vodafone",
    "fedex",
    "dhl",
    "swiggy",
    "zomato",
    "irctc",
    "uber",
    "ola",
    "linkedin",
    "adobe",
    "twitter",
    "bank",
    "banking",
    "secure",
    "support",
    "helpline",
}

# Hosts that legitimately own these brand names (exact or suffix match).
BRAND_DOMAINS = {
    "paypal.com",
    "icicibank.com",
    "hdfcbank.com",
    "onlinesbi.sbi",
    "axisbank.com",
    "kotak.com",
    "yesbank.in",
    "amazon.in",
    "amazon.com",
    "flipkart.com",
    "google.com",
    "microsoft.com",
    "netflix.com",
    "gmail.com",
    "apple.com",
    "facebook.com",
    "instagram.com",
    "whatsapp.com",
    "paytm.com",
    "phonepe.com",
    "airtel.in",
    "jio.com",
    "vodafone.in",
    "fedex.com",
    "dhl.com",
    "swiggy.com",
    "zomato.com",
    "irctc.co.in",
    "uber.com",
    "olacabs.com",
    "linkedin.com",
    "adobe.com",
    "twitter.com",
    "x.com",
}

SUSPICIOUS_PATH_WORDS = {
    "login",
    "verify",
    "verification",
    "confirm",
    "update",
    "account",
    "security",
    "bank",
    "paypal",
    "secure",
    "unlock",
    "signin",
    "wallet",
    "reward",
    "prize",
    "gift",
    "claim",
    "bonus",
    "promo",
    "track",
    "refund",
    "billing",
    "invoice",
    "otp",
    "kyc",
}

URL_RE = re.compile(r"https?://[^\s]+|www\.[^\s]+", re.IGNORECASE)


class UrlAnalysis:
    """Structured result of the static URL checks."""

    def __init__(self, url: str) -> None:
        norm = url.rstrip(".,;:!?)>]}")
        if not norm.lower().startswith(("http://", "https://")):
            norm = "http://" + norm
        self.url = url
        self.parsed = urlparse(norm)
        self.is_shortened = False
        self.has_ip_host = False
        self.suspicious_tld = False
        self.suspicious_chars = False
        self.path_keywords: list[str] = []
        self.pattern_warnings: list[str] = []
        self._analyze()

    # ------------------------------------------------------------ analysis
    def _analyze(self) -> None:
        host = (self.parsed.hostname or "").lower()
        scheme = self.parsed.scheme.lower()

        if scheme != "https":
            self.pattern_warnings.append("Non-HTTPS link detected")
        if not scheme:
            self.pattern_warnings.append("Link without an explicit protocol")

        # shortening services
        if host in SHORTENERS:
            self.is_shortened = True
            self.pattern_warnings.append("URL is shortened with a known link shortener")

        # raw IP host
        if self._is_ip(host):
            self.has_ip_host = True
            self.pattern_warnings.append(
                "Potentially suspicious URL pattern: host is a raw IP address"
            )

        # brand impersonation (lookalike domains)
        if self._looks_like_brand_impersonation(host):
            self.suspicious_chars = True
            self.pattern_warnings.append(
                "Potentially suspicious URL pattern: domain resembles a known brand "
                "but is not the official domain"
            )

        # suspicious TLD
        tld = self._tld(host)
        if tld in SUSPICIOUS_TLDS:
            self.suspicious_tld = True
            self.pattern_warnings.append(
                f"Potentially suspicious top-level domain (.{tld})"
            )
        if tld and host.count(".") < 1:
            self.suspicious_tld = True
            self.pattern_warnings.append("Unusual one-part domain")

        # obfuscation
        if "@" in host:
            self.suspicious_chars = True
            self.pattern_warnings.append("Suspicious '@' character in the URL")
        if re.search(r"\.\.+", host):
            self.suspicious_chars = True
        if host.startswith("-") or host.endswith("-"):
            self.suspicious_chars = True
            self.pattern_warnings.append("Unusual hyphen placement in domain")
        if "xn--" in host:
            self.suspicious_chars = True
            self.pattern_warnings.append("Punycode/IDN encoding detected")
        if host.count("-") >= 3:
            self.suspicious_chars = True
            self.pattern_warnings.append(
                "Unusually long hyphenated domain (lookalike pattern)"
            )

        # path keywords
        path = (self.parsed.path or "").lower()
        self.path_keywords = [w for w in SUSPICIOUS_PATH_WORDS if w in path]
        if self.path_keywords:
            self.pattern_warnings.append(
                f"URL path contains sensitive keywords: {', '.join(self.path_keywords[:4])}"
            )

    # ------------------------------------------------------------ helpers
    def _looks_like_brand_impersonation(self, host: str) -> bool:
        """True when the host borrows a known brand but is not the official domain."""
        if not host or self._is_ip(host) or host.count(".") < 1:
            return False
        for official in BRAND_DOMAINS:
            if host == official or host.endswith("." + official):
                return False
        host_body = host.split(".")[:-1]
        for word in BRAND_WORDS:
            if (
                word in host_body
                or host.startswith(word + "-")
                or "-" + word + "-" in host
            ):
                return True
        return False

    @staticmethod
    def _is_ip(host: str) -> bool:
        try:
            ipaddress.ip_address(host)
            return True
        except ValueError:
            return False

    @staticmethod
    def _tld(host: str) -> str:
        parts = host.split(".")
        if len(parts) < 2:
            return ""
        return parts[-1]

    @property
    def risk_flags(self) -> int:
        """Number of flagged pattern features (used by the risk engine)."""
        return sum(
            [
                self.has_ip_host,
                self.suspicious_tld,
                self.suspicious_chars,
                1 if len(self.path_keywords) >= 2 else 0,
            ]
        )


def analyze_urls(text: str) -> list[dict]:
    """Analyze all URLs in the text; returns structured results for the API."""
    results: list[dict] = []
    for url in extract_urls(text):
        analysis = UrlAnalysis(url)
        results.append(
            {
                "url": url,
                "scheme": analysis.parsed.scheme or "none",
                "host": analysis.parsed.hostname or "",
                "is_shortened": analysis.is_shortened,
                "has_ip_host": analysis.has_ip_host,
                "suspicious_tld": analysis.suspicious_tld,
                "suspicious_chars": analysis.suspicious_chars,
                "path_keywords": analysis.path_keywords,
                "warnings": analysis.pattern_warnings,
                "flag_count": analysis.risk_flags,
            }
        )
    return results


def analyze_domain(domain: str) -> dict:
    """Analyze a bare domain (e.g. an email sender domain)."""
    if not domain:
        return {"host": "", "warnings": [], "flag_count": 0, "suspicious": False}
    analysis = UrlAnalysis(domain)
    return {
        "host": analysis.parsed.hostname or domain,
        "warnings": analysis.pattern_warnings,
        "flag_count": analysis.risk_flags,
        "suspicious": analysis.risk_flags > 0,
    }
