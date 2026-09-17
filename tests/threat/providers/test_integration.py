import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from app.api.v2.routes_threat_providers import router, api_router


def _make_app():
    app = FastAPI()
    app.include_router(router)
    app.include_router(api_router)
    return app


def test_api_openphish():
    app = _make_app()
    client = TestClient(app)
    r = client.get("/v2/threat/providers/openphish")
    assert r.status_code == 200
    data = r.json()
    assert data["provider"] == "openphish"
    assert "metadata" in data
    assert "capabilities" in data
    assert "url_reputation" in data["capabilities"]


def test_api_phishtank():
    app = _make_app()
    client = TestClient(app)
    r = client.get("/v2/threat/providers/phishtank")
    assert r.status_code == 200
    assert r.json()["provider"] == "phishtank"
    assert "phishing_metadata" in r.json()["capabilities"]


def test_api_urlhaus():
    app = _make_app()
    client = TestClient(app)
    r = client.get("/v2/threat/providers/urlhaus")
    assert r.status_code == 200
    assert r.json()["provider"] == "urlhaus"
    assert "malware_url_detection" in r.json()["capabilities"]


def test_api_abuseipdb():
    app = _make_app()
    client = TestClient(app)
    r = client.get("/v2/threat/providers/abuseipdb")
    assert r.status_code == 200
    assert r.json()["provider"] == "abuseipdb"
    assert "abuse_confidence" in r.json()["capabilities"]


def test_api_generic():
    app = _make_app()
    client = TestClient(app)
    r = client.get("/v2/threat/providers/google_safe_browsing")
    assert r.status_code == 200
    assert r.json()["provider"] == "google_safe_browsing"


def test_api_not_found():
    app = _make_app()
    client = TestClient(app)
    r = client.get("/v2/threat/providers/unknown_provider_xyz")
    assert r.status_code == 404


def test_api_prefix_api_v2():
    app = _make_app()
    client = TestClient(app)
    for name in ["openphish", "phishtank", "urlhaus", "abuseipdb"]:
        r = client.get(f"/api/v2/threat/providers/{name}")
        assert r.status_code == 200
        assert r.json()["provider"] == name


def test_api_health_fields():
    app = _make_app()
    client = TestClient(app)
    for name in ["openphish", "phishtank", "urlhaus", "abuseipdb"]:
        data = client.get(f"/v2/threat/providers/{name}").json()
        assert "health" in data
        assert "healthy" in data["health"]
        assert "metadata" in data
        assert data["metadata"]["name"] == name
        assert data["metadata"]["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_integration_all_providers_async():
    from app.threat.providers.openphish import OpenPhishProvider
    from app.threat.providers.phishtank import PhishTankProvider
    from app.threat.providers.urlhaus import URLhausProvider
    from app.threat.providers.abuseipdb import AbuseIPDBProvider

    providers = [OpenPhishProvider(), PhishTankProvider(), URLhausProvider(), AbuseIPDBProvider()]
    for p in providers:
        p.initialize()
        assert p.health_check()["healthy"] is True
        # url providers should handle url; ip provider handles ip
        if p.name in ("openphish", "phishtank", "urlhaus"):
            ind = await p.lookup_url("http://example.com")
            # may be None (benign) but must not raise
            assert ind is None or ind.provider == p.name
        if p.name == "abuseipdb":
            ind = await p.lookup_ip("8.8.8.8")
            assert ind is None  # whitelisted benign
            ind2 = await p.lookup_ip("203.0.113.1")
            assert ind2 is not None and ind2.provider == "abuseipdb"


@pytest.mark.asyncio
async def test_normalization_evidence_never_leaks_response():
    """Provider-specific response must never leave provider layer: ensure provider returns ThreatIndicator not raw Response."""
    from app.threat.providers.openphish import OpenPhishProvider

    prov = OpenPhishProvider()
    ind = await prov.lookup_url("http://openphish-malicious-test.com")
    # Should be ThreatIndicator, not OpenPhishResponse
    assert ind is not None
    assert hasattr(ind, "indicator")
    assert not hasattr(ind, "is_phishing")  # that's Response field
    # Same for other providers
    from app.threat.providers.phishtank import PhishTankProvider
    prov2 = PhishTankProvider()
    ind2 = await prov2.lookup_url("http://phishtank-malicious.com")
    assert ind2 is not None
    assert not hasattr(ind2, "in_database")


def test_provider_rate_limit_exposed_in_metadata():
    from app.threat.providers.openphish import OpenPhishProvider
    p = OpenPhishProvider()
    assert "rate_limit_per_minute" in p.metadata
    assert "max_retries" in p.metadata
