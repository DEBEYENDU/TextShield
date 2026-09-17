"""RFC-008 provider tests: extraction, normalization, registry, mock,
failures, offline mode, cache, rate limiting, privacy, aggregation."""

from __future__ import annotations

import time

import pytest

from app.threat_intel import aggregator as aggregator_mod
from app.threat_intel.cache import ThreatIntelCache
from app.threat_intel.config import ThreatIntelConfig
from app.threat_intel.exceptions import PrivacyViolationError, RateLimitExceededError
from app.threat_intel.extractor import extract_iocs
from app.threat_intel.manager import build_default_manager
from app.threat_intel.models import IOC, ProviderResult
from app.threat_intel.normalizer import normalize_all, normalize_url
from app.threat_intel.privacy import PrivacyPolicy
from app.threat_intel.providers.google_safe_browsing import GoogleSafeBrowsingAdapter
from app.threat_intel.providers.mock import MockProvider
from app.threat_intel.providers.static import static_assess_url
from app.threat_intel.providers.virustotal import VirusTotalAdapter
from app.threat_intel.rate_limit import ProviderRateLimiter
from app.threat_intel.registry import ThreatIntelRegistry


# ------------------------------------------------------------ extraction
def test_extract_url_domain_ip_email_hash():
    iocs = extract_iocs("Visit http://bit.ly/x or example.com, mail a@b.com, "
                        "host 8.8.8.8 hash " + "a" * 64)
    by_type = {}
    for ioc in iocs:
        by_type.setdefault(ioc.ioc_type, []).append(ioc.original_value)
    assert any("bit.ly" in v for v in by_type.get("url", []))
    assert "example.com" in by_type.get("domain", [])
    assert "a@b.com" in by_type.get("email", [])
    assert "8.8.8.8" in by_type.get("ipv4", [])
    assert any(len(v) == 64 for v in by_type.get("sha256", []))


def test_no_bare_numbers_as_ips_or_words_as_domains():
    iocs = extract_iocs("Call 99999 88888 about hello world meeting tomorrow")
    assert not [i for i in iocs if i.ioc_type == "ipv4"]
    assert not [i for i in iocs if i.ioc_type == "domain"]
    bad = extract_iocs("version 999.999.999.999 released")
    assert not [i for i in bad if i.ioc_type == "ipv4"]


def test_ipv6_and_hash_lengths():
    iocs = extract_iocs("peer 2001:0db8:85a3:0000:0000:8a2e:0370:7334 md5 " + "b" * 32)
    assert any(i.ioc_type == "ipv6" for i in iocs)
    assert any(i.ioc_type == "md5" for i in iocs)


# ------------------------------------------------------------ normalization
def test_normalization_preserves_original():
    iocs = normalize_all(extract_iocs("Visit HTTPS://Bit.Ly/X?a=1, mail A@Example.COM"))
    url = next(i for i in iocs if i.ioc_type == "url")
    assert url.original_value.startswith("HTTPS://")
    assert url.normalized_value.startswith("https://bit.ly/")
    email = next(i for i in iocs if i.ioc_type == "email")
    assert email.normalized_value.endswith("@example.com")


def test_normalize_url_idna_ports_encoding():
    assert normalize_url("http://example.com:80/a%20b").startswith("http://example.com/a")
    assert "xn--" in normalize_url("http://münchen.de/x")


# ------------------------------------------------------------ registry & interface
def test_registry_register_unregister_list():
    registry = ThreatIntelRegistry()
    mock = MockProvider()
    registry.register(mock)
    assert registry.get_provider("mock") is mock
    assert "mock" in registry.list_providers()
    assert registry.unregister("mock") is True
    assert registry.get_provider("mock") is None


def test_provider_interface_defaults_unsupported():
    mock = MockProvider()
    email_result = mock.lookup_email("a@b.com")
    assert email_result.verdict == "unsupported"


# ------------------------------------------------------------ mock provider
def test_mock_verdicts():
    mock = MockProvider()
    assert mock.lookup_url("http://bit.ly/sbi-kyc-verify").verdict == "known_malicious"
    assert mock.lookup_domain("example.com").verdict == "benign"
    assert mock.lookup_domain("brand-new-xyz123.info").verdict == "unknown"


# ------------------------------------------------------------ offline / failure
def test_adapters_unavailable_without_keys():
    cfg = ThreatIntelConfig(google_safe_browsing_key="", virustotal_key="")
    gsb = GoogleSafeBrowsingAdapter(cfg)
    vt = VirusTotalAdapter(cfg)
    assert gsb.is_configured() is False
    assert vt.is_configured() is False
    assert gsb.lookup_url("http://example.com").provider_status == "unavailable"
    assert vt.lookup_hash("a" * 64).provider_status == "unavailable"


def test_manager_offline_full_pipeline(tmp_path):
    cfg = ThreatIntelConfig(google_safe_browsing_key="", virustotal_key="",
                            cache_path=str(tmp_path / "cache.json"))
    manager = build_default_manager(cfg)
    out = manager.check_message("Verify at http://bit.ly/sbi-kyc-91 now!")
    assert out["worst_verdict"] == "known_malicious"
    assert out["n_iocs"] >= 1
    benign = manager.check_message("Team lunch tomorrow at 1 PM.")
    assert benign["worst_verdict"] in {"unknown", "benign"}


# ------------------------------------------------------------ cache
def test_cache_hit_miss_expiry(tmp_path):
    cache = ThreatIntelCache(path=tmp_path / "c.json", default_ttl=60)
    assert cache.get("url", "http://x.test", "mock") is None
    result = ProviderResult(ioc="http://x.test", ioc_type="url",
                            provider="mock", verdict="suspicious",
                            confidence=0.5)
    cache.put(result)
    assert cache.get("url", "http://x.test", "mock") is not None
    assert cache.stats()["hits"] == 1
    expired = ThreatIntelCache(path=tmp_path / "c2.json", default_ttl=-1)
    expired.put(ProviderResult(ioc="http://y.test", ioc_type="url",
                               provider="mock", verdict="benign"))
    assert expired.get("url", "http://y.test", "mock") is None
    assert expired.purge_expired() >= 0


# ------------------------------------------------------------ rate limiting
def test_rate_limit_blocks_and_recovers():
    limiter = ProviderRateLimiter({"demo": (2, 100)})
    assert limiter.allow("demo") is True
    limiter.record("demo")
    limiter.record("demo")
    assert limiter.allow("demo") is False
    with pytest.raises(RateLimitExceededError):
        limiter.check("demo")
    assert limiter.allow("unlimited-provider") is True


# ------------------------------------------------------------ privacy
def test_privacy_shares_ioc_only():
    policy = PrivacyPolicy()
    url_ioc = IOC("http://bit.ly/x", "http://bit.ly/x", "url")
    assert policy.shareable_value(url_ioc) == "http://bit.ly/x"
    email_ioc = IOC("A@Example.COM", "a@example.com", "email")
    shared = policy.shareable_value(email_ioc)
    assert shared.startswith("email-hash:") and "example.com" not in shared
    with pytest.raises(PrivacyViolationError):
        policy.shareable_value(IOC("whatever", "whatever", "qr_code_url"))
    assert PrivacyPolicy(allow_external=False).check(url_ioc) is False


# ------------------------------------------------------------ aggregation
def test_aggregation_malicious_wins_and_disagreement_kept():
    results = [
        ProviderResult(ioc="e.com", ioc_type="domain", provider="mock",
                       verdict="known_malicious", confidence=0.8),
        ProviderResult(ioc="e.com", ioc_type="domain", provider="static",
                       verdict="unknown", confidence=0.0),
    ]
    out = aggregator_mod.aggregate("e.com", "domain", results)
    assert out["aggregated_verdict"] == "known_malicious"
    assert out["threat_level"] == "HIGH"
    assert out["disagreement"] is True
    assert len(out["results"]) == 2


def test_aggregation_unknown_never_safe():
    out = aggregator_mod.aggregate("new-xyz.test", "domain", [
        ProviderResult(ioc="new-xyz.test", ioc_type="domain",
                       provider="mock", verdict="unknown")])
    assert out["aggregated_verdict"] == "unknown"
    assert out["threat_level"] == "UNKNOWN"


def test_aggregation_conflicting_providers():
    out = aggregator_mod.aggregate("x.test", "domain", [
        ProviderResult(ioc="x.test", ioc_type="domain", provider="a",
                       verdict="suspicious", confidence=0.6),
        ProviderResult(ioc="x.test", ioc_type="domain", provider="b",
                       verdict="benign", confidence=0.7)])
    assert out["disagreement"] is True
    assert out["aggregated_verdict"] in {"suspicious", "unknown", "benign"}


# ------------------------------------------------------------ static analysis
def test_static_shortener_typosquat_ip():
    verdict, _, evidence = static_assess_url("http://bit.ly/claim-prize-now")
    assert verdict in {"known_malicious", "suspicious"}
    verdict, _, _ = static_assess_url("http://hdfccbank-secure.com/login")
    assert verdict in {"known_malicious", "suspicious"}
    verdict, _, _ = static_assess_url("http://192.168.5.5/login")
    assert verdict in {"known_malicious", "suspicious"}
    verdict, _, _ = static_assess_url("https://www.google.com/search?q=hi")
    assert verdict == "benign"
