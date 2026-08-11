"""Tests for URL extraction and static URL analysis."""
from __future__ import annotations

from app.ml.preprocess import extract_urls
from app.ml.url_analyzer import UrlAnalysis, analyze_domain, analyze_urls


def test_extract_urls_basic():
    assert extract_urls("go to http://example.com now") == ["http://example.com"]


def test_shortened_url_flagged():
    analysis = UrlAnalysis("https://bit.ly/3xYzAb")
    assert analysis.is_shortened
    assert "shortened" in " ".join(analysis.pattern_warnings).lower()


def test_ip_host_flagged():
    analysis = UrlAnalysis("http://185.220.101.5/login")
    assert analysis.has_ip_host


def test_suspicious_tld_flagged():
    analysis = UrlAnalysis("https://claim-prize.xyz")
    assert analysis.suspicious_tld
    warnings = " ".join(analysis.pattern_warnings).lower()
    assert "suspicious" in warnings


def test_sensitive_path_keywords():
    analysis = UrlAnalysis("https://free-gift.site/verify-account-login")
    assert "verify" in analysis.path_keywords
    assert "login" in analysis.path_keywords


def test_lookalike_hyphenated_domain_flagged():
    analysis = UrlAnalysis("https://paypal-secure-verify-login.tk")
    assert analysis.risk_flags >= 1


def test_normal_url_no_warnings():
    analysis = UrlAnalysis("https://icicibank.com/Login")
    warnings = " ".join(analysis.pattern_warnings).lower()
    assert "suspicious" not in warnings
    assert analysis.risk_flags == 0


def test_analyze_urls_returns_structured_list():
    results = analyze_urls("click http://bit.ly/abc and https://icicibank.com/home")
    assert len(results) == 2
    assert results[0]["is_shortened"]
    assert results[1]["host"] == "icicibank.com"
    for item in results:
        assert "warnings" in item and "flag_count" in item


def test_analyze_domain_utility():
    result = analyze_domain("secure-update-bank.xyz")
    assert result["suspicious"]
    assert not analyze_domain("gmail.com")["suspicious"]
    assert analyze_domain("")["host"] == ""


def test_wording_is_cautious():
    # TextShield must never claim a URL is definitely malicious
    analysis = UrlAnalysis("http://185.220.101.5")
    joined = " ".join(analysis.pattern_warnings).lower()
    assert "malicious" not in joined
    assert "potentially" in joined or "pattern" in joined or "suspicious" in joined