"""Expanded threat indicator engine (RFC-001 taxonomy, 19 families).

Builds on the existing rule engine (app.ml.indicators) and URL analyzer,
adding credential harvesting, authority abuse, fear/scarcity, reward bait,
lottery/investment/crypto, impersonation, typosquatting/homograph, sensitive
info requests, remote access, malware/attachment/macro delivery signals.
Threat score in 0..1 from severity-weighted evidence.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

from app.ml import indicators as base_indicators
from app.ml.preprocess import extract_urls

_EXTRA_PATTERNS: list[dict] = [
    {"name": "credential_harvesting", "severity": "high", "weight": 1.5,
     "regex": re.compile(r"\b(verify|confirm|update|validate).{0,30}?(login|account|credentials|identity)\b|\b(sign in|log in).{0,20}?to (secure|verify|unlock)\b", re.IGNORECASE)},
    {"name": "authority_abuse", "severity": "high", "weight": 1.2,
     "regex": re.compile(r"\b(rbi|reserve bank|income tax|cbi|court order|police|government).{0,30}?(directs?|orders?|mandates?|freezes?|seizes?)\b", re.IGNORECASE)},
    {"name": "fear", "severity": "medium", "weight": 0.9,
     "regex": re.compile(r"\b(account will be (blocked|frozen|closed|suspended)|legal action|arrest warrant|penalty of|account compromised|fraud detected on)\b", re.IGNORECASE)},
    {"name": "scarcity", "severity": "medium", "weight": 0.8,
     "regex": re.compile(r"\b(only \d+ (left|slots|seats)|first \d+ (callers|users)|offer ends|last day|final (call|notice|reminder))\b", re.IGNORECASE)},
    {"name": "reward_bait", "severity": "high", "weight": 1.2,
     "regex": re.compile(r"\b(free (iphone|gift|recharge|cash)|cashback of|reward points|bonus of).{0,20}?(claim|click|register)\b", re.IGNORECASE)},
    {"name": "lottery", "severity": "high", "weight": 1.3,
     "regex": re.compile(r"\b(lottery|jackpot|lucky draw|winner).{0,30}?(claim|prize|won)\b", re.IGNORECASE)},
    {"name": "investment_scam", "severity": "high", "weight": 1.3,
     "regex": re.compile(r"\b(double your (money|investment)|guaranteed returns|risk-free profit|earn \d+x|daily profit of)\b", re.IGNORECASE)},
    {"name": "crypto_scam", "severity": "high", "weight": 1.3,
     "regex": re.compile(r"\b(send.*(btc|eth|usdt|crypto)|crypto (giveaway|doubling|investment)|wallet (connect|verify|sync))\b", re.IGNORECASE)},
    {"name": "impersonation", "severity": "high", "weight": 1.2,
     "regex": re.compile(r"\b(on behalf of|authorized (representative|agent) of|ceo.*instruct|md.*request|head office.*direct)\b", re.IGNORECASE)},
    {"name": "suspicious_url", "severity": "high", "weight": 1.2,
     "regex": re.compile(r"\b(bit\.ly|tinyurl|t\.co|goo\.gl|is\.gd|cutt\.ly|shorturl)\b", re.IGNORECASE)},
    {"name": "credential_request", "severity": "high", "weight": 1.5,
     "regex": re.compile(r"\b(share|send|tell).{0,20}?(otp|password|pin|cvv|card number)\b", re.IGNORECASE)},
    {"name": "sensitive_info_request", "severity": "high", "weight": 1.3,
     "regex": re.compile(r"\b(aadhaar|pan|passport|bank account|dob|mother'?s maiden).{0,20}?(number|details|share|send|provide)\b", re.IGNORECASE)},
    {"name": "remote_access_request", "severity": "high", "weight": 1.5,
     "regex": re.compile(r"\b(install|download).{0,25}?(anydesk|teamviewer|quicksupport|remote|screen share|apk)\b|\bgrant.*remote access\b", re.IGNORECASE)},
    {"name": "malware_delivery", "severity": "high", "weight": 1.4,
     "regex": re.compile(r"\b(open the attachment|download.*invoice.*\.zip|enable (macros|content|editing)|statement\.scr|payment\.exe)\b", re.IGNORECASE)},
    {"name": "attachment_abuse", "severity": "medium", "weight": 0.9,
     "regex": re.compile(r"\b(see attached|attachment|enclosed (file|document|invoice)|open.*\.pdf\.exe)\b", re.IGNORECASE)},
    {"name": "macro_documents", "severity": "medium", "weight": 0.9,
     "regex": re.compile(r"\b(enable macros|enable content|allow editing|protected view.*enable)\b", re.IGNORECASE)},
]

_SEVERITY_WEIGHT = {"high": 1.0, "medium": 0.55, "low": 0.25}

_FALSE_POSITIVE_GUARDS = [
    # (family to guard, benign-context pattern, evidence allowlist that is benign)
    ("promotion", re.compile(r"toll[\s-]?free", re.IGNORECASE), {"free"}),
]

_CITATION_GUARD = re.compile(r"\b(as per|per|vide|under|circular|order no\.?)\b", re.IGNORECASE)

_IP_HOST = re.compile(r"https?://\d{1,3}(?:\.\d{1,3}){3}")
_PUNYCODE = re.compile(r"xn--", re.IGNORECASE)
_LOOKALike = re.compile(r"(.)\1{2,}|[il1]{3,}|[o0]{3,}")


def _typosquat_signals(urls: list[str]) -> list[dict]:
    out = []
    for url in urls:
        try:
            host = (urlparse(url if "://" in url else "http://" + url).hostname or "").lower()
        except Exception:
            continue
        if not host:
            continue
        if _IP_HOST.search(url):
            out.append({"indicator": "suspicious_url", "family": "suspicious_url",
                        "severity": "high", "weight": 1.2, "evidence": f"raw IP host: {host[:40]}"})
        if _PUNYCODE.search(host):
            out.append({"indicator": "homograph_domain", "family": "homograph",
                        "severity": "high", "weight": 1.4, "evidence": f"punycode host: {host[:40]}"})
        elif _LOOKALike.search(host.replace(".", "")) and len(host) > 12:
            out.append({"indicator": "typosquatting", "family": "typosquatting",
                        "severity": "medium", "weight": 0.9, "evidence": f"irregular host: {host[:40]}"})
    return out


class ThreatEngine:
    """Combine base rule engine + RFC-001 families + URL host analysis."""

    def analyze(self, text: str) -> dict:
        lowered = text or ""
        found: list[dict] = []
        # 1. existing engine (kept verbatim for backward compatibility)
        try:
            base = base_indicators.detect_indicators(lowered)
        except Exception:
            base = []
        for item in base:
            found.append({"indicator": item.get("indicator", "unknown"),
                          "family": item.get("category", "general"),
                          "severity": item.get("severity", "low"),
                          "weight": _SEVERITY_WEIGHT.get(item.get("severity", "low"), 0.25),
                          "evidence": str(item.get("evidence", ""))[:60]})
        # 2. urgency family (explicit RFC category)
        if re.search(r"\b(urgent|immediately|act now|asap|hurry|expires today|last warning)\b",
                     lowered, re.IGNORECASE):
            match = re.search(r"\b(urgent|immediately|act now|asap|hurry|expires today|last warning)\b",
                              lowered, re.IGNORECASE)
            found.append({"indicator": "urgency", "family": "urgency", "severity": "medium",
                          "weight": 0.8, "evidence": match.group(0) if match else "urgency"})
        # 3. extra RFC families (with citation guard for authority_abuse:
        # "as per government order 482/2026" is a circular reference, not abuse)
        for rule in _EXTRA_PATTERNS:
            match = rule["regex"].search(lowered)
            if match:
                if rule["name"] == "authority_abuse":
                    prefix = lowered[max(0, match.start() - 20):match.start()]
                    if _CITATION_GUARD.search(prefix) or _CITATION_GUARD.search(match.group(0)[:20]):
                        continue
                snippet = " ".join(match.group(0).split())[:60]
                found.append({"indicator": rule["name"], "family": rule["name"],
                              "severity": rule["severity"], "weight": rule["weight"],
                              "evidence": snippet})
        # 4. typosquat / homograph on extracted urls
        try:
            urls = extract_urls(lowered)
        except Exception:
            urls = []
        found.extend(_typosquat_signals(urls))
        # dedupe by (family, evidence), then apply FP guards (e.g. "toll free"
        # must not count as promotional language)
        seen: set[tuple[str, str]] = set()
        unique: list[dict] = []
        for item in found:
            key = (item["family"], item["evidence"])
            if key not in seen:
                seen.add(key)
                unique.append(item)
        guarded: list[dict] = []
        for item in unique:
            drop = False
            for family, benign, benign_evidence in _FALSE_POSITIVE_GUARDS:
                if (item["family"] == family and benign.search(lowered)
                        and item.get("evidence", "").strip().lower() in benign_evidence):
                    drop = True
                    break
            if not drop:
                guarded.append(item)
        unique = guarded
        weight_sum = sum(i["weight"] for i in unique)
        threat = round(weight_sum / (weight_sum + 2.5), 3)
        families = sorted({i["family"] for i in unique})
        return {"threat_score": threat, "indicators": unique,
                "count": len(unique), "families": families,
                "weight_sum": round(weight_sum, 2)}


threat_engine = ThreatEngine()
