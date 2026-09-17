from app.analytics.history import (
    AnalysisHistory,
    HistoryService,
    get_dashboard_history,
    get_severity_distribution,
)


def test_analysis_history():
    ah = AnalysisHistory()
    ah.add({"id": 1, "severity": "High", "ioc_type": "url"})
    ah.add({"id": 2, "severity": "Low", "ioc_type": "domain"})
    all_records = ah.get_all()
    assert len(all_records) == 2
    filtered = ah.filter(severity="High")
    assert len(filtered) == 1
    assert filtered[0]["id"] == 1


def test_history_service():
    ah = AnalysisHistory()
    ah.add({"id": 1, "timestamp": "2025-01-01T00:00:00+00:00"})
    svc = HistoryService(ah)
    recent = svc.get_recent(hours=48)
    assert len(recent) == 1
    stats = svc.statistics()
    assert "total_analyses" in stats
    assert stats["total_analyses"] == 1


def test_get_dashboard_history():
    hist = get_dashboard_history(page=1, page_size=5)
    assert len(hist["entries"]) == 5
    assert hist["page"] == 1
    assert hist["total_pages"] > 0
    for entry in hist["entries"]:
        assert "ioc_value" in entry
        assert "provider" in entry
        assert "severity" in entry


def test_get_dashboard_history_filtered():
    hist = get_dashboard_history(page=1, page_size=20, severity="High")
    for entry in hist["entries"]:
        assert entry["severity"] == "High"


def test_get_severity_distribution():
    hist = get_dashboard_history(page=1, page_size=50)
    dist = get_severity_distribution(hist["entries"])
    assert "distribution" in dist
    assert "percentages" in dist
    assert "Low" in dist["distribution"]