from app.analytics.metrics import (
    MetricKeys,
    MetricsRecord,
    MetricsSummary,
    MetricsEngine,
    get_execution_metrics,
)


def test_metric_keys():
    keys = MetricKeys()
    assert keys.average_lookup_time_ms == "average_lookup_time_ms"
    assert keys.concurrency == "concurrency"


def test_metrics_record():
    rec = MetricsRecord(
        timestamp="2025-01-01T00:00:00+00:00",
        average_lookup_time_ms=100.0,
        concurrency=10,
        queue_depth=3,
        retries_total=5,
        timeouts=0,
        requests_per_second=500.0,
    )
    assert rec.average_lookup_time_ms == 100.0
    assert rec.concurrency == 10


def test_metrics_engine():
    engine = MetricsEngine()
    engine.record(MetricsRecord(
        timestamp="2025-01-01T00:00:00+00:00",
        average_lookup_time_ms=100.0,
        concurrency=10,
        queue_depth=3,
        retries_total=5,
        timeouts=0,
        requests_per_second=500.0,
    ))
    summary = engine.summary()
    assert summary.average_lookup_time_ms == 100.0
    assert summary.concurrency == 10.0
    assert summary.records_count == 1


def test_metrics_summary():
    rec = MetricsRecord(
        timestamp="2025-01-01T00:00:00+00:00",
        average_lookup_time_ms=200.0,
        concurrency=5,
        queue_depth=1,
        retries_total=2,
        timeouts=1,
        requests_per_second=300.0,
    )
    summary = MetricsSummary(records_count=1, **rec._asdict())
    assert summary.average_lookup_time_ms == 200.0
    assert summary.records_count == 1


def test_get_execution_metrics():
    metrics = get_execution_metrics()
    assert metrics["average_lookup_time_ms"] == 87
    assert metrics["concurrency"] == 12
    assert metrics["retries_total"] == 342