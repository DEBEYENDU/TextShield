"""Research repositories."""

from __future__ import annotations
from typing import Dict, List
from .models import ResearchRequest, Evidence, KnowledgeItem, ResearchReport
from .enums import ResearchState


class ResearchRepository:
    def __init__(self):
        self._requests: Dict[str, ResearchRequest] = {}
        self._evidence: Dict[str, List[Evidence]] = {}
        self._knowledge: Dict[str, List[KnowledgeItem]] = {}
        self._reports: Dict[str, ResearchReport] = {}

    def create_request(self, req: ResearchRequest) -> str:
        self._requests[req.research_id] = req
        return req.research_id

    def get_request(self, research_id: str) -> ResearchRequest | None:
        return self._requests.get(research_id)

    def update_state(self, research_id: str, state: ResearchState) -> None:
        if research_id in self._requests:
            self._requests[research_id].status = state

    def add_evidence(self, evidence: Evidence) -> None:
        self._evidence.setdefault(evidence.research_id, []).append(evidence)

    def get_evidence(self, research_id: str) -> List[Evidence]:
        return self._evidence.get(research_id, [])

    def add_knowledge(self, item: KnowledgeItem) -> None:
        self._knowledge.setdefault(item.research_id, []).append(item)

    def get_knowledge(self, research_id: str) -> List[KnowledgeItem]:
        return self._knowledge.get(research_id, [])

    def save_report(self, report: ResearchReport) -> None:
        self._reports[report.research_id] = report

    def get_report(self, research_id: str) -> ResearchReport | None:
        return self._reports.get(research_id)
