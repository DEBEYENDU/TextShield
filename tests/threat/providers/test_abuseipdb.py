import pytest
from app.threat.providers.abuseipdb import AbuseIPDBProvider, AbuseIPDBConfig, AbuseIPDBClient, AbuseIPDBRequest, AbuseIPDBResponse
from app.threat.providers.abuseipdb.validator import is_valid_ipv4, is_valid_ipv6, is_valid_ip, validate_lookup_input
from app.threat.providers.abuseipdb.mapper import response_to_indicator, indicator_to_evidence, response_to_evidence


def test_config():
    cfg = AbuseIPDBConfig(api_key="k", abuse_threshold=30)
    assert cfg.abuse_threshold == 30
    assert AbuseIPDBConfig.from_dict(cfg.to_dict()).abuse_threshold == 30


def test_models():
    req = AbuseIPDBRequest(ip_address="1.1.1.1")
    assert req.ip_address == "1.1.1.1"
    resp = AbuseIPDBResponse(ip_address="203.0.113.1", abuse_confidence_score=92, total_reports=42)
    assert resp.is_malicious is True
    assert resp.to_dict()["is_malicious"] is True
    assert AbuseIPDBResponse.from_dict(resp.to_dict()).ip_address == resp.ip_address
    # whitelisted not malicious
    resp2 = AbuseIPDBResponse(ip_address="8.8.8.8", abuse_confidence_score=90, is_whitelisted=True)
    assert resp2.is_malicious is False


def test_validator():
    assert is_valid_ipv4("1.1.1.1") is True
    assert is_valid_ipv4("999.1.1.1") is False
    assert is_valid_ipv6("2001:db8::1") is True
    assert is_valid_ip("1.1.1.1") is True
    assert is_valid_ip("2001:db8::1") is True
    assert is_valid_ip("bad") is False
    valid, _ = validate_lookup_input("1.1.1.1", "ip")
    assert valid is True
    valid, msg = validate_lookup_input("bad", "ip")
    assert valid is False
    valid, msg = validate_lookup_input("1.1.1.1", "url")
    assert valid is False


def test_mapper_malicious():
    resp = AbuseIPDBResponse(ip_address="203.0.113.1", abuse_confidence_score=92, total_reports=10, num_distinct_users=5)
    ind = response_to_indicator(resp)
    assert ind is not None
    assert ind.provider == "abuseipdb"
    assert ind.severity == "critical"
    assert ind.indicator_type.value in ("ipv4", "ip")
    # medium threshold 25-49
    resp2 = AbuseIPDBResponse(ip_address="203.0.113.2", abuse_confidence_score=30)
    assert response_to_indicator(resp2).severity == "medium"
    # high 50-74
    resp3 = AbuseIPDBResponse(ip_address="203.0.113.3", abuse_confidence_score=60)
    assert response_to_indicator(resp3).severity == "high"


def test_mapper_benign():
    resp = AbuseIPDBResponse(ip_address="8.8.8.8", abuse_confidence_score=0, is_whitelisted=True)
    assert response_to_indicator(resp) is None
    resp2 = AbuseIPDBResponse(ip_address="1.1.1.1", abuse_confidence_score=5)
    assert response_to_indicator(resp2) is None


def test_mapper_evidence():
    resp = AbuseIPDBResponse(ip_address="203.0.113.1", abuse_confidence_score=92)
    assert response_to_evidence(resp) is not None
    ind = response_to_indicator(resp)
    assert indicator_to_evidence(ind) is not None
    # ipv6
    resp6 = AbuseIPDBResponse(ip_address="2001:db8::1", abuse_confidence_score=78)
    assert response_to_indicator(resp6).indicator_type.value == "ipv6"
    assert indicator_to_evidence({"indicator": "1.1.1.1", "indicator_type": "ipv4", "detection_status": "malicious", "confidence": 0.9, "severity": "high", "source": "abuseipdb", "explanation": "x", "ttl": 900}) is not None


@pytest.mark.asyncio
async def test_client_malicious():
    client = AbuseIPDBClient(rate_limit_per_minute=100)
    resp = await client.check_ip(AbuseIPDBRequest(ip_address="203.0.113.1"))
    assert resp.is_malicious is True
    assert resp.abuse_confidence_score == 92


@pytest.mark.asyncio
async def test_client_benign_whitelisted():
    client = AbuseIPDBClient(rate_limit_per_minute=100)
    resp = await client.check_ip(AbuseIPDBRequest(ip_address="8.8.8.8"))
    assert resp.is_malicious is False
    assert resp.is_whitelisted is True


@pytest.mark.asyncio
async def test_client_ipv6():
    client = AbuseIPDBClient(rate_limit_per_minute=100)
    resp = await client.check_ip(AbuseIPDBRequest(ip_address="2001:db8::1"))
    assert resp.is_malicious is True
    # benign ipv6
    resp2 = await client.check_ip(AbuseIPDBRequest(ip_address="2001:db8:abcd:0012::1"))
    # depends on heuristic: 2001:db8:: covers malicious, other may be benign - just check not crash
    assert resp2 is not None


@pytest.mark.asyncio
async def test_client_cache():
    client = AbuseIPDBClient(rate_limit_per_minute=100)
    req = AbuseIPDBRequest(ip_address="203.0.113.5")
    a = await client.check_ip(req)
    b = await client.check_ip(req)
    assert a.is_malicious == b.is_malicious
    client.clear_cache()
    assert len(client._cache) == 0


@pytest.mark.asyncio
async def test_client_invalid():
    client = AbuseIPDBClient()
    with pytest.raises(ValueError):
        await client.check_ip(AbuseIPDBRequest(ip_address="bad-ip"))


@pytest.mark.asyncio
async def test_client_retry():
    client = AbuseIPDBClient(max_retries=2, backoff_factor=0.01)
    calls = {"n": 0}

    async def flaky(ip):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("transient")
        return AbuseIPDBResponse(ip_address=ip, abuse_confidence_score=90)

    client._do_lookup = flaky  # type: ignore
    resp = await client.check_ip(AbuseIPDBRequest(ip_address="1.1.1.1"))
    assert resp.is_malicious is True


def test_rate_limit():
    client = AbuseIPDBClient(rate_limit_per_minute=1)
    import time

    client._request_timestamps = [time.time()]
    assert client._check_rate_limit() is False
    client._request_timestamps = []
    assert client._check_rate_limit() is True


@pytest.mark.asyncio
async def test_provider():
    prov = AbuseIPDBProvider(enabled=True)
    assert prov.name == "abuseipdb"
    assert "abuse_confidence" in prov.capabilities()
    prov.initialize()
    assert prov.health_check()["healthy"] is True
    ind = await prov.lookup_ip("203.0.113.1")
    assert ind is not None
    assert ind.provider == "abuseipdb"
    assert ind.confidence > 0.5
    # benign
    assert await prov.lookup_ip("8.8.8.8") is None
    # invalid
    assert await prov.lookup_ip("bad") is None
    # disabled
    prov.enabled = False
    assert await prov.lookup_ip("203.0.113.1") is None
    prov.enabled = True
    # unsupported types
    assert await prov.lookup_url("http://example.com") is None
    assert await prov.lookup_domain("example.com") is None
    assert await prov.lookup_hash("abcd") is None
    # request object
    class Req:
        ioc = "203.0.113.1"

    assert await prov.lookup_ip(Req()) is not None  # type: ignore
    prov.shutdown()
    assert prov._initialized is False


@pytest.mark.asyncio
async def test_provider_ipv6():
    prov = AbuseIPDBProvider(enabled=True)
    ind = await prov.lookup_ip("2001:db8::1")
    assert ind is not None
    assert ind.indicator_type.value == "ipv6"


@pytest.mark.asyncio
async def test_provider_graceful():
    prov = AbuseIPDBProvider(enabled=True)

    async def fail(*a, **kw):
        raise RuntimeError("boom")

    prov._client.check_ip = fail  # type: ignore
    assert await prov.lookup_ip("203.0.113.1") is None
    assert prov._error_count >= 1


def test_provider_dict():
    prov = AbuseIPDBProvider(api_key="k")
    assert prov.to_dict()["api_key_configured"] is True
    assert AbuseIPDBProvider.from_dict({"api_key": "k"})._api_key == "k"
