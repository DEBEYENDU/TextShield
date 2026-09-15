"""Hunting data models."""

from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
from .enums import FindingState, FindingType, HypothesisState, RecommendationState


class Observation(BaseModel):
    observation_id: str
    analysis_id: str
    message_id: str
    timestamp: datetime
    channel: str
    sender_entity: Optional[str] = None
    recipient_entity: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    domain: Optional[str] = None
    url: Optional[str] = None
    ip: Optional[str] = None
    intent: Optional[str] = None
    behavior_profile: Optional[str] = None
    semantic_embedding_id: Optional[str] = None
    threat_evidence: Dict = {}
    campaign_id: Optional[str] = None
    attribution_hypothesis_id: Optional[str] = None
    decision_result: Optional[str] = None
    response_result: Optional[str] = None
    confidence: float = 0.0
    provenance: Dict = {}


class Pattern(BaseModel):
    pattern_id: str
    pattern_type: str
    observed_entities: List[str] = []
    occurrence_count: int = 0
    first_seen: datetime
    last_seen: datetime
    confidence: float = 0.0
    supporting_observations: List[str] = []
    contradictions: List[str] = []
    provenance: Dict = {}


class Anomaly(BaseModel):
    anomaly_id: str
    metric: str
    value: float
    expected_value: float
    z_score: float
    timestamp: datetime
    observations: List[str] = []
    severity: str = "MEDIUM"


class Finding(BaseModel):
    finding_id: str
    finding_type: FindingType
    state: FindingState
    score: float
    confidence: float
    first_seen: datetime
    last_seen: datetime
    observations: List[str] = []
    pattern_id: Optional[str] = None
    evidence: List[Dict] = []
    contradictions: List[Dict] = []
    provenance: Dict = {}
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()


class Hypothesis(BaseModel):
    hypothesis_id: str
    finding_id: str
    description: str
    confidence: float
    evidence: List[Dict] = []
    contradictions: List[Dict] = []
    state: HypothesisState = HypothesisState.DISCOVERED
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()


class Recommendation(BaseModel):
    recommendation_id: str
    finding_id: str
    type: str
    description: str
    evidence_summary: str
    false_positive_assessment: str
    state: RecommendationState = RecommendationState.PROPOSED
    created_at: datetime = datetime.utcnow()
