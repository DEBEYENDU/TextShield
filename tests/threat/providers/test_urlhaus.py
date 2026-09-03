import pytest
from app.threat.providers.urlhaus import URLhausProvider, URLhausConfig, URLhausClient, URLhausRequest, URLhausResponse
from app.threat.providers.urlhaus.validator import is_valid_url, validate_lookup_input
from app.threat.providers.urlhaus.mapper import response_to_indicator, indicator_to_evidence, response_to_evidence


def test_config():
    cfg = URLhausConfig(ttl=600)
    assert cfg.ttl == 600
    d = cfg.to_dict()
    assert URLhausConfig.from_dict(d).ttl == 600


def test_models():
    req = URLhausRequest(url="http://example.com")
    assert req.url == "http://example.com"
    resp = URLhausResponse(url="http://a.com", query_status="ok", threat="malware_download", confidence=0.91)
    assert resp.is_malicious is True
    assert resp.to_dict()["is_malicious"] is True
    assert URLhausResponse.from_dict(resp.to_dict()).url == resp.url


def test_validator():
    assert is_valid_url("https://example.com/malware") is True
    assert is_valid_url("bad") is False
    valid, _ = validate_lookup_input("https://example.com", "url")
    assert valid is True
    valid, msg = validate_lookup_input("http://example.com", "ip")
    assert valid is False


def test_mapper_malicious():
    resp = URLhausResponse(url="http://urlhaus-malicious.com/malware.exe", query_status="ok", threat="malware_download", confidence=0.91, payloads=[{"signature": "test"}])
    ind = response_to_indicator(resp)
    assert ind is not None
    assert ind.provider == "urlhaus"
    assert ind.detection_status == "malware"
    # ransomware should be critical
    resp2 = URLhausResponse(url="http://urlhaus-malicious.com/ransomware", query_status="ok", threat="ransomware", confidence=0.91)
    assert response_to_indicator(resp2).severity == "critical"


def test_mapper_benign():
    resp = URLhausResponse(url="http://example.com", query_status="no_results", confidence=0.03)
    assert response_to_indicator(resp) is None


def test_mapper_evidence():
    resp = URLhausResponse(url="http://urlhaus-malicious.com/malware", query_status="ok", threat="malware_download", confidence=0.91)
    assert response_to_evidence(resp) is not None
    assert indicator_to_evidence(response_to_indicator(resp)) is not None
    assert indicator_to_evidence({"indicator": "http://x", "indicator_type": "url", "detection_status": "malware", "confidence": 0.9, "severity": "high", "source": "urlhaus", "explanation": "x", "ttl": 600}) is not None


@pytest.mark.asyncio
async def test_client():
    client = URLhausClient(rate_limit_per_minute=100)
    resp = await client.check_url(URLhausRequest(url="http://urlhaus-malicious-test.com"))
    assert resp.is_malicious is True
    resp2 = await client.check_url(URLhausRequest(url="http://example.com"))
    assert resp2.is_malicious is False


@pytest.mark.asyncio
async def test_client_cache():
    client = URLhausClient(rate_limit_per_minute=100)
    req = URLhausRequest(url="http://urlhaus-malicious-cache.com")
    a = await client.check_url(req)
    b = await client.check_url(req)
    assert a.is_malicious == b.is_malicious
    client.clear_cache()
    assert len(client._cache) == 0


@pytest.mark.asyncio
async def test_client_invalid():
    client = URLhausClient()
    with pytest.raises(ValueError):
        await client.check_url(URLhausRequest(url="bad"))


@pytest.mark.asyncio
async def test_client_retry():
    client = URLhausClient(max_retries=2, backoff_factor=0.01)
    calls = {"n": 0}

    async def flaky(url):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("transient")
        return URLhausResponse(url=url, query_status="ok", threat="malware_download", confidence=0.9)

    client._do_lookup = flaky  # type: ignore
    resp = await client.check_url(URLhausRequest(url="http://example.com"))
    assert resp.is_malicious is True


def test_rate_limit():
    client = URLhausClient(rate_limit_per_minute=1)
    import time

    client._request_timestamps = [time.time()]
    assert client._check_rate_limit() is False


@pytest.mark.asyncio
async def test_provider():
    prov = URLhausProvider(enabled=True)
    assert prov.name == "urlhaus"
    assert "malware_url_detection" in prov.capabilities()
    prov.initialize()
    assert prov.health_check()["healthy"] is True
    ind = await prov.lookup_url("http://urlhaus-malicious-test.com")
    assert ind is not None
    assert await prov.lookup_url("http://example.com") is None
    assert await prov.lookup_url("bad") is None
    prov.enabled = False
    assert await prov.lookup_url("http://urlhaus-malicious-test.com") is None
    prov.enabled = True
    assert await prov.lookup_domain("example.com") is None
    assert await prov.lookup_ip("1.1.1.1") is None
    assert await prov.lookup_hash("abcd") is None
    class Req:
        ioc = "http://urlhaus-malicious-req.com"
    assert await prov.lookup_url(Req()) is not None  # type: ignore
    prov.shutdown()
    assert prov._initialized is False


@pytest.mark.asyncio
async def test_provider_graceful():
    prov = URLhausProvider(enabled=True)

    async def fail(*a, **kw):
        raise RuntimeError("boom")

    prov._client.check_url = fail  # type: ignore
    assert await prov.lookup_url("http://urlhaus-malicious.com") is None


def test_provider_dict():
    prov = URLhausProvider(api_key="k")
    assert prov.to_dict()["api_key_configured"] is True
    assert URLhausProvider.from_dict({"api_key": "k"})._api_key == "k"
