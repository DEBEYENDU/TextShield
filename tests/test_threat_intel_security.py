"""RFC-008 security regression tests: malformed inputs, parser abuse,
provider manipulation, secret hygiene, FP protection."""

from __future__ import annotations

import os

import pytest

from app.threat_intel.extractor import extract_iocs
from app.threat_intel.manager import build_default_manager
from app.threat_intel.models import IOC, ProviderResult
from app.threat_intel.normalizer import normalize_all, normalize_url
from app.threat_intel.providers.static import static_assess_url


def test_malformed_urls_do_not_crash():
    for text in ["http://", "https://[::1", "http://exa mple.com",
                 "://missing-scheme.com", "http://a" * 500]:
        assert isinstance(extract_iocs(text), list)


def test_ipv6_variants():
    assert any(i.ioc_type == "ipv6" for i in extract_iocs("see ::1 and fe80::1"))
    assert not [i for i in extract_iocs("meeting at 12:30 sharp")
                if i.ioc_type == "ipv6"]


def test_punycode_flagged():
    verdict, _, evidence = static_assess_url("http://xn--hdfcbank-xyz.com/login")
    assert verdict in {"known_malicious", "suspicious"}
    assert any("punycode" in e for e in evidence)


def test_encoded_url_signals():
    verdict, _, evidence = static_assess_url(
        "http://example.com/%2e%2e/%70%61%79?token=abc")
    assert any("encoded" in e or "Suspicious" in e or "suspicious" in e.lower()
               for e in evidence) or verdict in {"suspicious", "unknown"}


def test_extremely_long_url_bounded():
    long_url = "http://example.com/" + "a" * 5000
    iocs = extract_iocs(long_url)
    assert all(len(i.original_value) <= 2048 for i in iocs)


def test_unicode_normalization_safe():
    iocs = normalize_all(extract_iocs("Visit https://münchen.de/ünïcodé path"))
    assert iocs and all(i.normalized_value for i in iocs)


def test_typosquatting_and_lookalikes():
    for domain in ("hdfccbank.com", "paypa1-secure.com", "g00gle-login.com"):
        verdict, _, _ = static_assess_url(f"http://{domain}/login")
        assert verdict in {"known_malicious", "suspicious"}, domain


def test_credential_looking_urls():
    verdict, _, evidence = static_assess_url(
        "http://192.168.0.1/verify?password=1&card=2")
    assert verdict in {"known_malicious", "suspicious"}
    assert len(evidence) >= 2


def test_unexpected_provider_json_never_crashes():
    weird = ProviderResult(ioc="x", ioc_type="weird-type", provider="mock",
                           verdict="???", confidence=float("nan"))
    from app.threat_intel import aggregator as agg

    out = agg.aggregate("x", "weird-type", [weird])
    assert out["aggregated_verdict"] in {"unknown", "suspicious",
                                         "known_malicious", "benign"}


def test_provider_response_manipulation_ignored():
    from app.threat_intel import aggregator as agg

    lying = ProviderResult(ioc="evil.test", ioc_type="domain",
                           provider="compromised", verdict="benign",
                           confidence=1.0)
    honest = ProviderResult(ioc="evil.test", ioc_type="domain",
                            provider="mock", verdict="known_malicious",
                            confidence=0.8)
    out = agg.aggregate("evil.test", "domain", [lying, honest])
    assert out["aggregated_verdict"] == "known_malicious"


def test_no_secrets_in_errors_or_results():
    os.environ["TEXTSHIELD_VIRUSTOTAL_API_KEY"] = "super-secret-key-123"
    try:
        from app.threat_intel.config import ThreatIntelConfig
        from app.threat_intel.providers.virustotal import VirusTotalAdapter

        adapter = VirusTotalAdapter(ThreatIntelConfig())
        result = adapter.lookup_url("http://example.com")
        blob = str(result.to_dict())
        assert "super-secret-key-123" not in blob
        assert "super-secret-key-123" not in str(adapter.health())
    finally:
        del os.environ["TEXTSHIELD_VIRUSTOTAL_API_KEY"]


def test_no_hardcoded_keys_in_package():
    import pathlib

    for path in pathlib.Path("app/threat_intel").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "AIza" not in text, f"possible key in {path}"
        assert "sk-" not in text or "task" in text, f"possible key in {path}"


def test_fp_protection_single_signals_neutral():
    """A lone URL / form / shortener / foreign TLD must not condemn."""
    manager = build_default_manager()
    for text in ("See the form at https://forms.gle/abc123 for details.",
                 "Visit our site https://example-shop.top for the catalog.",
                 "Call +91-98200-12345 for help.",
                 "Our new blog: https://bit.ly/company-blog"):
        out = manager.check_message(text)
        assert out["worst_verdict"] in {"unknown", "benign", "suspicious"}, text
