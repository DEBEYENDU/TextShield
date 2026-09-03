import asyncio
import pytest

from app.threat.providers.openphish import (
    OpenPhishProvider,
    OpenPhishConfig,
    OpenPhishClient,
    OpenPhishRequest,
    OpenPhishResponse,
)
from app.threat.providers.openphish.validator import is_valid_url, sanitize_url, validate_lookup_input
from app.threat.providers.openphish.mapper import response_to_indicator, indicator_to_evidence, response_to_evidence


# ------------------------------------------------------------------ config
def test_config_defaults():
    cfg = OpenPhishConfig()
    assert cfg.ttl == 3600
    assert cfg.enabled is True
    assert cfg.feed_url == "https://openphish.com/feed.txt"


def test_config_to_from_dict():
    cfg = OpenPhishConfig(api_key="k", ttl=123)
    d = cfg.to_dict()
    cfg2 = OpenPhishConfig.from_dict(d)
    assert cfg2.api_key == "k"
    assert cfg2.ttl == 123


# ------------------------------------------------------------------ models
def test_models_request_response():
    req = OpenPhishRequest(url="http://example.com")
    assert req.url == "http://example.com"
    resp = OpenPhishResponse(url="http://example.com", is_phishing=True, confidence=0.9)
    assert resp.is_phishing is True
    d = resp.to_dict()
    resp2 = OpenPhishResponse.from_dict(d)
    assert resp2.url == resp.url
    assert resp2.is_phishing == resp.is_phishing


# ------------------------------------------------------------------ validator
def test_validator_url():
    assert is_valid_url("https://example.com") is True
    assert is_valid_url("http://example.com/phish") is True
    assert is_valid_url("not-a-url") is False
    assert is_valid_url("") is False
    valid, _ = validate_lookup_input("https://example.com", "url")
    assert valid is True
    valid, msg = validate_lookup_input("bad", "url")
    assert valid is False


def test_sanitize_url():
    assert sanitize_url("Example.COM/path") == "http://example.com/path"
    assert sanitize_url("https://Example.COM:443/a") == "https://example.com/a"


# ------------------------------------------------------------------ mapper
def test_mapper_response_to_indicator_malicious():
    resp = OpenPhishResponse(url="http://test-openphish-malicious.com", is_phishing=True, confidence=0.92)
    ind = response_to_indicator(resp, ttl=3600)
    assert ind is not None
    assert ind.provider == "openphish"
    assert ind.detection_status == "phishing"
    assert ind.confidence == 0.92


def test_mapper_response_to_indicator_benign():
    resp = OpenPhishResponse(url="http://example.com", is_phishing=False, confidence=0.05)
    assert response_to_indicator(resp) is None


def test_mapper_indicator_to_evidence():
    resp = OpenPhishResponse(url="http://test-openphish-malicious.com", is_phishing=True, confidence=0.92)
    ind = response_to_indicator(resp)
    ev = indicator_to_evidence(ind)
    # evidence may be dict or object; handle both
    if isinstance(ev, dict):
        assert ev["indicator"] == "http://test-openphish-malicious.com"
        assert ev["source"] == "openphish"
    else:
        assert ev.indicator == "http://test-openphish-malicious.com"


def test_mapper_response_to_evidence():
    resp = OpenPhishResponse(url="http://test-openphish-malicious.com", is_phishing=True, confidence=0.88)
    ev = response_to_evidence(resp)
    assert ev is not None


def test_mapper_dict_input():
    ev = indicator_to_evidence({"indicator": "http://x.com", "indicator_type": "url", "detection_status": "phishing", "confidence": 0.9, "severity": "high", "source": "openphish", "explanation": "x", "ttl": 3600})
    assert ev is not None


# ------------------------------------------------------------------ client
@pytest.mark.asyncio
async def test_client_check_url_malicious_and_benign():
    client = OpenPhishClient(rate_limit_per_minute=100)
    # malicious trigger
    resp = await client.check_url(OpenPhishRequest(url="http://openphish-malicious-test.com"))
    assert resp.is_phishing is True
    # benign
    resp2 = await client.check_url(OpenPhishRequest(url="http://example.com"))
    assert resp2.is_phishing is False


@pytest.mark.asyncio
async def test_client_cache():
    client = OpenPhishClient(rate_limit_per_minute=100)
    req = OpenPhishRequest(url="http://openphish-malicious-unique-cache.com")
    first = await client.check_url(req)
    second = await client.check_url(req)
    # second should be cached (same object identity or equal)
    assert second.is_phishing == first.is_phishing
    assert len(client._cache) >= 1
    client.clear_cache()
    assert len(client._cache) == 0


@pytest.mark.asyncio
async def test_client_invalid_url_raises():
    client = OpenPhishClient()
    with pytest.raises(ValueError):
        await client.check_url(OpenPhishRequest(url="not-a-url"))


@pytest.mark.asyncio
async def test_client_retry():
    client = OpenPhishClient(max_retries=2, backoff_factor=0.01)
    calls = {"n": 0}

    async def flaky(url):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("transient")
        return OpenPhishResponse(url=url, is_phishing=True, confidence=0.9)

    client._do_lookup = flaky  # type: ignore
    resp = await client.check_url(OpenPhishRequest(url="http://example.com"))
    assert resp.is_phishing is True
    assert calls["n"] == 2


@pytest.mark.asyncio
async def test_client_rate_limit():
    client = OpenPhishClient(rate_limit_per_minute=2)
    # fill timestamps to trigger limit
    import time

    client._request_timestamps = [time.time(), time.time()]
    assert client._check_rate_limit() is False
    # wait logic should allow after old timestamps expire - simulate by clearing
    client._request_timestamps = []
    assert client._check_rate_limit() is True


# ------------------------------------------------------------------ provider
@pytest.mark.asyncio
async def test_provider_lifecycle():
    prov = OpenPhishProvider(enabled=True)
    assert prov.enabled is True
    assert prov.name == "openphish"
    assert "url_reputation" in prov.capabilities()
    meta = prov.metadata
    assert meta["name"] == "openphish"
    prov.initialize()
    assert prov._initialized is True
    hc = prov.health_check()
    assert hc["healthy"] is True
    prov.shutdown()
    assert prov._initialized is False


def test_provider_enabled_toggle():
    prov = OpenPhishProvider(enabled=True)
    prov.enabled = False
    assert prov.enabled is False
    meta = prov.metadata
    assert meta["enabled"] is False


def test_provider_to_from_dict():
    prov = OpenPhishProvider(api_key="k")
    d = prov.to_dict()
    prov2 = OpenPhishProvider.from_dict({"api_key": "k", "enabled": True})
    assert prov2._api_key == "k"


@pytest.mark.asyncio
async def test_provider_lookup_url_malicious():
    prov = OpenPhishProvider(enabled=True)
    ind = await prov.lookup_url("http://openphish-malicious-test.com")
    assert ind is not None
    assert ind.provider == "openphish"


@pytest.mark.asyncio
async def test_provider_lookup_url_benign():
    prov = OpenPhishProvider(enabled=True)
    ind = await prov.lookup_url("http://example.com")
    assert ind is None


@pytest.mark.asyncio
async def test_provider_lookup_url_invalid():
    prov = OpenPhishProvider(enabled=True)
    ind = await prov.lookup_url("not-a-url")
    assert ind is None


@pytest.mark.asyncio
async def test_provider_disabled_returns_none():
    prov = OpenPhishProvider(enabled=False)
    ind = await prov.lookup_url("http://openphish-malicious-test.com")
    assert ind is None


@pytest.mark.asyncio
async def test_provider_lookup_domain_ip_hash_graceful():
    prov = OpenPhishProvider(enabled=True)
    assert await prov.lookup_domain("example.com") is None
    assert await prov.lookup_ip("8.8.8.8") is None
    assert await prov.lookup_hash("abcd") is None


@pytest.mark.asyncio
async def test_provider_lookup_with_request_object():
    prov = OpenPhishProvider(enabled=True)

    class Req:
        ioc = "http://openphish-malicious-req.com"

    ind = await prov.lookup_url(Req())  # type: ignore
    assert ind is not None


@pytest.mark.asyncio
async def test_provider_graceful_degrade_on_client_failure():
    prov = OpenPhishProvider(enabled=True)

    async def fail(*a, **kw):
        raise RuntimeError("boom")

    prov._client.check_url = fail  # type: ignore
    ind = await prov.lookup_url("http://openphish-malicious-test.com")
    assert ind is None  # graceful
    assert prov._error_count >= 1
    hc = prov.health_check()
    assert "error_count" in hc
