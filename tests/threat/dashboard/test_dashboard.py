from app.analytics.dashboards import (
    get_dashboard_summary,
    get_provider_status,
    get_cache_statistics,
    get_execution_metrics,
    get_confidence_breakdown,
    get_threat_history,
)


def test_dashboard_summary():
    summary = get_dashboard_summary()
    assert "total_analyses" in summary
    assert "threat_score_distribution" in summary
    assert "average_confidence" in summary
    assert summary["total_analyses"] > 0


def test_provider_status():
    status = get_provider_status()
    assert "google_safe_browsing" in status
    assert "virustotal" in status
    assert "health" in status["google_safe_browsing"]
    assert "latency_ms" in status["google_safe_browsing"]


def test_cache_statistics():
    cache = get_cache_statistics()
    assert "cache_size" in cache
    assert "hit_ratio" in cache
    assert 0 <= cache["hit_ratio"] <= 1


def test_execution_metrics():
    metrics = get_execution_metrics()
    assert "average_lookup_time_ms" in metrics
    assert "concurrency" in metrics
    assert "queue_depth" in metrics
    assert "retries_total" in metrics
    assert "timeouts" in metrics
    assert "requests_per_second" in metrics


def test_confidence_breakdown():
    breakdown = get_confidence_breakdown()
    assert "threat_intelligence" in breakdown
    assert "hybrid_ml" in breakdown
    assert "llm_reasoning" in breakdown
    total = sum(breakdown.values())
    assert 0.9 <= total <= 1.1  # allow rounding


def test_threat_history():
    hist = get_threat_history(page=1, page_size=10)
    assert "entries" in hist
    assert "total" in hist
    assert len(hist["entries"]) == 10
    assert hist["page"] == 1
    assert hist["total_pages"] > 0