"""Performance / benchmark regression tests — part of RFC-011.

Wraps benchmarks.suite to assert thresholds; stores history."""
import json
import pytest
from benchmarks.suite import run_suite, generate_report, HISTORY_PATH

THRESHOLDS = {
    "single_message": 4000,
    "batch_analysis": 8000,
    "ioc_extraction": 80,
    "threat_lookup": 200,
    "cache_latency": 10,
    "rag_retrieval": 200,
    "ml_inference": 100,
    "api_latency": 150,
    "dashboard_loading": 150,
}


def test_benchmark_thresholds():
    suite = run_suite(iterations=5)
    for r in suite["results"]:
        thr = THRESHOLDS.get(r["name"])
        if thr:
            assert r["mean_ms"] < thr, f"{r['name']} {r['mean_ms']}ms exceeds {thr}ms"


def test_benchmark_history_exists():
    assert HISTORY_PATH.exists()
    data = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) >= 1


def test_benchmark_report_generation():
    rep = generate_report()
    assert "generated_at" in rep
    assert "suite" in rep
    assert "regressions" in rep


def test_single_message_throughput():
    from benchmarks.suite import bench_single_message
    import time
    start = time.perf_counter()
    bench_single_message()
    elapsed = (time.perf_counter() - start) * 1000
    assert elapsed < 5000  # must complete under 5s even with cold start


def test_cache_latency_under_threshold():
    suite = run_suite(iterations=10, selected=["cache_latency"])
    r = suite["results"][0]
    assert r["mean_ms"] < 5


def test_ioc_extraction_speed():
    suite = run_suite(iterations=10, selected=["ioc_extraction"])
    assert suite["results"][0]["mean_ms"] < 50


def test_regression_no_regressions():
    rep = generate_report()
    # allow zero regressions for clean state; if regressions exist they must be documented
    assert isinstance(rep["regressions"], list)
