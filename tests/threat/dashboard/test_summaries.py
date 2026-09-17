from app.analytics.summaries import (
    get_threat_score_distribution,
    get_provider_comparison,
)


def test_threat_score_distribution():
    dist = get_threat_score_distribution()
    assert "labels" in dist
    assert "data" in dist
    assert "background_colors" in dist
    assert len(dist["labels"]) == 4  # Low, Medium, High, Critical
    assert len(dist["data"]) == 4
    assert len(dist["background_colors"]) == 4


def test_provider_comparison():
    result = get_provider_comparison("http://example.com")
    assert "ioc_value" in result
    assert "providers" in result
    assert "agreement" in result
    assert "disagreement" in result
    assert "confidence_range" in result
    assert "google_safe_browsing" in result["providers"]
    assert "virustotal" in result["providers"]
    assert "openphish" in result["providers"]
    for provider in result["providers"].values():
        assert "threat_status" in provider
        assert "confidence" in provider
        assert "latency_ms" in provider