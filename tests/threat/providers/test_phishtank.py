import pytest

from app.threat.providers.phishtank import PhishTankProvider, PhishTankConfig, PhishTankClient, PhishTankRequest, PhishTankResponse
from app.threat.providers.phishtank.validator import is_valid_url, validate_lookup_input
from app.threat.providers.phishtank.mapper import response_to_indicator, indicator_to_evidence, response_to_evidence


def test_config():
    cfg = PhishTankConfig(api_key="k", ttl=1800)
    assert cfg.ttl == 1800
    d = cfg.to_dict()
    cfg2 = PhishTankConfig.from_dict(d)
    assert cfg2.api_key == "k"


def test_models():
    req = PhishTankRequest(url="http://example.com")
    assert req.url == "http://example.com"
    resp = PhishTankResponse(url="http://a.com", in_database=True, verified=True, valid=True, confidence=0.95)
    assert resp.is_phishing is True
    assert resp.to_dict()["is_phishing"] is True
    resp2 = PhishTankResponse.from_dict(resp.to_dict())
    assert resp2.url == resp.url


def test_validator():
    assert is_valid_url("https://example.com") is True
    assert is_valid_url("bad") is False
    valid, _ = validate_lookup_input("https://example.com", "url")
    assert valid is True


def test_mapper_malicious_verified():
    resp = PhishTankResponse(url="http://phishtank-malicious.com", in_database=True, verified=True, valid=True, confidence=0.95, phish_id="1")
    ind = response_to_indicator(resp)
    assert ind is not None
    assert ind.severity == "critical"
    assert ind.provider == "phishtank"


def test_mapper_malicious_unverified():
    resp = PhishTankResponse(url="http://phishing-test.com", in_database=True, verified=False, valid=True, confidence=0.78)
    ind = response_to_indicator(resp)
    assert ind is not None
    assert ind.severity == "high"


def test_mapper_benign():
    resp = PhishTankResponse(url="http://example.com", in_database=False, valid=False, confidence=0.02)
    assert response_to_indicator(resp) is None


def test_mapper_evidence():
    resp = PhishTankResponse(url="http://phishtank-malicious.com", in_database=True, verified=True, valid=True, confidence=0.95)
    ev = response_to_evidence(resp)
    assert ev is not None
    ind = response_to_indicator(resp)
    ev2 = indicator_to_evidence(ind)
    assert ev2 is not None
    ev3 = indicator_to_evidence({"indicator": "http://x", "indicator_type": "url", "detection_status": "phishing", "confidence": 0.9, "severity": "high", "source": "phishtank", "explanation": "x", "ttl": 1800})
    assert ev3 is not None


@pytest.mark.asyncio
async def test_client_malicious():
    client = PhishTankClient(rate_limit_per_minute=100)
    resp = await client.check_url(PhishTankRequest(url="http://phishtank-malicious.com"))
    assert resp.is_phishing is True
    assert resp.verified is True


@pytest.mark.asyncio
async def test_client_benign():
    client = PhishTankClient(rate_limit_per_minute=100)
    resp = await client.check_url(PhishTankRequest(url="http://example.com"))
    assert resp.is_phishing is False


@pytest.mark.asyncio
async def test_client_cache():
    client = PhishTankClient(rate_limit_per_minute=100)
    req = PhishTankRequest(url="http://phishtank-malicious-cache.com")
    a = await client.check_url(req)
    b = await client.check_url(req)
    assert a.is_phishing == b.is_phishing
    client.clear_cache()
    assert len(client._cache) == 0


@pytest.mark.asyncio
async def test_client_invalid():
    client = PhishTankClient()
    with pytest.raises(ValueError):
        await client.check_url(PhishTankRequest(url="bad"))


@pytest.mark.asyncio
async def test_client_retry():
    client = PhishTankClient(max_retries=2, backoff_factor=0.01)
    calls = {"n": 0}

    async def flaky(url):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("transient")
        return PhishTankResponse(url=url, in_database=True, verified=False, valid=True, confidence=0.8)

    client._do_lookup = flaky  # type: ignore
    resp = await client.check_url(PhishTankRequest(url="http://example.com"))
    assert resp.is_phishing is True


def test_client_rate_limit():
    client = PhishTankClient(rate_limit_per_minute=1)
    import time

    client._request_timestamps = [time.time()]
    assert client._check_rate_limit() is False
    client._request_timestamps = []
    assert client._check_rate_limit() is True


@pytest.mark.asyncio
async def test_provider():
    prov = PhishTankProvider(enabled=True)
    assert prov.name == "phishtank"
    assert "url_reputation" in prov.capabilities()
    assert prov.metadata["name"] == "phishtank"
    prov.initialize()
    assert prov.health_check()["healthy"] is True
    prov.shutdown()
    assert prov._initialized is False


@pytest.mark.asyncio
async def test_provider_lookup():
    prov = PhishTankProvider(enabled=True)
    ind = await prov.lookup_url("http://phishtank-malicious.com")
    assert ind is not None
    assert await prov.lookup_url("http://example.com") is None
    assert await prov.lookup_url("bad-url") is None
    prov.enabled = False
    assert await prov.lookup_url("http://phishtank-malicious.com") is None
    prov.enabled = True
    assert await prov.lookup_domain("example.com") is None
    assert await prov.lookup_ip("1.1.1.1") is None
    assert await prov.lookup_hash("abcd") is None
    # request object
    class Req:
        ioc = "http://phishtank-malicious-req.com"

    assert await prov.lookup_url(Req()) is not None  # type: ignore


@pytest.mark.asyncio
async def test_provider_graceful():
    prov = PhishTankProvider(enabled=True)

    async def fail(*a, **kw):
        raise RuntimeError("boom")

    prov._client.check_url = fail  # type: ignore
    assert await prov.lookup_url("http://phishtank-malicious.com") is None
    assert prov._error_count >= 1


def test_provider_dict():
    prov = PhishTankProvider(api_key="k")
    d = prov.to_dict()
    assert d["api_key_configured"] is True
    prov2 = PhishTankProvider.from_dict({"api_key": "k"})
    assert prov2._api_key == "k"
