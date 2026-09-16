"""Tests for research models."""

from app.research.models import ResearchRequest
from app.research.enums import ResearchType, ResearchState


def test_research_request():
    req = ResearchRequest(
        research_id="r1",
        request_type=ResearchType.IOC_ENRICHMENT,
        target="example.com",
        scope="domain"
    )
    assert req.status == ResearchState.CREATED
    assert req.request_type == ResearchType.IOC_ENRICHMENT
