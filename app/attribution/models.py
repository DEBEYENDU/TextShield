"""Attribution data models."""

from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


class ActorProfile(BaseModel):
    id: str
    name: str
    aliases: List[str] = []
    types: List[str] = []
    confidence: float = 0.0
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    ttp_fingerprints: Dict[str, float] = {}
    infrastructure_fingerprints: Dict[str, float] = {}
    linguistic_fingerprints: Dict[str, float] = {}
    evidence_count: int = 0
    status: str = "HYPOTHESIZED"


class InfrastructureNode(BaseModel):
    id: str
    type: str
    normalized_value: str
    display_value: str
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    usage_count: int = 0
    associated_actors: List[str] = []
    associated_campaigns: List[str] = []
    reputation_score: float = 0.0


class EvidenceItem(BaseModel):
    id: str
    type: str
    source_id: str
    target_id: str
    confidence: float
    weight: float
    created_at: datetime
    metadata: Dict = {}


class Hypothesis(BaseModel):
    id: str
    actor_id: str
    campaign_id: str
    confidence: float
    evidence: List[EvidenceItem] = []
    reasoning: str = ""
    created_at: datetime
    status: str = "ACTIVE"


class AttributionResult(BaseModel):
    message_id: str
    actor_hypotheses: List[Hypothesis] = []
    infrastructure_links: List[InfrastructureNode] = []
    timeline: List[Dict] = []
    confidence: float = 0.0
    explanation: str = ""
    created_at: datetime = datetime.utcnow()
