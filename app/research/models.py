"""Research data models."""

from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
from .enums import ResearchType, ResearchState, EvidenceType, KnowledgeState, ContradictionState, SourceType


class ResearchRequest(BaseModel):
    research_id: str
    request_type: ResearchType
    target: str
    scope: str
    priority: int = 5
    created_at: datetime = datetime.utcnow()
    requested_by: str = "system"
    status: ResearchState = ResearchState.CREATED
    deadline: Optional[datetime] = None
    sources_allowed: List[str] = []
    max_sources: int = 10
    max_depth: int = 3
    max_runtime: int = 600
    privacy_policy: str = "standard"
    confidence_threshold: float = 0.6


class ResearchTask(BaseModel):
    task_id: str
    research_id: str
    task_type: str
    status: str = "PENDING"
    created_at: datetime = datetime.utcnow()
    completed_at: Optional[datetime] = None


class Source(BaseModel):
    source_id: str
    provider: str
    source_type: SourceType
    reliability: float = 0.5
    freshness_days: int = 30
    coverage: str = ""
    historical_accuracy: float = 0.5
    timestamp: datetime = datetime.utcnow()
    provenance: Dict = {}


class Evidence(BaseModel):
    evidence_id: str
    research_id: str
    source_id: str
    source_type: SourceType
    claim: str
    observed_value: str
    entity: Optional[str] = None
    timestamp: datetime = datetime.utcnow()
    reliability: float = 0.5
    freshness: float = 1.0
    confidence: float = 0.5
    provenance: Dict = {}
    evidence_type: EvidenceType = EvidenceType.OBSERVED


class Contradiction(BaseModel):
    contradiction_id: str
    research_id: str
    evidence_id_a: str
    evidence_id_b: str
    claim: str
    state: ContradictionState = ContradictionState.UNRESOLVED
    resolution: Optional[str] = None


class KnowledgeItem(BaseModel):
    knowledge_id: str
    research_id: str
    entity_type: str
    entity_value: str
    attributes: Dict = {}
    confidence: float = 0.5
    state: KnowledgeState = KnowledgeState.DISCOVERED
    provenance: Dict = {}
    created_at: datetime = datetime.utcnow()
    expires_at: Optional[datetime] = None


class ResearchReport(BaseModel):
    report_id: str
    research_id: str
    summary: str
    evidence_summary: List[str] = []
    findings: List[str] = []
    confidence: float = 0.5
    recommendations: List[str] = []
    provenance: Dict = {}
    created_at: datetime = datetime.utcnow()
