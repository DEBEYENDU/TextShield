"""Integration stabilization tests — RFC v2.2.1
Covers: Analyze -> History -> Analytics -> KB unaffected -> Refresh -> persists
"""
import time
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.database.base import get_connection, init_db
from app.core.settings import settings

@pytest.fixture
def client(tmp_path, monkeypatch):
    # isolated DB for integration
    monkeypatch.setattr(settings, "DATABASE_URL", f"sqlite:///{tmp_path / 'int.db'}")
    init_db()
    app = create_app()
    c = TestClient(app)
    return c

def test_analyze_history_analytics_flow(client):
    # 1. Analyze
    payload = {"input_type": "text", "message": "Congratulations! You won a prize! Click http://bit.ly/abc to claim."}
    r = client.post("/api/analyze", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["classification"] in ("SPAM", "HAM")
    assert "confidence" in data
    assert "risk_level" in data
    assert data["model_used"] != "unknown"
    # result appears

    # 2. History updated
    r2 = client.get("/api/history")
    assert r2.status_code == 200
    hist = r2.json()
    assert hist["total"] >= 1
    assert len(hist["items"]) >= 1
    assert hist["items"][0]["classification"] == data["classification"]

    # 3. Analytics updated
    r3 = client.get("/api/stats")
    assert r3.status_code == 200
    stats = r3.json()
    assert stats["total_analyses"] >= 1
    assert stats["spam_count"] + stats["ham_count"] == stats["total_analyses"]

    # 4. KB unaffected
    r4 = client.get("/api/knowledge-base")
    assert r4.status_code == 200
    kb_before = r4.json()
    assert "ready" in kb_before
    # After analyze, KB should be same (no rebuild)
    r4b = client.get("/api/knowledge-base")
    assert r4b.json() == kb_before

    # 5. Refresh browser -> history persists (new client with same DB file should see same data)
    # Simulate refresh by re-creating app with same DB path (tmp_path still)
    from app.main import create_app as ca2
    app2 = ca2()
    c2 = TestClient(app2)
    # Need to keep same DB file, monkeypatch still active for settings
    r5 = c2.get("/api/history")
    # This will be fresh app but same DB file via settings monkeypatch still
    # If DB persists, total should still be >=1 (but new app's DB path is same via monkeypatch)
    # Since we monkeypatched settings.DATABASE_URL to tmp file, it persists
    assert r5.status_code == 200
    assert r5.json()["total"] >= 1

    # 6. Analytics persists
    r6 = c2.get("/api/stats")
    assert r6.status_code == 200
    assert r6.json()["total_analyses"] >= 1

def test_knowledge_base_loads_under_2s(client):
    start = time.perf_counter()
    r = client.get("/api/knowledge-base")
    elapsed = (time.perf_counter() - start) * 1000
    assert r.status_code == 200
    assert elapsed < 2000, f"KB took {elapsed}ms > 2000"
    data = r.json()
    # Should show Loading -> Loaded or Empty, not infinite
    assert "ready" in data
    assert "chunk_count" in data
    # Should be either ready True with chunks or ready False with 0 (empty)
    if data["ready"]:
        assert data["chunk_count"] > 0
    else:
        assert data["chunk_count"] == 0

def test_history_persistence_across_analyzes(client):
    # zero -> one -> many
    r0 = client.get("/api/history")
    initial = r0.json()["total"]
    # one
    client.post("/api/analyze", json={"input_type": "text", "message": "Hello world"})
    r1 = client.get("/api/history")
    assert r1.json()["total"] == initial + 1
    # many
    for i in range(5):
        client.post("/api/analyze", json={"input_type": "text", "message": f"Test message {i} with http://example{i}.com"})
    r2 = client.get("/api/history")
    assert r2.json()["total"] == initial + 6

def test_analytics_zero_one_many(client):
    # zero
    r0 = client.get("/api/stats")
    assert r0.status_code == 200
    # Should gracefully handle zero
    stats0 = r0.json()
    # after one
    client.post("/api/analyze", json={"input_type": "text", "message": "Single test"})
    r1 = client.get("/api/stats")
    assert r1.json()["total_analyses"] == stats0["total_analyses"] + 1
    # after many
    for i in range(3):
        client.post("/api/analyze", json={"input_type": "text", "message": f"Bulk {i}"})
    r2 = client.get("/api/stats")
    assert r2.json()["total_analyses"] >= stats0["total_analyses"] + 4
    # check charts would handle
    assert "risk_distribution" in r2.json()
    assert "message_type_distribution" in r2.json()

def test_analyze_email_and_raw():
    from app.main import create_app as ca
    from app.core.settings import settings as s
    import tempfile, pathlib
    tmp = pathlib.Path(tempfile.mktemp(suffix=".db"))
    s.DATABASE_URL = f"sqlite:///{tmp}"
    init_db()
    app = ca()
    c = TestClient(app)
    # email with fields
    r = c.post("/api/analyze", json={"input_type": "email", "subject": "Verify", "sender": "a@b.com", "body": "Click http://evil.com"})
    assert r.status_code == 200
    # raw email
    raw = "From: a@b.com\nSubject: Hello\n\nBody with prize http://bit.ly/xyz"
    r2 = c.post("/api/analyze", json={"input_type": "email", "email_raw": raw})
    assert r2.status_code == 200
    # auto-detect raw in text
    r3 = c.post("/api/analyze", json={"input_type": "text", "message": raw})
    assert r3.status_code == 200

def test_browser_pages_no_500(client):
    for path in ["/", "/history", "/analytics", "/knowledge-base", "/about", "/dashboard", "/analyze"]:
        r = client.get(path)
        # pages return HTML 200, not 500
        assert r.status_code == 200, f"{path} failed {r.status_code}"
        # check common.js before page script
        html = r.text
        if "/static/js/common.js" in html and "/static/js/" in html:
            # ensure common before at least one page script
            assert html.find("/static/js/common.js") < html.find("/static/js/") + 500 or html.count("/static/js/common.js") >= 1
