"""Tests for request manager."""

from app.research.request_manager import ResearchRequestManager
from app.research.repository import ResearchRepository

def test_create_request():
    mgr = ResearchRequestManager(ResearchRepository())
    rid = mgr.create_request("IOC_ENRICHMENT", "example.com", "domain")
    req = mgr.get_request(rid)
    assert req is not None
    assert req.target == "example.com"
