"""Tests for research repository."""

from app.research.repository import ResearchRepository
from app.research.models import ResearchRequest, Evidence
from app.research.enums import ResearchType, ResearchState, EvidenceType, SourceType


def test_repository_crud():
    repo = ResearchRepository()
    req = ResearchRequest(research_id="r1", request_type=ResearchType.IOC_ENRICHMENT, target="example.com", scope="domain")
    repo.create_request(req)
    assert repo.get_request("r1") is not None
    repo.update_state("r1", ResearchState.PLANNED)
    assert repo.get_request("r1").status == ResearchState.PLANNED

    ev = Evidence(evidence_id="e1", research_id="r1", source_id="s1", source_type=SourceType.LOCAL_DATABASE, claim="malicious", observed_value="true", evidence_type=EvidenceType.OBSERVED)
    repo.add_evidence(ev)
    assert len(repo.get_evidence("r1")) == 1
